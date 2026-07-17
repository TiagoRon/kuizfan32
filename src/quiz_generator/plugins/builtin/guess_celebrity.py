"""Plugin: Adivina la Celebridad.

El espectador debe identificar una celebridad a partir de datos
biográficos, logros, frases famosas o pistas progresivas.
Genera mucho engagement por la conexión con la cultura pop.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessCelebrityPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina la Celebridad."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_CELEBRITY

    @property
    def name(self) -> str:
        return "Adivina la Celebridad"

    @property
    def description(self) -> str:
        return "Identifica celebridades por datos biográficos, logros o frases."

    @property
    def tags(self) -> list[str]:
        return ["celebridades", "famosos", "cultura pop", "entretenimiento"]

    @property
    def requires_images(self) -> bool:
        return True

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina la Celebridad

- Cada pregunta da pistas sobre una CELEBRIDAD específica (actores, cantantes,
  deportistas, influencers, líderes, científicos).
- Varía los formatos de pistas:
  1. Biografía: "Nació en Colombia, es la latina más escuchada en Spotify"
  2. Logros: "Ha ganado 8 Balones de Oro y es considerado el mejor de la historia"
  3. Frases famosas: "Dijo: 'Yo tengo un sueño' en 1963"
  4. Datos curiosos: "Fue rechazado por 12 editoriales antes de publicar Harry Potter"
  5. Emojis: Usa emoji_pista (ej: ⚽🐐🇦🇷 → "Messi")
  6. Pistas progresivas: De más difícil a más fácil
- Las 4 opciones deben ser celebridades del MISMO CAMPO.
  Ejemplo: Si es Messi → Cristiano, Mbappé, Neymar, Messi.
- Mezcla campos: música, cine, deporte, ciencia, historia, redes sociales.
- Para FÁCIL: celebridades universales (Messi, Taylor Swift, Elon Musk).
- Para MEDIO: celebridades de nicho o regionales famosas.
- Para DIFÍCIL: datos poco conocidos de celebridades famosas.
- Para IMPOSIBLE: celebridades históricas o datos ultra-específicos.
- En "imagen_url", poner el nombre de la celebridad para buscar la imagen.
- En la curiosidad, incluir datos que nadie esperaría de esa persona.
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "image_centered",
            "show_timer": True,
            "animation_reveal": "zoom",
            "background_style": "gradient",
        })
        return config


PluginRegistry().register(GuessCelebrityPlugin())
