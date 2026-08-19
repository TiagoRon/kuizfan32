"""Tests unitarios para la resiliencia de proveedores de IA y el fallback offline."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from quiz_generator.ai.groq_provider import GroqProvider
from quiz_generator.ai.offline_provider import OfflineQuizProvider
from quiz_generator.config import Settings
from quiz_generator.core.enums import Difficulty, QuizType, ViralTrigger
from quiz_generator.core.exceptions import AIRateLimitError
from quiz_generator.core.models import GenerationRequest, Quiz
from quiz_generator.orchestrator.pipeline import GenerationPipeline
from quiz_generator.plugins.registry import discover_and_register_builtin_plugins


class TestOfflineQuizProvider:
    """Pruebas para el proveedor Offline de emergencia."""

    @pytest.fixture
    def offline_provider(self) -> OfflineQuizProvider:
        return OfflineQuizProvider()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "quiz_type",
        [
            QuizType.TRIVIA,
            QuizType.TRUE_OR_FALSE,
            QuizType.WOULD_YOU_RATHER,
            QuizType.EMOJI_QUIZ,
            QuizType.GUESS_FLAG,
            QuizType.GUESS_POKEMON,
            QuizType.GUESS_FOOTBALL_PLAYER,
            QuizType.BRAIN_TEASER,
            QuizType.IMPOSSIBLE_QUIZ,
            QuizType.RIDDLE,
        ],
    )
    async def test_generate_quiz_for_all_types(
        self, offline_provider: OfflineQuizProvider, quiz_type: QuizType
    ):
        """El proveedor offline genera quizzes válidos para cualquier tipo."""
        quiz = await offline_provider.generate_quiz(
            quiz_type=quiz_type,
            difficulty=Difficulty.MEDIO,
            num_questions=4,
            language="es",
        )

        assert isinstance(quiz, Quiz)
        assert quiz.tipo == quiz_type
        assert len(quiz.preguntas) == 4
        assert quiz.hook.texto
        assert quiz.metadata.titulo

        for q in quiz.preguntas:
            correctas = sum(1 for r in q.respuestas if r.es_correcta)
            assert correctas == 1, f"Pregunta '{q.texto}' debe tener exactamente 1 respuesta correcta"

    @pytest.mark.asyncio
    async def test_offline_hooks_and_metadata(self, offline_provider: OfflineQuizProvider):
        """Generación de hooks y metadata offline."""
        hooks = await offline_provider.generate_hooks(QuizType.TRIVIA, count=3)
        assert len(hooks) == 3
        assert all(isinstance(h, str) and len(h) > 0 for h in hooks)

        trends = await offline_provider.analyze_trends("fútbol")
        assert "tendencias" in trends
        assert len(trends["tendencias"]) > 0


class TestGroqProviderResilience:
    """Pruebas para la resiliencia y corrección de GroqProvider."""

    def test_parse_viral_trigger(self, sample_settings: Settings):
        """_parse_viral_trigger mapea correctamente triggers en español e inglés."""
        sample_settings.groq_api_key = "test-key"
        provider = GroqProvider(sample_settings)

        assert provider._parse_viral_trigger("curiosidad") == ViralTrigger.CURIOSIDAD
        assert provider._parse_viral_trigger("curiosity") == ViralTrigger.CURIOSIDAD
        assert provider._parse_viral_trigger("competencia") == ViralTrigger.COMPETENCIA
        assert provider._parse_viral_trigger("desafio") == ViralTrigger.DESAFIO
        assert provider._parse_viral_trigger("unknown_trigger") == ViralTrigger.CURIOSIDAD

    @pytest.mark.asyncio
    async def test_get_available_models_prioritizes_fast_models(self, sample_settings: Settings):
        """_get_available_models prioriza modelos livianos como llama-3.1-8b-instant."""
        sample_settings.groq_api_key = "test-key"
        provider = GroqProvider(sample_settings)

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "whisper-large-v3"},
                {"id": "llama-3.3-70b-versatile"},
                {"id": "llama-3.1-8b-instant"},
                {"id": "gemma2-9b-it"},
            ]
        }
        mock_client.get.return_value = mock_response

        models = await provider._get_available_models(mock_client, {})
        assert "whisper-large-v3" not in models
        assert "llama-3.1-8b-instant" in models
        assert models[0] == "llama-3.1-8b-instant"


class TestPipelineFallback:
    """Pruebas para el mecanismo de fallback multinivel en GenerationPipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_fallback_to_offline_when_apis_fail(self, sample_settings: Settings):
        """Cuando Gemini y Groq fallan por RateLimit, el pipeline usa OfflineQuizProvider sin caer."""
        sample_settings.groq_api_key = "test-groq"
        pipeline = GenerationPipeline(sample_settings)

        # Mockear Gemini para que falle por RateLimit
        pipeline._ai_provider.generate_quiz = AsyncMock(
            side_effect=AIRateLimitError("Gemini")
        )

        # Mockear Groq para que falle por RateLimit
        if pipeline._fallback_provider:
            pipeline._fallback_provider.generate_quiz = AsyncMock(
                side_effect=AIRateLimitError("Groq", retry_after=4.0)
            )

        registry = discover_and_register_builtin_plugins()
        plugin = registry.get(QuizType.TRIVIA)
        request = GenerationRequest(
            tipo=QuizType.TRIVIA,
            dificultad=Difficulty.MEDIO,
            num_preguntas=4,
        )

        # Debe generar exitosamente usando el generador offline
        quiz = await pipeline._generate_quiz(request, plugin)

        assert isinstance(quiz, Quiz)
        assert quiz.tipo == QuizType.TRIVIA
        assert len(quiz.preguntas) == 4
        assert len(plugin.validate_quiz(quiz)) == 0

    @pytest.mark.asyncio
    async def test_pipeline_fallback_without_groq(self, sample_settings: Settings):
        """Si Groq no está configurado y Gemini falla, el pipeline usa OfflineQuizProvider directamente."""
        sample_settings.groq_api_key = ""
        pipeline = GenerationPipeline(sample_settings)
        assert pipeline._fallback_provider is None

        pipeline._ai_provider.generate_quiz = AsyncMock(
            side_effect=AIRateLimitError("Gemini")
        )

        registry = discover_and_register_builtin_plugins()
        plugin = registry.get(QuizType.TRUE_OR_FALSE)
        request = GenerationRequest(
            tipo=QuizType.TRUE_OR_FALSE,
            dificultad=Difficulty.FACIL,
            num_preguntas=3,
        )

        quiz = await pipeline._generate_quiz(request, plugin)

        assert isinstance(quiz, Quiz)
        assert quiz.tipo == QuizType.TRUE_OR_FALSE
        assert len(quiz.preguntas) == 3
        assert len(plugin.validate_quiz(quiz)) == 0
