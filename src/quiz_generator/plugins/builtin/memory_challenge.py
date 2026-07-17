"""Plugin: Desafío de Memoria.

El espectador ve una serie de objetos, números o patrones por
un tiempo limitado y luego debe recordarlos. Genera engagement
porque el espectador quiere demostrar su capacidad mental.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class MemoryChallengePlugin(BaseQuizPlugin):
    """Plugin para quizzes de Desafío de Memoria."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.MEMORY_CHALLENGE

    @property
    def name(self) -> str:
        return "Desafío de Memoria"

    @property
    def description(self) -> str:
        return "Recuerda patrones, objetos o secuencias. ¿Qué tan buena es tu memoria?"

    @property
    def tags(self) -> list[str]:
        return ["memoria", "concentración", "desafío", "mental"]

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Desafío de Memoria

- Cada pregunta presenta una SECUENCIA que el espectador debe memorizar
  y luego responder una pregunta sobre ella.
- El campo "texto" debe incluir la secuencia Y la pregunta.
  Formato: "Memoriza: [secuencia]. ¿Cuál era el [detalle]?"
- Tipos de desafíos:
  1. Secuencia de emojis: "Memoriza: 🍎🐶🌟⚽🎵. ¿Cuál era el tercero?"
     Usa emoji_pista para mostrar la secuencia.
  2. Secuencia de números: "Memoriza: 7-3-9-1-5. ¿Cuál era el cuarto número?"
  3. Lista de objetos: "Memoriza estos 6 objetos. ¿Cuál NO estaba en la lista?"
  4. Colores: "Memoriza la secuencia de colores. ¿Cuál iba después del azul?"
  5. Patrones: "¿Qué número sigue en esta secuencia: 2, 4, 8, 16, ...?"
  6. Conteo: "¿Cuántos objetos rojos había en la imagen?"
- Cada pregunta tiene 4 opciones de respuesta.
- Para FÁCIL: secuencias de 3-4 elementos simples.
- Para MEDIO: secuencias de 5-6 elementos.
- Para DIFÍCIL: secuencias de 7-8 elementos o con elementos similares.
- Para IMPOSIBLE: secuencias de 10+ elementos o con distractores.
- En la curiosidad, incluir datos sobre la memoria humana.
- El hook debe apelar a COMPETENCIA: "Solo el 2% puede recordar todo esto 🧠"
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "emoji_centered",
            "show_timer": True,
            "timer_seconds": 15,
            "animation_reveal": "flash",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#7C4DFF",
                "secondary": "#1A1A2E",
            },
        })
        return config


PluginRegistry().register(MemoryChallengePlugin())
