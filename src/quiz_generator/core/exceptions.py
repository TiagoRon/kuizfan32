"""Jerarquía de excepciones personalizadas.

Todas las excepciones del proyecto heredan de QuizGeneratorError,
permitiendo capturar errores de forma granular o general.
"""


class QuizGeneratorError(Exception):
    """Excepción base de todo el proyecto."""

    def __init__(self, message: str = "Error en el generador de quizzes") -> None:
        self.message = message
        super().__init__(self.message)


# --- Errores de IA ---


class AIProviderError(QuizGeneratorError):
    """Error al comunicarse con el proveedor de IA."""

    def __init__(self, provider: str, detail: str) -> None:
        super().__init__(f"Error del proveedor de IA '{provider}': {detail}")
        self.provider = provider
        self.detail = detail


class AIRateLimitError(AIProviderError):
    """Se excedió el límite de solicitudes del proveedor de IA."""

    def __init__(self, provider: str, retry_after: float | None = None) -> None:
        detail = "Límite de solicitudes excedido"
        if retry_after:
            detail += f" — reintentar en {retry_after}s"
        super().__init__(provider, detail)
        self.retry_after = retry_after


class AIInvalidResponseError(AIProviderError):
    """La respuesta de la IA no tiene el formato esperado."""

    def __init__(self, provider: str, detail: str = "Respuesta inválida") -> None:
        super().__init__(provider, detail)


# --- Errores de TTS ---


class TTSError(QuizGeneratorError):
    """Error en la generación de texto a voz."""

    def __init__(self, provider: str, detail: str) -> None:
        super().__init__(f"Error de TTS '{provider}': {detail}")
        self.provider = provider
        self.detail = detail


class VoiceNotFoundError(TTSError):
    """La voz solicitada no existe o no está disponible."""

    def __init__(self, provider: str, voice: str) -> None:
        super().__init__(provider, f"Voz no encontrada: '{voice}'")
        self.voice = voice


# --- Errores de Video ---


class VideoError(QuizGeneratorError):
    """Error en la composición o renderizado de video."""


class RenderError(VideoError):
    """Error durante el renderizado del video con FFmpeg."""

    def __init__(self, detail: str, ffmpeg_output: str | None = None) -> None:
        super().__init__(f"Error de renderizado: {detail}")
        self.ffmpeg_output = ffmpeg_output


# --- Errores de Plugins ---


class PluginError(QuizGeneratorError):
    """Error relacionado con el sistema de plugins."""


class PluginNotFoundError(PluginError):
    """El plugin solicitado no está registrado."""

    def __init__(self, quiz_type: str) -> None:
        super().__init__(f"Plugin no encontrado para el tipo de quiz: '{quiz_type}'")
        self.quiz_type = quiz_type


class PluginValidationError(PluginError):
    """El quiz generado no pasó la validación del plugin."""

    def __init__(self, quiz_type: str, errors: list[str]) -> None:
        error_list = "; ".join(errors)
        super().__init__(f"Validación fallida para '{quiz_type}': {error_list}")
        self.quiz_type = quiz_type
        self.errors = errors


# --- Errores de Assets ---


class AssetError(QuizGeneratorError):
    """Error en la gestión de recursos."""


class AssetNotFoundError(AssetError):
    """El recurso solicitado no se encontró."""

    def __init__(self, asset_type: str, query: str) -> None:
        super().__init__(f"Asset no encontrado — tipo: '{asset_type}', búsqueda: '{query}'")
        self.asset_type = asset_type
        self.query = query


class AssetDownloadError(AssetError):
    """Error al descargar un recurso externo."""

    def __init__(self, url: str, status_code: int | None = None) -> None:
        detail = f"Error al descargar '{url}'"
        if status_code:
            detail += f" (HTTP {status_code})"
        super().__init__(detail)
        self.url = url
        self.status_code = status_code


# --- Errores de Anti-Repetición ---


class DuplicateContentError(QuizGeneratorError):
    """El contenido generado es demasiado similar a uno existente."""

    def __init__(self, text: str, similarity: float) -> None:
        super().__init__(
            f"Contenido duplicado detectado (similitud: {similarity:.2%}): '{text[:80]}...'"
        )
        self.text = text
        self.similarity = similarity


# --- Errores de Configuración ---


class ConfigurationError(QuizGeneratorError):
    """Error en la configuración del sistema."""


class MissingAPIKeyError(ConfigurationError):
    """Falta una clave API requerida."""

    def __init__(self, provider: str, env_var: str) -> None:
        super().__init__(
            f"Falta la clave API para '{provider}'. "
            f"Configura la variable de entorno: {env_var}"
        )
        self.provider = provider
        self.env_var = env_var


# --- Errores del Pipeline ---


class PipelineError(QuizGeneratorError):
    """Error en el pipeline de generación."""

    def __init__(self, step: str, detail: str) -> None:
        super().__init__(f"Error en el paso '{step}': {detail}")
        self.step = step
        self.detail = detail
