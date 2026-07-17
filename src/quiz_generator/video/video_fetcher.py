"""Buscador y descargador de videos de respuesta desde Pexels.

Busca videos cortos relacionados con la respuesta correcta de cada
pregunta para mostrar clips dinámicos en lugar de imágenes estáticas.

Características:
- Búsqueda por keyword en Pexels API (gratuita)
- Descarga automática en resolución vertical (9:16)
- Caché en disco para evitar re-descargas
- Fallback: si no hay API key o no encuentra video, se usa None
  y el engine genera un clip animado de texto
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Orientaciones preferidas para video vertical
_PREFERRED_ORIENTATIONS = ["portrait", "square"]
_MIN_DURATION = 3  # segundos mínimos
_MAX_DURATION = 15  # segundos máximos


class VideoFetcher:
    """Busca y descarga videos cortos desde Pexels API.

    Los videos se buscan por keyword (la respuesta correcta del quiz)
    y se descargan en la resolución más adecuada para formato vertical.
    Se cachean en disco para reutilización.
    """

    def __init__(
        self,
        api_key: str = "",
        cache_dir: str | Path = "cache/assets/videos",
    ) -> None:
        self._api_key = api_key
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_available(self) -> bool:
        """Verifica si el fetcher puede funcionar (tiene API key)."""
        return bool(self._api_key)

    async def fetch_video(
        self,
        keyword: str,
        max_duration: int = _MAX_DURATION,
    ) -> Path | None:
        """Busca y descarga un video corto relacionado con el keyword.

        Args:
            keyword: Término de búsqueda (ej: "lion", "France", "pizza").
            max_duration: Duración máxima del video en segundos.

        Returns:
            Path al video descargado, o None si no se encontró o hay error.
        """
        if not self._api_key:
            logger.debug("Sin API key de Pexels, usando fallback")
            return None

        # Verificar caché
        cache_key = hashlib.md5(keyword.lower().encode()).hexdigest()[:12]
        cached = self._cache_dir / f"{cache_key}.mp4"
        if cached.exists():
            logger.debug("Video en caché: %s → %s", keyword, cached)
            return cached

        try:
            import httpx

            # Traducir keyword al inglés para mejores resultados en Pexels
            search_query = keyword.strip()

            async with httpx.AsyncClient(timeout=30) as client:
                # Buscar videos
                response = await client.get(
                    "https://api.pexels.com/videos/search",
                    params={
                        "query": search_query,
                        "per_page": 10,
                        "size": "medium",
                    },
                    headers={"Authorization": self._api_key},
                )
                response.raise_for_status()

                data = response.json()
                videos = data.get("videos", [])

                if not videos:
                    logger.info("No se encontraron videos para: '%s'", keyword)
                    return None

                # Seleccionar el mejor video
                best = self._select_best_video(videos, max_duration)
                if not best:
                    logger.info("No hay video adecuado para: '%s'", keyword)
                    return None

                # Descargar
                video_url = best["url"]
                logger.info(
                    "Descargando video: '%s' → %s",
                    keyword, video_url[:80],
                )

                video_response = await client.get(video_url)
                video_response.raise_for_status()

                cached.write_bytes(video_response.content)
                logger.info(
                    "Video descargado: %s (%.1f MB)",
                    cached, len(video_response.content) / (1024 * 1024),
                )
                return cached

        except Exception:
            logger.exception("Error al buscar/descargar video para: '%s'", keyword)
            return None

    def _select_best_video(
        self,
        videos: list[dict[str, Any]],
        max_duration: int,
    ) -> dict[str, str] | None:
        """Selecciona el mejor video y archivo de video de la lista.

        Prioriza:
        1. Videos verticales o cuadrados
        2. Duración entre 3 y max_duration segundos
        3. Resolución HD (720p-1080p)
        """
        candidates = []

        for video in videos:
            duration = video.get("duration", 0)
            if not (_MIN_DURATION <= duration <= max_duration):
                continue

            # Buscar el mejor archivo de video
            video_files = video.get("video_files", [])
            best_file = None
            best_score = -1

            for vf in video_files:
                width = vf.get("width", 0)
                height = vf.get("height", 0)
                quality = vf.get("quality", "")
                file_type = vf.get("file_type", "")

                if "mp4" not in file_type:
                    continue

                score = 0

                # Preferir vertical
                if height > width:
                    score += 100
                elif height == width:
                    score += 50

                # Preferir HD
                if 720 <= min(width, height) <= 1080:
                    score += 50
                elif quality in ("hd", "sd"):
                    score += 25

                # Penalizar resoluciones muy altas (archivos grandes)
                if max(width, height) > 1920:
                    score -= 30

                if score > best_score:
                    best_score = score
                    best_file = vf

            if best_file:
                candidates.append({
                    "url": best_file["link"],
                    "width": best_file.get("width", 0),
                    "height": best_file.get("height", 0),
                    "duration": duration,
                    "score": best_score,
                })

        if not candidates:
            return None

        # Ordenar por score
        candidates.sort(key=lambda c: c["score"], reverse=True)
        return candidates[0]

    async def fetch_videos_batch(
        self,
        keywords: list[str],
    ) -> dict[str, Path | None]:
        """Descarga videos para múltiples keywords.

        Args:
            keywords: Lista de términos de búsqueda.

        Returns:
            Dict de keyword → Path (o None si no se encontró).
        """
        results: dict[str, Path | None] = {}

        for keyword in keywords:
            results[keyword] = await self.fetch_video(keyword)

        return results

    def clear_cache(self) -> int:
        """Limpia la caché de videos descargados.

        Returns:
            Número de archivos eliminados.
        """
        count = 0
        for f in self._cache_dir.glob("*.mp4"):
            f.unlink()
            count += 1
        logger.info("Caché de videos limpiada: %d archivos eliminados", count)
        return count
