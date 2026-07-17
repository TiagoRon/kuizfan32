"""Gestor de plantillas de prompts con Jinja2.

Carga y renderiza las plantillas .j2 que definen los prompts
enviados al LLM para cada tarea de generación.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Directorio donde están las plantillas .j2
_PROMPTS_DIR = Path(__file__).parent / "prompts"


class PromptManager:
    """Gestor centralizado de plantillas de prompts.

    Usa Jinja2 para renderizar plantillas con variables dinámicas,
    permitiendo separar la lógica de los prompts del código Python.
    """

    def __init__(self, prompts_dir: Path | None = None) -> None:
        self._dir = prompts_dir or _PROMPTS_DIR
        self._env = Environment(
            loader=FileSystemLoader(str(self._dir)),
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, **kwargs: Any) -> str:
        """Renderiza una plantilla de prompt con las variables dadas.

        Args:
            template_name: Nombre del archivo de plantilla (ej: "quiz_generation.j2").
            **kwargs: Variables para inyectar en la plantilla.

        Returns:
            Prompt renderizado listo para enviar al LLM.
        """
        template = self._env.get_template(template_name)
        return template.render(**kwargs)

    def list_templates(self) -> list[str]:
        """Lista todas las plantillas disponibles."""
        return [
            p.name for p in self._dir.glob("*.j2")
        ]
