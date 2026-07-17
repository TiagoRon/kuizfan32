"""Clase base abstracta para plugins de tipo de quiz.

Cada tipo de quiz (trivia, emoji_quiz, guess_pokemon, etc.) hereda
de esta clase y define su prompt, validación y configuración visual.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from quiz_generator.core.enums import Difficulty, QuizType
from quiz_generator.core.models import Quiz


class BaseQuizPlugin(ABC):
    """Clase base abstracta que todo plugin de quiz debe implementar.

    Los plugins son la forma de extender el sistema con nuevos tipos
    de quiz sin modificar el núcleo del proyecto.
    """

    @property
    @abstractmethod
    def quiz_type(self) -> QuizType:
        """El tipo de quiz que este plugin maneja."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre legible del plugin en español."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Descripción corta del tipo de quiz."""

    @property
    def tags(self) -> list[str]:
        """Etiquetas para categorización del plugin."""
        return []

    @property
    def min_questions(self) -> int:
        """Mínimo de preguntas permitidas."""
        return 3

    @property
    def max_questions(self) -> int:
        """Máximo de preguntas permitidas."""
        return 20

    @property
    def default_questions(self) -> int:
        """Número de preguntas por defecto."""
        return 8

    @property
    def answers_per_question(self) -> int:
        """Número de opciones de respuesta por pregunta."""
        return 4

    @property
    def requires_images(self) -> bool:
        """Si este tipo de quiz necesita imágenes para funcionar."""
        return False

    @property
    def requires_audio(self) -> bool:
        """Si este tipo de quiz necesita clips de audio (ej: Adivina la Canción)."""
        return False

    @abstractmethod
    def build_prompt_instructions(self) -> str:
        """Retorna las instrucciones específicas para el prompt de IA.

        Estas instrucciones se inyectan en la plantilla de generación
        para que el LLM entienda las reglas del tipo de quiz.

        Returns:
            Texto con instrucciones específicas del tipo de quiz.
        """

    def validate_quiz(self, quiz: Quiz) -> list[str]:
        """Valida que el quiz generado cumple las reglas del tipo.

        La implementación por defecto verifica reglas básicas.
        Los plugins pueden sobrescribirla para validaciones específicas.

        Returns:
            Lista de errores encontrados (vacía si es válido).
        """
        errors: list[str] = []

        if not quiz.preguntas:
            errors.append("El quiz no tiene preguntas")
            return errors

        if len(quiz.preguntas) < self.min_questions:
            errors.append(
                f"Mínimo de preguntas no alcanzado: {len(quiz.preguntas)}/{self.min_questions}"
            )

        for i, pregunta in enumerate(quiz.preguntas):
            if not pregunta.texto.strip():
                errors.append(f"Pregunta {i + 1}: texto vacío")

            if not pregunta.respuestas:
                errors.append(f"Pregunta {i + 1}: sin opciones de respuesta")
                continue

            correctas = sum(1 for r in pregunta.respuestas if r.es_correcta)
            if correctas != 1:
                errors.append(
                    f"Pregunta {i + 1}: debe tener exactamente 1 respuesta correcta "
                    f"(tiene {correctas})"
                )

        return errors

    def get_visual_config(self) -> dict[str, Any]:
        """Retorna la configuración visual por defecto del plugin.

        Los plugins pueden sobrescribir para personalizar colores,
        layout, efectos, etc.

        Returns:
            Dict con preferencias visuales.
        """
        return {
            "layout": "classic",  # classic | grid | fullscreen
            "show_timer": True,
            "show_progress_bar": True,
            "show_question_number": True,
            "animation_reveal": "flash",  # flash | slide | zoom
            "animation_correct": "shake",  # shake | confetti | glow
            "background_style": "gradient",  # solid | gradient | animated
        }

    def get_suggested_duration(self, num_questions: int) -> float:
        """Calcula la duración estimada del video en segundos.

        Args:
            num_questions: Número de preguntas en el quiz.

        Returns:
            Duración estimada en segundos.
        """
        # Intro (2s) + Hook (3s) + Preguntas + Outro (3s)
        time_per_question = 12.0  # lectura + timer + revelación
        return 2.0 + 3.0 + (num_questions * time_per_question) + 3.0
