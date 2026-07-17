"""Plugin: Elección de Supervivencia.

Formato de escenarios extremos donde el espectador debe elegir
la mejor opción para sobrevivir. Genera mucho debate y
comentarios por la tensión de los escenarios.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.core.models import Quiz
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class SurvivalChoicePlugin(BaseQuizPlugin):
    """Plugin para quizzes de Elección de Supervivencia."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.SURVIVAL_CHOICE

    @property
    def name(self) -> str:
        return "Elección de Supervivencia"

    @property
    def description(self) -> str:
        return "Elige la mejor opción para sobrevivir en escenarios extremos."

    @property
    def tags(self) -> list[str]:
        return ["supervivencia", "extremo", "tensión", "debate"]

    @property
    def answers_per_question(self) -> int:
        return 4

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Elección de Supervivencia

- Cada pregunta presenta un ESCENARIO DE SUPERVIVENCIA extremo
  y el espectador debe elegir la mejor opción para sobrevivir.
- SÍ hay una respuesta correcta (basada en lógica o ciencia real).
- Formato: "Estás perdido en [escenario]. ¿Qué haces?" + 4 opciones.
- Las opciones incorrectas deben parecer lógicas pero ser erróneas.
- Categorías de escenarios:
  1. Naturaleza: "Estás cara a cara con un oso grizzly. ¿Qué haces?"
  2. Desastres: "Estás en un barco que se hunde en aguas heladas"
  3. Urbano: "Estás atrapado en un ascensor durante un terremoto"
  4. Desierto/Selva: "Llevas 2 días sin agua en el desierto del Sahara"
  5. Animales: "Una medusa te picó en la playa. ¿Qué haces?"
  6. Extremos: "Caes a un lago congelado y el hielo se rompe"
- La respuesta correcta debe estar basada en TÉCNICAS REALES de supervivencia.
- En la curiosidad, explicar POR QUÉ es la respuesta correcta con datos científicos.
  Ejemplo: "Hacerte el muerto funciona con osos grizzly porque son defensivos,
  pero NO con osos negros que son depredadores."
- Las opciones incorrectas deben incluir MITOS POPULARES (orinar sobre medusa, etc.).
- El hook debe generar TENSIÓN: "¿Sobrevivirías a estas situaciones? 💀"
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "classic",
            "show_timer": True,
            "timer_seconds": 15,
            "animation_reveal": "flash",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#FF3D00",
                "secondary": "#1A1A1A",
            },
        })
        return config


PluginRegistry().register(SurvivalChoicePlugin())
