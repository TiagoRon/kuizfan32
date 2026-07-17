"""Punto de entrada CLI del AI Viral Quiz Generator.

Permite ejecutar generaciones desde la línea de comandos o GitHub Actions.
Uso:
    python -m quiz_generator generate --type trivia --difficulty medio --questions 8
    python -m quiz_generator list-types
"""

from __future__ import annotations

import asyncio
import logging
import sys

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from quiz_generator import __app_name__, __version__
from quiz_generator.core.enums import Difficulty, PipelineStep, QuizType
from quiz_generator.plugins.registry import discover_and_register_builtin_plugins

console = Console()


def _setup_logging(verbose: bool = False) -> None:
    """Configura el sistema de logging con Rich."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, console=console)],
    )


@click.group()
@click.version_option(version=__version__, prog_name=__app_name__)
@click.option("--verbose", "-v", is_flag=True, help="Modo detallado (debug)")
def cli(verbose: bool) -> None:
    """🧠 AI Viral Quiz Generator — Genera videos de quiz virales con IA."""
    _setup_logging(verbose)


@cli.command()
@click.option(
    "--type", "-t", "quiz_type",
    type=click.Choice([qt.value for qt in QuizType], case_sensitive=False),
    default="trivia",
    help="Tipo de quiz a generar",
)
@click.option(
    "--difficulty", "-d",
    type=click.Choice([d.value for d in Difficulty], case_sensitive=False),
    default="medio",
    help="Nivel de dificultad",
)
@click.option(
    "--questions", "-q",
    type=int, default=8,
    help="Número de preguntas (3-20)",
)
@click.option(
    "--topic",
    type=str, default=None,
    help="Tema específico (opcional, ej: 'Pokémon Gen 1')",
)
@click.option(
    "--language", "-l",
    type=str, default="es",
    help="Idioma del contenido",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="Directorio de salida personalizado",
)
def generate(
    quiz_type: str,
    difficulty: str,
    questions: int,
    topic: str | None,
    language: str,
    output: str | None,
) -> None:
    """🎬 Genera un video de quiz viral completo."""
    console.print(Panel.fit(
        f"[bold magenta]🧠 {__app_name__} v{__version__}[/]\n"
        f"[dim]Generando video de quiz...[/]",
        border_style="magenta",
    ))

    console.print(f"  📋 Tipo: [cyan]{quiz_type}[/]")
    console.print(f"  📊 Dificultad: [yellow]{difficulty}[/]")
    console.print(f"  ❓ Preguntas: [green]{questions}[/]")
    if topic:
        console.print(f"  🎯 Tema: [blue]{topic}[/]")
    console.print()

    # Importar aquí para evitar carga lenta de dependencias
    from quiz_generator.orchestrator.pipeline import run_generation

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Iniciando pipeline...", total=None)

        try:
            result = asyncio.run(
                run_generation(
                    quiz_type=quiz_type,
                    difficulty=difficulty,
                    num_questions=questions,
                    topic=topic,
                    language=language,
                )
            )

            progress.update(task, description="✅ ¡Completado!")

            # Mostrar resultado
            console.print()
            console.print(Panel.fit(
                f"[bold green]✅ Video generado exitosamente[/]\n\n"
                f"📁 Archivo: [cyan]{result.video_path}[/]\n"
                f"📝 Título: {result.quiz.metadata.titulo}\n"
                f"🏷️  Hashtags: {', '.join(result.quiz.metadata.hashtags[:5])}\n"
                f"⚡ Tokens IA: {result.metadata_extra.get('tokens_usados', 'N/A')}",
                title="Resultado",
                border_style="green",
            ))

            if result.errores:
                console.print(f"\n[yellow]⚠️  Advertencias: {len(result.errores)}[/]")
                for error in result.errores:
                    console.print(f"  • {error}")

        except Exception as e:
            progress.update(task, description="❌ Error")
            console.print(f"\n[bold red]❌ Error:[/] {e}")
            logging.exception("Error en la generación")
            sys.exit(1)


@cli.command("list-types")
def list_types() -> None:
    """📋 Lista todos los tipos de quiz disponibles."""
    registry = discover_and_register_builtin_plugins()
    plugins = registry.list_all()

    table = Table(
        title="🧠 Tipos de Quiz Disponibles",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Tipo", style="cyan")
    table.add_column("Nombre", style="green")
    table.add_column("Descripción")
    table.add_column("Preguntas", justify="center")
    table.add_column("Imágenes", justify="center")

    for plugin in sorted(plugins, key=lambda p: p.name):
        table.add_row(
            plugin.quiz_type.value,
            plugin.name,
            plugin.description,
            f"{plugin.min_questions}-{plugin.max_questions}",
            "✅" if plugin.requires_images else "❌",
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(plugins)} tipos disponibles[/]")


@cli.command()
def config() -> None:
    """⚙️  Muestra la configuración actual."""
    from quiz_generator.config import get_settings

    settings = get_settings()

    console.print(Panel.fit(
        f"[bold]Configuración Actual[/]\n\n"
        f"🤖 IA: {settings.ia.proveedor} ({settings.ia.modelo})\n"
        f"🗣️  TTS: {settings.tts.proveedor} ({settings.tts.voz})\n"
        f"📐 Video: {settings.video.ancho}×{settings.video.alto} @ {settings.video.fps}fps\n"
        f"🌍 Idioma: {settings.general.idioma}\n"
        f"📊 Dificultad: {settings.general.dificultad_default}\n"
        f"🔄 Anti-Repetición: {'✅' if settings.anti_repeticion.habilitado else '❌'}\n"
        f"📁 Salida: {settings.exportacion.directorio_salida}\n"
        f"🗄️  BD: {settings.base_datos.url}",
        title="⚙️  Configuración",
        border_style="blue",
    ))


def main() -> None:
    """Punto de entrada principal."""
    cli()


if __name__ == "__main__":
    main()
