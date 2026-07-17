"""Plugin: ¿Quién es más...?

Formato comparativo donde el espectador debe adivinar cuál de dos
entidades (personas, países, animales, etc.) tiene más de algo.
Genera mucha sorpresa porque las respuestas suelen ser contraintuitivas.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.core.models import Quiz
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class WhoIsMorePlugin(BaseQuizPlugin):
    """Plugin para quizzes de ¿Quién es más...?"""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.WHO_IS_MORE

    @property
    def name(self) -> str:
        return "¿Quién es más...?"

    @property
    def description(self) -> str:
        return "Adivina quién tiene más de algo. Respuestas sorprendentes."

    @property
    def tags(self) -> list[str]:
        return ["comparación", "sorpresa", "datos", "viral"]

    @property
    def answers_per_question(self) -> int:
        return 2  # Comparación entre dos opciones

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para ¿Quién es más...?

- Cada pregunta compara DOS entidades y pregunta cuál tiene MÁS de algo.
- El formato es: "¿Quién es más [adjetivo]? A) ... o B) ..."
- SIEMPRE hay una respuesta correcta (basada en datos reales).
- Las comparaciones deben ser CONTRAINTUITIVAS — la respuesta que la gente
  no esperaría debería ser la correcta para generar sorpresa.
- Categorías de comparación:
  1. Edad: "¿Quién es más viejo: Google o Wikipedia?"
  2. Tamaño: "¿Qué país es más grande: Australia o Brasil?"
  3. Riqueza: "¿Quién es más rico: el CEO de Tesla o el de Amazon?"
  4. Velocidad: "¿Qué animal es más rápido: un hipopótamo o un humano?"
  5. Altura: "¿Qué edificio es más alto: la Torre Eiffel o la Estatua de la Libertad?"
  6. Antigüedad: "¿Qué es más antiguo: la Universidad de Oxford o el Imperio Azteca?"
- Las comparaciones deben basarse en DATOS VERIFICABLES.
- En la curiosidad, incluir los números exactos de la comparación.
  Ejemplo: "Australia mide 7.7M km² y Brasil 8.5M km²"
- El hook debe provocar SORPRESA: "El #3 te va a volar la cabeza 🤯"
"""

    def validate_quiz(self, quiz: Quiz) -> list[str]:
        errors = super().validate_quiz(quiz)
        for i, pregunta in enumerate(quiz.preguntas):
            if len(pregunta.respuestas) != 2:
                errors.append(
                    f"Pregunta {i + 1}: ¿Quién es más? requiere exactamente 2 opciones"
                )
        return errors

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "versus",
            "show_timer": True,
            "animation_reveal": "slide",
            "vs_style": True,
        })
        return config


PluginRegistry().register(WhoIsMorePlugin())
