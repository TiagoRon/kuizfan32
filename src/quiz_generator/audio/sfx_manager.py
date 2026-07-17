"""Gestor de efectos de sonido sintéticos para videos de quiz.

Genera SFX profesionales de forma procedural usando numpy:
- Ticks de countdown
- Alertas de último segundo
- Celebración de respuesta correcta
- Buzzer de respuesta incorrecta
- Whoosh de transición
- Pop de aparición
- Fanfare final

Los SFX se generan una vez y se cachean en assets/sounds/.
"""

from __future__ import annotations

import logging
import struct
import wave
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Frecuencia de muestreo
SAMPLE_RATE = 44100


def _envelope(length: int, attack: float = 0.01, release: float = 0.1) -> np.ndarray:
    """Genera un envelope ADSR simplificado (attack + release)."""
    samples = np.ones(length, dtype=np.float64)
    attack_len = int(SAMPLE_RATE * attack)
    release_len = int(SAMPLE_RATE * release)

    if attack_len > 0:
        samples[:attack_len] = np.linspace(0, 1, attack_len)
    if release_len > 0 and release_len < length:
        samples[-release_len:] = np.linspace(1, 0, release_len)

    return samples


def _sine_wave(freq: float, duration: float, amplitude: float = 0.5) -> np.ndarray:
    """Genera una onda sinusoidal."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float64)


def _save_wav(data: np.ndarray, path: Path) -> Path:
    """Guarda un array numpy como archivo WAV de 16 bits."""
    path.parent.mkdir(parents=True, exist_ok=True)

    # Normalizar a [-1, 1] y convertir a 16 bits
    peak = np.max(np.abs(data))
    if peak > 0:
        data = data / peak * 0.85  # Headroom
    samples = (data * 32767).astype(np.int16)

    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(samples.tobytes())

    return path


class SFXManager:
    """Genera y cachea efectos de sonido sintéticos para videos de quiz.

    Todos los SFX se generan con numpy de forma procedural,
    evitando dependencias de archivos externos. Se cachean en
    disco para reutilización.
    """

    # Nombres estándar de SFX
    TICK = "tick"
    TICK_URGENT = "tick_urgent"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    WHOOSH = "whoosh"
    POP = "pop"
    QUESTION_APPEAR = "question_appear"
    COUNTDOWN_START = "countdown_start"
    REVEAL = "reveal"
    FANFARE = "fanfare"
    CONFETTI = "confetti"
    TRANSITION = "transition"

    def __init__(self, sounds_dir: str | Path = "assets/sounds") -> None:
        self._sounds_dir = Path(sounds_dir)
        self._sounds_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Path] = {}

    def get_sfx(self, name: str) -> Path:
        """Obtiene la ruta de un SFX por nombre, generándolo si no existe.

        Args:
            name: Nombre del SFX (usar constantes de clase).

        Returns:
            Path al archivo WAV del efecto.
        """
        if name in self._cache:
            return self._cache[name]

        path = self._sounds_dir / f"{name}.wav"
        if path.exists():
            self._cache[name] = path
            return path

        # Generar el SFX
        generator = self._generators.get(name)
        if generator:
            logger.info("Generando SFX: %s", name)
            generator(self, path)
            self._cache[name] = path
            return path

        logger.warning("SFX desconocido: %s", name)
        # Generar un beep genérico como fallback
        self._generate_tick(path)
        self._cache[name] = path
        return path

    def generate_all(self) -> dict[str, Path]:
        """Genera todos los SFX de una vez. Útil para pre-calentar la caché."""
        result = {}
        for name in self._generators:
            result[name] = self.get_sfx(name)
        logger.info("Todos los SFX generados: %d archivos", len(result))
        return result

    # =========================================================================
    # Generadores de SFX
    # =========================================================================

    def _generate_tick(self, path: Path) -> None:
        """Tick corto de countdown (clic sutil)."""
        duration = 0.08
        freq = 880.0
        wave_data = _sine_wave(freq, duration, 0.4)
        env = _envelope(len(wave_data), attack=0.002, release=0.05)
        _save_wav(wave_data * env, path)

    def _generate_tick_urgent(self, path: Path) -> None:
        """Tick urgente para los últimos 3 segundos."""
        duration = 0.12
        freq = 1200.0
        wave_data = _sine_wave(freq, duration, 0.6)
        # Añadir armónico
        wave_data += _sine_wave(freq * 2, duration, 0.2)
        env = _envelope(len(wave_data), attack=0.002, release=0.08)
        _save_wav(wave_data * env, path)

    def _generate_correct(self, path: Path) -> None:
        """Acorde mayor ascendente — celebración de respuesta correcta."""
        # C5 → E5 → G5 (acorde de Do mayor)
        notes = [523.25, 659.25, 783.99]
        full = np.array([], dtype=np.float64)

        for i, freq in enumerate(notes):
            note = _sine_wave(freq, 0.15, 0.5)
            # Añadir armónico suave
            note += _sine_wave(freq * 2, 0.15, 0.15)
            note += _sine_wave(freq * 3, 0.15, 0.05)
            env = _envelope(len(note), attack=0.005, release=0.08)
            note *= env

            # Silencio corto entre notas
            if i < len(notes) - 1:
                gap = np.zeros(int(SAMPLE_RATE * 0.03))
                note = np.concatenate([note, gap])

            full = np.concatenate([full, note])

        # Nota final sostenida
        final = _sine_wave(783.99, 0.3, 0.4)
        final += _sine_wave(783.99 * 2, 0.3, 0.1)
        final *= _envelope(len(final), attack=0.005, release=0.25)
        full = np.concatenate([full, final])

        _save_wav(full, path)

    def _generate_incorrect(self, path: Path) -> None:
        """Buzzer descendente — respuesta incorrecta."""
        duration = 0.4
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)

        # Frecuencia descendente (200Hz → 100Hz)
        freq = np.linspace(200, 100, len(t))
        wave_data = 0.5 * np.sin(2 * np.pi * freq * t / SAMPLE_RATE * np.arange(len(t)))

        # Enfoque más simple: buzzer disonante
        wave_data = _sine_wave(180, duration, 0.4)
        wave_data += _sine_wave(190, duration, 0.3)  # Batimiento
        wave_data += _sine_wave(120, duration, 0.2)

        env = _envelope(len(wave_data), attack=0.01, release=0.2)
        _save_wav(wave_data * env, path)

    def _generate_whoosh(self, path: Path) -> None:
        """Whoosh de transición — ruido filtrado con sweep."""
        duration = 0.35
        n_samples = int(SAMPLE_RATE * duration)

        # Ruido blanco
        noise = np.random.RandomState(42).randn(n_samples) * 0.3

        # Filtro paso banda que se mueve (simula whoosh)
        env = np.zeros(n_samples)
        center = n_samples // 2
        width = n_samples // 3
        env[max(0, center - width):min(n_samples, center + width)] = 1.0

        # Suavizar
        from numpy import convolve
        kernel = np.ones(500) / 500
        env = convolve(env, kernel, mode="same")

        wave_data = noise * env
        _save_wav(wave_data, path)

    def _generate_pop(self, path: Path) -> None:
        """Pop de aparición — clic corto con resonancia."""
        duration = 0.06
        n_samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)

        # Tono con pitch descendente rápido
        freq_start = 1500.0
        freq_end = 400.0
        freqs = np.linspace(freq_start, freq_end, n_samples)

        phase = np.cumsum(freqs / SAMPLE_RATE) * 2 * np.pi
        wave_data = 0.5 * np.sin(phase)

        env = _envelope(n_samples, attack=0.001, release=0.04)
        _save_wav(wave_data * env, path)

    def _generate_question_appear(self, path: Path) -> None:
        """Sonido sutil de aparición de pregunta."""
        duration = 0.2
        # Dos notas rápidas ascendentes
        note1 = _sine_wave(600, 0.08, 0.3)
        note1 += _sine_wave(1200, 0.08, 0.1)
        note1 *= _envelope(len(note1), attack=0.003, release=0.05)

        gap = np.zeros(int(SAMPLE_RATE * 0.02))

        note2 = _sine_wave(800, 0.10, 0.3)
        note2 += _sine_wave(1600, 0.10, 0.1)
        note2 *= _envelope(len(note2), attack=0.003, release=0.07)

        _save_wav(np.concatenate([note1, gap, note2]), path)

    def _generate_countdown_start(self, path: Path) -> None:
        """Sonido de inicio de countdown — alerta suave."""
        note = _sine_wave(660, 0.15, 0.4)
        note += _sine_wave(880, 0.15, 0.2)
        note *= _envelope(len(note), attack=0.005, release=0.1)
        _save_wav(note, path)

    def _generate_reveal(self, path: Path) -> None:
        """Sonido dramático de revelación."""
        duration = 0.5
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)

        # Sweep ascendente
        freq_start = 300.0
        freq_end = 1200.0
        freqs = np.linspace(freq_start, freq_end, len(t))
        phase = np.cumsum(freqs / SAMPLE_RATE) * 2 * np.pi
        wave_data = 0.4 * np.sin(phase)
        wave_data += 0.15 * np.sin(phase * 2)

        env = _envelope(len(wave_data), attack=0.01, release=0.3)
        _save_wav(wave_data * env, path)

    def _generate_fanfare(self, path: Path) -> None:
        """Fanfare final — secuencia celebratoria."""
        notes = [
            (523.25, 0.15),  # C5
            (587.33, 0.10),  # D5
            (659.25, 0.15),  # E5
            (783.99, 0.12),  # G5
            (1046.50, 0.40),  # C6
        ]

        full = np.array([], dtype=np.float64)
        for freq, dur in notes:
            note = _sine_wave(freq, dur, 0.45)
            note += _sine_wave(freq * 2, dur, 0.15)
            note += _sine_wave(freq * 1.5, dur, 0.1)  # Quinta
            note *= _envelope(len(note), attack=0.005, release=dur * 0.6)

            gap = np.zeros(int(SAMPLE_RATE * 0.02))
            full = np.concatenate([full, note, gap])

        _save_wav(full, path)

    def _generate_confetti(self, path: Path) -> None:
        """Sonido de confetti — cascada de tonos agudos."""
        rng = np.random.RandomState(123)
        full = np.zeros(int(SAMPLE_RATE * 0.6))

        for _ in range(15):
            freq = rng.uniform(1000, 3000)
            start = rng.randint(0, len(full) - int(SAMPLE_RATE * 0.05))
            note = _sine_wave(freq, 0.04, 0.15)
            note *= _envelope(len(note), attack=0.002, release=0.03)
            end = min(start + len(note), len(full))
            full[start:end] += note[: end - start]

        _save_wav(full, path)

    def _generate_transition(self, path: Path) -> None:
        """Transición suave entre escenas."""
        duration = 0.25
        n_samples = int(SAMPLE_RATE * duration)

        # Sweep descendente suave
        t = np.linspace(0, duration, n_samples, endpoint=False)
        freq_start = 800.0
        freq_end = 300.0
        freqs = np.linspace(freq_start, freq_end, n_samples)
        phase = np.cumsum(freqs / SAMPLE_RATE) * 2 * np.pi
        wave_data = 0.25 * np.sin(phase)

        # Añadir ruido suave
        noise = np.random.RandomState(77).randn(n_samples) * 0.05
        wave_data += noise

        env = _envelope(n_samples, attack=0.01, release=0.15)
        _save_wav(wave_data * env, path)

    # Mapeo de nombre → generador
    _generators: dict[str, any] = {
        TICK: _generate_tick,
        TICK_URGENT: _generate_tick_urgent,
        CORRECT: _generate_correct,
        INCORRECT: _generate_incorrect,
        WHOOSH: _generate_whoosh,
        POP: _generate_pop,
        QUESTION_APPEAR: _generate_question_appear,
        COUNTDOWN_START: _generate_countdown_start,
        REVEAL: _generate_reveal,
        FANFARE: _generate_fanfare,
        CONFETTI: _generate_confetti,
        TRANSITION: _generate_transition,
    }
