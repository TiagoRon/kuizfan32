"""Plugin: Adivina el Auto.

El espectador debe identificar un auto a partir de su silueta,
datos técnicos, marca o características de diseño.
Muy popular entre entusiastas automotrices.
"""

from typing import Any

from quiz_generator.core.enums import QuizType
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry


class GuessCarPlugin(BaseQuizPlugin):
    """Plugin para quizzes de Adivina el Auto."""

    @property
    def quiz_type(self) -> QuizType:
        return QuizType.GUESS_CAR

    @property
    def name(self) -> str:
        return "Adivina el Auto"

    @property
    def description(self) -> str:
        return "Identifica autos por silueta, datos técnicos o características."

    @property
    def tags(self) -> list[str]:
        return ["autos", "coches", "motores", "velocidad"]

    @property
    def requires_images(self) -> bool:
        return True

    def build_prompt_instructions(self) -> str:
        return """
## Instrucciones para Adivina el Auto

- Cada pregunta da pistas sobre un AUTO O MODELO específico.
- Varía los formatos de pistas:
  1. Datos técnicos: "Motor V12, 0-100 en 2.9 segundos, fabricado en Maranello"
  2. Historia: "Fue el primer auto eléctrico de lujo y su empresa lleva el nombre de un inventor"
  3. Diseño: "Tiene las puertas de alas de gaviota y apareció en una película de los 80s"
  4. Apodos populares: "Le dicen 'El auto del pueblo' y fue diseñado por Ferdinand Porsche"
  5. Emojis: Usa emoji_pista (ej: 🏎️🇮🇹🐎 → "Ferrari")
  6. Récords: "Es el auto de producción más rápido del mundo, supera los 490 km/h"
- Las 4 opciones deben ser autos del MISMO SEGMENTO o MARCA.
  Ejemplo: Si es Ferrari F40 → Lamborghini Countach, Porsche 959, McLaren F1.
- Para FÁCIL: autos icónicos (Ferrari, Lamborghini, Tesla Model S, VW Beetle).
- Para MEDIO: modelos específicos populares (BMW M3, Toyota Supra, Mustang).
- Para DIFÍCIL: autos de nicho o concept cars.
- Para IMPOSIBLE: modelos de edición limitada o autos de competición específicos.
- En "imagen_url", poner el nombre del modelo para buscar la imagen.
- En la curiosidad, incluir datos de producción, récords o anécdotas.
"""

    def get_visual_config(self) -> dict[str, Any]:
        config = super().get_visual_config()
        config.update({
            "layout": "image_centered",
            "show_timer": True,
            "animation_reveal": "zoom",
            "background_style": "gradient",
            "theme_colors": {
                "primary": "#D32F2F",
                "secondary": "#212121",
            },
        })
        return config


PluginRegistry().register(GuessCarPlugin())
