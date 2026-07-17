"""Plugin: Adivina el Personaje.

El espectador debe identificar un personaje de ficción (anime, series,
películas, cómics, videojuegos) a partir de pistas progresivas.
Apela a la identidad de fan y la nostalgia.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.core.models import Quiz
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessCharacterPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina el Personaje."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_CHARACTER

    @property
    def name(self) -> str:
        return "Adivina el Personaje"

    @property
    def description(self) -> str:
        return "Identifica personajes de ficción por pistas o descripciones."

    @property
    def tags(self) -> list[str]:
        return ["ficción", "anime", "series", "películas", "personajes"]

    @property
    def requires_images(self) -> bool:
        return True

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina el Personaje

- Cada pregunta debe hacer referencia a un PERSONAJE DE FICCIÓN conocido.
- Mezcla universos: anime, series de TV, películas, cómics, videojuegos, libros.
- Usa diferentes formatos de pistas:
  1. Descripción sin decir el nombre: "Este personaje usa una espada láser azul y es hijo de Darth Vader"
  2. Frases icónicas: "Es famoso por decir 'Yo soy tu padre'"
  3. Emojis: Usa emoji_pista (ej: 🦸‍♂️🕸️🗽 para Spider-Man)
  4. Datos del universo: "Vive en Gotham City y tiene un mayordomo llamado Alfred"
- Las 4 opciones deben ser personajes del MISMO universo o tipo para confundir.
  Ejemplo: Si es Goku, opciones como Vegeta, Naruto, Luffy.
- Para dificultad FÁCIL: personajes icónicos (Goku, Batman, Harry Potter, Mario).
- Para MEDIO: personajes populares pero no los más famosos (Killua, Zuko, Gandalf).
- Para DIFÍCIL: personajes secundarios o de obras menos mainstream.
- Para IMPOSIBLE: personajes muy específicos de obras nicho.
- En "imagen_url", poner el nombre del personaje para buscar la imagen.
- En la curiosidad, incluir datos del actor/creador/historia de creación.
- El hook debe apelar a IDENTIDAD: "Solo los verdaderos otakus aciertan todas 🎌"
"""

    def validate_quiz(self, quiz: Quiz) -> list[str]:
        errors = super().validate_quiz(quiz)
        for i, pregunta in enumerate(quiz.preguntas):
            if not pregunta.imagen_url and not pregunta.emoji_pista:
                errors.append(
                    f"Pregunta {i + 1}: Adivina el Personaje requiere "
                    f"'imagen_url' o 'emoji_pista'"
                )
        return errors

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "image_centered",
            "show_timer": True,
            "animation_reveal": "zoom",
            "background_style": "gradient",
        })
        return config


PluginRegistry().register(GuessCharacterPlugin())
