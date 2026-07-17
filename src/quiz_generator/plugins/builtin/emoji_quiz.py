"""Plugin: Emoji Quiz — Adivina con Emojis.

El espectador debe adivinar una película, canción, persona o concepto
a partir de una secuencia de emojis. Extremadamente viral por su
naturaleza visual y la satisfacción de descifrar.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.core.models import Quiz
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class EmojiQuizPlugin(BaseQuizPlugin):
    """Plugin para Emoji Quiz."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.EMOJI_QUIZ

    @property
    def name(self) -> str:
        return "Emoji Quiz"

    @property
    def description(self) -> str:
        return "Adivina películas, series, canciones o conceptos a partir de emojis."

    @property
    def tags(self) -> list[str]:
        return ["visual", "emojis", "adivinanza", "divertido"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Emoji Quiz

- Cada pregunta muestra una SECUENCIA DE EMOJIS que representa algo.
- El campo "emoji_pista" debe contener la secuencia de emojis (3-6 emojis).
- El campo "texto" debe ser "¿Qué representan estos emojis?"
  o una variación como "Adivina la película 🎬" según el tema.
- Las categorías pueden ser: películas, series, canciones, países, comidas,
  profesiones, animales, videojuegos, marcas, deportes.
- Cada pregunta debe tener 4 opciones de respuesta.
- Los emojis deben ser lo suficientemente claros para que sea POSIBLE
  adivinar, pero no tan obvio que sea instantáneo.
- Mezcla categorías para variedad.
- Ejemplos:
  - 🦁👑🌍 → "El Rey León"
  - 🕷️🕸️🏙️ → "Spider-Man"
  - 🧊🚢💔 → "Titanic"
  - 🍕🐢🥷 → "Tortugas Ninja"
  - ⚽🐐🇦🇷 → "Messi"
- La dificultad se controla con la cantidad y ambigüedad de los emojis.
"""

    def validate_quiz(self, quiz: Quiz) -> list[str]:
        errors = super().validate_quiz(quiz)
        for i, pregunta in enumerate(quiz.preguntas):
            if not pregunta.emoji_pista:
                errors.append(
                    f"Pregunta {i + 1}: Emoji Quiz requiere el campo 'emoji_pista'"
                )
        return errors

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "emoji_centered",  # Emojis grandes centrados
            "emoji_size": 96,  # Tamaño de fuente de emojis
            "show_timer": True,
            "animation_reveal": "zoom",
            "background_style": "gradient",
        })
        return config


PluginRegistry().register(EmojiQuizPlugin())
