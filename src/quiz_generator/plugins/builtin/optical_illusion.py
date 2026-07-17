"""Plugin: Ilusión Óptica.

El espectador ve una ilusión óptica o imagen ambigua y debe
responder qué ve primero, qué es real, o cuál es la respuesta
correcta. Altamente visual y viral.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class OpticalIllusionPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Ilusiones Ópticas."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.OPTICAL_ILLUSION

    @property
    def name(self) -> str:
        return "Ilusión Óptica"

    @property
    def description(self) -> str:
        return "Ilusiones ópticas y percepción. ¿Qué ves primero?"

    @property
    def tags(self) -> list[str]:
        return ["visual", "percepción", "ilusiones", "psicología"]

    @property
    def requires_images(self) -> bool:
        return True

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Ilusión Óptica

- NOTA: Las imágenes de ilusiones se generarán aparte. El texto describe la ilusión.
- Cada pregunta presenta una ILUSIÓN ÓPTICA o IMAGEN AMBIGUA y una pregunta sobre ella.
- Tipos de preguntas:
  1. Percepción: "¿Qué ves primero en esta imagen?" → Opciones de lo que la gente ve.
  2. Tamaño/Longitud: "¿Cuál de estas líneas es más larga? Son iguales."
  3. Color: "¿De qué color es este vestido?" (tipo The Dress viral).
  4. Conteo: "¿Cuántos cubos hay en esta figura?"
  5. Movimiento: "¿Esta espiral se mueve o está quieta?" → Está quieta.
  6. Rostros ocultos: "¿Cuántas caras puedes encontrar en esta imagen?"
- Para cada pregunta, describir la ilusión en el campo "texto":
  "Mira esta imagen. ¿Las líneas horizontales son paralelas o están inclinadas?"
- La respuesta correcta suele ser CONTRAINTUITIVA.
- Incluye la explicación psicológica/visual en la curiosidad.
  Ejemplo: "Esta es la ilusión de Müller-Lyer. Las líneas son exactamente
  iguales pero las flechas de los extremos engañan al cerebro."
- Para FÁCIL: ilusiones conocidas y con respuesta clara.
- Para MEDIO: ilusiones que dividen opiniones.
- Para DIFÍCIL: ilusiones que requieren concentración.
- Para IMPOSIBLE: ilusiones donde casi nadie ve la respuesta correcta.
- El hook debe provocar CURIOSIDAD: "Tu cerebro te va a engañar con el #3 👁️"
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "image_centered",
            "image_size": (800, 600),
            "show_timer": True,
            "timer_seconds": 12,
            "animation_reveal": "zoom",
            "background_style": "solid",
            "theme_colors": {
                "primary": "#E040FB",
                "secondary": "#0D0D0D",
            },
        })
        return config


PluginRegistry().register(OpticalIllusionPlugin())
