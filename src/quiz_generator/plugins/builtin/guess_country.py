"""Plugin: Adivina el País.

El espectador debe identificar un país a partir de datos geográficos,
culturales, siluetas o pistas progresivas. Educativo y viral.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessCountryPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina el País."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_COUNTRY

    @property
    def name(self) -> str:
        return "Adivina el País"

    @property
    def description(self) -> str:
        return "Identifica países por datos, capitales, cultura o pistas geográficas."

    @property
    def tags(self) -> list[str]:
        return ["geografía", "países", "educativo", "cultura"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina el País

- Cada pregunta da pistas sobre un PAÍS específico.
- Usa diferentes formatos de pistas (varía entre preguntas):
  1. Datos geográficos: "Este país tiene más de 17,000 islas y está en el sudeste asiático"
  2. Comida típica: "Es famoso por el sushi, el ramen y el takoyaki"
  3. Datos curiosos: "En este país, las vacas son sagradas y no se comen"
  4. Emojis: Usa emoji_pista con la bandera del país (ej: 🗼🥖🧀 para Francia)
  5. Personajes famosos: "De aquí son Shakira, Gabriel García Márquez y James Rodríguez"
  6. Datos mixtos: Mezcla capital, idioma, población, continente
- Las 4 opciones deben ser países de la MISMA REGIÓN.
  Ejemplo: Si es Perú → Bolivia, Ecuador, Colombia, Perú.
- Para FÁCIL: países muy conocidos (Japón, Francia, Brasil, EEUU).
- Para MEDIO: países conocidos pero no tan obvios (Noruega, Turquía, Vietnam).
- Para DIFÍCIL: países pequeños o confundibles (Eslovenia vs Eslovaquia).
- Para IMPOSIBLE: microestados o países poco conocidos (Lesoto, Brunéi, Surinam).
- En la curiosidad, incluir un dato que el espectador nunca esperaría de ese país.
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "classic",
            "show_timer": True,
            "animation_reveal": "flash",
        })
        return config


PluginRegistry().register(GuessCountryPlugin())
