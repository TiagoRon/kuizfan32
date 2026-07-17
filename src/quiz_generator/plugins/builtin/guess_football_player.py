"""Plugin: Adivina el Futbolista.

El espectador debe identificar un futbolista a partir de
estadísticas, trayectoria, datos curiosos o pistas visuales.
Extremadamente viral en Latinoamérica y Europa.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessFootballPlayerPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina el Futbolista."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_FOOTBALL_PLAYER

    @property
    def name(self) -> str:
        return "Adivina el Futbolista"

    @property
    def description(self) -> str:
        return "Identifica futbolistas por estadísticas, clubes o pistas."

    @property
    def tags(self) -> list[str]:
        return ["fútbol", "deportes", "futbolistas", "competencia"]

    @property
    def requires_images(self) -> bool:
        return True

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina el Futbolista

- Cada pregunta da pistas sobre un FUTBOLISTA específico.
- Varía los formatos de pistas:
  1. Trayectoria de clubes (SIN mencionar el nombre):
     "Jugó en Santos, Barcelona, PSG y ahora está en Al-Hilal"
  2. Estadísticas: "Tiene más de 800 goles oficiales en su carrera"
  3. Apodos: "Le dicen 'La Pulga' y ganó 8 Balones de Oro"
  4. Selección + datos: "Llevó a su selección a ganar el Mundial 2022"
  5. Emojis: Usa emoji_pista (ej: ⚽🐐🏆7️⃣ → "Cristiano Ronaldo")
  6. Datos curiosos: "De niño tenía un problema de crecimiento y fue operado gratis por el club"
- Las 4 opciones deben ser futbolistas de la MISMA POSICIÓN o ÉPOCA.
  Ejemplo: Si es Messi → Cristiano, Neymar, Mbappé, Messi.
- Para FÁCIL: leyendas actuales (Messi, Cristiano, Neymar, Haaland).
- Para MEDIO: estrellas recientes (Modric, Kanté, Salah, Benzema).
- Para DIFÍCIL: jugadores históricos o de ligas menores (Zidane, Cruyff, Di Stéfano).
- Para IMPOSIBLE: jugadores de una sola temporada brillante, promesas olvidadas.
- En "imagen_url", poner el nombre del futbolista.
- En la curiosidad, incluir récords o datos de su carrera.
- El hook debe apelar a COMPETENCIA: "Solo un verdadero fan del fútbol acierta el #7 ⚽"
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "image_centered",
            "show_timer": True,
            "animation_reveal": "flash",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#00C853",  # Verde campo
                "secondary": "#1B5E20",
            },
        })
        return config


PluginRegistry().register(GuessFootballPlayerPlugin())
