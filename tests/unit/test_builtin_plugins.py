"""Tests unitarios para los 30 plugins builtin de quiz.

Verifica que todos los plugins se registren correctamente,
tengan instrucciones de prompt válidas y configuraciones
visuales adecuadas.
"""

from __future__ import annotations

import pytest

from quiz_generator.core.enums import Difficulty, QuizType, ViralTrigger
from quiz_generator.core.models import Answer, Hook, Question, Quiz, QuizMetadata
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry, discover_and_register_builtin_plugins


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def registry() -> PluginRegistry:
    """Registra todos los plugins builtin y devuelve el registry."""
    return discover_and_register_builtin_plugins()


@pytest.fixture
def all_quiz_types() -> list[QuizType]:
    """Lista de todos los QuizType definidos en el enum."""
    return list(QuizType)


def _make_quiz(
    quiz_type: QuizType,
    num_answers: int = 4,
    num_questions: int = 3,
    has_emoji_pista: bool = False,
    has_imagen_url: bool = False,
) -> Quiz:
    """Crea un quiz de ejemplo para validación."""
    answers = [
        Answer(
            texto=f"Respuesta {i + 1}",
            es_correcta=(i == 0),
            emoji=f"{chr(0x1F1E0 + i)}",
        )
        for i in range(num_answers)
    ]

    preguntas = [
        Question(
            texto=f"Pregunta de prueba #{q + 1}",
            respuestas=answers,
            dificultad=Difficulty.MEDIO,
            tiempo_segundos=10,
            curiosidad="Dato curioso de prueba",
            emoji_pista="🔥🌟💡" if has_emoji_pista else None,
            imagen_url="test_image" if has_imagen_url else None,
        )
        for q in range(num_questions)
    ]

    return Quiz(
        tipo=quiz_type,
        dificultad=Difficulty.MEDIO,
        idioma="es",
        hook=Hook(
            texto="Hook de prueba",
            tipo=ViralTrigger.CURIOSIDAD,
            emoji="🧠",
        ),
        preguntas=preguntas,
        metadata=QuizMetadata(
            titulo="Quiz de prueba",
            descripcion="Descripción de prueba",
            hashtags=["test"],
        ),
    )


# =========================================================================
# Tests de Descubrimiento y Registro
# =========================================================================


class TestPluginDiscovery:
    """Tests para el descubrimiento automático de plugins."""

    def test_all_30_types_registered(self, registry: PluginRegistry) -> None:
        """Verifica que los 30 tipos de quiz tienen plugin registrado."""
        assert registry.count() == 30, (
            f"Se esperaban 30 plugins, se encontraron {registry.count()}"
        )

    def test_all_enum_values_have_plugin(
        self, registry: PluginRegistry, all_quiz_types: list[QuizType],
    ) -> None:
        """Cada valor del enum QuizType debe tener un plugin registrado."""
        missing = [qt for qt in all_quiz_types if not registry.has(qt)]
        assert not missing, f"Tipos sin plugin: {[m.value for m in missing]}"

    def test_each_plugin_is_instance_of_base(self, registry: PluginRegistry) -> None:
        """Cada plugin registrado debe ser instancia de BaseQuizPlugin."""
        for plugin in registry.list_all():
            assert isinstance(plugin, BaseQuizPlugin), (
                f"Plugin {plugin.name} no hereda de BaseQuizPlugin"
            )

    def test_list_all_returns_all(self, registry: PluginRegistry) -> None:
        """list_all() debe devolver exactamente 30 plugins."""
        plugins = registry.list_all()
        assert len(plugins) == 30

    def test_no_duplicate_types(self, registry: PluginRegistry) -> None:
        """No debe haber dos plugins con el mismo QuizType."""
        types = [p.quiz_type for p in registry.list_all()]
        assert len(types) == len(set(types)), "Hay tipos duplicados"


# =========================================================================
# Tests de Propiedades del Plugin
# =========================================================================


class TestPluginProperties:
    """Tests para las propiedades de cada plugin."""

    def test_name_not_empty(self, registry: PluginRegistry) -> None:
        """Cada plugin debe tener un nombre no vacío."""
        for plugin in registry.list_all():
            assert plugin.name.strip(), f"Plugin {plugin.quiz_type} tiene nombre vacío"

    def test_description_not_empty(self, registry: PluginRegistry) -> None:
        """Cada plugin debe tener una descripción no vacía."""
        for plugin in registry.list_all():
            assert plugin.description.strip(), (
                f"Plugin {plugin.name} tiene descripción vacía"
            )

    def test_min_max_questions_valid(self, registry: PluginRegistry) -> None:
        """min_questions debe ser <= max_questions para cada plugin."""
        for plugin in registry.list_all():
            assert plugin.min_questions <= plugin.max_questions, (
                f"Plugin {plugin.name}: min ({plugin.min_questions}) > "
                f"max ({plugin.max_questions})"
            )

    def test_default_questions_in_range(self, registry: PluginRegistry) -> None:
        """default_questions debe estar entre min y max."""
        for plugin in registry.list_all():
            assert plugin.min_questions <= plugin.default_questions <= plugin.max_questions, (
                f"Plugin {plugin.name}: default ({plugin.default_questions}) "
                f"fuera de rango [{plugin.min_questions}, {plugin.max_questions}]"
            )

    def test_answers_per_question_valid(self, registry: PluginRegistry) -> None:
        """answers_per_question debe ser >= 2."""
        for plugin in registry.list_all():
            assert plugin.answers_per_question >= 2, (
                f"Plugin {plugin.name}: answers_per_question < 2"
            )


# =========================================================================
# Tests de Prompt Instructions
# =========================================================================


class TestPromptInstructions:
    """Tests para las instrucciones de prompt de cada plugin."""

    def test_instructions_not_empty(self, registry: PluginRegistry) -> None:
        """build_prompt_instructions() no debe retornar string vacío."""
        for plugin in registry.list_all():
            instructions = plugin.build_prompt_instructions()
            assert instructions.strip(), (
                f"Plugin {plugin.name}: instrucciones de prompt vacías"
            )

    def test_instructions_minimum_length(self, registry: PluginRegistry) -> None:
        """Las instrucciones deben tener al menos 100 caracteres."""
        for plugin in registry.list_all():
            instructions = plugin.build_prompt_instructions()
            assert len(instructions) >= 100, (
                f"Plugin {plugin.name}: instrucciones muy cortas ({len(instructions)} chars)"
            )

    def test_instructions_contain_header(self, registry: PluginRegistry) -> None:
        """Las instrucciones deben contener un encabezado markdown ##."""
        for plugin in registry.list_all():
            instructions = plugin.build_prompt_instructions()
            assert "##" in instructions, (
                f"Plugin {plugin.name}: instrucciones sin encabezado ##"
            )


# =========================================================================
# Tests de Validación
# =========================================================================


class TestPluginValidation:
    """Tests para la validación de quizzes."""

    def test_valid_trivia_quiz_passes(self, registry: PluginRegistry) -> None:
        """Un quiz de trivia válido debe pasar sin errores."""
        plugin = registry.get(QuizType.TRIVIA)
        quiz = _make_quiz(QuizType.TRIVIA, num_answers=4)
        errors = plugin.validate_quiz(quiz)
        assert errors == []

    def test_empty_quiz_fails(self, registry: PluginRegistry) -> None:
        """Un quiz sin preguntas debe fallar la validación."""
        plugin = registry.get(QuizType.TRIVIA)
        quiz = _make_quiz(QuizType.TRIVIA, num_questions=0)
        errors = plugin.validate_quiz(quiz)
        assert len(errors) > 0

    def test_true_false_requires_2_options(self, registry: PluginRegistry) -> None:
        """Verdadero/Falso con 4 opciones debe dar error."""
        plugin = registry.get(QuizType.TRUE_OR_FALSE)
        quiz = _make_quiz(QuizType.TRUE_OR_FALSE, num_answers=4)
        errors = plugin.validate_quiz(quiz)
        assert any("2 opciones" in e for e in errors)

    def test_would_you_rather_requires_2_options(
        self, registry: PluginRegistry,
    ) -> None:
        """¿Qué Prefieres? con 4 opciones debe dar error."""
        plugin = registry.get(QuizType.WOULD_YOU_RATHER)
        quiz = _make_quiz(QuizType.WOULD_YOU_RATHER, num_answers=4)
        errors = plugin.validate_quiz(quiz)
        assert any("2 opciones" in e for e in errors)

    def test_emoji_quiz_requires_emoji_pista(self, registry: PluginRegistry) -> None:
        """Emoji Quiz sin emoji_pista debe dar error."""
        plugin = registry.get(QuizType.EMOJI_QUIZ)
        quiz = _make_quiz(QuizType.EMOJI_QUIZ, has_emoji_pista=False)
        errors = plugin.validate_quiz(quiz)
        assert any("emoji_pista" in e for e in errors)

    def test_emoji_quiz_with_emoji_passes(self, registry: PluginRegistry) -> None:
        """Emoji Quiz con emoji_pista no debe dar error por eso."""
        plugin = registry.get(QuizType.EMOJI_QUIZ)
        quiz = _make_quiz(QuizType.EMOJI_QUIZ, has_emoji_pista=True)
        errors = plugin.validate_quiz(quiz)
        assert not any("emoji_pista" in e for e in errors)


# =========================================================================
# Tests de Configuración Visual
# =========================================================================


class TestVisualConfig:
    """Tests para la configuración visual de cada plugin."""

    def test_visual_config_is_dict(self, registry: PluginRegistry) -> None:
        """get_visual_config() debe retornar un dict."""
        for plugin in registry.list_all():
            config = plugin.get_visual_config()
            assert isinstance(config, dict), (
                f"Plugin {plugin.name}: visual config no es dict"
            )

    def test_visual_config_has_layout(self, registry: PluginRegistry) -> None:
        """La config visual debe tener un campo 'layout'."""
        for plugin in registry.list_all():
            config = plugin.get_visual_config()
            assert "layout" in config, (
                f"Plugin {plugin.name}: visual config sin 'layout'"
            )

    def test_visual_config_has_show_timer(self, registry: PluginRegistry) -> None:
        """La config visual debe tener un campo 'show_timer'."""
        for plugin in registry.list_all():
            config = plugin.get_visual_config()
            assert "show_timer" in config, (
                f"Plugin {plugin.name}: visual config sin 'show_timer'"
            )


# =========================================================================
# Tests de Duración Sugerida
# =========================================================================


class TestSuggestedDuration:
    """Tests para la duración sugerida del video."""

    def test_duration_positive(self, registry: PluginRegistry) -> None:
        """La duración sugerida debe ser positiva."""
        for plugin in registry.list_all():
            duration = plugin.get_suggested_duration(8)
            assert duration > 0, (
                f"Plugin {plugin.name}: duración negativa o cero"
            )

    def test_duration_increases_with_questions(
        self, registry: PluginRegistry,
    ) -> None:
        """Más preguntas deben dar mayor duración."""
        for plugin in registry.list_all():
            d5 = plugin.get_suggested_duration(5)
            d10 = plugin.get_suggested_duration(10)
            assert d10 > d5, (
                f"Plugin {plugin.name}: 10 preguntas no da más duración que 5"
            )
