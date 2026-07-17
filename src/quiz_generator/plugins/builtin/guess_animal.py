"""Plugin: Adivina el Animal.

El espectador debe identificar un animal a partir de sus
características, hábitat, comportamiento o datos curiosos.
Educativo y con datos que sorprenden.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessAnimalPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina el Animal."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_ANIMAL

    @property
    def name(self) -> str:
        return "Adivina el Animal"

    @property
    def description(self) -> str:
        return "Identifica animales por características, hábitat o datos curiosos."

    @property
    def tags(self) -> list[str]:
        return ["animales", "naturaleza", "educativo", "ciencia"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina el Animal

- Cada pregunta da pistas sobre un ANIMAL específico.
- Varía los formatos de pistas:
  1. Características físicas: "Este animal tiene rayas blancas y negras y vive en África"
  2. Comportamiento: "Es el único mamífero que puede volar de verdad"
  3. Récords: "Es el animal más rápido del mundo en tierra"
  4. Datos sorprendentes: "Este animal duerme 22 horas al día"
  5. Emojis: Usa emoji_pista (ej: 🐾🖤🎋 → "Oso panda")
  6. Hábitat: "Vive solo en Madagascar y se llama como un personaje de una película animada"
- Las 4 opciones deben ser animales del MISMO GRUPO (mamíferos, aves, reptiles, etc.)
  o del mismo hábitat.
- Para FÁCIL: animales muy conocidos (león, perro, gato, delfín).
- Para MEDIO: animales conocidos pero con datos que confunden (narval, axolotl).
- Para DIFÍCIL: animales raros o poco conocidos (pangolín, okapi, quokka).
- Para IMPOSIBLE: subespecies, animales extintos recientemente o de las profundidades.
- En la curiosidad, incluir el dato MÁS sorprendente del animal.
  Ejemplo: "El corazón de un camarón está en su cabeza."
- El hook debe provocar CURIOSIDAD: "¿Puedes adivinar estos animales? El #5 te sorprenderá 🐾"
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "classic",
            "show_timer": True,
            "animation_reveal": "zoom",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#4CAF50",
                "secondary": "#1B5E20",
            },
        })
        return config


PluginRegistry().register(GuessAnimalPlugin())
