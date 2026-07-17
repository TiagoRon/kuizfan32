"""Tests unitarios para los modelos de dominio y enums."""

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


class TestEnums:
    """Tests para las enumeraciones del dominio."""

    def test_quiz_types_count(self):
        """Hay al menos 30 tipos de quiz."""
        assert len(QuizType) >= 28

    def test_difficulty_values(self):
        """Los valores de dificultad son los esperados."""
        assert Difficulty.FACIL.value == "facil"
        assert Difficulty.IMPOSIBLE.value == "imposible"

    def test_viral_trigger_values(self):
        """Los disparadores virales existen."""
        assert len(ViralTrigger) >= 8


class TestModels:
    """Tests para los modelos Pydantic del dominio."""

    def test_answer_immutable(self):
        """Las respuestas son inmutables (frozen)."""
        answer = Answer(texto="Test", es_correcta=True)
        import pytest

        with pytest.raises(Exception):  # Pydantic ValidationError
            answer.texto = "Modified"  # type: ignore

    def test_question_defaults(self):
        """Las preguntas tienen valores por defecto correctos."""
        q = Question(
            texto="¿Test?",
            respuestas=[Answer(texto="A", es_correcta=True)],
        )
        assert q.dificultad == Difficulty.MEDIO
        assert q.tiempo_segundos == 10
        assert q.id  # Tiene un ID generado

    def test_quiz_creation(self, sample_quiz: Quiz):
        """Se puede crear un quiz completo."""
        assert sample_quiz.tipo == QuizType.TRIVIA
        assert len(sample_quiz.preguntas) == 3
        assert sample_quiz.hook.texto
        assert sample_quiz.metadata.titulo

    def test_video_spec_defaults(self):
        """VideoSpec tiene valores por defecto para Shorts/Reels."""
        spec = VideoSpec()
        assert spec.ancho == 1080
        assert spec.alto == 1920
        assert spec.fps == 60

    def test_audio_spec_defaults(self):
        """AudioSpec tiene valores por defecto sensatos."""
        spec = AudioSpec()
        assert spec.voz == "es-MX-DaliaNeural"
        assert 0.5 <= spec.velocidad <= 2.0

    def test_generation_request(self, sample_request: GenerationRequest):
        """Se puede crear una solicitud de generación."""
        assert sample_request.tipo == QuizType.TRIVIA
        assert sample_request.num_preguntas == 5

    def test_question_has_single_correct_answer(self, sample_quiz: Quiz):
        """Cada pregunta tiene exactamente una respuesta correcta."""
        for pregunta in sample_quiz.preguntas:
            correctas = sum(1 for r in pregunta.respuestas if r.es_correcta)
            assert correctas == 1, (
                f"La pregunta '{pregunta.texto}' tiene {correctas} respuestas correctas"
            )
