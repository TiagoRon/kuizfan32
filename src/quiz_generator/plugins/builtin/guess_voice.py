"""Plugin: Adivina la Voz.

El espectador debe identificar de quién es una voz (celebridad,
personaje de ficción, cantante, etc.) a partir de una descripción
textual de la voz o del contexto en que se escucha. Requiere audio.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessVoicePlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina la Voz."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_VOICE

    @property
    def name(self) -> str:
        return "Adivina la Voz"

    @property
    def description(self) -> str:
        return "Identifica de quién es una voz famosa. Formato auditivo único."

    @property
    def tags(self) -> list[str]:
        return ["audio", "voces", "celebridades", "entretenimiento"]

    @property
    def requires_audio(self) -> bool:
        return True

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina la Voz

- NOTA: Como el audio no se puede generar con IA textual, cada pregunta debe
  describir una voz o una frase icónica que el sistema usará como referencia.
- El campo "texto" debe dar CONTEXTO sobre la voz:
  "¿De quién es esta voz que dice 'Yo soy tu padre'?"
  o "¿Quién narra los documentales de naturaleza más famosos?"
- Incluye pistas sobre el TONO, ACENTO o ESTILO de la voz.
- Las 4 opciones deben ser personas con voces confundibles.
  Ejemplo: Si es Morgan Freeman → Samuel L. Jackson, James Earl Jones, Idris Elba.
- Categorías: actores de doblaje, cantantes, narradores, presentadores, políticos.
- Para FÁCIL: voces ultra-reconocibles (Morgan Freeman, Mufasa, Siri).
- Para MEDIO: voces de personajes animados conocidos.
- Para DIFÍCIL: actores de doblaje latinos/españoles o voces poco reconocibles.
- Para IMPOSIBLE: voces de radio o doblaje de videojuegos específicos.
- En la curiosidad, incluir datos sobre la carrera vocal de la persona.
- El campo "imagen_url" puede contener el nombre del personaje/actor.
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "classic",
            "show_timer": True,
            "animation_reveal": "flash",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#FF6F00",
                "secondary": "#1A1A2E",
            },
        })
        return config


PluginRegistry().register(GuessVoicePlugin())
