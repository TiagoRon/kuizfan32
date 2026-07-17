"""Plugin: Adivina la Canción.

El espectador debe identificar una canción a partir de un fragmento
de letra, pistas sobre el artista, o emojis que representen el tema.
Genera mucha interacción por la conexión emocional con la música.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessSongPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina la Canción."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_SONG

    @property
    def name(self) -> str:
        return "Adivina la Canción"

    @property
    def description(self) -> str:
        return "Adivina canciones por fragmentos de letra, pistas o emojis."

    @property
    def tags(self) -> list[str]:
        return ["música", "canciones", "letras", "artistas"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina la Canción

- Cada pregunta da pistas sobre una CANCIÓN específica.
- Varía los formatos de pistas:
  1. Fragmento de letra (SIN mencionar el título):
     "Despacito, quiero respirar tu cuello despacito..."
  2. Descripción del videoclip: "El video muestra al artista bailando en un set colorido"
  3. Emojis: Usa emoji_pista (ej: 🌧️☔💜 → "Purple Rain")
  4. Datos del artista + época: "Esta canción de los 80s de un artista llamado Michael..."
  5. Pistas mixtas: "Fue #1 en 2017, tiene más de 8 mil millones de vistas en YouTube"
- Las 4 opciones deben ser canciones del MISMO ARTISTA o GÉNERO.
  Ejemplo: Si es "Bohemian Rhapsody" → otras de Queen o rock clásico.
- Mezcla géneros: pop, reggaetón, rock, rap, clásica, electrónica.
- Mezcla épocas: 80s, 90s, 2000s, 2010s, actual.
- Para FÁCIL: hits universales (Despacito, Shape of You, Bohemian Rhapsody).
- Para MEDIO: canciones populares pero no mega-hits.
- Para DIFÍCIL: canciones de álbumes (no singles), B-sides famosos.
- Para IMPOSIBLE: versiones demo, canciones de un solo país.
- En la curiosidad, incluir récords de la canción o datos del artista.
- El hook debe apelar a NOSTALGIA: "¿Reconoces esta canción con solo leer la letra? 🎵"
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "classic",
            "show_timer": True,
            "animation_reveal": "slide",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#1DB954",  # Verde Spotify
                "secondary": "#191414",
            },
        })
        return config


PluginRegistry().register(GuessSongPlugin())
