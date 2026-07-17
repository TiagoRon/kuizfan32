"""Plugin: Adivina el Sonido.

El espectador debe identificar un sonido a partir de una descripción
textual o contexto. Similar a Adivina la Voz pero con sonidos
ambientales, instrumentos, efectos o sonidos de la naturaleza.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessSoundPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina el Sonido."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_SOUND

    @property
    def name(self) -> str:
        return "Adivina el Sonido"

    @property
    def description(self) -> str:
        return "Identifica sonidos de la naturaleza, instrumentos o efectos."

    @property
    def tags(self) -> list[str]:
        return ["audio", "sonidos", "naturaleza", "instrumentos"]

    @property
    def requires_audio(self) -> bool:
        return True

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina el Sonido

- NOTA: Como el audio no se puede generar con IA textual, cada pregunta debe
  DESCRIBIR un sonido y dar pistas sobre su origen.
- El campo "texto" debe describir el contexto del sonido:
  "¿Qué animal hace este sonido?" o "¿Qué instrumento produce este sonido?"
- Varía las categorías de sonidos:
  1. Animales: "Un sonido agudo y repetitivo que hace un animal nocturno"
  2. Instrumentos musicales: "Un instrumento de cuerda que se toca con arco"
  3. Sonidos cotidianos: "El sonido que hace un tren al frenar"
  4. Naturaleza: "El sonido de un géiser expulsando agua caliente"
  5. Tecnología: "El sonido icónico de inicio de Windows XP"
  6. Efectos: "El sonido que escuchas cuando recibes un mensaje en WhatsApp"
- Las 4 opciones deben ser sonidos del MISMO TIPO.
  Ejemplo: Si es un búho → lobo, búho, murciélago, lechuza.
- Para FÁCIL: sonidos que todo el mundo reconoce.
- Para MEDIO: sonidos ambientales menos comunes.
- Para DIFÍCIL: instrumentos raros o sonidos de animales exóticos.
- Para IMPOSIBLE: sonidos industriales, frecuencias o efectos de cine específicos.
- En la curiosidad, incluir datos sobre el sonido (frecuencia, origen, etc.).
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "classic",
            "show_timer": True,
            "animation_reveal": "flash",
            "background_style": "gradient",
        })
        return config


PluginRegistry().register(GuessSoundPlugin())
