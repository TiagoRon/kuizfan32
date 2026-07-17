"""Motor principal de generación de video.

Construye la línea de tiempo del video combinando escenas de Pillow,
audio de TTS, y efectos para producir un video completo de quiz.

Estructura del video:
1. Hook (2-3s) — gancho de apertura
2. Por cada pregunta:
   a. Lectura de la pregunta (2-3s)
   b. Countdown con opciones visibles (10s)
   c. Revelación de respuesta (2s)
   d. Dato curioso (opcional, 3s)
3. CTA final (3s)
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import numpy as np
from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
)
from PIL import Image

from quiz_generator.audio.engine import QuizAudioPack
from quiz_generator.config import Settings
from quiz_generator.core.models import Quiz
from quiz_generator.video.composer import SceneComposer
from quiz_generator.video.effects import VisualEffects
from quiz_generator.video.thumbnail import ThumbnailGenerator

logger = logging.getLogger(__name__)


def _pil_to_numpy(img: Image.Image) -> np.ndarray:
    """Convierte una imagen Pillow a array numpy para MoviePy."""
    return np.array(img.convert("RGB"))


class VideoEngine:
    """Motor principal de composición de video.

    Combina las escenas renderizadas con Pillow, el audio de TTS
    y los efectos para crear un video de quiz completo.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._composer = SceneComposer(settings)
        self._effects = VisualEffects()
        self._thumbnail_gen = ThumbnailGenerator(settings)
        self._fps = settings.video.fps
        self._tiempos = settings.video.tiempos

    async def compose_video(
        self,
        quiz: Quiz,
        audio_pack: QuizAudioPack,
        output_path: Path,
    ) -> Path:
        """Compone el video final del quiz.

        Args:
            quiz: Quiz con todas las preguntas y metadatos.
            audio_pack: Paquete de audio con todos los segmentos TTS.
            output_path: Ruta donde exportar el video final.

        Returns:
            Ruta al video exportado.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        clips: list[CompositeVideoClip | ImageClip] = []

        logger.info("Componiendo video: %d preguntas", len(quiz.preguntas))

        # 1. Escena del Hook
        hook_clip = self._create_hook_clip(quiz, audio_pack)
        clips.append(hook_clip)

        # 2. Escenas de preguntas
        for i, pregunta in enumerate(quiz.preguntas):
            logger.info("Componiendo pregunta %d/%d...", i + 1, len(quiz.preguntas))

            # 2a. Escena de lectura de la pregunta
            question_clip = self._create_question_clip(
                quiz, i, audio_pack,
            )
            clips.append(question_clip)

            # 2b. Escena de countdown (opciones visibles, sin respuesta)
            countdown_clip = self._create_countdown_clip(quiz, i)
            clips.append(countdown_clip)

            # 2c. Escena de revelación
            reveal_clip = self._create_reveal_clip(
                quiz, i, audio_pack,
            )
            clips.append(reveal_clip)

            # 2d. Escena de dato curioso (si existe)
            if i < len(audio_pack.curiosities) and pregunta.curiosidad:
                curiosity_clip = self._create_curiosity_clip(
                    quiz, i, audio_pack,
                )
                clips.append(curiosity_clip)

        # 3. Escena CTA
        cta_clip = self._create_cta_clip(quiz, audio_pack)
        clips.append(cta_clip)

        # Concatenar todos los clips
        logger.info("Concatenando %d clips...", len(clips))
        final_video = concatenate_videoclips(clips, method="compose")

        # Exportar
        logger.info("Exportando video a: %s", output_path)
        final_video.write_videofile(
            str(output_path),
            fps=self._fps,
            codec=self._settings.exportacion.codec,
            audio_codec="aac",
            preset=self._settings.exportacion.preset,
            threads=4,
            logger=None,  # Silenciar logs de MoviePy
        )

        # Generar miniatura
        thumbnail_path = output_path.parent / f"{quiz.id}_thumbnail.png"
        try:
            self._thumbnail_gen.generate(quiz, thumbnail_path)
            logger.info("Miniatura generada: %s", thumbnail_path)
        except Exception:
            logger.exception("Error al generar miniatura, continuando sin ella")

        # Limpiar
        final_video.close()
        for clip in clips:
            clip.close()

        logger.info("Video exportado exitosamente: %s", output_path)
        return output_path

    def _create_hook_clip(
        self,
        quiz: Quiz,
        audio_pack: QuizAudioPack,
    ) -> CompositeVideoClip:
        """Crea el clip del hook de apertura con efecto viñeta."""
        scene = self._composer.render_hook_scene(
            hook_text=quiz.hook.texto,
            emoji=quiz.hook.emoji,
        )

        # Aplicar viñeta cinematográfica al hook
        if self._settings.video.efectos.zoom_habilitado:
            scene = VisualEffects.apply_vignette(scene, intensity=0.3)

        frame = _pil_to_numpy(scene)

        duration = self._tiempos.hook
        img_clip = ImageClip(frame, duration=duration)

        # Añadir audio del hook si existe
        if audio_pack.hook and audio_pack.hook.audio_path.exists():
            audio = AudioFileClip(str(audio_pack.hook.audio_path))
            duration = max(duration, audio.duration + 0.5)
            img_clip = ImageClip(frame, duration=duration)
            img_clip = img_clip.with_audio(audio)

        return img_clip

    def _create_question_clip(
        self,
        quiz: Quiz,
        question_idx: int,
        audio_pack: QuizAudioPack,
    ) -> CompositeVideoClip:
        """Crea el clip de lectura de la pregunta (sin opciones visibles aún)."""
        pregunta = quiz.preguntas[question_idx]
        answers_data = [
            {"texto": r.texto, "emoji": r.emoji, "es_correcta": r.es_correcta}
            for r in pregunta.respuestas
        ]

        scene = self._composer.render_question_scene(
            question_number=question_idx + 1,
            total_questions=len(quiz.preguntas),
            question_text=pregunta.texto,
            answers=answers_data,
            emoji_pista=pregunta.emoji_pista,
        )
        frame = _pil_to_numpy(scene)

        duration = self._tiempos.pregunta_lectura

        # Ajustar duración al audio de la pregunta
        if question_idx < len(audio_pack.questions):
            q_audio_seg = audio_pack.questions[question_idx]
            if q_audio_seg.audio_path.exists():
                audio = AudioFileClip(str(q_audio_seg.audio_path))
                duration = max(duration, audio.duration + 0.3)
                img_clip = ImageClip(frame, duration=duration)
                img_clip = img_clip.with_audio(audio)
                return img_clip

        return ImageClip(frame, duration=duration)

    def _create_countdown_clip(
        self,
        quiz: Quiz,
        question_idx: int,
    ) -> CompositeVideoClip:
        """Crea el clip del countdown (temporizador visual)."""
        pregunta = quiz.preguntas[question_idx]
        timer_seconds = pregunta.tiempo_segundos
        answers_data = [
            {"texto": r.texto, "emoji": r.emoji, "es_correcta": r.es_correcta}
            for r in pregunta.respuestas
        ]

        # Crear fotogramas del countdown (1 por segundo)
        frames = []
        for t in range(timer_seconds, 0, -1):
            scene = self._composer.render_question_scene(
                question_number=question_idx + 1,
                total_questions=len(quiz.preguntas),
                question_text=pregunta.texto,
                answers=answers_data,
                timer_value=t,
                emoji_pista=pregunta.emoji_pista,
            )
            frames.append(_pil_to_numpy(scene))

        # Crear clips de 1 segundo cada uno
        clips = [ImageClip(frame, duration=1.0) for frame in frames]
        return concatenate_videoclips(clips, method="compose")

    def _create_reveal_clip(
        self,
        quiz: Quiz,
        question_idx: int,
        audio_pack: QuizAudioPack,
    ) -> CompositeVideoClip:
        """Crea el clip de revelación con efectos de confeti/color."""
        pregunta = quiz.preguntas[question_idx]
        answers_data = [
            {"texto": r.texto, "emoji": r.emoji, "es_correcta": r.es_correcta}
            for r in pregunta.respuestas
        ]

        correct_idx = next(
            (i for i, r in enumerate(pregunta.respuestas) if r.es_correcta),
            0,
        )

        scene = self._composer.render_question_scene(
            question_number=question_idx + 1,
            total_questions=len(quiz.preguntas),
            question_text=pregunta.texto,
            answers=answers_data,
            show_correct=True,
            correct_index=correct_idx,
            emoji_pista=pregunta.emoji_pista,
        )

        # Aplicar efectos visuales a la revelación
        efectos = self._settings.video.efectos
        if efectos.confeti_habilitado:
            scene = VisualEffects.apply_confetti(
                scene, num_particles=60, seed=question_idx,
            )
        if efectos.flash_habilitado:
            # Flash suave verde para respuesta correcta
            scene = VisualEffects.apply_color_overlay(
                scene, (0, 230, 118), intensity=0.08,
            )

        frame = _pil_to_numpy(scene)

        duration = self._tiempos.revelacion

        # Audio de la respuesta
        if question_idx < len(audio_pack.answers):
            a_audio_seg = audio_pack.answers[question_idx]
            if a_audio_seg.audio_path.exists():
                audio = AudioFileClip(str(a_audio_seg.audio_path))
                duration = max(duration, audio.duration + 0.3)
                img_clip = ImageClip(frame, duration=duration)
                img_clip = img_clip.with_audio(audio)
                return img_clip

        return ImageClip(frame, duration=duration)

    def _create_curiosity_clip(
        self,
        quiz: Quiz,
        question_idx: int,
        audio_pack: QuizAudioPack,
    ) -> CompositeVideoClip:
        """Crea el clip del dato curioso."""
        pregunta = quiz.preguntas[question_idx]
        correcta = next(
            (r.texto for r in pregunta.respuestas if r.es_correcta),
            "",
        )

        scene = self._composer.render_curiosity_scene(
            curiosity_text=pregunta.curiosidad or "",
            correct_answer=correcta,
        )
        frame = _pil_to_numpy(scene)

        duration = self._tiempos.curiosidad

        # Audio del dato curioso
        if question_idx < len(audio_pack.curiosities):
            c_audio_seg = audio_pack.curiosities[question_idx]
            if c_audio_seg.audio_path.exists():
                audio = AudioFileClip(str(c_audio_seg.audio_path))
                duration = max(duration, audio.duration + 0.5)
                img_clip = ImageClip(frame, duration=duration)
                img_clip = img_clip.with_audio(audio)
                return img_clip

        return ImageClip(frame, duration=duration)

    def _create_cta_clip(
        self,
        quiz: Quiz,
        audio_pack: QuizAudioPack,
    ) -> CompositeVideoClip:
        """Crea el clip final del CTA."""
        cta_text = quiz.metadata.cta or "¡Comenta cuántas acertaste! 🎯"
        scene = self._composer.render_cta_scene(cta_text)
        frame = _pil_to_numpy(scene)

        duration = self._tiempos.outro

        if audio_pack.cta and audio_pack.cta.audio_path.exists():
            audio = AudioFileClip(str(audio_pack.cta.audio_path))
            duration = max(duration, audio.duration + 0.5)
            img_clip = ImageClip(frame, duration=duration)
            img_clip = img_clip.with_audio(audio)
            return img_clip

        return ImageClip(frame, duration=duration)
