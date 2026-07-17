"""Tests unitarios para el generador de miniaturas."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from quiz_generator.config import Settings
from quiz_generator.core.enums import Difficulty, QuizType, ViralTrigger
from quiz_generator.core.models import (
    Answer,
    Hook,
    Question,
    Quiz,
    QuizMetadata,
    ThumbnailSpec,
)
from quiz_generator.video.thumbnail import ThumbnailGenerator


@pytest.fixture
def settings() -> Settings:
    """Settings de prueba."""
    return Settings(gemini_api_key="test-key")


@pytest.fixture
def generator(settings: Settings) -> ThumbnailGenerator:
    """Instancia del generador de miniaturas."""
    return ThumbnailGenerator(settings)


@pytest.fixture
def sample_quiz() -> Quiz:
    """Quiz de ejemplo para tests de miniatura."""
    return Quiz(
        tipo=QuizType.TRIVIA,
        dificultad=Difficulty.MEDIO,
        idioma="es",
        hook=Hook(
            texto="¿Puedes con este quiz?",
            tipo=ViralTrigger.CURIOSIDAD,
            emoji="🧠",
        ),
        preguntas=[
            Question(
                texto="Pregunta de prueba",
                respuestas=[
                    Answer(texto="A", es_correcta=True),
                    Answer(texto="B", es_correcta=False),
                    Answer(texto="C", es_correcta=False),
                    Answer(texto="D", es_correcta=False),
                ],
            ),
        ],
        metadata=QuizMetadata(
            titulo="🧠 Quiz de Prueba Viral",
            descripcion="Descripción de prueba",
            hashtags=["test"],
            cta="¡Comenta!",
        ),
    )


class TestThumbnailGenerator:
    """Tests para el generador de miniaturas."""

    def test_generate_creates_file(
        self,
        generator: ThumbnailGenerator,
        sample_quiz: Quiz,
        tmp_path: Path,
    ) -> None:
        """Debe crear un archivo PNG en la ruta especificada."""
        output = tmp_path / "thumbnail.png"
        result = generator.generate(sample_quiz, output)
        assert result.exists()
        assert result.suffix == ".png"

    def test_generate_correct_size(
        self,
        generator: ThumbnailGenerator,
        sample_quiz: Quiz,
        tmp_path: Path,
    ) -> None:
        """La miniatura debe tener el tamaño correcto (1080x1920)."""
        output = tmp_path / "thumbnail.png"
        generator.generate(sample_quiz, output)

        img = Image.open(output)
        assert img.size == (1080, 1920)

    def test_generate_from_spec(
        self,
        generator: ThumbnailGenerator,
        tmp_path: Path,
    ) -> None:
        """Debe generar miniatura desde ThumbnailSpec directamente."""
        spec = ThumbnailSpec(
            texto_principal="¡Quiz Épico!",
            texto_secundario="¿Puedes lograrlo?",
            emojis=["🔥", "🧠", "⭐"],
        )
        output = tmp_path / "thumb_spec.png"
        result = generator.generate_from_spec(spec, output)
        assert result.exists()

    def test_generate_creates_parent_dirs(
        self,
        generator: ThumbnailGenerator,
        sample_quiz: Quiz,
        tmp_path: Path,
    ) -> None:
        """Debe crear directorios padre si no existen."""
        output = tmp_path / "nested" / "dir" / "thumbnail.png"
        result = generator.generate(sample_quiz, output)
        assert result.exists()

    def test_generate_valid_image(
        self,
        generator: ThumbnailGenerator,
        sample_quiz: Quiz,
        tmp_path: Path,
    ) -> None:
        """El archivo generado debe ser una imagen válida."""
        output = tmp_path / "thumbnail.png"
        generator.generate(sample_quiz, output)

        img = Image.open(output)
        assert img.mode == "RGB"
        assert img.size[0] > 0
        assert img.size[1] > 0
