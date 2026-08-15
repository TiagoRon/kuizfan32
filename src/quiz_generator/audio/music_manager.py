"""Generador de música de fondo procedural para videos de quiz.

Crea loops de música en múltiples estilos usando numpy:
- Electrónico: 4-on-the-floor, hi-hats, bass, pad
- Trap: 808 bass, hi-hats rápidos, snare trap
- Lo-Fi: Jazz chords, vinyl crackle, kick suave
- Epic/Cinematic: Strings/pads dramáticos, timpani
- Reggaetón: Dembow pattern, perreo bass, clap

La música se genera de forma procedural, evitando problemas
de copyright y permitiendo duraciones exactas.
"""

from __future__ import annotations

import logging
import random
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 44100

# BPM óptimos por estilo
STYLE_BPM = {
    "electronico": 125,
    "trap": 140,
    "lofi": 85,
    "epic": 100,
    "reggaeton": 95,
}

AVAILABLE_STYLES = list(STYLE_BPM.keys())


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
    freq = 150 * np.exp(-30 * t) + 50
    phase = np.cumsum(freq / SAMPLE_RATE) * 2 * np.pi
    kick = 0.7 * np.sin(phase)
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
    filtered = np.diff(noise, prepend=noise[0]) * 3
    filtered *= _envelope(n, attack=0.001, release=0.03)
    return filtered


def _generate_bass_note(freq: float, duration: float = 0.2) -> np.ndarray:
    """Genera una nota de bajo sintetizada."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    bass = 0.35 * np.sin(2 * np.pi * freq * t)
    bass += 0.1 * np.sin(2 * np.pi * freq * 2 * t)
    bass *= _envelope(n, attack=0.005, release=0.08)
    return bass


def _generate_pad(freq: float, duration: float) -> np.ndarray:
    """Genera un pad armónico suave."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    pad = 0.06 * np.sin(2 * np.pi * freq * t)
    pad += 0.04 * np.sin(2 * np.pi * freq * 1.25 * t)
    pad += 0.03 * np.sin(2 * np.pi * freq * 1.5 * t)
    pad += 0.02 * np.sin(2 * np.pi * freq * 2 * t)
    lfo = 0.3 * np.sin(2 * np.pi * 0.5 * t)
    pad *= (1 + lfo * 0.2)
    pad *= _envelope(n, attack=0.2, release=0.3)
    return pad


# =========================================================================
# Nuevos generadores de instrumentos para estilos adicionales
# =========================================================================

def _generate_808_bass(freq: float, duration: float = 0.5) -> np.ndarray:
    """Genera un bajo 808 trap — sub-bass largo con slide."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    pitch_env = freq + 40 * np.exp(-15 * t)
    phase = np.cumsum(pitch_env / SAMPLE_RATE) * 2 * np.pi
    bass = 0.6 * np.sin(phase)
    bass = np.tanh(bass * 1.5) * 0.5
    bass *= _envelope(n, attack=0.003, release=duration * 0.4)
    return bass


def _generate_trap_hihat(duration: float = 0.03) -> np.ndarray:
    """Hi-hat cerrado estilo trap — más agudo y corto."""
    n = int(SAMPLE_RATE * duration)
    noise = np.random.RandomState(13).randn(n) * 0.2
    filtered = np.diff(np.diff(noise, prepend=noise[0]), prepend=noise[0]) * 5
    filtered *= _envelope(n, attack=0.001, release=0.02)
    return filtered


def _generate_trap_snare(duration: float = 0.2) -> np.ndarray:
    """Snare trap — corto con mucho ruido."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    tone = 0.3 * np.sin(2 * np.pi * (250 * np.exp(-20 * t)) * t)
    noise = np.random.RandomState(31).randn(n) * 0.3
    snare = tone + noise
    snare *= _envelope(n, attack=0.001, release=0.15)
    return snare


def _generate_clap(duration: float = 0.12) -> np.ndarray:
    """Clap sintético."""
    n = int(SAMPLE_RATE * duration)
    rng = np.random.RandomState(55)
    clap = np.zeros(n)
    for offset in [0, 0.005, 0.01, 0.015]:
        start = int(SAMPLE_RATE * offset)
        length = min(int(SAMPLE_RATE * 0.015), n - start)
        if length > 0 and start < n:
            clap[start:start + length] += rng.randn(length) * 0.25
    clap *= _envelope(n, attack=0.001, release=0.08)
    return clap


def _generate_vinyl_crackle(duration: float) -> np.ndarray:
    """Genera crujido de vinilo lo-fi."""
    n = int(SAMPLE_RATE * duration)
    rng = np.random.RandomState(99)
    crackle = np.zeros(n)
    num_pops = int(duration * 15)
    for _ in range(num_pops):
        pos = rng.randint(0, max(1, n - 100))
        pop_len = rng.randint(5, 30)
        pop_end = min(pos + pop_len, n)
        crackle[pos:pop_end] += rng.randn(pop_end - pos) * 0.02
    return crackle


def _generate_timpani(duration: float = 0.6) -> np.ndarray:
    """Genera un golpe de timpani épico."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    freq = 120 * np.exp(-5 * t) + 60
    phase = np.cumsum(freq / SAMPLE_RATE) * 2 * np.pi
    hit = 0.7 * np.sin(phase)
    hit += 0.2 * np.sin(phase * 1.5) * np.exp(-8 * t)
    hit *= _envelope(n, attack=0.002, release=duration * 0.7)
    return hit


def _generate_string_pad(freq: float, duration: float) -> np.ndarray:
    """Genera un pad de cuerdas épico."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    pad = 0.08 * np.sin(2 * np.pi * freq * t)
    pad += 0.07 * np.sin(2 * np.pi * freq * 1.003 * t)
    pad += 0.06 * np.sin(2 * np.pi * freq * 0.997 * t)
    pad += 0.04 * np.sin(2 * np.pi * freq * 1.5 * t)
    pad += 0.03 * np.sin(2 * np.pi * freq * 2 * t)
    vibrato = 1 + 0.003 * np.sin(2 * np.pi * 5 * t)
    pad *= vibrato
    pad *= _envelope(n, attack=0.5, release=0.5)
    return pad


class MusicManager:
    """Genera música de fondo procedural en múltiples estilos.

    Soporta 5 estilos: electrónico, trap, lo-fi, epic, reggaetón.
    El estilo se puede seleccionar manualmente o dejarse en "auto"
    para selección aleatoria por video.
    """

    def __init__(self, sounds_dir: str | Path = "assets/sounds") -> None:
        self._sounds_dir = Path(sounds_dir)
        self._sounds_dir.mkdir(parents=True, exist_ok=True)

    def generate_background_music(
        self,
        duration_seconds: float,
        output_path: Path | None = None,
        volume: float = 0.15,
        bpm: int = 125,
        style: str = "auto",
    ) -> Path:
        """Genera música de fondo en el estilo especificado.

        Args:
            duration_seconds: Duración total en segundos.
            output_path: Ruta de salida.
            volume: Volumen master (0.0 a 1.0).
            bpm: Tempo en BPM (se ignora si el estilo tiene BPM propio).
            style: Estilo musical ("auto", "electronico", "trap", "lofi", "epic", "reggaeton").

        Returns:
            Path al archivo WAV de música generada.
        """
        # Seleccionar estilo
        if style == "auto" or style not in AVAILABLE_STYLES:
            style = random.choice(AVAILABLE_STYLES)
            logger.info("Estilo musical seleccionado automáticamente: %s", style)

        effective_bpm = STYLE_BPM.get(style, bpm)

        if output_path is None:
            output_path = self._sounds_dir / f"bgm_{style}_{int(duration_seconds)}s.wav"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists():
            logger.debug("Música ya existe: %s", output_path)
            return output_path

        logger.info(
            "Generando música [%s] de fondo: %.1fs @ %d BPM",
            style, duration_seconds, effective_bpm,
        )

        generator = {
            "electronico": self._generate_electronico,
            "trap": self._generate_trap,
            "lofi": self._generate_lofi,
            "epic": self._generate_epic,
            "reggaeton": self._generate_reggaeton,
        }[style]

        music = generator(duration_seconds, effective_bpm)

        # Fade in y fade out global
        total_samples = len(music)
        fade_in_len = min(int(SAMPLE_RATE * 1.5), total_samples)
        fade_out_len = min(int(SAMPLE_RATE * 2.0), total_samples)
        music[:fade_in_len] *= np.linspace(0, 1, fade_in_len)
        music[-fade_out_len:] *= np.linspace(1, 0, fade_out_len)

        music *= volume
        peak = np.max(np.abs(music))
        if peak > 0:
            music = music / peak * 0.85
        music *= volume

        self._save_wav(music, output_path)
        logger.info("Música [%s] generada: %s (%.1fs)", style, output_path, duration_seconds)
        return output_path

    # =========================================================================
    # Generadores por Estilo
    # =========================================================================

    def _generate_electronico(self, duration_seconds: float, bpm: int) -> np.ndarray:
        """Estilo electrónico — 4-on-the-floor, hi-hats, bass, pad."""
        total_samples = int(SAMPLE_RATE * duration_seconds)
        music = np.zeros(total_samples, dtype=np.float64)
        beat_duration = 60.0 / bpm
        beat_samples = int(SAMPLE_RATE * beat_duration)

        bass_notes = [130.81, 174.61, 164.81, 196.00]
        kick = _generate_kick()
        hihat = _generate_hihat()

        pos = 0
        beat_count = 0
        while pos < total_samples:
            beat_in_bar = beat_count % 4
            bar_num = beat_count // 4
            end = min(pos + len(kick), total_samples)
            music[pos:end] += kick[:end - pos]
            hihat_offset = beat_samples // 2
            hihat_pos = pos + hihat_offset
            if hihat_pos < total_samples:
                end = min(hihat_pos + len(hihat), total_samples)
                music[hihat_pos:end] += hihat[:end - hihat_pos]
            if hihat_pos - beat_samples // 4 > 0:
                ghost_pos = pos + beat_samples // 4
                if ghost_pos < total_samples:
                    ghost_hat = hihat * 0.4
                    end = min(ghost_pos + len(ghost_hat), total_samples)
                    music[ghost_pos:end] += ghost_hat[:end - ghost_pos]
            if beat_in_bar == 0:
                bass_freq = bass_notes[bar_num % len(bass_notes)]
                bass = _generate_bass_note(bass_freq, beat_duration * 2)
                end = min(pos + len(bass), total_samples)
                music[pos:end] += bass[:end - pos]
            pos += beat_samples
            beat_count += 1

        pad_freqs = [130.81, 174.61, 164.81, 196.00]
        pad_duration = beat_duration * 16
        pad_pos = 0
        pad_idx = 0
        while pad_pos < total_samples:
            pad = _generate_pad(
                pad_freqs[pad_idx % len(pad_freqs)],
                min(pad_duration, (total_samples - pad_pos) / SAMPLE_RATE),
            )
            end = min(pad_pos + len(pad), total_samples)
            music[pad_pos:end] += pad[:end - pad_pos]
            pad_pos += len(pad)
            pad_idx += 1

        return music

    def _generate_trap(self, duration_seconds: float, bpm: int) -> np.ndarray:
        """Estilo trap — 808 bass, hi-hats rápidos con rolls, snare trap."""
        total_samples = int(SAMPLE_RATE * duration_seconds)
        music = np.zeros(total_samples, dtype=np.float64)
        beat_duration = 60.0 / bpm
        beat_samples = int(SAMPLE_RATE * beat_duration)

        bass_notes = [55.0, 65.41, 73.42, 61.74]
        kick = _generate_kick(0.18)
        trap_hh = _generate_trap_hihat()
        snare = _generate_trap_snare()

        pos = 0
        beat_count = 0
        while pos < total_samples:
            beat_in_bar = beat_count % 4
            bar_num = beat_count // 4

            if beat_in_bar in (0, 2):
                end = min(pos + len(kick), total_samples)
                music[pos:end] += kick[:end - pos]

            if beat_in_bar in (1, 3):
                end = min(pos + len(snare), total_samples)
                music[pos:end] += snare[:end - pos] * 0.6

            sixteenth = beat_samples // 4
            for i in range(4):
                hh_pos = pos + i * sixteenth
                if hh_pos < total_samples:
                    vol = 0.8 if i == 0 else 0.4
                    end = min(hh_pos + len(trap_hh), total_samples)
                    music[hh_pos:end] += trap_hh[:end - hh_pos] * vol

            if beat_in_bar == 3 and bar_num % 4 == 3:
                thirtysecond = sixteenth // 2
                for i in range(8):
                    roll_pos = pos + i * thirtysecond
                    if roll_pos < total_samples:
                        end = min(roll_pos + len(trap_hh), total_samples)
                        vol = 0.3 + 0.5 * (i / 8)
                        music[roll_pos:end] += trap_hh[:end - roll_pos] * vol

            if beat_in_bar == 0:
                bass_freq = bass_notes[bar_num % len(bass_notes)]
                bass = _generate_808_bass(bass_freq, beat_duration * 2.5)
                end = min(pos + len(bass), total_samples)
                music[pos:end] += bass[:end - pos]

            pos += beat_samples
            beat_count += 1

        return music

    def _generate_lofi(self, duration_seconds: float, bpm: int) -> np.ndarray:
        """Estilo lo-fi — jazz chords, vinyl crackle, kick suave, hi-hat lazy."""
        total_samples = int(SAMPLE_RATE * duration_seconds)
        music = np.zeros(total_samples, dtype=np.float64)
        beat_duration = 60.0 / bpm
        beat_samples = int(SAMPLE_RATE * beat_duration)

        chord_freqs = [130.81, 174.61, 146.83, 196.00]
        kick = _generate_kick(0.12)
        kick *= 0.5
        hihat = _generate_hihat(0.04)
        hihat *= 0.3

        pos = 0
        beat_count = 0
        while pos < total_samples:
            beat_in_bar = beat_count % 4
            bar_num = beat_count // 4

            if beat_in_bar in (0, 2):
                k_offset = int(SAMPLE_RATE * 0.01)
                k_pos = pos + (k_offset if beat_in_bar == 2 else 0)
                if k_pos < total_samples:
                    end = min(k_pos + len(kick), total_samples)
                    music[k_pos:end] += kick[:end - k_pos]

            hh_pos = pos + beat_samples // 2 + int(SAMPLE_RATE * 0.015)
            if hh_pos < total_samples:
                end = min(hh_pos + len(hihat), total_samples)
                music[hh_pos:end] += hihat[:end - hh_pos]

            if beat_in_bar == 0:
                chord_freq = chord_freqs[bar_num % len(chord_freqs)]
                chord_dur = beat_duration * 4
                chord = _generate_pad(chord_freq, min(chord_dur, (total_samples - pos) / SAMPLE_RATE))
                chord *= 1.5
                end = min(pos + len(chord), total_samples)
                music[pos:end] += chord[:end - pos]

            pos += beat_samples
            beat_count += 1

        crackle = _generate_vinyl_crackle(duration_seconds)
        end = min(len(crackle), total_samples)
        music[:end] += crackle[:end]

        return music

    def _generate_epic(self, duration_seconds: float, bpm: int) -> np.ndarray:
        """Estilo epic/cinematic — strings, timpani, crescendos dramáticos."""
        total_samples = int(SAMPLE_RATE * duration_seconds)
        music = np.zeros(total_samples, dtype=np.float64)
        beat_duration = 60.0 / bpm
        beat_samples = int(SAMPLE_RATE * beat_duration)

        string_freqs = [110.00, 174.61, 130.81, 196.00]
        timpani = _generate_timpani()

        pos = 0
        beat_count = 0
        while pos < total_samples:
            beat_in_bar = beat_count % 4
            bar_num = beat_count // 4

            if beat_in_bar == 0:
                end = min(pos + len(timpani), total_samples)
                music[pos:end] += timpani[:end - pos] * 0.4
            elif beat_in_bar == 2 and bar_num % 2 == 1:
                end = min(pos + len(timpani), total_samples)
                music[pos:end] += timpani[:end - pos] * 0.25

            if beat_in_bar == 0:
                s_freq = string_freqs[bar_num % len(string_freqs)]
                s_dur = beat_duration * 4
                strings = _generate_string_pad(
                    s_freq, min(s_dur, (total_samples - pos) / SAMPLE_RATE),
                )
                progress = pos / total_samples
                intensity = 0.7 + 0.3 * progress
                end = min(pos + len(strings), total_samples)
                music[pos:end] += strings[:end - pos] * intensity

            pos += beat_samples
            beat_count += 1

        sub_dur = min(duration_seconds, total_samples / SAMPLE_RATE)
        sub_n = int(SAMPLE_RATE * sub_dur)
        sub_t = np.linspace(0, sub_dur, sub_n, endpoint=False)
        sub_bass = 0.04 * np.sin(2 * np.pi * 55 * sub_t)
        sub_bass *= _envelope(sub_n, attack=2.0, release=2.0)
        end = min(len(sub_bass), total_samples)
        music[:end] += sub_bass[:end]

        return music

    def _generate_reggaeton(self, duration_seconds: float, bpm: int) -> np.ndarray:
        """Estilo reggaetón — dembow pattern, perreo bass, clap."""
        total_samples = int(SAMPLE_RATE * duration_seconds)
        music = np.zeros(total_samples, dtype=np.float64)
        beat_duration = 60.0 / bpm
        beat_samples = int(SAMPLE_RATE * beat_duration)

        bass_notes = [73.42, 82.41, 65.41, 87.31]
        kick = _generate_kick(0.12)
        clap = _generate_clap()
        hihat = _generate_hihat(0.04)

        pos = 0
        beat_count = 0
        while pos < total_samples:
            beat_in_bar = beat_count % 4
            bar_num = beat_count // 4

            eighth = beat_samples // 2
            if beat_in_bar in (0, 2):
                end = min(pos + len(kick), total_samples)
                music[pos:end] += kick[:end - pos]
            if beat_in_bar in (1, 3):
                off_pos = pos + eighth
                if off_pos < total_samples:
                    end = min(off_pos + len(kick), total_samples)
                    music[off_pos:end] += kick[:end - off_pos] * 0.8

            if beat_in_bar in (1, 3):
                end = min(pos + len(clap), total_samples)
                music[pos:end] += clap[:end - pos] * 0.5

            for i in range(2):
                hh_pos = pos + i * eighth
                if hh_pos < total_samples:
                    end = min(hh_pos + len(hihat), total_samples)
                    music[hh_pos:end] += hihat[:end - hh_pos] * 0.35

            if beat_in_bar % 2 == 0:
                bass_freq = bass_notes[bar_num % len(bass_notes)]
                bass = _generate_808_bass(bass_freq, beat_duration * 1.5)
                bass *= 0.7
                end = min(pos + len(bass), total_samples)
                music[pos:end] += bass[:end - pos]

            pos += beat_samples
            beat_count += 1

        pad_freqs = [146.83, 164.81, 130.81, 174.61]
        pad_duration = beat_duration * 8
        pad_pos = 0
        pad_idx = 0
        while pad_pos < total_samples:
            pad = _generate_pad(
                pad_freqs[pad_idx % len(pad_freqs)],
                min(pad_duration, (total_samples - pad_pos) / SAMPLE_RATE),
            )
            pad *= 0.6
            end = min(pad_pos + len(pad), total_samples)
            music[pad_pos:end] += pad[:end - pad_pos]
            pad_pos += len(pad)
            pad_idx += 1

        return music

    # =========================================================================
    # Ducking y Utilidades
    # =========================================================================

    def apply_ducking(
        self,
        music: np.ndarray,
        voice_segments: list[tuple[float, float]],
        duck_level: float = 0.3,
        attack: float = 0.1,
        release: float = 0.3,
    ) -> np.ndarray:
        """Aplica ducking a la música cuando hay voz."""
        result = music.copy()
        envelope_arr = np.ones(len(music), dtype=np.float64)

        for start, end in voice_segments:
            s = int(start * SAMPLE_RATE)
            e = int(end * SAMPLE_RATE)
            s = max(0, min(s, len(music)))
            e = max(0, min(e, len(music)))
            envelope_arr[s:e] = duck_level

        kernel_size = int(SAMPLE_RATE * attack)
        if kernel_size > 0:
            kernel = np.ones(kernel_size) / kernel_size
            envelope_arr = np.convolve(envelope_arr, kernel, mode="same")

        result *= envelope_arr
        return result

    @staticmethod
    def _save_wav(data: np.ndarray, path: Path) -> None:
        """Guarda un array como WAV de 16 bits."""
        import wave

        peak = np.max(np.abs(data))
        normalized = data / peak * 0.85 if peak > 0 else data
        samples = (normalized * 32767).astype(np.int16)

        with wave.open(str(path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(samples.tobytes())
