"""Configuración global de pytest y fixtures compartidas."""

from __future__ import annotations

import pytest

from quiz_generator.config import Settings, reset_settings
from quiz_generator.core.enums import Difficulty, QuizType, ViralTrigger
from quiz_generator.core.models import (
    Answer,
    AudioSpec,
    GenerationRequest,
    Hook,
    Question,
    Quiz,
    QuizMetadata,
    VideoSpec,
)
from quiz_generator.plugins.registry import PluginRegistry


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Resetea singletons entre tests."""
    PluginRegistry.reset()
    reset_settings()
    yield
    PluginRegistry.reset()
    reset_settings()


@pytest.fixture
def sample_settings() -> Settings:
    """Settings de prueba con valores por defecto."""
    return Settings(
        gemini_api_key="test-key-not-real",
    )


@pytest.fixture
def sample_quiz() -> Quiz:
    """Quiz de ejemplo para tests."""
    return Quiz(
        tipo=QuizType.TRIVIA,
        dificultad=Difficulty.MEDIO,
        idioma="es",
        hook=Hook(
            texto="🧠 Solo el 1% puede responder TODAS",
            tipo=ViralTrigger.COMPETENCIA,
            emoji="🧠",
        ),
        preguntas=[
            Question(
                texto="¿Cuál es el planeta más grande del sistema solar?",
                respuestas=[
                    Answer(texto="Marte", es_correcta=False, emoji="🔴"),
                    Answer(
                        texto="Júpiter", es_correcta=True, emoji="🟠",
                        explicacion="Júpiter es 11 veces más grande que la Tierra",
                    ),
                    Answer(texto="Saturno", es_correcta=False, emoji="💫"),
                    Answer(texto="Neptuno", es_correcta=False, emoji="🔵"),
                ],
                dificultad=Difficulty.FACIL,
                tiempo_segundos=10,
                curiosidad="Júpiter tiene 95 lunas conocidas",
                categoria="Ciencia",
            ),
            Question(
                texto="¿En qué año llegó el hombre a la Luna?",
                respuestas=[
                    Answer(texto="1965", es_correcta=False),
                    Answer(texto="1969", es_correcta=True,
                           explicacion="Neil Armstrong pisó la Luna el 20 de julio de 1969"),
                    Answer(texto="1972", es_correcta=False),
                    Answer(texto="1968", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                tiempo_segundos=10,
                curiosidad="La misión Apollo 11 duró 8 días",
                categoria="Historia",
            ),
            Question(
                texto="¿Cuál es el animal más rápido del mundo?",
                respuestas=[
                    Answer(texto="León", es_correcta=False),
                    Answer(texto="Águila", es_correcta=False),
                    Answer(texto="Guepardo", es_correcta=True,
                           explicacion="Alcanza 120 km/h en carrera corta"),
                    Answer(texto="Caballo", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                tiempo_segundos=10,
                categoria="Naturaleza",
            ),
        ],
        metadata=QuizMetadata(
            titulo="🧠 ¡Quiz de Cultura General! ¿Cuántas aciertas?",
            descripcion="Pon a prueba tus conocimientos con este quiz viral",
            hashtags=["quiz", "trivia", "culturageneral", "viral"],
            cta="¡Comenta cuántas acertaste! 🎯",
        ),
        disparadores_virales=[
            ViralTrigger.COMPETENCIA,
            ViralTrigger.CURIOSIDAD,
        ],
    )


@pytest.fixture
def sample_request() -> GenerationRequest:
    """Solicitud de generación de ejemplo."""
    return GenerationRequest(
        tipo=QuizType.TRIVIA,
        dificultad=Difficulty.MEDIO,
        num_preguntas=5,
        idioma="es",
    )
