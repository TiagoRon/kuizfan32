"""Tests unitarios para el sistema de plugins."""

from quiz_generator.core.enums import Difficulty, QuizType
from quiz_generator.core.models import Quiz
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry, discover_and_register_builtin_plugins


class TestPluginRegistry:
    """Tests para el registro de plugins."""

    def test_singleton(self):
        """El registry es un singleton."""
        r1 = PluginRegistry()
        r2 = PluginRegistry()
        assert r1 is r2

    def test_register_and_get(self):
        """Puede registrar y recuperar un plugin."""

        class TestPlugin(BaseQuizPlugin):
            @property
            def quiz_type(self) -> QuizType:
                return QuizType.TRIVIA

            @property
            def name(self) -> str:
                return "Test Trivia"

            @property
            def description(self) -> str:
                return "Plugin de prueba"

            def build_prompt_instructions(self) -> str:
                return "Instrucciones de prueba"

        registry = PluginRegistry()
        plugin = TestPlugin()
        registry.register(plugin)

        assert registry.has(QuizType.TRIVIA)
        assert registry.get(QuizType.TRIVIA).name == "Test Trivia"

    def test_list_all(self):
        """Lista todos los plugins registrados."""
        registry = PluginRegistry()
        assert registry.count() == 0

        discover_and_register_builtin_plugins()
        assert registry.count() >= 6  # Al menos los 6 de Fase 1

    def test_discover_builtin_plugins(self):
        """Descubre y registra plugins built-in automáticamente."""
        registry = discover_and_register_builtin_plugins()

        # Verificar que los 6 plugins de Fase 1 están registrados
        expected_types = [
            QuizType.TRIVIA,
            QuizType.TRUE_OR_FALSE,
            QuizType.WOULD_YOU_RATHER,
            QuizType.EMOJI_QUIZ,
            QuizType.GUESS_FLAG,
            QuizType.GUESS_POKEMON,
        ]
        for qt in expected_types:
            assert registry.has(qt), f"Plugin para {qt.value} no registrado"

    def test_plugin_not_found(self):
        """Lanza error al buscar un plugin no registrado."""
        registry = PluginRegistry()
        import pytest
        from quiz_generator.core.exceptions import PluginNotFoundError

        with pytest.raises(PluginNotFoundError):
            registry.get(QuizType.TRIVIA)


class TestBaseQuizPlugin:
    """Tests para la clase base de plugins."""

    def test_validate_quiz_basic(self, sample_quiz: Quiz):
        """Validación básica pasa con un quiz bien formado."""
        registry = discover_and_register_builtin_plugins()
        plugin = registry.get(QuizType.TRIVIA)
        errors = plugin.validate_quiz(sample_quiz)
        assert errors == []

    def test_validate_quiz_no_questions(self):
        """Detecta quiz sin preguntas."""
        from quiz_generator.core.models import Hook, QuizMetadata
        from quiz_generator.core.enums import ViralTrigger

        empty_quiz = Quiz(
            tipo=QuizType.TRIVIA,
            hook=Hook(texto="Test", tipo=ViralTrigger.CURIOSIDAD),
            preguntas=[],
            metadata=QuizMetadata(titulo="T", descripcion="D"),
        )

        registry = discover_and_register_builtin_plugins()
        plugin = registry.get(QuizType.TRIVIA)
        errors = plugin.validate_quiz(empty_quiz)
        assert len(errors) > 0
        assert any("no tiene preguntas" in e for e in errors)

    def test_suggested_duration(self):
        """Calcula duración estimada del video."""
        registry = discover_and_register_builtin_plugins()
        plugin = registry.get(QuizType.TRIVIA)
        duration = plugin.get_suggested_duration(8)
        assert duration > 0
        assert duration > 60  # Al menos 1 minuto para 8 preguntas

    def test_visual_config(self):
        """Retorna configuración visual válida."""
        registry = discover_and_register_builtin_plugins()
        plugin = registry.get(QuizType.TRIVIA)
        config = plugin.get_visual_config()
        assert "layout" in config
        assert "show_timer" in config
