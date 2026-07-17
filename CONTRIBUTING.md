# Contribuir al AI Viral Quiz Generator

¡Gracias por tu interés en contribuir! 🎉

## Cómo Contribuir

1. Haz fork del repositorio
2. Crea una rama para tu feature: `git checkout -b feature/mi-nueva-feature`
3. Instala en modo desarrollo: `pip install -e ".[dev]"`
4. Haz tus cambios siguiendo las guías de estilo
5. Ejecuta los tests: `pytest tests/ -v`
6. Ejecuta el linter: `ruff check src/ && ruff format src/`
7. Crea un Pull Request con una descripción clara

## Guía de Estilo

- **Linter**: Usamos `ruff` con la configuración de `ruff.toml`
- **Tipado**: Todo el código debe tener type hints
- **Documentación**: Docstrings en español para módulos, clases y funciones públicas
- **Tests**: Cada nueva feature debe incluir tests unitarios
- **Commits**: Mensajes descriptivos en español

## Agregar un Nuevo Tipo de Quiz

1. Crea un archivo en `src/quiz_generator/plugins/builtin/`
2. Hereda de `BaseQuizPlugin`
3. Implementa `quiz_type`, `name`, `description`, `build_prompt_instructions()`
4. El plugin se auto-registra al importarse
5. Agrega tests en `tests/unit/`

## Estructura de un Plugin

```python
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry
from quiz_generator.core.enums import QuizType

class MiPlugin(BaseQuizPlugin):
    @property
    def quiz_type(self) -> QuizType:
        return QuizType.MI_TIPO

    @property
    def name(self) -> str:
        return "Mi Tipo de Quiz"

    @property
    def description(self) -> str:
        return "Descripción del tipo"

    def build_prompt_instructions(self) -> str:
        return "Instrucciones para la IA..."

PluginRegistry().register(MiPlugin())
```

## Reportar Bugs

Abre un Issue con:
- Descripción del problema
- Pasos para reproducirlo
- Logs relevantes
- Versión de Python y SO
