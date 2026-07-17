"""Modelos de dominio inmutables para el generador de quizzes virales.

Todos los modelos son frozen (inmutables) para garantizar la integridad
de los datos a lo largo del pipeline de generación.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from quiz_generator.core.enums import (
    Difficulty,
    Emotion,
    ExportQuality,
    QuizType,
    VideoAspectRatio,
    ViralTrigger,
)


def _generate_id() -> str:
    """Genera un ID único para cada entidad del dominio."""
    return uuid.uuid4().hex[:12]


# =============================================================================
# Modelos del Quiz
# =============================================================================


class Answer(BaseModel, frozen=True):
    """Una opción de respuesta para una pregunta del quiz."""

    texto: str = Field(description="Texto visible de la respuesta")
    es_correcta: bool = Field(default=False, description="Si esta respuesta es la correcta")
    explicacion: str | None = Field(
        default=None,
        description="Explicación o dato curioso que aparece al revelar la respuesta",
    )
    emoji: str | None = Field(
        default=None,
        description="Emoji representativo de esta opción",
    )


class Question(BaseModel, frozen=True):
    """Una pregunta individual dentro del quiz."""

    id: str = Field(default_factory=_generate_id)
    texto: str = Field(description="Texto de la pregunta")
    respuestas: list[Answer] = Field(
        description="Lista de opciones de respuesta (2-4 opciones)",
    )
    dificultad: Difficulty = Field(default=Difficulty.MEDIO)
    tiempo_segundos: int = Field(
        default=10,
        ge=3,
        le=30,
        description="Tiempo límite para responder (en segundos)",
    )
    curiosidad: str | None = Field(
        default=None,
        description="Dato curioso que se muestra después de la respuesta",
    )
    imagen_url: str | None = Field(
        default=None,
        description="URL de imagen asociada (para quizzes visuales)",
    )
    emoji_pista: str | None = Field(
        default=None,
        description="Secuencia de emojis como pista (para Emoji Quiz)",
    )
    categoria: str | None = Field(
        default=None,
        description="Categoría temática de la pregunta",
    )


class Hook(BaseModel, frozen=True):
    """Un gancho viral para el inicio del video.

    Los hooks son frases diseñadas para captar la atención del espectador
    en los primeros 1-3 segundos del video.
    """

    texto: str = Field(description="Texto del hook")
    tipo: ViralTrigger = Field(description="Tipo de disparador viral usado")
    emoji: str | None = Field(default=None, description="Emoji acompañante")


class QuizMetadata(BaseModel, frozen=True):
    """Metadatos del quiz para publicación en redes sociales."""

    titulo: str = Field(description="Título del video para la plataforma")
    descripcion: str = Field(description="Descripción del video")
    hashtags: list[str] = Field(default_factory=list, description="Hashtags relevantes")
    prompt_miniatura: str | None = Field(
        default=None,
        description="Prompt para generar la miniatura del video",
    )
    cta: str | None = Field(
        default=None,
        description="Call-to-Action final del video",
    )


class Quiz(BaseModel, frozen=True):
    """Modelo principal del quiz — representa un video completo a generar."""

    id: str = Field(default_factory=_generate_id)
    tipo: QuizType = Field(description="Tipo de quiz")
    dificultad: Difficulty = Field(default=Difficulty.MEDIO)
    idioma: str = Field(default="es", description="Código de idioma ISO 639-1")

    hook: Hook = Field(description="Gancho viral de apertura")
    preguntas: list[Question] = Field(
        description="Lista de preguntas del quiz (entre 5 y 15)",
    )
    metadata: QuizMetadata = Field(description="Metadatos para publicación")

    disparadores_virales: list[ViralTrigger] = Field(
        default_factory=list,
        description="Disparadores psicológicos aplicados al video",
    )
    emociones: list[Emotion] = Field(
        default_factory=list,
        description="Emociones que evoca el contenido del quiz",
    )

    creado_en: datetime = Field(default_factory=datetime.now)


# =============================================================================
# Especificaciones de Producción
# =============================================================================


class AudioSpec(BaseModel, frozen=True):
    """Especificación de audio para la generación del video."""

    voz: str = Field(
        default="es-MX-DaliaNeural",
        description="Identificador de la voz de TTS",
    )
    velocidad: float = Field(
        default=1.1,
        ge=0.5,
        le=2.0,
        description="Velocidad de narración (1.0 = normal)",
    )
    volumen_musica: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Volumen de la música de fondo (0.0 = silencio)",
    )
    volumen_efectos: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Volumen de los efectos de sonido",
    )


class VideoSpec(BaseModel, frozen=True):
    """Especificación técnica del video a generar."""

    ancho: int = Field(default=1080, description="Ancho en píxeles")
    alto: int = Field(default=1920, description="Alto en píxeles")
    fps: int = Field(default=60, ge=24, le=120, description="Fotogramas por segundo")
    aspecto: VideoAspectRatio = Field(default=VideoAspectRatio.VERTICAL_9_16)
    calidad: ExportQuality = Field(default=ExportQuality.ALTA)

    # Colores del tema
    color_fondo: str = Field(default="#0F0F1A", description="Color de fondo principal (hex)")
    color_primario: str = Field(default="#6C5CE7", description="Color primario/acentuado (hex)")
    color_correcto: str = Field(default="#00E676", description="Color para respuesta correcta")
    color_incorrecto: str = Field(default="#FF1744", description="Color para respuesta incorrecta")
    color_texto: str = Field(default="#FFFFFF", description="Color del texto principal")
    color_texto_secundario: str = Field(default="#B0B0B0", description="Color de texto secundario")

    # Tipografía
    fuente_principal: str = Field(default="Montserrat", description="Fuente para títulos")
    fuente_secundaria: str = Field(default="Inter", description="Fuente para cuerpo de texto")

    # Tiempos (segundos)
    duracion_intro: float = Field(default=2.0, description="Duración del intro/hook")
    duracion_revelacion: float = Field(default=2.0, description="Duración de la revelación")
    duracion_outro: float = Field(default=3.0, description="Duración del outro/CTA")


class ThumbnailSpec(BaseModel, frozen=True):
    """Especificación para la generación de miniaturas."""

    ancho: int = Field(default=1080)
    alto: int = Field(default=1920)
    texto_principal: str = Field(description="Texto grande de la miniatura")
    texto_secundario: str | None = Field(default=None, description="Texto secundario/subtítulo")
    emojis: list[str] = Field(default_factory=list, description="Emojis decorativos")
    color_fondo: str = Field(default="#0F0F1A")
    color_texto: str = Field(default="#FFFFFF")


# =============================================================================
# Modelos del Pipeline
# =============================================================================


class GenerationRequest(BaseModel):
    """Solicitud de generación de un video de quiz."""

    tipo: QuizType = Field(description="Tipo de quiz a generar")
    dificultad: Difficulty = Field(default=Difficulty.MEDIO)
    num_preguntas: int = Field(default=8, ge=3, le=20)
    idioma: str = Field(default="es")
    tema: str | None = Field(
        default=None,
        description="Tema específico opcional (ej: 'Pokémon Gen 1')",
    )
    video_spec: VideoSpec = Field(default_factory=VideoSpec)
    audio_spec: AudioSpec = Field(default_factory=AudioSpec)


class GenerationResult(BaseModel):
    """Resultado final de una generación de video completa."""

    id: str = Field(default_factory=_generate_id)
    quiz: Quiz = Field(description="Quiz generado")
    video_path: str | None = Field(default=None, description="Ruta al video exportado")
    thumbnail_path: str | None = Field(default=None, description="Ruta a la miniatura")
    duracion_total: float = Field(default=0.0, description="Duración total del video (segundos)")
    metadata_extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadatos adicionales del proceso",
    )
    errores: list[str] = Field(
        default_factory=list,
        description="Errores no fatales ocurridos durante la generación",
    )
    creado_en: datetime = Field(default_factory=datetime.now)
