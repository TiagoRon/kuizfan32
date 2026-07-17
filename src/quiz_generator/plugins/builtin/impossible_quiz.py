"""Plugin: Quiz Imposible.

Preguntas deliberadamente tramposas, absurdas o con giros
inesperados. El punto es que la mayoría falle, generando
frustración viral y muchos compartidos.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class ImpossibleQuizPlugin(BaseQuizPlugin):
    """Plugin para quizzes imposibles con preguntas trampa."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.IMPOSSIBLE_QUIZ

    @property
    def name(self) -> str:
        return "Quiz Imposible"

    @property
    def description(self) -> str:
        return "Preguntas trampa y absurdas. ¡Nadie logra el 100%!"

    @property
    def tags(self) -> list[str]:
        return ["trampa", "absurdo", "imposible", "frustración viral"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Quiz Imposible

- Cada pregunta tiene una TRAMPA o GIRO INESPERADO en la respuesta.
- El espectador cree que sabe la respuesta, pero se equivoca.
- Tipos de preguntas trampa:
  1. Trampa lingüística: "¿Cuántos meses tienen 28 días?" → TODOS (12 meses).
  2. Trampa de lectura: "Un avión se estrella en la frontera entre EEUU y México.
     ¿En qué país entierran a los sobrevivientes?" → Los sobrevivientes NO se entierran.
  3. Trampa numérica: "Si tienes 10 velas y soplas 3, ¿cuántas tienes?" → 3
     (las que soplan se conservan, las demás se derriten).
  4. Falsa obviedad: "¿Qué pesa más: un kilo de plumas o un kilo de acero?" → Pesan igual.
  5. Lógica invertida: "¿Qué fue primero: el huevo o la gallina?"
     → El huevo (evolución).
  6. Absurdo controlado: "¿De qué color era el caballo blanco de Napoleón?" → Blanco.
- Cada pregunta DEBE tener una trampa que haga decir "¡AHHH!" al revelar.
- Las opciones incorrectas deben ser lo que la mayoría respondería por instinto.
- La respuesta correcta debe ser la MENOS intuitiva.
- NO mezcles con preguntas normales de trivia — TODAS deben tener trampa.
- En la curiosidad, explicar por qué la trampa funciona psicológicamente.
- El hook debe ser provocador: "NADIE ha logrado 100% en este quiz 💀"
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "classic",
            "show_timer": True,
            "animation_reveal": "shake",
            "animation_correct": "confetti",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#FF1744",
                "secondary": "#0D0D0D",
            },
        })
        return config


PluginRegistry().register(ImpossibleQuizPlugin())
