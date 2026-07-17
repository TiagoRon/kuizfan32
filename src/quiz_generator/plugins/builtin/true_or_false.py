"""Plugin: Verdadero o Falso.

Formato rápido y dinámico: el espectador debe decidir si una
afirmación es verdadera o falsa. Ideal para alto engagement
por su simplicidad y velocidad.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.core.models import Quiz
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class TrueOrFalsePlugin(BaseQuizPlugin):
    """Plugin para quizzes de Verdadero o Falso."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.TRUE_OR_FALSE

    @property
    def name(self) -> str:
        return "Verdadero o Falso"

    @property
    def description(self) -> str:
        return "Afirmaciones que pueden ser verdaderas o falsas. Rápido y adictivo."

    @property
    def tags(self) -> list[str]:
        return ["rapido", "simple", "adictivo", "conocimiento"]

    @property
    def answers_per_question(self) -> int:
        return 2  # Solo Verdadero / Falso

    @property
    def default_questions(self) -> int:
        return 10  # Más preguntas porque son más rápidas

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Verdadero o Falso

- Cada pregunta es una AFIRMACIÓN que puede ser verdadera o falsa.
- Cada pregunta debe tener EXACTAMENTE 2 opciones: "✅ Verdadero" y "❌ Falso".
- Mezcla respuestas: aproximadamente 50% verdadero, 50% falso.
- Las afirmaciones falsas deben sonar CREÍBLES (que parezcan verdaderas).
- Las afirmaciones verdaderas deben sonar SORPRENDENTES (que parezcan falsas).
- Este es el formato más efectivo para crear debate en los comentarios.
- Incluye datos que hagan al espectador decir "¡no puede ser!".
- Ejemplo: "El corazón de un camarón está en su cabeza" → ✅ Verdadero
- Ejemplo: "Los humanos usan solo el 10% de su cerebro" → ❌ Falso
- NO uses afirmaciones obvias o aburridas.
- La explicación debe incluir la fuente o un dato extra.
"""

    def validate_quiz(self, quiz: Quiz) -> list[str]:
        """Validación específica: cada pregunta debe tener exactamente 2 opciones."""
        errors = super().validate_quiz(quiz)

        for i, pregunta in enumerate(quiz.preguntas):
            if len(pregunta.respuestas) != 2:
                errors.append(
                    f"Pregunta {i + 1}: Verdadero o Falso requiere exactamente "
                    f"2 opciones (tiene {len(pregunta.respuestas)})"
                )

        return errors

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "binary",  # Layout especial para V/F
            "animation_reveal": "slide",
            "show_timer": True,
            "timer_seconds": 7,  # Menos tiempo (es más simple)
        })
        return config

    def get_suggested_duration(self, num_questions: int) -> float:
        # V/F es más rápido: 8 segundos por pregunta
        return 2.0 + 3.0 + (num_questions * 8.0) + 3.0


PluginRegistry().register(TrueOrFalsePlugin())
