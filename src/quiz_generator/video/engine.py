"""Motor principal de generación de video — nivel profesional.

Construye la línea de tiempo del video combinando:
- Escenas animadas de Pillow (con efectos Ken Burns, partículas, slide-in)
- Audio de TTS con subtítulos sincronizados
- Efectos de sonido procedurales
- Música de fondo con ducking automático
- Videos de respuesta de Pexels (con fallback animado)
- Transiciones crossfade entre escenas

Estructura del video:
1. Hook animado (3-5s) — subtítulos, zoom, partículas, countdown visual
2. Por cada pregunta:
   a. Aparición de pregunta con SFX (2-3s)
   b. Countdown animado a 60fps (10s)
   c. Flash de revelación + video de respuesta (2-3s)
3. CTA final animado (3s)

NO incluye pantalla de "¿Sabías que...?" — flujo directo.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoClip,
    VideoFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
)
from PIL import Image

from quiz_generator.audio.engine import QuizAudioPack
from quiz_generator.audio.music_manager import MusicManager
from quiz_generator.audio.sfx_manager import SFXManager
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
    """Motor principal de composición de video — nivel profesional.

    Combina las escenas renderizadas con Pillow, el audio de TTS,
    efectos de sonido, música de fondo, y videos de respuesta
    para crear un video de quiz viral completo.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._composer = SceneComposer(settings)
        self._effects = VisualEffects()
        self._thumbnail_gen = ThumbnailGenerator(settings)
        self._sfx_manager = SFXManager(settings.assets.directorio_sonidos)
        self._music_manager = MusicManager(settings.assets.directorio_sonidos)
        self._fps = settings.video.fps
        self._tiempos = settings.video.tiempos
        self._width = settings.video.ancho
        self._height = settings.video.alto

    async def compose_video(
        self,
        quiz: Quiz,
        audio_pack: QuizAudioPack,
        output_path: Path,
        answer_videos: dict[str, Path] | None = None,
    ) -> Path:
        """Compone el video final del quiz con animaciones y audio completo.

        Args:
            quiz: Quiz con todas las preguntas y metadatos.
            audio_pack: Paquete de audio con todos los segmentos TTS.
            output_path: Ruta donde exportar el video final.
            answer_videos: Dict de respuesta → path de video (Pexels).

        Returns:
            Ruta al video exportado.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        answer_videos = answer_videos or {}
        clips: list = []

        logger.info("Componiendo video: %d preguntas", len(quiz.preguntas))

        # Descargar fuentes si es necesario
        logger.info("Verificando fuentes...")
        await self._composer._font_manager.download_fonts()

        # Pre-generar todos los SFX
        self._sfx_manager.generate_all()

        # 1. Escena del Hook animado
        hook_clip = self._create_animated_hook_clip(quiz, audio_pack)
        clips.append(hook_clip)

        # 2. Escenas de preguntas (sin curiosidad)
        for i, pregunta in enumerate(quiz.preguntas):
            logger.info("Componiendo pregunta %d/%d...", i + 1, len(quiz.preguntas))

            # 2a. Aparición de pregunta con animación
            question_clip = self._create_animated_question_clip(
                quiz, i, audio_pack,
            )
            clips.append(question_clip)

            # 2b. Countdown animado a 60fps
            countdown_clip = self._create_smooth_countdown_clip(quiz, i)
            clips.append(countdown_clip)

            # 2c. Revelación con video/animación
            reveal_clip = self._create_animated_reveal_clip(
                quiz, i, audio_pack, answer_videos,
            )
            clips.append(reveal_clip)

        # 3. Escena CTA animado
        cta_clip = self._create_animated_cta_clip(quiz, audio_pack)
        clips.append(cta_clip)

        # Concatenar todos los clips
        logger.info("Concatenando %d clips...", len(clips))
        final_video = concatenate_videoclips(clips, method="compose")

        # 4. Agregar música de fondo con ducking
        if self._settings.video.musica.habilitada:
            final_video = self._add_background_music(
                final_video, audio_pack,
            )

        # Exportar
        logger.info("Exportando video a: %s", output_path)
        final_video.write_videofile(
            str(output_path),
            fps=self._fps,
            codec=self._settings.exportacion.codec,
            audio_codec="aac",
            preset=self._settings.exportacion.preset,
            threads=4,
            logger=None,
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
            try:
                clip.close()
            except Exception:
                pass

        logger.info("Video exportado exitosamente: %s", output_path)
        return output_path

    # =========================================================================
    # Clips Animados
    # =========================================================================

    def _create_animated_hook_clip(
        self,
        quiz: Quiz,
        audio_pack: QuizAudioPack,
    ) -> CompositeVideoClip:
        """Crea el clip del hook con animación de partículas y Ken Burns."""
        scene = self._composer.render_hook_scene(
            hook_text=quiz.hook.texto,
            emoji=quiz.hook.emoji,
        )

        # Duración basada en el audio
        duration = self._tiempos.hook
        if audio_pack.hook and audio_pack.hook.audio_path.exists():
            audio = AudioFileClip(str(audio_pack.hook.audio_path))
            duration = max(duration, audio.duration + 0.5)
        else:
            audio = None

        num_frames = int(duration * self._fps)
        particles = VisualEffects.create_particles(self._width, self._height, num_particles=25, seed=42)

        def make_frame(t: float) -> np.ndarray:
            # 1. Ken Burns
            zoomed = VisualEffects.apply_ken_burns_lazy(
                scene, t, duration, zoom_start=1.0, zoom_end=1.04,
            )
            # 2. Partículas
            frame = VisualEffects.apply_particles_lazy(zoomed, t, particles)
            return _pil_to_numpy(frame)

        clip = VideoClip(make_frame, duration=duration)

        # Añadir SFX de aparición
        sfx_clips = []
        try:
            pop_path = self._sfx_manager.get_sfx(SFXManager.POP)
            sfx_clips.append(AudioFileClip(str(pop_path)).with_start(0.1))
        except Exception:
            pass

        # Componer audio
        audio_layers = []
        if audio:
            audio_layers.append(audio.with_start(0.3))
        audio_layers.extend(sfx_clips)

        if audio_layers:
            composite_audio = CompositeAudioClip(audio_layers)
            clip = clip.with_audio(composite_audio)

        return clip

    def _create_animated_question_clip(
        self,
        quiz: Quiz,
        question_idx: int,
        audio_pack: QuizAudioPack,
    ) -> CompositeVideoClip:
        """Crea el clip de la pregunta con Ken Burns sutil y SFX."""
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

        duration = self._tiempos.pregunta_lectura

        # Audio TTS de la pregunta
        audio = None
        if question_idx < len(audio_pack.questions):
            q_audio_seg = audio_pack.questions[question_idx]
            if q_audio_seg.audio_path.exists():
                audio = AudioFileClip(str(q_audio_seg.audio_path))
                duration = max(duration, audio.duration + 0.3)

        def make_frame(t: float) -> np.ndarray:
            frame = VisualEffects.apply_ken_burns_lazy(
                scene, t, duration, zoom_start=1.0, zoom_end=1.02,
            )
            return _pil_to_numpy(frame)

        clip = VideoClip(make_frame, duration=duration)

        # SFX de aparición de pregunta
        audio_layers = []
        if audio:
            audio_layers.append(audio)

        try:
            q_sfx_path = self._sfx_manager.get_sfx(SFXManager.QUESTION_APPEAR)
            audio_layers.append(
                AudioFileClip(str(q_sfx_path)).with_start(0).with_volume_scaled(0.5),
            )
        except Exception:
            pass

        if audio_layers:
            composite_audio = CompositeAudioClip(audio_layers)
            clip = clip.with_audio(composite_audio)

        return clip

    def _create_smooth_countdown_clip(
        self,
        quiz: Quiz,
        question_idx: int,
    ) -> CompositeVideoClip:
        """Crea el clip del countdown animado a 60fps.

        Genera frames fluidos con:
        - Timer circular con arco que se reduce
        - Ken Burns zoom sutil
        - Ticks de sonido por segundo
        - Tick urgente en los últimos 3 segundos
        """
        pregunta = quiz.preguntas[question_idx]
        timer_seconds = pregunta.tiempo_segundos
        answers_data = [
            {"texto": r.texto, "emoji": r.emoji, "es_correcta": r.es_correcta}
            for r in pregunta.respuestas
        ]

        total_duration = float(timer_seconds)

        # Pre-renderizar base limpia (sin timer) para evitar hacerlo 600 veces
        base_scene = self._composer.render_question_scene(
            question_number=question_idx + 1,
            total_questions=len(quiz.preguntas),
            question_text=pregunta.texto,
            answers=answers_data,
            timer_value=None,
            emoji_pista=pregunta.emoji_pista,
        )

        def make_frame(t: float) -> np.ndarray:
            time_left = max(0.001, timer_seconds - t)
            
            # Dibujar el timer actual sobre una copia de la base
            frame_with_timer = base_scene.copy()
            draw = ImageDraw.Draw(frame_with_timer)
            # Y fijo para el timer (se calcula igual que en composer.py)
            self._composer._draw_premium_timer(draw, time_left, y=410)
            
            # Ken Burns sutil continuo a lo largo de todo el countdown
            final_frame = VisualEffects.apply_ken_burns_lazy(
                frame_with_timer, t, total_duration,
                zoom_start=1.0, zoom_end=1.04,
            )
            return _pil_to_numpy(final_frame)

        clip = VideoClip(make_frame, duration=total_duration)

        # Agregar ticks de countdown como audio
        audio_layers = []
        for t in range(timer_seconds):
            try:
                remaining = timer_seconds - t
                sfx_name = SFXManager.TICK_URGENT if remaining <= 3 else SFXManager.TICK
                tick_path = self._sfx_manager.get_sfx(sfx_name)
                tick_audio = AudioFileClip(str(tick_path)).with_start(float(t))
                audio_layers.append(tick_audio)
            except Exception:
                pass

        # SFX de inicio de countdown
        try:
            start_path = self._sfx_manager.get_sfx(SFXManager.COUNTDOWN_START)
            audio_layers.insert(0, AudioFileClip(str(start_path)).with_start(0))
        except Exception:
            pass

        if audio_layers:
            clip = clip.with_audio(CompositeAudioClip(audio_layers))

        return clip

    def _create_animated_reveal_clip(
        self,
        quiz: Quiz,
        question_idx: int,
        audio_pack: QuizAudioPack,
        answer_videos: dict[str, Path],
    ) -> CompositeVideoClip:
        """Crea el clip de revelación con flash, video de respuesta, y SFX.

        Flujo:
        1. Flash rápido (6 frames)
        2. Escena de respuesta correcta resaltada con confeti
        3. Si hay video de Pexels: overlay del video
        4. SFX de respuesta correcta + audio TTS
        """
        pregunta = quiz.preguntas[question_idx]
        answers_data = [
            {"texto": r.texto, "emoji": r.emoji, "es_correcta": r.es_correcta}
            for r in pregunta.respuestas
        ]

        correct_idx = next(
            (i for i, r in enumerate(pregunta.respuestas) if r.es_correcta),
            0,
        )
        correct_text = pregunta.respuestas[correct_idx].texto if pregunta.respuestas else ""

        # Renderizar escena de respuesta correcta
        reveal_scene = self._composer.render_question_scene(
            question_number=question_idx + 1,
            total_questions=len(quiz.preguntas),
            question_text=pregunta.texto,
            answers=answers_data,
            show_correct=True,
            correct_index=correct_idx,
            emoji_pista=pregunta.emoji_pista,
        )

        # Aplicar confeti
        efectos = self._settings.video.efectos
        if efectos.confeti_habilitado:
            reveal_scene = VisualEffects.apply_confetti(
                reveal_scene, num_particles=80, seed=question_idx,
            )

        duration = self._tiempos.revelacion

        # Audio de la respuesta
        audio = None
        if question_idx < len(audio_pack.answers):
            a_audio_seg = audio_pack.answers[question_idx]
            if a_audio_seg.audio_path.exists():
                audio = AudioFileClip(str(a_audio_seg.audio_path))
                duration = max(duration, audio.duration + 0.3)

        def make_frame(t: float) -> np.ndarray:
            # 1. Ken Burns
            zoomed = VisualEffects.apply_ken_burns_lazy(
                reveal_scene, t, duration, zoom_start=1.01, zoom_end=1.03,
            )
            # 2. Flash decay
            flashed = VisualEffects.apply_flash_lazy(zoomed, t, duration=0.5, peak_intensity=0.6)
            return _pil_to_numpy(flashed)

        clip = VideoClip(make_frame, duration=duration)

        # Intentar overlay de video de Pexels
        if correct_text in answer_videos:
            video_path = answer_videos[correct_text]
            try:
                clip = self._overlay_answer_video(clip, video_path, duration)
            except Exception:
                logger.exception("Error al overlay video de respuesta, usando fallback")

        # Audio: TTS + SFX
        audio_layers = []
        if audio:
            audio_layers.append(audio.with_start(0.2))

        try:
            correct_sfx = self._sfx_manager.get_sfx(SFXManager.CORRECT)
            audio_layers.append(AudioFileClip(str(correct_sfx)).with_start(0))
        except Exception:
            pass

        try:
            confetti_sfx = self._sfx_manager.get_sfx(SFXManager.CONFETTI)
            audio_layers.append(
                AudioFileClip(str(confetti_sfx)).with_start(0.15).with_volume_scaled(0.4),
            )
        except Exception:
            pass

        if audio_layers:
            clip = clip.with_audio(CompositeAudioClip(audio_layers))

        return clip

    def _create_animated_cta_clip(
        self,
        quiz: Quiz,
        audio_pack: QuizAudioPack,
    ) -> CompositeVideoClip:
        """Crea el clip final del CTA con animación."""
        cta_text = quiz.metadata.cta or "¡Comenta cuántas acertaste! 🎯"
        scene = self._composer.render_cta_scene(cta_text)

        duration = self._tiempos.outro

        if audio_pack.cta and audio_pack.cta.audio_path.exists():
            audio = AudioFileClip(str(audio_pack.cta.audio_path))
            duration = max(duration, audio.duration + 0.5)
        else:
            audio = None

        particles = VisualEffects.create_particles(self._width, self._height, num_particles=20, seed=99)

        def make_frame(t: float) -> np.ndarray:
            zoomed = VisualEffects.apply_ken_burns_lazy(
                scene, t, duration, zoom_start=1.0, zoom_end=1.03,
            )
            frame = VisualEffects.apply_particles_lazy(zoomed, t, particles)
            return _pil_to_numpy(frame)

        clip = VideoClip(make_frame, duration=duration)

        # Audio + fanfare SFX
        audio_layers = []
        if audio:
            audio_layers.append(audio.with_start(0.3))

        try:
            fanfare_path = self._sfx_manager.get_sfx(SFXManager.FANFARE)
            audio_layers.append(AudioFileClip(str(fanfare_path)).with_start(0))
        except Exception:
            pass

        if audio_layers:
            clip = clip.with_audio(CompositeAudioClip(audio_layers))

        return clip

    # =========================================================================
    # Música de Fondo
    # =========================================================================

    def _add_background_music(
        self,
        video: CompositeVideoClip,
        audio_pack: QuizAudioPack,
    ) -> CompositeVideoClip:
        """Agrega música de fondo con ducking automático.

        La música se reduce cuando hay voz (TTS) y se restaura
        en los momentos sin narración.
        """
        music_config = self._settings.video.musica
        total_duration = video.duration

        if total_duration <= 0:
            return video

        # Generar música de fondo
        output_dir = Path(self._settings.assets.directorio_sonidos)
        music_path = self._music_manager.generate_background_music(
            duration_seconds=total_duration,
            output_path=output_dir / f"bgm_{int(total_duration)}s.wav",
            volume=music_config.volumen,
            bpm=music_config.bpm,
        )

        try:
            music_audio = AudioFileClip(str(music_path))

            # Ajustar duración exacta
            if music_audio.duration > total_duration:
                music_audio = music_audio.subclipped(0, total_duration)

            # Mezclar con el audio existente del video
            if video.audio is not None:
                combined = CompositeAudioClip([
                    video.audio,
                    music_audio.with_volume_scaled(music_config.volumen),
                ])
                return video.with_audio(combined)
            else:
                return video.with_audio(
                    music_audio.with_volume_scaled(music_config.volumen),
                )

        except Exception:
            logger.exception("Error al agregar música de fondo")
            return video

    # =========================================================================
    # Overlay de Video de Respuesta
    # =========================================================================

    def _overlay_answer_video(
        self,
        base_clip: CompositeVideoClip,
        video_path: Path,
        duration: float,
    ) -> CompositeVideoClip:
        """Superpone un video de respuesta (Pexels) en una sección del clip.

        El video se muestra en un recuadro redondeado en la parte central,
        sobre el clip de revelación.
        """
        try:
            answer_vid = VideoFileClip(str(video_path))

            # Recortar al tiempo de revelación
            if answer_vid.duration > duration:
                answer_vid = answer_vid.subclipped(0, duration)

            # Redimensionar para que quepa en un recuadro (60% del ancho)
            target_w = int(self._width * 0.6)
            target_h = int(target_w * 9 / 16)  # Mantener aspecto
            answer_vid = answer_vid.resized((target_w, target_h))

            # Posicionar en el centro
            x_pos = (self._width - target_w) // 2
            y_pos = int(self._height * 0.25)

            answer_vid = answer_vid.with_position((x_pos, y_pos))

            return CompositeVideoClip([base_clip, answer_vid])

        except Exception:
            logger.exception("Error al procesar video de respuesta")
            return base_clip
