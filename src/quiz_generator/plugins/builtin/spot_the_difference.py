"""Plugin: Encuentra la Diferencia.

El espectador debe encontrar qué es diferente entre dos opciones
o imágenes. Altamente visual y adictivo. Requiere imágenes
para su versión completa.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class SpotTheDifferencePlugin(BaseQuizPlugin):
    """Plugin para quizzes de Encuentra la Diferencia."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.SPOT_THE_DIFFERENCE

    @property
    def name(self) -> str:
        return "Encuentra la Diferencia"

    @property
    def description(self) -> str:
        return "Encuentra el elemento diferente en un grupo. Visual y adictivo."

    @property
    def tags(self) -> list[str]:
        return ["visual", "atención", "diferencias", "observación"]

    @property
    def requires_images(self) -> bool:
        return True

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Encuentra la Diferencia

- Cada pregunta muestra un GRUPO DE ELEMENTOS donde uno es diferente.
- Para la versión textual/emoji, usa secuencias donde uno no encaja:
  1. Emojis: "Encuentra el diferente: 🐶🐶🐶🐱🐶🐶"
     Usa emoji_pista con la secuencia.
  2. Palabras: "¿Cuál de estas NO es una fruta? Manzana, Plátano, Zanahoria, Uva"
  3. Números: "¿Cuál de estos números NO es primo? 7, 11, 15, 13"
  4. Letras: "Encuentra la letra diferente: OOOOOO0OOOOO" (un cero entre oes)
  5. Datos: "¿Cuál de estos NO es un planeta? Venus, Marte, Plutón, Neptuno"
  6. Categoría: "¿Cuál de estos NO es un país de Sudamérica?"
- El truco está en que la diferencia sea SUTIL pero descubrible.
- Para FÁCIL: diferencias obvias (un gato entre perros).
- Para MEDIO: diferencias que requieren atención (emoji ligeramente diferente).
- Para DIFÍCIL: diferencias técnicas (un número no primo entre primos).
- Para IMPOSIBLE: diferencias que requieren conocimiento experto.
- En la curiosidad, explicar por qué ese elemento es diferente.
- El hook debe provocar CURIOSIDAD: "¿Puedes encontrar el impostor? 👀"
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "grid",
            "show_timer": True,
            "animation_reveal": "zoom",
            "background_style": "solid",
        })
        return config


PluginRegistry().register(SpotTheDifferencePlugin())
