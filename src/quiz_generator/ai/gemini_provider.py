"""Proveedor de IA basado en Google Gemini.

Implementa la interfaz IAIProvider usando el SDK de Google GenAI
para generar quizzes, hooks y metadatos mediante Gemini.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from google import genai
from google.genai import types as genai_types
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


class GeminiProvider(IAIProvider):
    """Proveedor de IA que usa Google Gemini para generar contenido.

    Características:
    - Usa Structured Outputs (JSON mode) para respuestas parseables.
    - Reintento automático con backoff exponencial.
    - Fallback a modelo alternativo si el principal falla.
    - Tracking de uso de tokens.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.gemini_api_key:
            raise MissingAPIKeyError("Gemini", "GEMINI_API_KEY")

        self._settings = settings
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.ia.modelo
        self._fallback_model = settings.ia.modelo_fallback
        self._prompt_manager = PromptManager()
        self._tokens_used = 0

    @property
    def tokens_used(self) -> int:
        """Total de tokens consumidos en esta sesión."""
        return self._tokens_used

    @retry(
        retry=retry_if_exception_type(AIProviderError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _call_gemini(
        self,
        prompt: str,
        model: str | None = None,
    ) -> str:
        """Envía un prompt a Gemini y retorna la respuesta en texto.

        Incluye reintentos automáticos y manejo de errores.
        """
        target_model = model or self._model

        try:
            response = self._client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=self._settings.ia.temperatura,
                    max_output_tokens=self._settings.ia.max_tokens,
                    response_mime_type="application/json",
                ),
            )

            if not response.text:
                raise AIInvalidResponseError("Gemini", "Respuesta vacía del modelo")

            # Tracking de tokens
            if response.usage_metadata:
                self._tokens_used += (
                    response.usage_metadata.prompt_token_count
                    + response.usage_metadata.candidates_token_count
                )

            return response.text

        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "quota" in error_str or "429" in error_str:
                raise AIRateLimitError("Gemini") from e
            if "api key" in error_str or "401" in error_str or "403" in error_str:
                raise MissingAPIKeyError("Gemini", "GEMINI_API_KEY") from e
            raise AIProviderError("Gemini", str(e)) from e

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        """Parsea la respuesta JSON de Gemini, manejando bloques de código."""
        clean = text.strip()

        # Remover bloques de código markdown si los hay
        if clean.startswith("```"):
            lines = clean.split("\n")
            # Remover primera y última línea (```json y ```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            clean = "\n".join(lines)

        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            raise AIInvalidResponseError(
                "Gemini",
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
        """Genera un quiz completo con preguntas, respuestas y hook."""
        context = context or {}

        # Obtener instrucciones específicas del plugin si existen
        instrucciones_plugin = context.get("instrucciones_plugin", "Sin instrucciones adicionales.")

        # Renderizar el prompt
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

        logger.info(
            "Generando quiz: tipo=%s, dificultad=%s, preguntas=%d",
            quiz_type, difficulty, num_questions,
        )

        # Llamar a Gemini
        response_text = await self._call_gemini(prompt)
        data = self._parse_json_response(response_text)

        # Construir el modelo de dominio
        return self._build_quiz(data, quiz_type, difficulty, language)

    def _build_quiz(
        self,
        data: dict[str, Any],
        quiz_type: QuizType,
        difficulty: Difficulty,
        language: str,
    ) -> Quiz:
        """Construye un Quiz a partir del JSON parseado de la respuesta de IA."""
        # Hook
        hook_data = data.get("hook", {})
        hook = Hook(
            texto=hook_data.get("texto", "¿Puedes con este quiz? 🧠"),
            tipo=self._parse_viral_trigger(hook_data.get("tipo", "curiosidad")),
            emoji=hook_data.get("emoji"),
        )

        # Preguntas
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
            preguntas.append(
                Question(
                    texto=q_data.get("texto", ""),
                    respuestas=respuestas,
                    dificultad=Difficulty(q_data.get("dificultad", difficulty.value)),
                    tiempo_segundos=q_data.get("tiempo_segundos", 10),
                    curiosidad=q_data.get("curiosidad"),
                    imagen_url=q_data.get("imagen_url"),
                    emoji_pista=q_data.get("emoji_pista"),
                    categoria=q_data.get("categoria"),
                )
            )

        # Metadata
        meta_data = data.get("metadata", {})
        metadata = QuizMetadata(
            titulo=meta_data.get("titulo", f"Quiz {quiz_type.value}"),
            descripcion=meta_data.get("descripcion", ""),
            hashtags=meta_data.get("hashtags", []),
            prompt_miniatura=meta_data.get("prompt_miniatura"),
            cta=meta_data.get("cta"),
        )

        # Disparadores virales
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

    @staticmethod
    def _parse_viral_trigger(value: str) -> ViralTrigger:
        """Convierte un string a ViralTrigger, con fallback a CURIOSIDAD."""
        mapping = {
            "curiosidad": ViralTrigger.CURIOSIDAD,
            "sorpresa": ViralTrigger.SORPRESA,
            "competencia": ViralTrigger.COMPETENCIA,
            "humor": ViralTrigger.HUMOR,
            "nostalgia": ViralTrigger.NOSTALGIA,
            "orgullo": ViralTrigger.ORGULLO,
            "fomo": ViralTrigger.FOMO,
            "recompensa": ViralTrigger.RECOMPENSA,
            "desafio": ViralTrigger.DESAFIO,
            "identidad": ViralTrigger.IDENTIDAD,
            "urgencia": ViralTrigger.URGENCIA,
        }
        return mapping.get(value.lower().strip(), ViralTrigger.CURIOSIDAD)

    async def generate_hooks(
        self,
        quiz_type: QuizType,
        count: int = 5,
        language: str = "es",
    ) -> list[str]:
        """Genera hooks virales para un tipo de quiz."""
        prompt = self._prompt_manager.render(
            "hook_generation.j2",
            quiz_type_display=_QUIZ_TYPE_DISPLAY.get(quiz_type, str(quiz_type)),
            count=count,
            hooks_existentes=[],
        )

        response_text = await self._call_gemini(prompt)
        hooks_data = json.loads(response_text)

        if isinstance(hooks_data, list):
            return [h.get("texto", "") for h in hooks_data if isinstance(h, dict)]
        return []

    async def generate_metadata(
        self,
        quiz: Quiz,
        language: str = "es",
    ) -> QuizMetadata:
        """Genera metadatos de publicación para un quiz existente."""
        preguntas_texto = [q.texto for q in quiz.preguntas]

        prompt = self._prompt_manager.render(
            "metadata_generation.j2",
            quiz_type_display=_QUIZ_TYPE_DISPLAY.get(quiz.tipo, str(quiz.tipo)),
            preguntas=preguntas_texto,
        )

        response_text = await self._call_gemini(prompt)
        data = self._parse_json_response(response_text)

        return QuizMetadata(
            titulo=data.get("titulo", ""),
            descripcion=data.get("descripcion", ""),
            hashtags=data.get("hashtags", []),
            prompt_miniatura=data.get("prompt_miniatura"),
            cta=data.get("cta"),
        )

    async def analyze_trends(
        self,
        category: str,
        language: str = "es",
    ) -> dict[str, Any]:
        """Analiza tendencias actuales para una categoría.

        Usa el conocimiento del LLM sobre tendencias recientes.
        En fases futuras se integrará con Google Trends.
        """
        prompt = (
            f"Lista las 10 tendencias más relevantes y actuales en la categoría "
            f"'{category}' para contenido viral en redes sociales en español.\n\n"
            f"Responde en JSON con esta estructura:\n"
            f'{{"tendencias": ["tendencia1", "tendencia2", ...], '
            f'"temas_calientes": ["tema1", "tema2", ...]}}'
        )

        response_text = await self._call_gemini(prompt)
        return self._parse_json_response(response_text)
