"""Plugin: Test de IQ.

Preguntas de razonamiento lógico, patrones, secuencias numéricas
y habilidades cognitivas. El espectador quiere demostrar su
inteligencia, generando muchos comentarios con puntajes.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class IQTestPlugin(BaseQuizPlugin):
    """Plugin para quizzes estilo Test de IQ."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.IQ_TEST

    @property
    def name(self) -> str:
        return "Test de IQ"

    @property
    def description(self) -> str:
        return "Preguntas de razonamiento, patrones y lógica estilo test de IQ."

    @property
    def tags(self) -> list[str]:
        return ["IQ", "inteligencia", "patrones", "razonamiento"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Test de IQ

- Cada pregunta evalúa una HABILIDAD COGNITIVA específica.
- Tipos de preguntas:
  1. Patrones numéricos: "¿Qué número sigue: 2, 6, 12, 20, 30, ...?" → 42
  2. Patrones visuales (con emojis): "🔵🔴🔵🔵🔴🔵🔵🔵🔴 → ¿Qué sigue?"
     Usa emoji_pista para el patrón.
  3. Analogías: "Pez es a agua como ave es a ___?"
  4. Series de letras: "A, C, F, J, O, ¿___?"
  5. Razonamiento espacial: "Si giras esta figura 90°, ¿cómo se ve?"
  6. Razonamiento verbal: "¿Cuál de estas palabras NO pertenece: Perro, Gato, Mesa, Pez?"
  7. Operaciones: "Si □ + △ = 10 y □ - △ = 4, ¿cuánto vale □?"
  8. Velocidad mental: "¿Cuánto es 17 × 3 + 9 - 4?"
- Cada pregunta tiene 4 opciones de respuesta.
- Para FÁCIL: patrones simples y analogías básicas.
- Para MEDIO: requiere 2-3 pasos de cálculo o razonamiento.
- Para DIFÍCIL: patrones complejos o razonamiento abstracto.
- Para IMPOSIBLE: secuencias con reglas no obvias o problemas multi-paso.
- Al final, asigna un "IQ estimado" en la curiosidad basado en la dificultad:
  FÁCIL = "IQ 90-110", MEDIO = "IQ 110-130", DIFÍCIL = "IQ 130-150", IMPOSIBLE = "IQ 150+"
- El hook debe apelar a COMPETENCIA: "¿Cuál es tu IQ? Descúbrelo ahora 🧠"
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "classic",
            "show_timer": True,
            "timer_seconds": 12,
            "animation_reveal": "flash",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#3F51B5",
                "secondary": "#0D1B2A",
            },
        })
        return config


PluginRegistry().register(IQTestPlugin())
