"""Proveedor de IA basado en Groq (emergencia/fallback).

Implementa la interfaz IAIProvider para comunicarse con la API de Groq
usando httpx, solicitando siempre respuestas en formato JSON.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import re
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from quiz_generator.ai.prompt_manager import PromptManager
from quiz_generator.config import Settings
from quiz_generator.core.enums import Difficulty, QuizType, ViralTrigger
from quiz_generator.core.exceptions import (
    AIInvalidResponseError,
    AIProviderError,
    AIRateLimitError,
    MissingAPIKeyError,
)
from quiz_generator.core.interfaces import IAIProvider
from quiz_generator.core.models import (
    Answer,
    Hook,
    Question,
    Quiz,
    QuizMetadata,
)

logger = logging.getLogger(__name__)

# Mapa de QuizType a nombres legibles para los prompts
_QUIZ_TYPE_DISPLAY: dict[QuizType, str] = {
    QuizType.TRIVIA: "Trivia de Cultura General",
    QuizType.TRUE_OR_FALSE: "Verdadero o Falso",
    QuizType.WOULD_YOU_RATHER: "¿Qué Prefieres?",
    QuizType.EMOJI_QUIZ: "Emoji Quiz — Adivina con Emojis",
    QuizType.GUESS_FLAG: "Adivina la Bandera",
    QuizType.GUESS_POKEMON: "Adivina el Pokémon",
    QuizType.GUESS_CHARACTER: "Adivina el Personaje",
    QuizType.GUESS_COUNTRY: "Adivina el País",
    QuizType.GUESS_LOGO: "Adivina el Logo",
    QuizType.GUESS_MOVIE: "Adivina la Película",
    QuizType.GUESS_SONG: "Adivina la Canción",
    QuizType.GUESS_ANIMAL: "Adivina el Animal",
    QuizType.GUESS_BRAND: "Adivina la Marca",
    QuizType.GUESS_FOOD: "Adivina la Comida",
    QuizType.GUESS_CELEBRITY: "Adivina la Celebridad",
    QuizType.GUESS_FOOTBALL_PLAYER: "Adivina el Futbolista",
    QuizType.GUESS_CAR: "Adivina el Auto",
    QuizType.GUESS_VOICE: "Adivina la Voz",
    QuizType.GUESS_SOUND: "Adivina el Sonido",
    QuizType.WHO_IS_MORE: "¿Quién es más...?",
    QuizType.FAST_CHOICE: "Decisión Rápida",
    QuizType.SURVIVAL_CHOICE: "Elección de Supervivencia",
    QuizType.MEMORY_CHALLENGE: "Desafío de Memoria",
    QuizType.SPOT_THE_DIFFERENCE: "Encuentra la Diferencia",
    QuizType.SPOT_THE_MISTAKE: "Encuentra el Error",
    QuizType.BRAIN_TEASER: "Acertijo Mental",
    QuizType.IMPOSSIBLE_QUIZ: "Quiz Imposible",
    QuizType.IQ_TEST: "Test de IQ",
    QuizType.RIDDLE: "Adivinanza",
    QuizType.OPTICAL_ILLUSION: "Ilusión Óptica",
}


class GroqProvider(IAIProvider):
    """Proveedor de IA que usa Groq para generar contenido de emergencia."""

    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise MissingAPIKeyError("Groq", "GROQ_API_KEY")

        self._settings = settings
        self._api_key = settings.groq_api_key
        self._prompt_manager = PromptManager()
        self._tokens_used = 0
        self._base_url = "https://api.groq.com/openai/v1/chat/completions"

    @property
    def tokens_used(self) -> int:
        return self._tokens_used

    async def _get_available_models(
        self, client: httpx.AsyncClient, headers: dict[str, str]
    ) -> list[str]:
        """Consulta dinámicamente los modelos de texto activos disponibles en Groq."""
        try:
            resp = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers=headers,
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                raw_models = data.get("data", [])
                excluded_keywords = (
                    "whisper", "tts", "guard", "vision", "embed", "prompt-guard",
                    "orpheus", "canopylabs", "audio", "speech", "distil-whisper",
                )
                models = [
                    m["id"]
                    for m in raw_models
                    if isinstance(m, dict)
                    and "id" in m
                    and not m.get("deprecated", False)
                    and not any(x in m["id"].lower() for x in excluded_keywords)
                ]
                if models:
                    # Priorizar modelos rápidos y con alto límite de TPM primero
                    priority = [
                        "llama-3.1-8b-instant",
                        "llama-3.3-70b-versatile",
                        "llama-3.1-70b-versatile",
                        "mixtral-8x7b-32768",
                        "gemma2-9b-it",
                        "deepseek-r1-distill-llama-70b",
                        "qwen-2.5-32b",
                    ]
                    def score(m_id: str) -> int:
                        for i, p in enumerate(priority):
                            if p in m_id.lower():
                                return i
                        return 99
                    models.sort(key=score)
                    logger.info("Modelos de texto activos detectados en Groq: %s", models)
                    return models
        except Exception as e:
            logger.warning("No se pudo obtener lista dinámica de modelos de Groq: %s", e)

        return [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "deepseek-r1-distill-llama-70b",
        ]

    @retry(
        retry=retry_if_exception_type(AIProviderError),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=3, max=30),
        reraise=True,
    )
    async def _call_groq(self, prompt: str) -> str:
        """Llama a la API de Groq usando httpx."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        errors_log: list[str] = []
        last_retry_after = 4.0

        async with httpx.AsyncClient(timeout=60.0) as client:
            models_to_try = await self._get_available_models(client, headers)
            max_tokens = min(self._settings.ia.max_tokens, 2500)

            for current_model in models_to_try:
                payload: dict[str, Any] = {
                    "model": current_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a professional quiz generator. "
                                "You MUST ONLY respond with a single valid JSON object. "
                                "Do NOT include any markdown formatting, explanations, or extra text."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": self._settings.ia.temperatura,
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"},
                }

                try:
                    response = await client.post(
                        self._base_url,
                        headers=headers,
                        json=payload,
                    )

                    if response.status_code == 429:
                        retry_header = response.headers.get("retry-after", "")
                        retry_after = 4.0
                        if retry_header:
                            with contextlib.suppress(ValueError):
                                retry_after = float(retry_header)
                        else:
                            match = re.search(r"try again in (\d+(?:\.\d+)?)s?", response.text, re.IGNORECASE)
                            if match:
                                with contextlib.suppress(ValueError):
                                    retry_after = float(match.group(1))

                        last_retry_after = max(retry_after, 2.0)
                        err_msg = f"{current_model}: RateLimit 429 (esperar {last_retry_after}s)"
                        errors_log.append(err_msg)
                        logger.warning(
                            "Groq modelo '%s' alcanzó rate limit. Esperando %.1fs antes de probar siguiente modelo...",
                            current_model, last_retry_after,
                        )
                        await asyncio.sleep(min(last_retry_after, 6.0))
                        continue

                    if response.status_code in (401, 403):
                        raise MissingAPIKeyError("Groq", "GROQ_API_KEY (clave inválida o no autorizada)")

                    if response.status_code == 400 and "response_format" in response.text:
                        # Si el modelo específico no soporta response_format json_object, reintentar sin él
                        payload.pop("response_format", None)
                        response = await client.post(
                            self._base_url,
                            headers=headers,
                            json=payload,
                        )

                    response.raise_for_status()

                    data = response.json()

                    # Token usage
                    if "usage" in data:
                        self._tokens_used += data["usage"].get("total_tokens", 0)

                    choices = data.get("choices", [])
                    if not choices:
                        raise AIInvalidResponseError("Groq", "No hay opciones en la respuesta")

                    content = choices[0].get("message", {}).get("content", "")
                    if not content:
                        raise AIInvalidResponseError("Groq", "Contenido vacío")

                    # Validar que el JSON sea parseable antes de aceptar esta respuesta
                    try:
                        self._parse_json_response(content)
                        return content
                    except Exception as json_err:
                        err_msg = f"{current_model}: JSON incompleto/inválido ({json_err})"
                        errors_log.append(err_msg)
                        logger.warning("Groq modelo '%s' retornó JSON inválido. Probando siguiente modelo...", current_model)
                        continue

                except httpx.HTTPStatusError as e:
                    error_body = e.response.text
                    err_msg = f"{current_model} (status {e.response.status_code}): {error_body}"
                    errors_log.append(err_msg)
                    logger.warning("Groq modelo '%s' falló: %s", current_model, err_msg)
                    if e.response.status_code == 429:
                        await asyncio.sleep(min(last_retry_after, 6.0))
                        continue
                    continue
                except httpx.RequestError as e:
                    err_msg = f"{current_model} (red): {e}"
                    errors_log.append(err_msg)
                    logger.warning("Error de red con Groq modelo '%s': %s", current_model, e)
                    continue

        # Si todos los modelos dieron 429, pausamos antes del siguiente intento de tenacity
        if any("429" in err or "ratelimit" in err.lower() for err in errors_log):
            logger.info("Esperando %.1f segundos antes de reintentar Groq...", last_retry_after)
            await asyncio.sleep(min(last_retry_after, 10.0))
            raise AIRateLimitError("Groq", retry_after=float(last_retry_after))

        raise AIProviderError("Groq", "Todos los modelos de Groq fallaron:\n" + "\n".join(errors_log))

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        """Parsea y repara la respuesta JSON de Groq si es necesario."""
        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            clean = "\n".join(lines).strip()

        # 1. Intento directo
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            pass

        # 2. Extraer bloque {...}
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(clean[start : end + 1])
            except json.JSONDecodeError:
                pass

        # 3. Intentar reparar JSON truncado
        if start != -1:
            candidate = clean[start:]
            if candidate.count('"') % 2 != 0:
                candidate += '"'
            open_braces = candidate.count("{") - candidate.count("}")
            open_brackets = candidate.count("[") - candidate.count("]")
            candidate += "]" * max(0, open_brackets)
            candidate += "}" * max(0, open_braces)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # Si falla todo, lanzar error descriptivo
        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            raise AIInvalidResponseError(
                "Groq",
                f"JSON inválido: {e}. Respuesta: {clean[:200]}...",
            ) from e

    async def generate_quiz(
        self,
        quiz_type: QuizType,
        difficulty: Difficulty,
        num_questions: int,
        language: str = "es",
        topic: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Quiz:
        """Genera un quiz completo llamando a Groq."""
        context = context or {}
        instrucciones_plugin = context.get("instrucciones_plugin", "Sin instrucciones adicionales.")

        prompt = self._prompt_manager.render(
            "quiz_generation.j2",
            quiz_type_display=_QUIZ_TYPE_DISPLAY.get(quiz_type, str(quiz_type)),
            dificultad=difficulty.value,
            num_preguntas=num_questions,
            idioma=language,
            tema=topic,
            instrucciones_plugin=instrucciones_plugin,
            preguntas_existentes=context.get("preguntas_existentes", []),
            tendencias=context.get("tendencias"),
        )

        logger.info("Generando quiz con GROQ (emergencia): tipo=%s", quiz_type)

        response_text = await self._call_groq(prompt)
        data = self._parse_json_response(response_text)
        return self._build_quiz(data, quiz_type, difficulty, language)

    def _parse_viral_trigger(self, trigger_str: str) -> Any:
        mapping = {
            "curiosidad": ViralTrigger.CURIOSIDAD,
            "curiosity": ViralTrigger.CURIOSIDAD,
            "sorpresa": ViralTrigger.SORPRESA,
            "surprise": ViralTrigger.SORPRESA,
            "competencia": ViralTrigger.COMPETENCIA,
            "competition": ViralTrigger.COMPETENCIA,
            "humor": ViralTrigger.HUMOR,
            "nostalgia": ViralTrigger.NOSTALGIA,
            "orgullo": ViralTrigger.ORGULLO,
            "pride": ViralTrigger.ORGULLO,
            "fomo": ViralTrigger.FOMO,
            "recompensa": ViralTrigger.RECOMPENSA,
            "reward": ViralTrigger.RECOMPENSA,
            "desafio": ViralTrigger.DESAFIO,
            "challenge": ViralTrigger.DESAFIO,
            "identidad": ViralTrigger.IDENTIDAD,
            "identity": ViralTrigger.IDENTIDAD,
            "urgencia": ViralTrigger.URGENCIA,
            "urgency": ViralTrigger.URGENCIA,
        }
        return mapping.get(trigger_str.lower().strip(), ViralTrigger.CURIOSIDAD)

    def _build_quiz(
        self,
        data: dict[str, Any],
        quiz_type: QuizType,
        difficulty: Difficulty,
        language: str,
    ) -> Quiz:
        """Construye un Quiz a partir del JSON de Groq."""
        hook_data = data.get("hook", {})
        hook = Hook(
            texto=hook_data.get("texto", "¿Puedes con este quiz? 🧠"),
            tipo=self._parse_viral_trigger(hook_data.get("tipo", "curiosidad")),
            emoji=hook_data.get("emoji"),
        )

        preguntas = []
        for q_data in data.get("preguntas", []):
            respuestas = [
                Answer(
                    texto=a.get("texto", ""),
                    es_correcta=a.get("es_correcta", False),
                    explicacion=a.get("explicacion"),
                    emoji=a.get("emoji"),
                )
                for a in q_data.get("respuestas", [])
            ]
            # Parse dificultad de forma segura
            raw_diff = q_data.get("dificultad")
            try:
                diff_val = Difficulty(raw_diff) if raw_diff else difficulty
            except (ValueError, KeyError):
                diff_val = difficulty

            preguntas.append(
                Question(
                    texto=q_data.get("texto", ""),
                    respuestas=respuestas,
                    dificultad=diff_val,
                    tiempo_segundos=q_data.get("tiempo_segundos", 10),
                    curiosidad=q_data.get("curiosidad"),
                    imagen_url=q_data.get("imagen_url"),
                    emoji_pista=q_data.get("emoji_pista"),
                    categoria=q_data.get("categoria"),
                )
            )

        meta_data = data.get("metadata", {})
        metadata = QuizMetadata(
            titulo=meta_data.get("titulo", f"Quiz {quiz_type.value}"),
            descripcion=meta_data.get("descripcion", ""),
            hashtags=meta_data.get("hashtags", []),
            prompt_miniatura=meta_data.get("prompt_miniatura"),
            cta=meta_data.get("cta"),
        )

        triggers = [
            self._parse_viral_trigger(t)
            for t in data.get("disparadores_virales", [])
        ]

        return Quiz(
            tipo=quiz_type,
            dificultad=difficulty,
            idioma=language,
            hook=hook,
            preguntas=preguntas,
            metadata=metadata,
            disparadores_virales=triggers,
        )

    async def generate_hooks(
        self,
        quiz_type: QuizType,
        count: int = 5,
        language: str = "es",
    ) -> list[str]:
        raise NotImplementedError("Generación de hooks aislada no implementada en Groq fallback")

    async def generate_metadata(
        self,
        quiz: Quiz,
        language: str = "es",
    ) -> QuizMetadata:
        raise NotImplementedError("Generación de metadata aislada no implementada en Groq fallback")

    async def analyze_trends(
        self,
        category: str,
        language: str = "es",
    ) -> dict[str, Any]:
        raise NotImplementedError("Análisis de tendencias no implementado en Groq fallback")
