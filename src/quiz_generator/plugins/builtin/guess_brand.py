"""Plugin: Adivina la Marca.

El espectador debe identificar una marca por su eslogan,
historia, productos o datos corporativos. Diferente del logo quiz
porque se basa en conocimiento, no en reconocimiento visual.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessBrandPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina la Marca."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_BRAND

    @property
    def name(self) -> str:
        return "Adivina la Marca"

    @property
    def description(self) -> str:
        return "Identifica marcas por eslogan, datos o productos. Conocimiento puro."

    @property
    def tags(self) -> list[str]:
        return ["marcas", "negocios", "eslóganes", "marketing"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina la Marca

- Cada pregunta da pistas sobre una MARCA O EMPRESA específica.
- DIFERENCIA con Adivina el Logo: aquí NO se muestra el logo, solo datos textuales.
- Varía los formatos de pistas:
  1. Eslogan: "Just Do It" → Nike
  2. Historia: "Fundada en un garaje en 1976 por Steve Jobs y Steve Wozniak"
  3. Productos: "Fabrica el Big Mac, las McNuggets y el Happy Meal"
  4. Datos de negocio: "Es la empresa más valiosa del mundo, supera los 3 billones de dólares"
  5. Curiosidades: "Su nombre viene de la diosa griega de la victoria"
  6. Emojis: Usa emoji_pista (ej: 🍔🍟🤡 → McDonald's)
- Las 4 opciones deben ser marcas del MISMO SECTOR.
- Mezcla sectores: tecnología, comida, moda, autos, entretenimiento.
- Para FÁCIL: marcas universales (Coca-Cola, Apple, Nike, Amazon).
- Para MEDIO: marcas conocidas con datos menos obvios.
- Para DIFÍCIL: marcas de nicho o datos poco conocidos de marcas famosas.
- Para IMPOSIBLE: empresas matrices, conglomerados, marcas regionales.
- En la curiosidad, incluir datos de negocio sorprendentes.
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "classic",
            "show_timer": True,
            "animation_reveal": "flash",
        })
        return config


PluginRegistry().register(GuessBrandPlugin())
