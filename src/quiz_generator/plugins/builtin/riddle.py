"""Plugin: Adivinanza.

Acertijos clásicos con un giro moderno. El espectador debe
adivinar la respuesta a partir de una descripción poética
o enigmática. Genera muchos comentarios con teorías.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class RiddlePlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivinanzas."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.RIDDLE

    @property
    def name(self) -> str:
        return "Adivinanza"

    @property
    def description(self) -> str:
        return "Acertijos clásicos y modernos. Descifra la respuesta."

    @property
    def tags(self) -> list[str]:
        return ["adivinanzas", "acertijos", "poesía", "enigma"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivinanza

- Cada pregunta es una ADIVINANZA en forma de verso, rima o descripción enigmática.
- El campo "texto" contiene la adivinanza completa.
- Las 4 opciones son posibles respuestas.
- Tipos de adivinanzas:
  1. Clásicas rimadas:
     "Blanca por dentro, verde por fuera. Si quieres que te lo diga, espera."
     → La pera.
  2. Descriptivas modernas:
     "Tengo teclas pero no soy piano. Tengo pantalla pero no soy TV. ¿Qué soy?"
     → Un celular/computadora.
  3. De doble sentido:
     "Cuanto más grande, menos se ve. ¿Qué es?" → La oscuridad.
  4. Numéricas: "Soy un número. Si me das la vuelta, valgo menos.
     ¿Quién soy?" → El 9 (al revés es 6).
  5. Culturales: Adivinanzas populares de diferentes países.
  6. Con emojis: Presenta la adivinanza con emojis en emoji_pista y
     la descripción en texto.
- Las opciones incorrectas deben encajar parcialmente con la descripción.
- Para FÁCIL: adivinanzas muy conocidas y directas.
- Para MEDIO: adivinanzas que requieren pensar un poco.
- Para DIFÍCIL: adivinanzas con doble sentido o abstractas.
- Para IMPOSIBLE: adivinanzas de otras culturas o con juegos de palabras complejos.
- En la curiosidad, incluir el origen cultural de la adivinanza.
- El hook debe crear CURIOSIDAD: "¿Puedes resolver estas adivinanzas? 🤔"
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "classic",
            "show_timer": True,
            "timer_seconds": 12,
            "animation_reveal": "slide",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#9C27B0",
                "secondary": "#1A1A2E",
            },
        })
        return config


PluginRegistry().register(RiddlePlugin())
