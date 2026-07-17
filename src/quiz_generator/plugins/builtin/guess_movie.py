"""Plugin: Adivina la Película.

El espectador debe identificar una película a partir de la trama,
emojis, escenas icónicas o descripciones. Uno de los formatos
más populares y compartibles.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessMoviePlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina la Película."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_MOVIE

    @property
    def name(self) -> str:
        return "Adivina la Película"

    @property
    def description(self) -> str:
        return "Adivina películas por su trama, emojis o escenas icónicas."

    @property
    def tags(self) -> list[str]:
        return ["películas", "cine", "emojis", "entretenimiento"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina la Película

- Cada pregunta da pistas sobre una PELÍCULA específica.
- Varía los formatos de pistas entre preguntas:
  1. Emojis: Usa emoji_pista (ej: 🧊🚢💔 → "Titanic")
  2. Trama resumida SIN mencionar el título:
     "Un arqueólogo busca reliquias antiguas y odia las serpientes"
  3. Frases icónicas: "Yo soy inevitable" → Avengers: Endgame
  4. Datos de producción: "Ganó 11 Oscars en 2004 y está ambientada en la Tierra Media"
  5. Actores: "Protagonizada por Leonardo DiCaprio y Kate Winslet"
- Las 4 opciones deben ser películas del MISMO GÉNERO o ÉPOCA.
  Ejemplo: Si es "Interestellar" → "Gravity", "The Martian", "Interestellar", "2001".
- Para FÁCIL: películas taquilleras universales (Titanic, Harry Potter, Star Wars).
- Para MEDIO: películas populares pero de nicho (Inception, Pulp Fiction).
- Para DIFÍCIL: películas de culto o premiadas pero menos conocidas.
- Para IMPOSIBLE: películas indie, documentales o de cine asiático/europeo.
- Mezcla géneros: acción, drama, comedia, animación, terror, ciencia ficción.
- En la curiosidad, incluir datos de detrás de cámaras o récords.
  Ejemplo: "Avatar tardó 12 años en producirse y fue la más taquillera de la historia."
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "emoji_centered",
            "show_timer": True,
            "animation_reveal": "slide",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#E50914",  # Rojo cine
                "secondary": "#141414",
            },
        })
        return config


PluginRegistry().register(GuessMoviePlugin())
