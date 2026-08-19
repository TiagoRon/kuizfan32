"""Proveedor de IA basado en Groq (emergencia/fallback).

Implementa la interfaz IAIProvider para comunicarse con la API de Groq
usando httpx, solicitando siempre respuestas en formato JSON.
"""

from __future__ import annotations

import json
import logging
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
from quiz_generator.core.enums import Difficulty, QuizType
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

    @retry(
        retry=retry_if_exception_type(AIProviderError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _call_groq(self, prompt: str) -> str:
        """Llama a la API de Groq usando httpx."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        # Models to try on Groq (current active models)
        models_to_try = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "gemma2-9b-it",
            "qwen-2.5-32b",
            "deepseek-r1-distill-llama-70b",
        ]

        last_error = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            for current_model in models_to_try:
                # Probar primero con response_format json_object, si falla probar estándar
                for use_json_format in (True, False):
                    payload: dict[str, Any] = {
                        "model": current_model,
                        "messages": [
                            {"role": "system", "content": "You are a professional quiz generator. You MUST ONLY respond with a valid JSON object. No markdown formatting, no explanations."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": self._settings.ia.temperatura,
                        "max_tokens": self._settings.ia.max_tokens,
                    }
                    if use_json_format:
                        payload["response_format"] = {"type": "json_object"}

                    try:
                        response = await client.post(
                            self._base_url,
                            headers=headers,
                            json=payload,
                        )

                        if response.status_code == 429:
                            raise AIRateLimitError("Groq")

                        if response.status_code in (401, 403):
                            raise MissingAPIKeyError("Groq", "GROQ_API_KEY")

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

                        return content

                    except httpx.HTTPStatusError as e:
                        error_body = e.response.text
                        last_error = f"HTTP {e.response.status_code} en {current_model}: {error_body}"
                        logger.warning("Groq modelo '%s' (json_mode=%s) falló: %s", current_model, use_json_format, last_error)
                        if e.response.status_code == 429:
                            raise AIRateLimitError("Groq") from e
                        # Si es 400 y estábamos usando json_format, intentamos sin json_format antes de cambiar de modelo
                        if e.response.status_code == 400 and use_json_format:
                            continue
                        break
                    except httpx.RequestError as e:
                        last_error = e
                        logger.warning("Error de red con Groq modelo '%s': %s", current_model, e)
                        break

        raise AIProviderError("Groq", f"Todos los modelos de Groq fallaron. Último error: {last_error}")

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        """Parsea la respuesta JSON de Groq."""
        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            clean = "\n".join(lines)

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
        # Simplificación de la conversión
        from quiz_generator.core.enums import ViralTrigger
        try:
            return ViralTrigger(trigger_str.lower())
        except ValueError:
            return ViralTrigger.CURIOSITY

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
