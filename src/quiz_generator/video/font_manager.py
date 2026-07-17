"""Gestor de fuentes con soporte de emojis multiplataforma.

Resuelve el problema de renderizado de emojis en Pillow:
- Descarga automática de Google Fonts (Montserrat, Inter, Noto Color Emoji)
- Búsqueda de fuentes en el sistema (Windows/Linux/Mac)
- Detección de codepoints emoji para renderizado separado
- Caché en assets/fonts/ para evitar re-descargas
"""

from __future__ import annotations

import logging
import re
import struct
import unicodedata
from pathlib import Path
from typing import Any

from PIL import ImageFont

logger = logging.getLogger(__name__)

# URLs de Google Fonts (archivos .ttf directos)
_GOOGLE_FONTS_URLS: dict[str, str] = {
    "Montserrat-Bold": (
        "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf"
    ),
    "Montserrat-ExtraBold": (
        "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-ExtraBold.ttf"
    ),
    "Montserrat-SemiBold": (
        "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-SemiBold.ttf"
    ),
    "Inter-Regular": (
        "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Regular.ttf"
    ),
    "Inter-Bold": (
        "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Bold.ttf"
    ),
    "Inter-SemiBold": (
        "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-SemiBold.ttf"
    ),
    "NotoColorEmoji": (
        "https://github.com/googlefonts/noto-emoji/raw/main/fonts/NotoColorEmoji.ttf"
    ),
}

# Rutas del sistema donde buscar fuentes
_SYSTEM_FONT_DIRS: list[str] = [
    # Windows
    r"C:\Windows\Fonts",
    # Linux
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    "~/.local/share/fonts",
    "~/.fonts",
    # macOS
    "/Library/Fonts",
    "/System/Library/Fonts",
    "~/Library/Fonts",
]

# Mapeo de nombres amigables → nombres de archivo en el sistema
_SYSTEM_FONT_ALIASES: dict[str, list[str]] = {
    "Montserrat": ["Montserrat-Bold.ttf", "Montserrat-SemiBold.ttf", "montserrat-bold.ttf"],
    "Inter": ["Inter-Regular.ttf", "Inter-SemiBold.ttf", "inter.ttf"],
    "Segoe UI Emoji": ["seguiemj.ttf", "SegoeUIEmoji.ttf"],
    "Noto Color Emoji": ["NotoColorEmoji.ttf", "NotoColorEmoji-Regular.ttf"],
    "Arial": ["arial.ttf", "Arial.ttf"],
}

# Rango de codepoints emoji (simplificado pero efectivo)
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
    "\U0001F680-\U0001F6FF"  # Transport and Map
    "\U0001F1E0-\U0001F1FF"  # Flags
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U0000FE00-\U0000FE0F"  # Variation Selectors
    "\U0000200D"             # Zero Width Joiner
    "\U000023EA-\U000023F3"  # Misc symbols
    "\U00002600-\U000026FF"  # Misc symbols
    "\U00002B50-\U00002B55"  # Stars
    "\U0000203C-\U00003299"  # CJK and misc
    "]+",
)


class FontManager:
    """Gestor de fuentes con descarga automática y soporte emoji.

    Resuelve automáticamente fuentes por nombre, buscando en:
    1. Caché local (assets/fonts/)
    2. Fuentes del sistema
    3. Descarga automática de Google Fonts (si hay red)

    Para emojis, detecta codepoints y usa Noto Color Emoji como
    fuente dedicada, evitando los cuadrados de "missing glyph".
    """

    def __init__(self, cache_dir: str | Path = "assets/fonts") -> None:
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}
        self._path_cache: dict[str, Path] = {}
        self._emoji_font_path: Path | None = None
        self._emoji_font_cache: dict[int, ImageFont.FreeTypeFont] = {}

        # Intentar localizar la fuente de emojis al inicio
        self._emoji_font_path = self._resolve_emoji_font()

    def _resolve_emoji_font(self) -> Path | None:
        """Busca la mejor fuente de emojis disponible."""
        # 1. Buscar en caché local
        local = self._cache_dir / "NotoColorEmoji.ttf"
        if local.exists():
            return local

        # 2. Buscar Segoe UI Emoji en sistema (Windows)
        segoe = self._find_system_font("Segoe UI Emoji")
        if segoe:
            return segoe

        # 3. Buscar Noto Color Emoji en sistema
        noto = self._find_system_font("Noto Color Emoji")
        if noto:
            return noto

        logger.warning(
            "No se encontró fuente de emojis. Los emojis podrían no renderizarse. "
            "Ejecuta FontManager.download_fonts() para descargar Noto Color Emoji."
        )
        return None

    def _find_system_font(self, name: str) -> Path | None:
        """Busca una fuente por nombre en las rutas del sistema."""
        aliases = _SYSTEM_FONT_ALIASES.get(name, [f"{name}.ttf"])

        for font_dir in _SYSTEM_FONT_DIRS:
            font_path = Path(font_dir).expanduser()
            if not font_path.exists():
                continue
            for alias in aliases:
                candidate = font_path / alias
                if candidate.exists():
                    logger.debug("Fuente encontrada: %s → %s", name, candidate)
                    return candidate
                # Búsqueda recursiva limitada (1 nivel)
                for sub in font_path.iterdir():
                    if sub.is_dir():
                        candidate = sub / alias
                        if candidate.exists():
                            logger.debug("Fuente encontrada: %s → %s", name, candidate)
                            return candidate
        return None

    def resolve_font_path(self, name: str) -> Path:
        """Resuelve un nombre de fuente a una ruta de archivo .ttf.

        Orden de búsqueda:
        1. Caché de paths resueltos
        2. Caché local (assets/fonts/)
        3. Sistema operativo
        4. Fallback a Arial

        Args:
            name: Nombre de la fuente (ej: "Montserrat", "Inter")

        Returns:
            Path al archivo .ttf de la fuente.
        """
        if name in self._path_cache:
            return self._path_cache[name]

        # 1. Buscar en caché local
        for suffix in ["-Bold.ttf", "-SemiBold.ttf", "-Regular.ttf", ".ttf"]:
            local = self._cache_dir / f"{name}{suffix}"
            if local.exists():
                self._path_cache[name] = local
                return local

        # 2. Buscar en sistema
        system_path = self._find_system_font(name)
        if system_path:
            self._path_cache[name] = system_path
            return system_path

        # 3. Intentar como nombre directo de archivo (ej: "arial.ttf")
        try:
            ImageFont.truetype(name, 12)
            # Si no lanza excepción, PIL puede encontrarla
            self._path_cache[name] = Path(name)
            return Path(name)
        except OSError:
            pass

        # 4. Fallback
        logger.warning("Fuente '%s' no encontrada, usando fallback", name)
        fallback = self._find_system_font("Arial")
        if fallback:
            self._path_cache[name] = fallback
            return fallback

        # Último recurso: fuente por defecto de Pillow
        self._path_cache[name] = Path("arial.ttf")
        return Path("arial.ttf")

    def get_font(self, name: str, size: int) -> ImageFont.FreeTypeFont:
        """Obtiene una fuente por nombre y tamaño con caché.

        Args:
            name: Nombre de la fuente.
            size: Tamaño en píxeles.

        Returns:
            Objeto FreeTypeFont listo para usar con Pillow.
        """
        key = (name, size)
        if key not in self._font_cache:
            path = self.resolve_font_path(name)
            try:
                self._font_cache[key] = ImageFont.truetype(str(path), size)
            except OSError:
                try:
                    self._font_cache[key] = ImageFont.truetype("arial.ttf", size)
                except OSError:
                    self._font_cache[key] = ImageFont.load_default(size)
        return self._font_cache[key]

    def get_emoji_font(self, size: int) -> ImageFont.FreeTypeFont | None:
        """Obtiene la fuente de emojis al tamaño solicitado.

        Returns:
            FreeTypeFont para emojis, o None si no hay fuente disponible.
        """
        if not self._emoji_font_path:
            return None

        if size not in self._emoji_font_cache:
            try:
                self._emoji_font_cache[size] = ImageFont.truetype(
                    str(self._emoji_font_path), size,
                )
            except OSError:
                logger.warning("Error al cargar fuente emoji: %s", self._emoji_font_path)
                return None

        return self._emoji_font_cache[size]

    @staticmethod
    def is_emoji(char: str) -> bool:
        """Determina si un carácter es un emoji."""
        if len(char) == 0:
            return False
        # Verificar por categoría Unicode
        cat = unicodedata.category(char[0])
        if cat == "So":  # Symbol, Other
            return True
        # Verificar por rango de codepoint
        cp = ord(char[0])
        return (
            0x1F600 <= cp <= 0x1F64F  # Emoticons
            or 0x1F300 <= cp <= 0x1F5FF  # Misc Symbols
            or 0x1F680 <= cp <= 0x1F6FF  # Transport
            or 0x1F1E0 <= cp <= 0x1F1FF  # Flags
            or 0x1F900 <= cp <= 0x1F9FF  # Supplemental
            or 0x1FA00 <= cp <= 0x1FAFF  # Extended-A
            or 0x2702 <= cp <= 0x27B0  # Dingbats
            or 0x2600 <= cp <= 0x26FF  # Misc symbols
            or 0x2B50 <= cp <= 0x2B55  # Stars
            or 0xFE00 <= cp <= 0xFE0F  # Variation Selectors
            or cp == 0x200D  # Zero Width Joiner
        )

    @staticmethod
    def split_text_and_emojis(text: str) -> list[tuple[str, bool]]:
        """Divide texto en segmentos de texto puro y emojis.

        Returns:
            Lista de (segmento, es_emoji) tuplas.
            Ejemplo: "Hola 🌍 Mundo" → [("Hola ", False), ("🌍", True), (" Mundo", False)]
        """
        segments: list[tuple[str, bool]] = []
        current_text = ""

        i = 0
        chars = list(text)
        while i < len(chars):
            char = chars[i]

            # Verificar si es inicio de una secuencia emoji
            if FontManager.is_emoji(char):
                # Guardar texto acumulado
                if current_text:
                    segments.append((current_text, False))
                    current_text = ""

                # Acumular toda la secuencia emoji (incluyendo ZWJ y variation selectors)
                emoji_seq = char
                i += 1
                while i < len(chars) and (
                    FontManager.is_emoji(chars[i])
                    or ord(chars[i]) == 0x200D  # ZWJ
                    or 0xFE00 <= ord(chars[i]) <= 0xFE0F  # Variation selectors
                ):
                    emoji_seq += chars[i]
                    i += 1

                segments.append((emoji_seq, True))
            else:
                current_text += char
                i += 1

        if current_text:
            segments.append((current_text, False))

        return segments if segments else [(text, False)]

    async def download_fonts(self) -> list[Path]:
        """Descarga las fuentes de Google Fonts necesarias.

        Descarga Montserrat-Bold, Inter-Regular/Bold, y Noto Color Emoji
        al directorio de caché. Solo descarga las que no existan aún.

        Returns:
            Lista de paths de fuentes descargadas.
        """
        import httpx

        downloaded: list[Path] = []

        async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
            for font_name, url in _GOOGLE_FONTS_URLS.items():
                target = self._cache_dir / f"{font_name}.ttf"
                if target.exists():
                    logger.debug("Fuente ya existe: %s", target)
                    continue

                try:
                    logger.info("Descargando fuente: %s ...", font_name)
                    response = await client.get(url)
                    response.raise_for_status()

                    target.write_bytes(response.content)
                    downloaded.append(target)
                    logger.info(
                        "Fuente descargada: %s (%.1f KB)",
                        font_name,
                        len(response.content) / 1024,
                    )
                except Exception:
                    logger.exception("Error al descargar fuente: %s", font_name)

        # Actualizar la fuente de emojis si se descargó
        if not self._emoji_font_path:
            self._emoji_font_path = self._resolve_emoji_font()

        # Limpiar caché de paths para que se re-resuelvan
        self._path_cache.clear()

        return downloaded

    def download_fonts_sync(self) -> list[Path]:
        """Versión síncrona de download_fonts (para uso fuera de async)."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            # Si hay loop activo, crear una coroutine y ejecutarla en un thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return loop.run_in_executor(
                    pool,
                    lambda: asyncio.run(self.download_fonts()),
                )
        except RuntimeError:
            return asyncio.run(self.download_fonts())
