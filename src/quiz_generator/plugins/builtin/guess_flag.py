"""Plugin: Adivina la Bandera.

El espectador debe identificar a qué país pertenece una bandera.
Requiere imágenes de banderas que se obtienen de la web.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessFlagPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina la Bandera."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_FLAG

    @property
    def name(self) -> str:
        return "Adivina la Bandera"

    @property
    def description(self) -> str:
        return "Identifica el país por su bandera. Visual y educativo."

    @property
    def tags(self) -> list[str]:
        return ["visual", "geografía", "banderas", "educativo"]

    @property
    def requires_images(self) -> bool:
        return True

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina la Bandera

- Cada pregunta muestra la bandera de un país y el espectador debe adivinar cuál es.
- El campo "texto" debe ser "¿A qué país pertenece esta bandera?" o variaciones.
- El campo "imagen_url" debe contener la URL de un emoji de bandera o
  usar el formato de código ISO para que el sistema busque la imagen.
  Usa el emoji de bandera en el campo "emoji_pista" (ej: 🇯🇵 para Japón).
- Las 4 opciones deben ser países de la misma REGIÓN para aumentar la dificultad.
  Ejemplo: Si la bandera es de Colombia, las opciones podrían ser
  Colombia, Venezuela, Ecuador, Bolivia.
- Para dificultad FÁCIL: incluir banderas muy reconocibles
  (EEUU, Japón, Brasil, México, España).
- Para MEDIO: banderas menos conocidas pero con diseños distintivos
  (Noruega, Corea del Sur, Grecia).
- Para DIFÍCIL: banderas similares entre sí (Chad vs Rumania, Indonesia vs Mónaco).
- Para IMPOSIBLE: banderas de microestados o territorios poco conocidos.
- En la curiosidad, incluir datos sobre el significado de los colores o símbolos.
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "image_centered",  # Imagen grande de la bandera centrada
            "image_size": (600, 400),  # Tamaño de la imagen de bandera
            "show_timer": True,
            "animation_reveal": "flash",
            "border_style": "rounded",  # Bordes redondeados en la bandera
        })
        return config


PluginRegistry().register(GuessFlagPlugin())
