"""Plugin: Adivina la Comida.

El espectador debe identificar un plato o comida a partir de sus
ingredientes, origen cultural, apariencia o datos curiosos.
Muy visual y genera debate sobre gustos.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessFoodPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina la Comida."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_FOOD

    @property
    def name(self) -> str:
        return "Adivina la Comida"

    @property
    def description(self) -> str:
        return "Identifica platos y comidas por ingredientes, origen o pistas."

    @property
    def tags(self) -> list[str]:
        return ["comida", "gastronomía", "cultura", "visual"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina la Comida

- Cada pregunta da pistas sobre un PLATO O COMIDA específica.
- Varía los formatos de pistas:
  1. Ingredientes: "Se hace con masa, salsa de tomate, queso mozzarella y se hornea"
  2. Origen: "Plato típico de Japón que consiste en arroz con vinagre y pescado crudo encima"
  3. Emojis: Usa emoji_pista (ej: 🌮🥑🌶️ → "Tacos")
  4. Descripción sensorial: "Es crujiente por fuera, suave por dentro, y se come con guacamole"
  5. Datos curiosos: "Se inventó por accidente cuando un chef olvidó la masa toda la noche"
  6. Cultural: "Se come con palillos y se moja en salsa de soya"
- Las 4 opciones deben ser comidas del MISMO TIPO o REGIÓN.
  Ejemplo: Si es sushi → ramen, tempura, pad thai, sushi.
- Mezcla cocinas internacionales: mexicana, italiana, japonesa, india, peruana, francesa.
- Para FÁCIL: comidas universales (pizza, hamburguesa, sushi, tacos).
- Para MEDIO: platos regionales conocidos (pad thai, falafel, ceviche).
- Para DIFÍCIL: platos tradicionales específicos (mole oaxaqueño, boeuf bourguignon).
- Para IMPOSIBLE: platos ultralocales o técnicas culinarias específicas.
- En la curiosidad, incluir el origen histórico del plato.
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "emoji_centered",
            "show_timer": True,
            "animation_reveal": "zoom",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#FF6B35",
                "secondary": "#F7C59F",
            },
        })
        return config


PluginRegistry().register(GuessFoodPlugin())
