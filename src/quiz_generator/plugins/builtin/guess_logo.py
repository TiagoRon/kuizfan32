"""Plugin: Adivina el Logo.

El espectador debe identificar una marca o empresa por su logo.
Altamente visual y viral por el reconocimiento de marca.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.core.models import Quiz
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessLogoPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina el Logo."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_LOGO

    @property
    def name(self) -> str:
        return "Adivina el Logo"

    @property
    def description(self) -> str:
        return "Identifica marcas famosas por su logo. Visual y adictivo."

    @property
    def tags(self) -> list[str]:
        return ["visual", "marcas", "logos", "reconocimiento"]

    @property
    def requires_images(self) -> bool:
        return True

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina el Logo

- Cada pregunta muestra el logo de una MARCA O EMPRESA famosa.
- El campo "texto" debe ser "¿A qué marca pertenece este logo?" o variaciones.
- El campo "imagen_url" debe contener el nombre de la marca en inglés
  para que el sistema busque el logo.
- Las 4 opciones deben ser marcas del MISMO SECTOR.
  Ejemplo: Si es Nike → Adidas, Puma, Reebok, Nike.
- Incluye marcas de diferentes sectores: tecnología, deportes, comida rápida,
  automotriz, ropa, redes sociales, entretenimiento.
- Para FÁCIL: logos icónicos (Apple, Nike, McDonald's, Google).
- Para MEDIO: logos conocidos pero que confunden (Pepsi vs Coca-Cola rediseños).
- Para DIFÍCIL: logos que cambiaron con el tiempo o marcas menos conocidas.
- Para IMPOSIBLE: logos de subsidiarias, marcas regionales o logos vintage.
- En la curiosidad, incluir la historia del logo o su significado oculto.
  Ejemplo: "La flecha del logo de Amazon va de la A a la Z porque venden de todo."
- Usa emoji_pista con emojis que representen la marca (ej: 🍎💻📱 para Apple).
"""

    def validate_quiz(self, quiz: Quiz) -> list[str]:
        errors = super().validate_quiz(quiz)
        for i, pregunta in enumerate(quiz.preguntas):
            if not pregunta.imagen_url and not pregunta.emoji_pista:
                errors.append(
                    f"Pregunta {i + 1}: Adivina el Logo requiere "
                    f"'imagen_url' o 'emoji_pista'"
                )
        return errors

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "image_centered",
            "image_size": (400, 400),
            "show_timer": True,
            "animation_reveal": "zoom",
            "background_style": "solid",
        })
        return config


PluginRegistry().register(GuessLogoPlugin())
