"""Plugin: ¿Qué Prefieres? (Would You Rather)

Formato de decisión entre dos opciones extremas o divertidas.
Genera muchos comentarios porque los espectadores quieren
expresar su opinión.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.core.models import Quiz
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class WouldYouRatherPlugin(BaseQuizPlugin):
    """Plugin para quizzes de ¿Qué Prefieres?"""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.WOULD_YOU_RATHER

    @property
    def name(self) -> str:
        return "¿Qué Prefieres?"

    @property
    def description(self) -> str:
        return "Elige entre dos opciones extremas. Genera debate y muchos comentarios."

    @property
    def tags(self) -> list[str]:
        return ["decision", "debate", "divertido", "social"]

    @property
    def answers_per_question(self) -> int:
        return 2  # Solo dos opciones

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para ¿Qué Prefieres?

- Cada pregunta presenta DOS opciones entre las que elegir.
- El formato es: "¿Qué prefieres? A) ... o B) ...?"
- NO hay respuesta "correcta" — marca la opción A como "correcta" (la más popular).
- Las opciones deben ser EXTREMAS, DIVERTIDAS o DIFÍCILES de decidir.
- Categorías populares: superpoderes, dinero, fama, situaciones absurdas, dilemas éticos.
- Incluye un dato o estadística inventada en la explicación
  (ej: "El 67% de las personas elegiría la opción A").
- Las opciones deben ser del mismo "nivel" de atractivo — no hagas una opción
  claramente superior.
- Ejemplos:
  - "¿Qué prefieres: poder volar pero solo a 5 km/h, o teletransportarte pero solo a lugares que ya visitaste?"
  - "¿Qué prefieres: nunca más poder usar tu celular, o nunca más poder comer tu comida favorita?"
- EVITA opciones violentas, inapropiadas o que puedan ser ofensivas.
"""

    def validate_quiz(self, quiz: Quiz) -> list[str]:
        errors = super().validate_quiz(quiz)
        for i, pregunta in enumerate(quiz.preguntas):
            if len(pregunta.respuestas) != 2:
                errors.append(
                    f"Pregunta {i + 1}: ¿Qué Prefieres? requiere exactamente 2 opciones"
                )
        return errors

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "versus",  # Layout VS con dos lados
            "show_timer": True,
            "timer_seconds": 8,
            "animation_reveal": "slide",
            "show_progress_bar": True,
            "vs_style": True,  # Efecto visual VS en el medio
        })
        return config


PluginRegistry().register(WouldYouRatherPlugin())
