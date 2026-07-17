"""Proveedor de TTS basado en Microsoft Edge TTS.

Gratuito, sin necesidad de API key. Genera audio de alta calidad
con voces neurales en español y otros idiomas. Soporta marcas de
tiempo por palabra para sincronización de subtítulos.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import edge_tts

from quiz_generator.core.exceptions import TTSError, VoiceNotFoundError
from quiz_generator.core.interfaces import ITTSProvider

logger = logging.getLogger(__name__)


class EdgeTTSProvider(ITTSProvider):
    """Proveedor de Texto a Voz usando Microsoft Edge TTS (gratuito).

    Características:
    - Sin API key requerida.
    - Voces neurales de alta calidad.
    - Soporte de marcas de tiempo palabra por palabra.
    - Control de velocidad mediante parámetro de rate.
    - Generación asíncrona eficiente.
    """

    async def synthesize(
        self,
        text: str,
        output_path: Path,
        voice: str = "es-MX-DaliaNeural",
        rate: float = 1.0,
    ) -> Path:
        """Sintetiza texto a un archivo MP3."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rate_str = self._format_rate(rate)

        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate_str,
            )
            await communicate.save(str(output_path))

            if not output_path.exists() or output_path.stat().st_size == 0:
                raise TTSError("edge_tts", f"Archivo de audio vacío: {output_path}")

            logger.debug("Audio generado: %s (%.1f KB)", output_path, output_path.stat().st_size / 1024)
            return output_path

        except Exception as e:
            if "voice" in str(e).lower():
                raise VoiceNotFoundError("edge_tts", voice) from e
            raise TTSError("edge_tts", str(e)) from e

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
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rate_str = self._format_rate(rate)
        timestamps: list[dict[str, Any]] = []

        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate_str,
            )

            # Recopilar audio y timestamps
            audio_chunks: list[bytes] = []

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    timestamps.append({
                        "word": chunk["text"],
                        "start_ms": chunk["offset"] // 10_000,  # Convertir de 100ns a ms
                        "end_ms": (chunk["offset"] + chunk["duration"]) // 10_000,
                    })

            # Escribir audio a archivo
            with open(output_path, "wb") as f:
                for audio_chunk in audio_chunks:
                    f.write(audio_chunk)

            logger.debug(
                "Audio con timestamps generado: %s (%d palabras)",
                output_path, len(timestamps),
            )
            return output_path, timestamps

        except Exception as e:
            if "voice" in str(e).lower():
                raise VoiceNotFoundError("edge_tts", voice) from e
            raise TTSError("edge_tts", str(e)) from e

    async def list_voices(self, language: str = "es") -> list[dict[str, str]]:
        """Lista las voces disponibles para un idioma."""
        try:
            all_voices = await edge_tts.list_voices()
            filtered = [
                {
                    "name": v["ShortName"],
                    "gender": v["Gender"],
                    "language": v["Locale"],
                    "provider": "edge_tts",
                    "friendly_name": v.get("FriendlyName", v["ShortName"]),
                }
                for v in all_voices
                if v["Locale"].startswith(language)
            ]
            return filtered
        except Exception as e:
            raise TTSError("edge_tts", f"Error al listar voces: {e}") from e

    @staticmethod
    def _format_rate(rate: float) -> str:
        """Convierte un factor de velocidad a formato de Edge TTS.

        Edge TTS espera formato "+XX%" o "-XX%".
        rate=1.0 → "+0%", rate=1.2 → "+20%", rate=0.8 → "-20%"
        """
        percentage = int((rate - 1.0) * 100)
        if percentage >= 0:
            return f"+{percentage}%"
        return f"{percentage}%"
