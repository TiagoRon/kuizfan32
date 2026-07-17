"""Plugin: Trivia de Cultura General.

El formato clásico de quiz con preguntas de conocimiento general.
El tipo más versátil y popular para contenido viral.
"""

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class TriviaPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Trivia de Cultura General."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.TRIVIA

    @property
    def name(self) -> str:
        return "Trivia de Cultura General"

    @property
    def description(self) -> str:
        return "Preguntas variadas de conocimiento general con 4 opciones de respuesta."

    @property
    def tags(self) -> list[str]:
        return ["conocimiento", "cultura", "educativo", "popular"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Trivia de Cultura General

- Cada pregunta debe tener EXACTAMENTE 4 opciones (A, B, C, D).
- Las preguntas deben cubrir categorías variadas: ciencia, historia, geografía,
  entretenimiento, deportes, tecnología, naturaleza, arte.
- NO repitas la misma categoría en preguntas consecutivas.
- Las opciones incorrectas deben ser CREÍBLES y plausibles.
- Incluye un dato curioso SORPRENDENTE en la explicación de la respuesta correcta.
- Las preguntas deben ser INTERESANTES — no preguntes lo típico y aburrido.
- Prioriza datos que la gente no conoce y que los haga querer compartir.
- Ordena las preguntas de menor a mayor dificultad (curva de enganche).
"""


# Auto-registrar al importar
PluginRegistry().register(TriviaPlugin())
