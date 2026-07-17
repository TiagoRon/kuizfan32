"""Plugin: Adivina el Pokémon.

Uno de los formatos más virales. El espectador debe identificar
un Pokémon a partir de pistas, siluetas o descripciones.
Apela directamente a la nostalgia y la identidad de fan.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessPokemonPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina el Pokémon."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_POKEMON

    @property
    def name(self) -> str:
        return "Adivina el Pokémon"

    @property
    def description(self) -> str:
        return "Identifica Pokémon por pistas o descripciones. Nostalgia pura."

    @property
    def tags(self) -> list[str]:
        return ["videojuegos", "pokemon", "nostalgia", "anime"]

    @property
    def requires_images(self) -> bool:
        return True

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina el Pokémon

- Cada pregunta debe hacer referencia a un Pokémon específico.
- Usa diferentes formatos de pistas:
  1. Descripción sin decir el nombre: "Este Pokémon de tipo fuego tiene una llama en la cola"
  2. Datos de la Pokédex: "Pokémon #025, tipo eléctrico, originario de Kanto"
  3. Emojis: Usa emoji_pista (ej: ⚡🐭💛 para Pikachu)
  4. Pistas crípticas: "El favorito de Ash, te electrocuta con las mejillas"
- Las 4 opciones deben ser Pokémon del MISMO tipo o generación para confundir.
- Para dificultad FÁCIL: Pokémon icónicos (Pikachu, Charizard, Mewtwo, Eevee).
- Para MEDIO: Pokémon de Gen 1-3 conocidos pero no los más famosos.
- Para DIFÍCIL: Pokémon de generaciones recientes o con nombres similares.
- Para IMPOSIBLE: Pokémon ultra raros, formas regionales, mega evoluciones específicas.
- En la curiosidad, incluir datos del juego o del anime.
- En "imagen_url", poner el nombre del Pokémon en inglés para buscar la imagen.
- El hook debe apelar a NOSTALGIA: "Solo los que jugaron de niños saben esto 🎮"
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "image_centered",
            "show_timer": True,
            "animation_reveal": "zoom",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#EE1515",  # Rojo Pokémon
                "secondary": "#FFFFFF",
                "accent": "#3D7DCA",  # Azul Pokémon
            },
        })
        return config


PluginRegistry().register(GuessPokemonPlugin())
