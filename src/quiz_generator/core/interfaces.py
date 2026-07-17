"""Interfaces abstractas (Puertos) — Arquitectura Hexagonal.

Define los contratos que deben cumplir los adaptadores (implementaciones concretas)
de cada componente del sistema. Esto permite intercambiar proveedores de IA, TTS,
imágenes, etc. sin modificar la lógica de negocio.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from quiz_generator.core.enums import Difficulty, QuizType
    from quiz_generator.core.models import (
        GenerationRequest,
        Quiz,
        QuizMetadata,
    )


# =============================================================================
# Proveedor de IA (LLM)
# =============================================================================


class IAIProvider(ABC):
    """Interfaz para proveedores de IA / LLM.

    Responsable de toda la generación de contenido textual:
    preguntas, respuestas, hooks, metadatos, etc.
    """

    @abstractmethod
    async def generate_quiz(
        self,
        quiz_type: QuizType,
        difficulty: Difficulty,
        num_questions: int,
        language: str = "es",
        topic: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Quiz:
        """Genera un quiz completo con preguntas, respuestas y hook."""

    @abstractmethod
    async def generate_hooks(
        self,
        quiz_type: QuizType,
        count: int = 5,
        language: str = "es",
    ) -> list[str]:
        """Genera hooks virales para un tipo de quiz."""

    @abstractmethod
    async def generate_metadata(
        self,
        quiz: Quiz,
        language: str = "es",
    ) -> QuizMetadata:
        """Genera metadatos de publicación (título, descripción, hashtags)."""

    @abstractmethod
    async def analyze_trends(
        self,
        category: str,
        language: str = "es",
    ) -> dict[str, Any]:
        """Analiza tendencias actuales para una categoría."""


# =============================================================================
# Proveedor de TTS (Texto a Voz)
# =============================================================================


class TTSTimestamp(ABC):
    """Marca de tiempo de una palabra en el audio generado."""

    @property
    @abstractmethod
    def word(self) -> str:
        """Palabra pronunciada."""

    @property
    @abstractmethod
    def start_ms(self) -> int:
        """Inicio en milisegundos."""

    @property
    @abstractmethod
    def end_ms(self) -> int:
        """Fin en milisegundos."""


class ITTSProvider(ABC):
    """Interfaz para proveedores de Texto a Voz.

    Genera archivos de audio a partir de texto, con control
    sobre la voz, velocidad y emoción.
    """

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        output_path: Path,
        voice: str = "es-MX-DaliaNeural",
        rate: float = 1.0,
    ) -> Path:
        """Sintetiza texto a un archivo de audio.

        Args:
            text: Texto a sintetizar.
            output_path: Ruta donde guardar el archivo de audio.
            voice: Identificador de la voz a usar.
            rate: Velocidad de habla (1.0 = normal).

        Returns:
            Ruta al archivo de audio generado.
        """

    @abstractmethod
    async def synthesize_with_timestamps(
        self,
        text: str,
        output_path: Path,
        voice: str = "es-MX-DaliaNeural",
        rate: float = 1.0,
    ) -> tuple[Path, list[dict[str, Any]]]:
        """Sintetiza texto y retorna marcas de tiempo por palabra.

        Returns:
            Tupla con (ruta_audio, lista_de_timestamps).
            Cada timestamp es un dict con: word, start_ms, end_ms.
        """

    @abstractmethod
    async def list_voices(self, language: str = "es") -> list[dict[str, str]]:
        """Lista las voces disponibles para un idioma.

        Returns:
            Lista de dicts con: name, gender, language, provider.
        """


# =============================================================================
# Plugin de Quiz
# =============================================================================


class IQuizPlugin(ABC):
    """Interfaz para plugins de tipo de quiz.

    Cada tipo de quiz (trivia, guess_pokemon, emoji_quiz, etc.)
    se implementa como un plugin que define su lógica específica.
    """

    @property
    @abstractmethod
    def quiz_type(self) -> QuizType:
        """El tipo de quiz que este plugin maneja."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre legible del plugin."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Descripción corta del tipo de quiz."""

    @abstractmethod
    def build_prompt(
        self,
        difficulty: Difficulty,
        num_questions: int,
        language: str = "es",
        topic: str | None = None,
    ) -> str:
        """Construye el prompt de IA para generar el quiz.

        Returns:
            Prompt completo listo para enviar al LLM.
        """

    @abstractmethod
    def validate_quiz(self, quiz: Quiz) -> list[str]:
        """Valida que el quiz generado cumple las reglas del tipo.

        Returns:
            Lista de errores encontrados (vacía si es válido).
        """

    @abstractmethod
    def get_visual_config(self) -> dict[str, Any]:
        """Retorna la configuración visual específica del tipo de quiz.

        Returns:
            Dict con preferencias de diseño (colores, layout, efectos, etc.)
        """


# =============================================================================
# Gestor de Assets
# =============================================================================


class IAssetManager(ABC):
    """Interfaz para la gestión de recursos (imágenes, sonidos, etc.)."""

    @abstractmethod
    async def get_image(
        self,
        query: str,
        category: str | None = None,
    ) -> Path | None:
        """Busca y descarga una imagen según el criterio dado.

        Returns:
            Ruta local a la imagen descargada, o None si no se encontró.
        """

    @abstractmethod
    async def get_sound(self, sound_name: str) -> Path | None:
        """Obtiene un efecto de sonido por nombre.

        Returns:
            Ruta local al archivo de sonido, o None si no existe.
        """

    @abstractmethod
    async def get_music(
        self,
        mood: str,
        duration_seconds: float,
    ) -> Path | None:
        """Obtiene una pista de música de fondo según el estado de ánimo.

        Returns:
            Ruta local al archivo de música, o None si no se encontró.
        """

    @abstractmethod
    def clear_cache(self) -> int:
        """Limpia la caché de assets descargados.

        Returns:
            Número de archivos eliminados.
        """


# =============================================================================
# Motor Anti-Repetición
# =============================================================================


class IAntiRepetitionEngine(ABC):
    """Interfaz para el sistema de detección de duplicados."""

    @abstractmethod
    async def is_duplicate(
        self,
        text: str,
        threshold: float = 0.85,
    ) -> bool:
        """Verifica si un texto es demasiado similar a uno ya registrado.

        Args:
            text: Texto a verificar.
            threshold: Umbral de similitud (0.0 a 1.0). Mayor = más estricto.

        Returns:
            True si el texto es considerado duplicado.
        """

    @abstractmethod
    async def register(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        """Registra un texto nuevo en el almacén de embeddings."""

    @abstractmethod
    async def check_batch(
        self,
        texts: list[str],
        threshold: float = 0.85,
    ) -> list[bool]:
        """Verifica un lote de textos. Retorna una lista de booleans (True = duplicado)."""


# =============================================================================
# Repositorios de Datos
# =============================================================================


class IQuizRepository(ABC):
    """Interfaz para el repositorio de quizzes en la base de datos."""

    @abstractmethod
    async def save(self, quiz: Quiz) -> str:
        """Guarda un quiz. Retorna el ID asignado."""

    @abstractmethod
    async def get_by_id(self, quiz_id: str) -> Quiz | None:
        """Obtiene un quiz por su ID."""

    @abstractmethod
    async def list_all(
        self,
        quiz_type: QuizType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Quiz]:
        """Lista quizzes con filtros opcionales."""

    @abstractmethod
    async def count(self, quiz_type: QuizType | None = None) -> int:
        """Cuenta el total de quizzes almacenados."""

    @abstractmethod
    async def delete(self, quiz_id: str) -> bool:
        """Elimina un quiz. Retorna True si existía."""
