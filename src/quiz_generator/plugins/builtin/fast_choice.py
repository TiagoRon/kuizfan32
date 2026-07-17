"""Plugin: Decisión Rápida.

Formato de alta presión donde el espectador tiene solo 3 segundos
para elegir entre dos opciones rápidas. Adictivo y dinámico,
ideal para contenido de alta retención.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.core.models import Quiz
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class FastChoicePlugin(BaseQuizPlugin):
    """Plugin para quizzes de Decisión Rápida."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.FAST_CHOICE

    @property
    def name(self) -> str:
        return "Decisión Rápida"

    @property
    def description(self) -> str:
        return "¡3 segundos para decidir! Elige rápido entre dos opciones."

    @property
    def tags(self) -> list[str]:
        return ["rápido", "presión", "decisión", "adictivo"]

    @property
    def answers_per_question(self) -> int:
        return 2

    @property
    def default_questions(self) -> int:
        return 12  # Más preguntas porque son ultra-rápidas

    @property
    def max_questions(self) -> int:
        return 20

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Decisión Rápida

- Cada pregunta presenta DOS opciones y el espectador tiene 3 SEGUNDOS para elegir.
- Las preguntas deben ser SIMPLES y DIRECTAS — no requieren pensar mucho.
- El formato es: "¿[Opción A] o [Opción B]?" — corto y contundente.
- NO hay respuesta correcta — marca la opción A como "correcta" (la más popular).
- El campo "tiempo_segundos" debe ser SIEMPRE 3.
- Las opciones deben ser RÁPIDAS de procesar:
  1. Comida: "¿Pizza o Sushi?"
  2. Preferencias: "¿Playa o Montaña?"
  3. Pop culture: "¿Marvel o DC?"
  4. Colores: "¿Azul o Rojo?"
  5. Tecnología: "¿iPhone o Android?"
  6. Absurdas: "¿Volar o Ser invisible?"
- NO incluyas opciones complejas o que requieran pensar.
- La explicación debe incluir "El XX% eligió la opción X" (inventar dato).
- El hook debe comunicar URGENCIA: "¡Solo tienes 3 SEGUNDOS! ⚡"
- Incluir emojis en cada opción para procesamiento visual rápido.
"""

    def validate_quiz(self, quiz: Quiz) -> list[str]:
        errors = super().validate_quiz(quiz)
        for i, pregunta in enumerate(quiz.preguntas):
            if len(pregunta.respuestas) != 2:
                errors.append(
                    f"Pregunta {i + 1}: Decisión Rápida requiere exactamente 2 opciones"
                )
        return errors

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "versus",
            "show_timer": True,
            "timer_seconds": 3,
            "animation_reveal": "flash",
            "vs_style": True,
            "high_pressure": True,
        })
        return config

    def get_suggested_duration(self, num_questions: int) -> float:
        # Ultra-rápido: 5 segundos por pregunta (3s timer + 2s reveal)
        return 2.0 + 2.0 + (num_questions * 5.0) + 3.0


PluginRegistry().register(FastChoicePlugin())
