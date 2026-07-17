"""Plugin: Acertijo Mental.

Acertijos de lógica, pensamiento lateral y resolución de problemas.
El espectador siente satisfacción al resolver el acertijo y
frustración viral al no poder — ambos generan comentarios.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class BrainTeaserPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Acertijo Mental."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.BRAIN_TEASER

    @property
    def name(self) -> str:
        return "Acertijo Mental"

    @property
    def description(self) -> str:
        return "Acertijos de lógica y pensamiento lateral. ¿Puedes resolverlos?"

    @property
    def tags(self) -> list[str]:
        return ["lógica", "acertijos", "pensamiento lateral", "inteligencia"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Acertijo Mental

- Cada pregunta es un ACERTIJO que requiere pensamiento lógico o lateral.
- El campo "texto" presenta el acertijo completo.
- Las 4 opciones incluyen la respuesta correcta y 3 distractores plausibles.
- Tipos de acertijos:
  1. Lógica clásica: "Si hay 5 gatos y cada uno ve 4 gatos, ¿cuántos gatos hay?"
  2. Secuencias: "¿Qué número sigue: 1, 1, 2, 3, 5, 8, ...?"
  3. Pensamiento lateral: "Un hombre empuja su auto hasta un hotel y pierde su fortuna. ¿Qué pasó?"
  4. Paradojas: "El barbero afeita a todos los que no se afeitan a sí mismos. ¿Quién afeita al barbero?"
  5. Matemáticos: "Si tienes 3 manzanas y te quitan 2, ¿cuántas tienes?"
     (Trampa: tienes 2, las que te quitaron ahora son tuyas).
  6. Situacionales: "Un hombre sale de casa, gira a la izquierda 3 veces y
     al llegar a casa ve a dos hombres enmascarados. ¿Dónde está?"
- Los acertijos deben ser SOLUCIONABLES pero no obvios.
- Para FÁCIL: acertijos clásicos con respuestas simples.
- Para MEDIO: requieren 2-3 pasos de razonamiento.
- Para DIFÍCIL: acertijos con trampa o giro inesperado.
- Para IMPOSIBLE: paradojas o acertijos que requieren conocimiento matemático.
- En la curiosidad, explicar la lógica paso a paso.
- El hook debe generar DESAFÍO: "Solo 1 de cada 100 resuelve el #5 🧩"
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "classic",
            "show_timer": True,
            "timer_seconds": 15,
            "animation_reveal": "slide",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#00BCD4",
                "secondary": "#0D1B2A",
            },
        })
        return config


PluginRegistry().register(BrainTeaserPlugin())
