"""Plugin: Encuentra el Error.

El espectador debe identificar un error en una afirmación,
dato histórico, ecuación o imagen. Perfecto para engagement
porque la gente quiere demostrar que detecta errores.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class SpotTheMistakePlugin(BaseQuizPlugin):
    """Plugin para quizzes de Encuentra el Error."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.SPOT_THE_MISTAKE

    @property
    def name(self) -> str:
        return "Encuentra el Error"

    @property
    def description(self) -> str:
        return "Detecta el error en afirmaciones, datos o ecuaciones."

    @property
    def tags(self) -> list[str]:
        return ["errores", "atención", "conocimiento", "detalle"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Encuentra el Error

- Cada pregunta presenta una AFIRMACIÓN, DATO O ECUACIÓN con un error
  y el espectador debe encontrarlo.
- El campo "texto" presenta la información CON el error incluido.
  Formato: "Encuentra el error: [afirmación con error]"
- Las 4 opciones explican cuál es el error o qué es correcto.
- Tipos de errores:
  1. Datos históricos: "Cristóbal Colón descubrió América en 1592"
     Error: fue en 1492.
  2. Geografía: "La capital de Australia es Sydney"
     Error: es Canberra.
  3. Ciencia: "El agua hierve a 50°C al nivel del mar"
     Error: hierve a 100°C.
  4. Matemáticas: "12 × 8 = 94"
     Error: es 96.
  5. Ortografía: "La palabra 'excelente' se escribe con S: 'exselente'"
  6. Cultura pop: "Iron Man es interpretado por Chris Hemsworth"
     Error: es Robert Downey Jr.
- El error debe ser SUTIL pero verificable — no errores absurdos.
- Para FÁCIL: errores que la mayoría detecta (fechas muy conocidas).
- Para MEDIO: errores que confunden (capitales poco conocidas).
- Para DIFÍCIL: errores técnicos o de cifras específicas.
- Para IMPOSIBLE: errores en datos que suenan correctos pero no lo son.
- En la curiosidad, incluir el dato correcto con contexto extra.
- El hook debe apelar a ORGULLO: "¿Eres lo suficientemente inteligente para encontrar el error? 🔍"
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "classic",
            "show_timer": True,
            "animation_reveal": "flash",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#FF5252",
                "secondary": "#1A1A2E",
            },
        })
        return config


PluginRegistry().register(SpotTheMistakePlugin())
