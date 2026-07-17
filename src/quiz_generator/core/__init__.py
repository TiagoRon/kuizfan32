"""Enumeraciones del dominio para el generador de quizzes virales."""

from enum import StrEnum, auto


class QuizType(StrEnum):
    """Todos los tipos de quiz soportados por la plataforma.

    Cada tipo corresponde a un plugin que define su lógica de generación,
    plantilla visual y prompt de IA específico.
    """

    # --- Preferencias ---
    WOULD_YOU_RATHER = auto()
    FAST_CHOICE = auto()
    SURVIVAL_CHOICE = auto()

    # --- Adivinanzas de entidades ---
    GUESS_CHARACTER = auto()
    GUESS_COUNTRY = auto()
    GUESS_FLAG = auto()
    GUESS_LOGO = auto()
    GUESS_MOVIE = auto()
    GUESS_SONG = auto()
    GUESS_ANIMAL = auto()
    GUESS_BRAND = auto()
    GUESS_FOOD = auto()
    GUESS_CELEBRITY = auto()
    GUESS_FOOTBALL_PLAYER = auto()
    GUESS_POKEMON = auto()
    GUESS_CAR = auto()
    GUESS_VOICE = auto()
    GUESS_SOUND = auto()

    # --- Conocimiento ---
    TRIVIA = auto()
    TRUE_OR_FALSE = auto()
    EMOJI_QUIZ = auto()
    WHO_IS_MORE = auto()

    # --- Desafíos mentales ---
    MEMORY_CHALLENGE = auto()
    SPOT_THE_DIFFERENCE = auto()
    SPOT_THE_MISTAKE = auto()
    BRAIN_TEASER = auto()
    IMPOSSIBLE_QUIZ = auto()
    IQ_TEST = auto()
    RIDDLE = auto()
    OPTICAL_ILLUSION = auto()


class Difficulty(StrEnum):
    """Niveles de dificultad para las preguntas del quiz."""

    FACIL = "facil"
    MEDIO = "medio"
    DIFICIL = "dificil"
    IMPOSIBLE = "imposible"


class Emotion(StrEnum):
    """Emociones que el video puede evocar — usadas para selección de música y TTS."""

    CURIOSIDAD = auto()
    SORPRESA = auto()
    HUMOR = auto()
    NOSTALGIA = auto()
    TENSION = auto()
    EMOCION = auto()
    COMPETENCIA = auto()
    ORGULLO = auto()


class ViralTrigger(StrEnum):
    """Disparadores psicológicos virales que aumentan el engagement.

    Cada video debe usar al menos 2-3 de estos disparadores para
    maximizar la retención, los comentarios y los compartidos.
    """

    CURIOSIDAD = auto()        # "¿Puedes adivinar...?"
    SORPRESA = auto()          # Respuesta inesperada
    COMPETENCIA = auto()       # "Solo el 1% puede..."
    HUMOR = auto()             # Elementos cómicos
    NOSTALGIA = auto()         # Referencias a cultura pop clásica
    ORGULLO = auto()           # "Demuestra que eres un genio"
    FOMO = auto()              # "No te pierdas esto"
    RECOMPENSA = auto()        # Satisfacción por responder bien
    DESAFIO = auto()           # "¿Te atreves?"
    IDENTIDAD = auto()         # "Solo los verdaderos fans..."
    URGENCIA = auto()          # Temporizadores, presión de tiempo


class ExportFormat(StrEnum):
    """Formatos de exportación de video soportados."""

    MP4_H264 = "mp4_h264"
    MP4_H265 = "mp4_h265"
    WEBM_VP9 = "webm_vp9"


class ExportQuality(StrEnum):
    """Niveles de calidad para la exportación."""

    BORRADOR = "borrador"      # Rápido, baja calidad (para preview)
    NORMAL = "normal"          # Calidad estándar
    ALTA = "alta"              # Alta calidad (producción)
    MAXIMA = "maxima"          # Máxima calidad (lento)


class TTSProvider(StrEnum):
    """Proveedores de texto a voz disponibles."""

    EDGE_TTS = auto()
    ELEVENLABS = auto()
    OPENAI_TTS = auto()


class AIProviderType(StrEnum):
    """Proveedores de IA disponibles para generación de contenido."""

    GEMINI = auto()
    GROQ = auto()  # Alternativa gratuita


class VideoAspectRatio(StrEnum):
    """Proporciones de video soportadas."""

    VERTICAL_9_16 = "9:16"     # Shorts, Reels, TikTok
    SQUARE_1_1 = "1:1"         # Posts
    HORIZONTAL_16_9 = "16:9"   # YouTube estándar


class PipelineStep(StrEnum):
    """Pasos del pipeline de generación — para tracking de progreso."""

    INVESTIGAR_TENDENCIAS = auto()
    GENERAR_QUIZ = auto()
    VERIFICAR_DUPLICADOS = auto()
    GENERAR_AUDIO = auto()
    DESCARGAR_ASSETS = auto()
    COMPONER_VIDEO = auto()
    GENERAR_MINIATURA = auto()
    EXPORTAR = auto()
    GENERAR_METADATA = auto()
