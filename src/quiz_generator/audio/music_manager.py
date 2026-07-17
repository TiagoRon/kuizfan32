"""Generador de música de fondo procedural para videos de quiz.

Crea loops de música electrónica/pop energética usando numpy:
- Patrón de kick drum (4-on-the-floor)
- Hi-hat pattern
- Bass line repetitiva
- Pad armónico sutil
- Ajuste automático de duración
- Ducking automático para la voz

La música se genera de forma procedural, evitando problemas
de copyright y permitiendo duraciones exactas.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 44100
BPM = 125  # Tempo energético para quiz


def _sine(freq: float, duration: float, amp: float = 0.5) -> np.ndarray:
    """Onda sinusoidal simple."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    return amp * np.sin(2 * np.pi * freq * t)


def _noise(duration: float, amp: float = 0.1) -> np.ndarray:
    """Ruido blanco."""
    n = int(SAMPLE_RATE * duration)
    return amp * np.random.RandomState(42).randn(n)


def _envelope(n_samples: int, attack: float = 0.005, release: float = 0.05) -> np.ndarray:
    """Envelope básico."""
    env = np.ones(n_samples, dtype=np.float64)
    att = min(int(SAMPLE_RATE * attack), n_samples)
    rel = min(int(SAMPLE_RATE * release), n_samples)
    if att > 0:
        env[:att] = np.linspace(0, 1, att)
    if rel > 0:
        env[-rel:] = np.linspace(1, 0, rel)
    return env


def _generate_kick(duration: float = 0.15) -> np.ndarray:
    """Genera un kick drum sintético."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    # Pitch envelope: empieza alto y baja rápido
    freq = 150 * np.exp(-30 * t) + 50
    phase = np.cumsum(freq / SAMPLE_RATE) * 2 * np.pi
    kick = 0.7 * np.sin(phase)

    # Clic de ataque
    click = np.zeros(n)
    click_len = min(int(SAMPLE_RATE * 0.003), n)
    click[:click_len] = 0.3

    kick += click
    kick *= _envelope(n, attack=0.001, release=0.12)
    return kick


def _generate_hihat(duration: float = 0.05) -> np.ndarray:
    """Genera un hi-hat sintético (ruido filtrado)."""
    n = int(SAMPLE_RATE * duration)
    noise = np.random.RandomState(7).randn(n) * 0.15

    # Filtro paso alto simple (diferencia)
    filtered = np.diff(noise, prepend=noise[0]) * 3
    filtered *= _envelope(n, attack=0.001, release=0.03)
    return filtered


def _generate_bass_note(freq: float, duration: float = 0.2) -> np.ndarray:
    """Genera una nota de bajo sintetizada."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    bass = 0.35 * np.sin(2 * np.pi * freq * t)
    bass += 0.1 * np.sin(2 * np.pi * freq * 2 * t)  # Armónico
    bass *= _envelope(n, attack=0.005, release=0.08)
    return bass


def _generate_pad(freq: float, duration: float) -> np.ndarray:
    """Genera un pad armónico suave."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    # Acorde (fundamental + tercera + quinta)
    pad = 0.06 * np.sin(2 * np.pi * freq * t)
    pad += 0.04 * np.sin(2 * np.pi * freq * 1.25 * t)  # Tercera mayor
    pad += 0.03 * np.sin(2 * np.pi * freq * 1.5 * t)  # Quinta
    pad += 0.02 * np.sin(2 * np.pi * freq * 2 * t)  # Octava

    # LFO para movimiento sutil
    lfo = 0.3 * np.sin(2 * np.pi * 0.5 * t)  # 0.5 Hz
    pad *= (1 + lfo * 0.2)

    pad *= _envelope(n, attack=0.2, release=0.3)
    return pad


class MusicManager:
    """Genera música de fondo procedural para videos de quiz.

    Crea un loop de música electrónica energética que se ajusta
    automáticamente a la duración del video. Incluye ducking
    automático para que la voz sea siempre clara.
    """

    def __init__(self, sounds_dir: str | Path = "assets/sounds") -> None:
        self._sounds_dir = Path(sounds_dir)
        self._sounds_dir.mkdir(parents=True, exist_ok=True)

    def generate_background_music(
        self,
        duration_seconds: float,
        output_path: Path | None = None,
        volume: float = 0.15,
        bpm: int = BPM,
    ) -> Path:
        """Genera música de fondo para la duración especificada.

        Args:
            duration_seconds: Duración total en segundos.
            output_path: Ruta de salida (default: assets/sounds/bgm_<dur>.wav).
            volume: Volumen master (0.0 a 1.0).
            bpm: Tempo en BPM.

        Returns:
            Path al archivo WAV de música generada.
        """
        if output_path is None:
            output_path = self._sounds_dir / f"bgm_{int(duration_seconds)}s.wav"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists():
            logger.debug("Música ya existe: %s", output_path)
            return output_path

        logger.info(
            "Generando música de fondo: %.1fs @ %d BPM",
            duration_seconds, bpm,
        )

        total_samples = int(SAMPLE_RATE * duration_seconds)
        music = np.zeros(total_samples, dtype=np.float64)

        beat_duration = 60.0 / bpm  # Duración de un beat en segundos
        beat_samples = int(SAMPLE_RATE * beat_duration)

        # Notas del bajo (progresión i-VI-III-VII en menor)
        bass_notes = [
            130.81,  # C3
            174.61,  # F3
            164.81,  # E3
            196.00,  # G3
        ]

        # Generar beats
        kick = _generate_kick()
        hihat = _generate_hihat()

        pos = 0
        beat_count = 0

        while pos < total_samples:
            beat_in_bar = beat_count % 4
            bar_num = beat_count // 4

            # Kick en cada beat (4-on-the-floor)
            end = min(pos + len(kick), total_samples)
            music[pos:end] += kick[: end - pos]

            # Hi-hat en offbeats
            hihat_offset = beat_samples // 2
            hihat_pos = pos + hihat_offset
            if hihat_pos < total_samples:
                end = min(hihat_pos + len(hihat), total_samples)
                music[hihat_pos:end] += hihat[: end - hihat_pos]

            # Hi-hat extra en cada beat (más cerrado)
            if hihat_pos - beat_samples // 4 > 0:
                ghost_pos = pos + beat_samples // 4
                if ghost_pos < total_samples:
                    ghost_hat = hihat * 0.4  # Más suave
                    end = min(ghost_pos + len(ghost_hat), total_samples)
                    music[ghost_pos:end] += ghost_hat[: end - ghost_pos]

            # Bajo: una nota por compás (cada 4 beats)
            if beat_in_bar == 0:
                bass_freq = bass_notes[bar_num % len(bass_notes)]
                bass = _generate_bass_note(bass_freq, beat_duration * 2)
                end = min(pos + len(bass), total_samples)
                music[pos:end] += bass[: end - pos]

            pos += beat_samples
            beat_count += 1

        # Pad armónico continuo (cambia cada 4 compases)
        pad_freqs = [130.81, 174.61, 164.81, 196.00]
        pad_duration = beat_duration * 16  # 4 compases
        pad_pos = 0
        pad_idx = 0

        while pad_pos < total_samples:
            pad = _generate_pad(
                pad_freqs[pad_idx % len(pad_freqs)],
                min(pad_duration, (total_samples - pad_pos) / SAMPLE_RATE),
            )
            end = min(pad_pos + len(pad), total_samples)
            music[pad_pos:end] += pad[: end - pad_pos]
            pad_pos += len(pad)
            pad_idx += 1

        # Fade in y fade out global
        fade_in_len = min(int(SAMPLE_RATE * 1.5), total_samples)
        fade_out_len = min(int(SAMPLE_RATE * 2.0), total_samples)
        music[:fade_in_len] *= np.linspace(0, 1, fade_in_len)
        music[-fade_out_len:] *= np.linspace(1, 0, fade_out_len)

        # Aplicar volumen master
        music *= volume

        # Normalizar
        peak = np.max(np.abs(music))
        if peak > 0:
            music = music / peak * 0.85

        music *= volume  # Re-aplicar después de normalizar

        # Guardar WAV
        self._save_wav(music, output_path)

        logger.info("Música generada: %s (%.1fs)", output_path, duration_seconds)
        return output_path

    def apply_ducking(
        self,
        music: np.ndarray,
        voice_segments: list[tuple[float, float]],
        duck_level: float = 0.3,
        attack: float = 0.1,
        release: float = 0.3,
    ) -> np.ndarray:
        """Aplica ducking a la música cuando hay voz.

        Reduce el volumen de la música durante los segmentos de voz
        para que la narración sea siempre clara.

        Args:
            music: Array de audio de la música.
            voice_segments: Lista de (start_sec, end_sec) con voz.
            duck_level: Nivel de reducción (0.0 = silencio, 1.0 = sin cambio).
            attack: Tiempo de ataque del ducking en segundos.
            release: Tiempo de release del ducking en segundos.

        Returns:
            Música con ducking aplicado.
        """
        result = music.copy()
        envelope = np.ones(len(music), dtype=np.float64)

        for start, end in voice_segments:
            s = int(start * SAMPLE_RATE)
            e = int(end * SAMPLE_RATE)
            s = max(0, min(s, len(music)))
            e = max(0, min(e, len(music)))

            envelope[s:e] = duck_level

        # Suavizar transiciones
        kernel_size = int(SAMPLE_RATE * attack)
        if kernel_size > 0:
            kernel = np.ones(kernel_size) / kernel_size
            envelope = np.convolve(envelope, kernel, mode="same")

        result *= envelope
        return result

    @staticmethod
    def _save_wav(data: np.ndarray, path: Path) -> None:
        """Guarda un array como WAV de 16 bits."""
        import wave

        peak = np.max(np.abs(data))
        if peak > 0:
            normalized = data / peak * 0.85
        else:
            normalized = data

        samples = (normalized * 32767).astype(np.int16)

        with wave.open(str(path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(samples.tobytes())
