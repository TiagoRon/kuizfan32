"""Pipeline principal de generación de videos de quiz.

Orquesta todos los componentes del sistema en secuencia:
1. Cargar configuración y plugins
2. Investigar tendencias (opcional)
3. Generar quiz con IA
4. Verificar duplicados
5. Generar audio TTS
6. Componer video
7. Exportar

Cada paso es idempotente y puede reintentarse independientemente.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from quiz_generator.ai.gemini_provider import GeminiProvider
from quiz_generator.anti_repetition.engine import AntiRepetitionEngine
from quiz_generator.audio.engine import AudioEngine
from quiz_generator.config import Settings, get_settings
from quiz_generator.core.enums import Difficulty, PipelineStep, QuizType
from quiz_generator.core.exceptions import DuplicateContentError, PipelineError
from quiz_generator.core.models import GenerationRequest, GenerationResult, Quiz
from quiz_generator.plugins.registry import PluginRegistry, discover_and_register_builtin_plugins
from quiz_generator.video.engine import VideoEngine
from quiz_generator.video.video_fetcher import VideoFetcher

logger = logging.getLogger(__name__)


class GenerationPipeline:
    """Pipeline principal que orquesta todo el proceso de generación.

    Coordina la generación de contenido por IA, la síntesis de audio,
    la composición de video y la exportación final.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._ai_provider = GeminiProvider(self._settings)
        self._audio_engine = AudioEngine(self._settings)
        self._video_engine = VideoEngine(self._settings)
        self._anti_rep = AntiRepetitionEngine(self._settings)
        self._registry = discover_and_register_builtin_plugins()
        self._video_fetcher = VideoFetcher(
            api_key=self._settings.pexels_api_key,
            cache_dir=self._settings.assets.directorio_cache + "/videos",
        )

        # Callbacks de progreso
        self._progress_callback: Any = None

    def on_progress(self, callback: Any) -> None:
        """Registra un callback para recibir actualizaciones de progreso.

        El callback recibe: (step: PipelineStep, progress: float, message: str)
        """
        self._progress_callback = callback

    def _report_progress(self, step: PipelineStep, progress: float, message: str) -> None:
        """Reporta progreso al callback registrado."""
        logger.info("[%s] %.0f%% — %s", step.value, progress * 100, message)
        if self._progress_callback:
            self._progress_callback(step, progress, message)

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Ejecuta el pipeline completo de generación.

        Args:
            request: Solicitud de generación con tipo, dificultad, etc.

        Returns:
            GenerationResult con el quiz, rutas de archivos y metadatos.

        Raises:
            PipelineError: Si algún paso crítico falla.
        """
        errors: list[str] = []

        try:
            # Paso 1: Resolver plugin
            self._report_progress(
                PipelineStep.GENERAR_QUIZ, 0.0,
                f"Iniciando generación: {request.tipo.value}",
            )
            plugin = self._registry.get(request.tipo)
            logger.info("Plugin resuelto: %s", plugin.name)

            # Paso 2: Generar quiz con IA
            self._report_progress(
                PipelineStep.GENERAR_QUIZ, 0.1,
                "Generando quiz con IA...",
            )
            quiz = await self._generate_quiz(request, plugin)

            # Paso 3: Verificar duplicados
            self._report_progress(
                PipelineStep.VERIFICAR_DUPLICADOS, 0.3,
                "Verificando duplicados...",
            )
            await self._check_duplicates(quiz)

            # Paso 4: Validar quiz
            validation_errors = plugin.validate_quiz(quiz)
            if validation_errors:
                logger.warning("Errores de validación: %s", validation_errors)
                errors.extend(validation_errors)

            # Paso 5: Generar audio
            self._report_progress(
                PipelineStep.GENERAR_AUDIO, 0.4,
                "Generando audio con TTS...",
            )
            output_dir = Path(self._settings.exportacion.directorio_salida) / quiz.id
            audio_dir = output_dir / "audio"
            audio_pack = await self._audio_engine.generate_quiz_audio(quiz, audio_dir)

            # Paso 6: Descargar videos de respuesta (Pexels)
            answer_videos: dict[str, Path] = {}
            if self._video_fetcher.is_available:
                self._report_progress(
                    PipelineStep.DESCARGAR_ASSETS, 0.55,
                    "Descargando videos de respuesta...",
                )
                answer_videos = await self._download_answer_videos(quiz)

            # Paso 7: Componer video
            self._report_progress(
                PipelineStep.COMPONER_VIDEO, 0.6,
                "Componiendo video...",
            )
            video_path = output_dir / f"{quiz.id}.mp4"
            await self._video_engine.compose_video(
                quiz, audio_pack, video_path, answer_videos=answer_videos,
            )

            # Paso 7: Registrar en anti-repetición
            self._report_progress(
                PipelineStep.GENERAR_METADATA, 0.9,
                "Registrando contenido...",
            )
            await self._register_content(quiz)

            # Resultado
            self._report_progress(
                PipelineStep.EXPORTAR, 1.0,
                "¡Video generado exitosamente!",
            )

            # Verificar si se generó miniatura
            thumbnail_path = output_dir / f"{quiz.id}_thumbnail.png"
            thumb_str = str(thumbnail_path) if thumbnail_path.exists() else None

            return GenerationResult(
                quiz=quiz,
                video_path=str(video_path),
                thumbnail_path=thumb_str,
                errores=errors,
                metadata_extra={
                    "tokens_usados": self._ai_provider.tokens_used,
                    "plugin": plugin.name,
                },
            )

        except DuplicateContentError as e:
            raise PipelineError(
                PipelineStep.VERIFICAR_DUPLICADOS.value,
                str(e),
            ) from e
        except Exception as e:
            raise PipelineError("pipeline", str(e)) from e

    async def _generate_quiz(
        self,
        request: GenerationRequest,
        plugin: Any,
    ) -> Quiz:
        """Genera el quiz usando el proveedor de IA y el plugin."""
        context = {
            "instrucciones_plugin": plugin.build_prompt_instructions(),
        }

        # Si anti-repetición está activo, incluir preguntas existentes
        if self._settings.anti_repeticion.habilitado and self._anti_rep.total_entries > 0:
            context["preguntas_existentes"] = []  # Se podrían cargar del store

        quiz = await self._ai_provider.generate_quiz(
            quiz_type=request.tipo,
            difficulty=request.dificultad,
            num_questions=request.num_preguntas,
            language=request.idioma,
            topic=request.tema,
            context=context,
        )

        return quiz

    async def _check_duplicates(self, quiz: Quiz) -> None:
        """Verifica que las preguntas no sean duplicadas."""
        if not self._settings.anti_repeticion.habilitado:
            return

        for pregunta in quiz.preguntas:
            is_dup = await self._anti_rep.is_duplicate(pregunta.texto)
            if is_dup:
                raise DuplicateContentError(pregunta.texto, 0.85)

    async def _register_content(self, quiz: Quiz) -> None:
        """Registra el contenido generado en el sistema anti-repetición."""
        if not self._settings.anti_repeticion.habilitado:
            return

        for pregunta in quiz.preguntas:
            await self._anti_rep.register(
                pregunta.texto,
                metadata={"quiz_id": quiz.id, "tipo": quiz.tipo.value},
            )

        # Registrar hook
        await self._anti_rep.register(
            quiz.hook.texto,
            metadata={"quiz_id": quiz.id, "tipo": "hook"},
        )

        # Persistir
        await self._anti_rep.flush()

    async def _download_answer_videos(self, quiz: Quiz) -> dict[str, Path]:
        """Descarga videos de Pexels para las respuestas correctas."""
        keywords = []
        for pregunta in quiz.preguntas:
            correcta = next(
                (r.texto for r in pregunta.respuestas if r.es_correcta),
                None,
            )
            if correcta:
                keywords.append(correcta)

        result = await self._video_fetcher.fetch_videos_batch(keywords)
        # Filtrar None values
        return {k: v for k, v in result.items() if v is not None}


async def run_generation(
    quiz_type: str = "trivia",
    difficulty: str = "medio",
    num_questions: int = 8,
    topic: str | None = None,
    language: str = "es",
) -> GenerationResult:
    """Función de conveniencia para ejecutar una generación completa.

    Ideal para uso desde CLI o GitHub Actions.
    """
    settings = get_settings()
    pipeline = GenerationPipeline(settings)

    request = GenerationRequest(
        tipo=QuizType(quiz_type),
        dificultad=Difficulty(difficulty),
        num_preguntas=num_questions,
        tema=topic,
        idioma=language,
    )

    return await pipeline.generate(request)
