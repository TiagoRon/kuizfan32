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

import contextlib
import logging
import math
from pathlib import Path

import numpy as np
from moviepy import (
    AudioArrayClip,
    AudioClip,
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    VideoClip,
    VideoFileClip,
    concatenate_videoclips,
    vfx,
)
from PIL import Image, ImageDraw

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


def _safe_audio_clip(path: str | Path) -> AudioClip:
    """Carga el audio completamente en RAM para evitar bugs de lectura (out-of-bounds) de MoviePy 2."""
    try:
        clip = AudioFileClip(str(path))
        fps = getattr(clip, "fps", 44100)

        # Leer todo a memoria de forma segura
        audio_array = clip.to_soundarray()
        clip.close()

        safe_clip = AudioArrayClip(audio_array, fps=fps)
        return safe_clip
    except Exception as e:
        logger.warning(f"Error cargando audio {path}: {e}")
        def silent_frame(t):
            return np.zeros((len(t), 2)) if hasattr(t, '__len__') else np.zeros(2)
        return AudioClip(silent_frame, duration=0.1)



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

        # Tipo de cada clip para elegir la transición correcta
        clip_types: list[str] = ["hook"]

        # 2. Escenas de preguntas (sin curiosidad)
        for i, _pregunta in enumerate(quiz.preguntas):
            logger.info("Componiendo pregunta %d/%d...", i + 1, len(quiz.preguntas))

            # 2a. Aparición de pregunta con animación
            question_clip = self._create_animated_question_clip(
                quiz, i, audio_pack,
            )
            clips.append(question_clip)
            clip_types.append("question")

            # 2b. Countdown animado a 60fps
            countdown_clip = self._create_smooth_countdown_clip(quiz, i)
            clips.append(countdown_clip)
            clip_types.append("countdown")

            # 2c. Revelación con video/animación
            reveal_clip = self._create_animated_reveal_clip(
                quiz, i, audio_pack, answer_videos,
            )
            clips.append(reveal_clip)
            clip_types.append("reveal")

        # 3. Escena CTA animado
        cta_clip = self._create_animated_cta_clip(quiz, audio_pack)
        clips.append(cta_clip)
        clip_types.append("cta")

        # Concatenar con transiciones premium variadas por tipo de escena
        logger.info("Concatenando %d clips con transiciones premium...", len(clips))
        final_video = self._concatenate_with_premium_transitions(
            clips, clip_types,
        )

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
            with contextlib.suppress(Exception):
                clip.close()

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
            audio = _safe_audio_clip(str(audio_pack.hook.audio_path))
            duration = max(duration, audio.duration + 0.5)
        else:
            audio = None

        int(duration * self._fps)
        particles = VisualEffects.create_particles(self._width, self._height, num_particles=25, seed=42)

        def make_frame(t: float) -> np.ndarray:
            # Entry animation: slide-up + zoom-out + fade-in
            entry_dur = 0.7
            if t < entry_dur:
                p = t / entry_dur
                p = 1 - (1 - p) ** 3  # ease-out cubic
                scale = 1.12 - 0.12 * p
                zoomed = VisualEffects.apply_ken_burns_lazy(
                    scene, 0, 1, zoom_start=scale, zoom_end=scale,
                )
                # Slide-up reveal
                zoomed = VisualEffects.apply_slide_up_reveal_lazy(
                    zoomed, t, entry_dur, max_offset=50,
                )
                # Fade in
                dark = Image.new("RGB", scene.size, (0, 0, 0))
                zoomed = Image.blend(dark, zoomed, p)
            else:
                zoomed = VisualEffects.apply_ken_burns_lazy(
                    scene, t, duration, zoom_start=1.0, zoom_end=1.04,
                )
            frame = VisualEffects.apply_particles_lazy(zoomed, t, particles)
            return _pil_to_numpy(frame)

        clip = VideoClip(make_frame, duration=duration)

        # Añadir SFX de aparición
        sfx_clips = []
        try:
            pop_path = self._sfx_manager.get_sfx(SFXManager.POP)
            sfx_clips.append(_safe_audio_clip(str(pop_path)).with_start(0.1))
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
        """Crea el clip de la pregunta con Ken Burns, partículas y SFX."""
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
                audio = _safe_audio_clip(str(q_audio_seg.audio_path))
                duration = max(duration, audio.duration + 0.3)

        # Partículas para la escena de pregunta
        particles = VisualEffects.create_particles(
            self._width, self._height, num_particles=30, seed=question_idx * 10,
        )

        def make_frame(t: float) -> np.ndarray:
            # Entry animation: slide-up + scale pop-in + fade
            entry_dur = 0.6
            if t < entry_dur:
                p = t / entry_dur
                p = 1 - (1 - p) ** 3  # ease-out cubic
                scale = 1.06 - 0.06 * p
                frame = VisualEffects.apply_ken_burns_lazy(
                    scene, 0, 1, zoom_start=scale, zoom_end=scale,
                )
                # Slide content up into place
                frame = VisualEffects.apply_slide_up_reveal_lazy(
                    frame, t, entry_dur, max_offset=45,
                )
                # Fade in from black
                dark = Image.new("RGB", scene.size, (0, 0, 0))
                frame = Image.blend(dark, frame, p)
            else:
                # Normal Ken Burns
                frame = VisualEffects.apply_ken_burns_lazy(
                    scene, t, duration, zoom_start=1.0, zoom_end=1.02,
                )
            # Partículas
            frame = VisualEffects.apply_particles_lazy(frame, t, particles)
            return _pil_to_numpy(frame)

        clip = VideoClip(make_frame, duration=duration)

        # SFX de aparición de pregunta
        audio_layers = []
        if audio:
            audio_layers.append(audio)

        try:
            q_sfx_path = self._sfx_manager.get_sfx(SFXManager.QUESTION_APPEAR)
            audio_layers.append(
                _safe_audio_clip(str(q_sfx_path)).with_start(0).with_volume_scaled(0.5),
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
        """Crea el clip del countdown animado a 60fps con partículas."""
        pregunta = quiz.preguntas[question_idx]
        timer_seconds = pregunta.tiempo_segundos
        answers_data = [
            {"texto": r.texto, "emoji": r.emoji, "es_correcta": r.es_correcta}
            for r in pregunta.respuestas
        ]

        total_duration = float(timer_seconds)

        # Pre-renderizar base limpia (sin timer)
        base_scene = self._composer.render_question_scene(
            question_number=question_idx + 1,
            total_questions=len(quiz.preguntas),
            question_text=pregunta.texto,
            answers=answers_data,
            timer_value=None,
            emoji_pista=pregunta.emoji_pista,
        )

        # Partículas para el countdown
        particles = VisualEffects.create_particles(
            self._width, self._height, num_particles=25, seed=question_idx * 10 + 5,
        )

        def make_frame(t: float) -> np.ndarray:
            time_left = max(0.001, timer_seconds - t)

            frame_with_timer = base_scene.copy()
            draw = ImageDraw.Draw(frame_with_timer)
            # Timer ahora en esquina superior derecha
            timer_x = self._width - 120
            self._composer._draw_premium_timer(
                draw, time_left,
                y=self._composer._last_timer_y,
                center_x=timer_x,
            )

            # Accelerating Ken Burns zoom in final seconds for tension
            if time_left <= 3:
                zoom_extra = 0.03 * (1 - time_left / 3)
                zoom_end = 1.04 + zoom_extra
            else:
                zoom_end = 1.04

            final_frame = VisualEffects.apply_ken_burns_lazy(
                frame_with_timer, t, total_duration,
                zoom_start=1.0, zoom_end=zoom_end,
            )

            # Radial glow pulse around timer (esquina superior derecha)
            timer_cy = self._composer._last_timer_y + 50
            glow_color = (255, 40, 40) if time_left <= 3 else (
                (255, 214, 0) if time_left <= 5 else (108, 92, 231)
            )
            # Frecuencia del glow se ACELERA conforme baja el tiempo (heartbeat)
            if time_left <= 3:
                glow_freq = 6.0 + (3 - time_left) * 3  # 6→15 Hz
                glow_intensity = 0.8
            elif time_left <= 5:
                glow_freq = 4.0
                glow_intensity = 0.5
            else:
                glow_freq = 2.5
                glow_intensity = 0.3

            final_frame = VisualEffects.apply_radial_glow_pulse_lazy(
                final_frame, t,
                center=(timer_x, timer_cy),
                radius=90,
                color=glow_color,
                frequency=glow_freq,
                intensity=glow_intensity,
            )

            # Neon border pulse — siempre presente, más intenso al final
            border_color = glow_color
            border_intensity = 0.15 if time_left > 5 else (0.35 if time_left > 3 else 0.6)
            final_frame = VisualEffects.apply_neon_border_pulse_lazy(
                final_frame, t,
                color=border_color,
                frequency=glow_freq * 0.5,
                intensity=border_intensity,
            )

            # Chromatic aberration en los últimos 3 segundos
            if time_left <= 3:
                aberration_amount = int(3 * (1 - time_left / 3))
                if aberration_amount > 0:
                    final_frame = VisualEffects.apply_chromatic_aberration_lazy(
                        final_frame, offset=aberration_amount,
                    )

            # Screen shake sutil en los últimos 2 segundos
            if time_left <= 2:
                shake_intensity = int(4 * (1 - time_left / 2))
                if shake_intensity > 0:
                    final_frame = VisualEffects.apply_shake(
                        final_frame, intensity=shake_intensity, seed=int(t * 100),
                    )

            # Red urgency tint pulse when timer < 3 seconds
            if time_left <= 3:
                pulse = abs(math.sin(t * 8)) * 0.08
                red_layer = Image.new("RGB", final_frame.size, (255, 30, 30))
                final_frame = Image.blend(final_frame, red_layer, pulse)

            # Partículas
            final_frame = VisualEffects.apply_particles_lazy(final_frame, t, particles)
            return _pil_to_numpy(final_frame)

        clip = VideoClip(make_frame, duration=total_duration)

        # Agregar ticks de countdown como audio
        audio_layers = []
        for t in range(timer_seconds):
            try:
                remaining = timer_seconds - t
                sfx_name = SFXManager.TICK_URGENT if remaining <= 3 else SFXManager.TICK
                tick_path = self._sfx_manager.get_sfx(sfx_name)
                tick_audio = _safe_audio_clip(str(tick_path)).with_start(float(t))
                audio_layers.append(tick_audio)
            except Exception:
                pass

        # SFX de inicio de countdown
        try:
            start_path = self._sfx_manager.get_sfx(SFXManager.COUNTDOWN_START)
            audio_layers.insert(0, _safe_audio_clip(str(start_path)).with_start(0))
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
        """Crea el clip de revelación con confeti animado, flash verde y SFX."""
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

        # Renderizar escena de respuesta correcta (con banner, vignette, etc.)
        reveal_scene = self._composer.render_question_scene(
            question_number=question_idx + 1,
            total_questions=len(quiz.preguntas),
            question_text=pregunta.texto,
            answers=answers_data,
            show_correct=True,
            correct_index=correct_idx,
            emoji_pista=pregunta.emoji_pista,
        )

        duration = self._tiempos.revelacion

        # Audio de la respuesta
        audio = None
        if question_idx < len(audio_pack.answers):
            a_audio_seg = audio_pack.answers[question_idx]
            if a_audio_seg.audio_path.exists():
                audio = _safe_audio_clip(str(a_audio_seg.audio_path))
                duration = max(duration, audio.duration + 0.3)

        # Confeti animado con gravedad
        confetti_particles = VisualEffects.create_confetti_particles(
            self._width, self._height, num_particles=120, seed=question_idx,
        )

        def make_frame(t: float) -> np.ndarray:
            # Zoom bounce with elastic overshoot for dramatic reveal
            zoomed = VisualEffects.apply_zoom_bounce_lazy(
                reveal_scene, t,
                bounce_duration=0.5,
                initial_scale=1.18,
                overshoot=0.02,
            )
            if t >= 0.5:
                # After bounce settles, gentle Ken Burns
                zoomed = VisualEffects.apply_ken_burns_lazy(
                    reveal_scene, t - 0.5, duration - 0.5,
                    zoom_start=1.0, zoom_end=1.03,
                )
            # Bright flash for impact
            flashed = VisualEffects.apply_flash_lazy(
                zoomed, t, duration=0.45,
                color=(0, 255, 130),
                peak_intensity=0.7,
            )
            # Dense confetti
            confettied = VisualEffects.apply_animated_confetti_lazy(
                flashed, t, confetti_particles,
            )
            return _pil_to_numpy(confettied)

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
            audio_layers.append(_safe_audio_clip(str(correct_sfx)).with_start(0))
        except Exception:
            pass

        try:
            confetti_sfx = self._sfx_manager.get_sfx(SFXManager.CONFETTI)
            audio_layers.append(
                _safe_audio_clip(str(confetti_sfx)).with_start(0.15).with_volume_scaled(0.4),
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
        """Crea el clip final del CTA con animación y shimmer premium."""
        cta_text = quiz.metadata.cta or "¡Comenta cuántas acertaste! 🎯"
        scene = self._composer.render_cta_scene(cta_text)

        duration = self._tiempos.outro

        if audio_pack.cta and audio_pack.cta.audio_path.exists():
            audio = _safe_audio_clip(str(audio_pack.cta.audio_path))
            duration = max(duration, audio.duration + 0.5)
        else:
            audio = None

        particles = VisualEffects.create_particles(self._width, self._height, num_particles=20, seed=99)

        def make_frame(t: float) -> np.ndarray:
            # Entry animation with fade-in + scale
            entry_dur = 0.6
            if t < entry_dur:
                p = t / entry_dur
                p = 1 - (1 - p) ** 3  # ease-out
                scale = 1.10 - 0.10 * p
                zoomed = VisualEffects.apply_ken_burns_lazy(
                    scene, 0, 1, zoom_start=scale, zoom_end=scale,
                )
                dark = Image.new("RGB", scene.size, (0, 0, 0))
                zoomed = Image.blend(dark, zoomed, p)
            else:
                # Subtle breathing zoom pulse
                pulse = 1.0 + 0.006 * math.sin((t - entry_dur) * 3.0)
                zoomed = VisualEffects.apply_ken_burns_lazy(
                    scene, t, duration, zoom_start=pulse, zoom_end=pulse * 1.01,
                )
            # Shimmer premium que recorre el CTA
            zoomed = VisualEffects.apply_text_shimmer(
                zoomed, t, speed=1.5,
                color=(255, 255, 255), intensity=0.12,
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
            audio_layers.append(_safe_audio_clip(str(fanfare_path)).with_start(0))
        except Exception:
            pass

        if audio_layers:
            clip = clip.with_audio(CompositeAudioClip(audio_layers))

        return clip

    # =========================================================================
    # Transiciones Premium entre Escenas
    # =========================================================================

    def _concatenate_with_premium_transitions(
        self,
        clips: list,
        clip_types: list[str],
    ) -> CompositeVideoClip:
        """Concatena clips con transiciones animadas variadas según el tipo de escena.

        Selecciona la transición más apropiada para cada par de escenas:
        - hook → question:     zoom transition (dramático)
        - question → countdown: sin transición (misma escena visual)
        - countdown → reveal:  radial reveal (revelado circular)
        - reveal → question:   slide lateral (frescura)
        - reveal → cta:        wipe horizontal (cierre)
        """
        if len(clips) <= 1:
            return clips[0] if clips else CompositeVideoClip([])

        trans_duration = 0.6  # Duración de cada transición

        # Construir lista final: clip, transición, clip, transición, ...
        final_clips = [clips[0]]

        for i in range(1, len(clips)):
            prev_type = clip_types[i - 1] if i - 1 < len(clip_types) else "unknown"
            curr_type = clip_types[i] if i < len(clip_types) else "unknown"

            # Elegir tipo de transición según el par de escenas
            transition_style = self._pick_transition_style(prev_type, curr_type)

            if transition_style == "none":
                # Sin transición animada, solo concatenar directo
                final_clips.append(clips[i])
            else:
                # Crear clip de transición animada
                try:
                    trans_clip = self._create_transition_clip(
                        clips[i - 1], clips[i],
                        transition_style, trans_duration,
                    )
                    final_clips.append(trans_clip)
                    final_clips.append(clips[i])
                except Exception:
                    logger.warning(
                        "Error creando transición %s, usando crossfade",
                        transition_style,
                    )
                    try:
                        final_clips.append(
                            clips[i].with_effects([vfx.CrossFadeIn(0.3)]),
                        )
                    except Exception:
                        final_clips.append(clips[i])

        return concatenate_videoclips(final_clips, method="compose")

    @staticmethod
    def _pick_transition_style(prev_type: str, curr_type: str) -> str:
        """Elige el estilo de transición según el par de tipos de escena."""
        pair = (prev_type, curr_type)
        transition_map = {
            ("hook", "question"): "zoom",
            ("question", "countdown"): "none",  # Misma escena, sin corte
            ("countdown", "reveal"): "radial",
            ("reveal", "question"): "slide",
            ("reveal", "cta"): "wipe",
        }
        return transition_map.get(pair, "zoom")

    def _create_transition_clip(
        self,
        clip_out,
        clip_in,
        style: str,
        duration: float,
    ) -> VideoClip:
        """Crea un VideoClip de transición animada entre dos clips.

        Captura el último frame del clip saliente y el primer frame del
        clip entrante, y genera una transición animada entre ellos.
        """
        # Capturar frames extremos
        try:
            last_frame_time = max(0, clip_out.duration - 0.05)
            frame_out = Image.fromarray(clip_out.get_frame(last_frame_time))
        except Exception:
            frame_out = Image.new("RGB", (self._width, self._height), (0, 0, 0))

        try:
            frame_in = Image.fromarray(clip_in.get_frame(0.0))
        except Exception:
            frame_in = Image.new("RGB", (self._width, self._height), (0, 0, 0))

        def make_frame(t: float) -> np.ndarray:
            if style == "zoom":
                result = VisualEffects.apply_zoom_transition_lazy(
                    frame_out, frame_in, t, duration,
                )
            elif style == "slide":
                result = VisualEffects.apply_slide_transition_lazy(
                    frame_out, frame_in, t, duration, direction="left",
                )
            elif style == "radial":
                result = VisualEffects.apply_radial_reveal_lazy(
                    frame_out, frame_in, t, duration,
                )
            elif style == "wipe":
                result = VisualEffects.apply_wipe_transition_lazy(
                    frame_out, frame_in, t, duration, direction="right",
                )
            else:
                # Fallback: simple blend
                progress = max(0.0, min(1.0, t / max(duration, 0.001)))
                result = Image.blend(frame_out, frame_in, progress)

            return _pil_to_numpy(result)

        return VideoClip(make_frame, duration=duration)

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
        style = getattr(music_config, "estilo", "auto")
        music_path = self._music_manager.generate_background_music(
            duration_seconds=total_duration,
            output_path=None,  # Dejar que el manager elija el nombre con el estilo
            volume=music_config.volumen,
            bpm=music_config.bpm,
            style=style,
        )

        try:
            music_audio = _safe_audio_clip(str(music_path))

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
