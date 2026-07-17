"""Sistema de configuración con Pydantic Settings.

Carga configuración en cascada:
1. defaults.yaml (valores por defecto embebidos)
2. config/config.yaml (personalización del usuario)
3. Variables de entorno (máxima prioridad)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_project_root() -> Path:
    """Busca la raíz del proyecto subiendo desde el directorio actual."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return current


def _load_yaml_config(path: Path) -> dict[str, Any]:
    """Carga un archivo YAML. Retorna dict vacío si no existe."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Fusiona dos diccionarios de forma recursiva. Override gana sobre base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# =============================================================================
# Sub-configuraciones tipadas
# =============================================================================


class GeneralConfig(BaseSettings):
    """Configuración general del sistema."""

    idioma: str = "es"
    dificultad_default: str = "medio"
    num_preguntas_default: int = 8
    tema_default: str | None = None


class IAConfig(BaseSettings):
    """Configuración del proveedor de IA."""

    proveedor: str = "gemini"
    modelo: str = "gemini-2.0-flash"
    modelo_fallback: str = "gemini-1.5-flash"
    temperatura: float = 0.9
    max_tokens: int = 4096
    max_reintentos: int = 3
    timeout: int = 60


class VoicePreset(BaseSettings):
    """Preset de voz de TTS."""

    id: str
    nombre: str
    genero: str


class TTSConfig(BaseSettings):
    """Configuración de Texto a Voz."""

    proveedor: str = "edge_tts"
    voz: str = "es-MX-DaliaNeural"
    velocidad: float = 1.1
    voces_disponibles: list[dict[str, str]] = Field(default_factory=list)


class ColoresConfig(BaseSettings):
    """Paleta de colores del video."""

    fondo: str = "#0F0F1A"
    fondo_secundario: str = "#1A1A2E"
    primario: str = "#6C5CE7"
    primario_claro: str = "#A29BFE"
    secundario: str = "#00CEC9"
    correcto: str = "#00E676"
    incorrecto: str = "#FF1744"
    advertencia: str = "#FFD600"
    texto: str = "#FFFFFF"
    texto_secundario: str = "#B0B0B0"
    texto_oscuro: str = "#2D2D3A"
    gradiente_inicio: str = "#6C5CE7"
    gradiente_fin: str = "#00CEC9"


class FuentesConfig(BaseSettings):
    """Configuración de tipografía."""

    principal: str = "Montserrat"
    secundaria: str = "Inter"
    emoji: str = "Segoe UI Emoji"
    tamanio_titulo: int = 64
    tamanio_pregunta: int = 48
    tamanio_respuesta: int = 40
    tamanio_hook: int = 56
    tamanio_timer: int = 72
    tamanio_subtitulo: int = 36


class TiemposConfig(BaseSettings):
    """Configuración de tiempos del video (en segundos)."""

    intro: float = 2.0
    hook: float = 3.0
    pregunta_lectura: float = 2.0
    tiempo_por_pregunta: int = 10
    revelacion: float = 2.5
    curiosidad: float = 3.0
    transicion: float = 0.5
    outro: float = 3.0
    pausa_entre_preguntas: float = 0.3


class EfectosConfig(BaseSettings):
    """Configuración de efectos visuales."""

    shake_habilitado: bool = True
    shake_intensidad: int = 5
    flash_habilitado: bool = True
    flash_duracion: float = 0.15
    zoom_habilitado: bool = True
    zoom_factor: float = 1.05
    particulas_habilitadas: bool = False
    confeti_habilitado: bool = True
    progress_bar_habilitado: bool = True
    timer_habilitado: bool = True
    subtitulos_habilitados: bool = True


class VideoConfig(BaseSettings):
    """Configuración completa de video."""

    ancho: int = 1080
    alto: int = 1920
    fps: int = 60
    aspecto: str = "9:16"
    colores: ColoresConfig = Field(default_factory=ColoresConfig)
    fuentes: FuentesConfig = Field(default_factory=FuentesConfig)
    tiempos: TiemposConfig = Field(default_factory=TiemposConfig)
    efectos: EfectosConfig = Field(default_factory=EfectosConfig)


class AntiRepeticionConfig(BaseSettings):
    """Configuración del sistema anti-repetición."""

    habilitado: bool = True
    modelo_embeddings: str = "all-MiniLM-L6-v2"
    umbral_similitud: float = 0.85
    ruta_almacen: str = "data/embeddings"


class ExportacionConfig(BaseSettings):
    """Configuración de exportación de video."""

    formato: str = "mp4_h264"
    calidad: str = "alta"
    codec: str = "libx264"
    preset: str = "medium"
    crf: int = 18
    audio_bitrate: str = "192k"
    directorio_salida: str = "output"


class AssetsConfig(BaseSettings):
    """Configuración de gestión de recursos."""

    directorio_cache: str = "cache/assets"
    directorio_sonidos: str = "assets/sounds"
    directorio_musica: str = "assets/music"
    directorio_fuentes: str = "assets/fonts"
    directorio_imagenes: str = "assets/images"
    max_cache_mb: int = 500


class BaseDatosConfig(BaseSettings):
    """Configuración de la base de datos."""

    url: str = "sqlite+aiosqlite:///./data/quiz_generator.db"
    echo: bool = False


class GitHubActionsConfig(BaseSettings):
    """Configuración para ejecución en GitHub Actions."""

    timeout_minutos: int = 30
    artefacto_nombre: str = "quiz-video"
    retener_dias: int = 7


# =============================================================================
# Configuración Principal (Raíz)
# =============================================================================


class Settings(BaseSettings):
    """Configuración raíz del sistema — punto de entrada único.

    Carga valores en cascada: defaults.yaml → config.yaml → env vars.
    """

    model_config = SettingsConfigDict(
        env_prefix="QUIZ_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Claves API (inyectadas por env vars o .env)
    gemini_api_key: str = ""
    groq_api_key: str = ""
    elevenlabs_api_key: str = ""
    openai_api_key: str = ""

    # Sub-configuraciones
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    ia: IAConfig = Field(default_factory=IAConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    video: VideoConfig = Field(default_factory=VideoConfig)
    anti_repeticion: AntiRepeticionConfig = Field(default_factory=AntiRepeticionConfig)
    exportacion: ExportacionConfig = Field(default_factory=ExportacionConfig)
    assets: AssetsConfig = Field(default_factory=AssetsConfig)
    base_datos: BaseDatosConfig = Field(default_factory=BaseDatosConfig)
    github_actions: GitHubActionsConfig = Field(default_factory=GitHubActionsConfig)

    # Hooks predefinidos
    hooks_plantillas: list[str] = Field(default_factory=list)


def load_settings(
    config_path: Path | None = None,
    defaults_path: Path | None = None,
) -> Settings:
    """Carga la configuración completa del sistema.

    Orden de prioridad (de menor a mayor):
    1. defaults.yaml (embebido en el proyecto)
    2. config/config.yaml (personalización del usuario)
    3. Variables de entorno

    Args:
        config_path: Ruta al archivo config.yaml del usuario.
        defaults_path: Ruta al archivo defaults.yaml.

    Returns:
        Instancia de Settings completamente configurada.
    """
    project_root = _find_project_root()

    # Cargar defaults
    if defaults_path is None:
        defaults_path = project_root / "config" / "defaults.yaml"
    defaults = _load_yaml_config(defaults_path)

    # Cargar configuración del usuario
    if config_path is None:
        config_path = project_root / "config" / "config.yaml"
    user_config = _load_yaml_config(config_path)

    # Fusionar (usuario gana sobre defaults)
    merged = _deep_merge(defaults, user_config)

    # Extraer hooks si existen
    hooks_data = merged.pop("hooks", {})
    hooks_templates = hooks_data.get("plantillas", []) if isinstance(hooks_data, dict) else []

    # Extraer secciones de viral y github_actions que no son sub-modelos directos
    merged.pop("viral", None)

    # Construir Settings con los datos fusionados + env vars
    settings = Settings(
        hooks_plantillas=hooks_templates,
        **{k: v for k, v in merged.items() if k in Settings.model_fields},
    )

    return settings


# Singleton — se carga una vez y se reutiliza
_settings: Settings | None = None


def get_settings() -> Settings:
    """Obtiene la instancia singleton de configuración.

    En la primera llamada carga desde los archivos YAML.
    Las llamadas subsiguientes retornan la misma instancia.
    """
    global _settings  # noqa: PLW0603
    if _settings is None:
        _settings = load_settings()
    return _settings


def reset_settings() -> None:
    """Resetea el singleton de configuración (útil para tests)."""
    global _settings  # noqa: PLW0603
    _settings = None
