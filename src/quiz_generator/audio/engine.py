"""Motor de audio — orquesta la generación de TTS y la selección de música.

Genera todos los segmentos de audio de un quiz:
- Hook de apertura
- Lectura de cada pregunta
- Revelación de respuesta
- Datos curiosos
- CTA de cierre
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from quiz_generator.audio.edge_tts_provider import EdgeTTSProvider
from quiz_generator.config import Settings
from quiz_generator.core.models import Quiz

logger = logging.getLogger(__name__)


@dataclass
class AudioSegment:
    """Un segmento de audio generado con su metadata."""

    audio_path: Path
    text: str
    timestamps: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: int = 0
    segment_type: str = ""  # hook, question, answer, curiosity, cta


@dataclass
class QuizAudioPack:
    """Paquete completo de audio para un quiz."""

    hook: AudioSegment | None = None
    questions: list[AudioSegment] = field(default_factory=list)
    answers: list[AudioSegment] = field(default_factory=list)
    curiosities: list[AudioSegment] = field(default_factory=list)
    cta: AudioSegment | None = None
    total_duration_ms: int = 0


class AudioEngine:
    """Motor principal de generación de audio.

    Coordina la generación de todos los segmentos de audio
    necesarios para un video de quiz completo.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._tts = EdgeTTSProvider()  # Proveedor por defecto (gratuito)

    async def generate_quiz_audio(
        self,
        quiz: Quiz,
        output_dir: Path,
    ) -> QuizAudioPack:
        """Genera todos los archivos de audio para un quiz.

        Args:
            quiz: El quiz con todas sus preguntas.
            output_dir: Directorio donde guardar los archivos de audio.

        Returns:
            QuizAudioPack con todos los segmentos generados.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        voice = self._settings.tts.voz
        rate = self._settings.tts.velocidad
        pack = QuizAudioPack()

        # 1. Generar audio del hook
        logger.info("Generando audio del hook...")
        hook_path = output_dir / "hook.mp3"
        audio_path, timestamps = await self._tts.synthesize_with_timestamps(
            text=quiz.hook.texto,
            output_path=hook_path,
            voice=voice,
            rate=rate,
        )
        pack.hook = AudioSegment(
            audio_path=audio_path,
            text=quiz.hook.texto,
            timestamps=timestamps,
            segment_type="hook",
        )

        # 2. Generar audio de cada pregunta
        for i, pregunta in enumerate(quiz.preguntas):
            logger.info("Generando audio pregunta %d/%d...", i + 1, len(quiz.preguntas))

            # Audio de la pregunta
            q_path = output_dir / f"question_{i:02d}.mp3"
            q_audio, q_timestamps = await self._tts.synthesize_with_timestamps(
                text=pregunta.texto,
                output_path=q_path,
                voice=voice,
                rate=rate,
            )
            pack.questions.append(AudioSegment(
                audio_path=q_audio,
                text=pregunta.texto,
                timestamps=q_timestamps,
                segment_type="question",
            ))

            # Audio de la respuesta correcta
            correcta = next(
                (r for r in pregunta.respuestas if r.es_correcta),
                pregunta.respuestas[0] if pregunta.respuestas else None,
            )
            if correcta:
                answer_text = f"La respuesta correcta es: {correcta.texto}"
                a_path = output_dir / f"answer_{i:02d}.mp3"
                a_audio, a_timestamps = await self._tts.synthesize_with_timestamps(
                    text=answer_text,
                    output_path=a_path,
                    voice=voice,
                    rate=rate,
                )
                pack.answers.append(AudioSegment(
                    audio_path=a_audio,
                    text=answer_text,
                    timestamps=a_timestamps,
                    segment_type="answer",
                ))

            # Audio del dato curioso (si existe)
            if pregunta.curiosidad:
                c_path = output_dir / f"curiosity_{i:02d}.mp3"
                c_audio, c_timestamps = await self._tts.synthesize_with_timestamps(
                    text=pregunta.curiosidad,
                    output_path=c_path,
                    voice=voice,
                    rate=rate,
                )
                pack.curiosities.append(AudioSegment(
                    audio_path=c_audio,
                    text=pregunta.curiosidad,
                    timestamps=c_timestamps,
                    segment_type="curiosity",
                ))

        # 3. Generar audio del CTA
        if quiz.metadata.cta:
            logger.info("Generando audio del CTA...")
            cta_path = output_dir / "cta.mp3"
            cta_audio, cta_timestamps = await self._tts.synthesize_with_timestamps(
                text=quiz.metadata.cta,
                output_path=cta_path,
                voice=voice,
                rate=rate,
            )
            pack.cta = AudioSegment(
                audio_path=cta_audio,
                text=quiz.metadata.cta,
                timestamps=cta_timestamps,
                segment_type="cta",
            )

        logger.info(
            "Audio generado: hook + %d preguntas + %d respuestas + %d curiosidades + CTA",
            len(pack.questions), len(pack.answers), len(pack.curiosities),
        )

        return pack
