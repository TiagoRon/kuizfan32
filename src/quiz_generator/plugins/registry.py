"""Registro y descubrimiento automático de plugins.

El PluginRegistry mantiene un mapa de QuizType → plugin.
Los plugins built-in se registran automáticamente al importar el paquete.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from typing import TYPE_CHECKING

from quiz_generator.core.enums import QuizType
from quiz_generator.core.exceptions import PluginNotFoundError

if TYPE_CHECKING:
    from quiz_generator.plugins.base_plugin import BaseQuizPlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registro global de plugins de tipos de quiz.

    Singleton que gestiona el descubrimiento, registro y acceso
    a todos los plugins disponibles.
    """

    _instance: PluginRegistry | None = None
    _plugins: dict[QuizType, BaseQuizPlugin]

    def __new__(cls) -> PluginRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._plugins = {}
        return cls._instance

    def register(self, plugin: BaseQuizPlugin) -> None:
        """Registra un plugin en el registro.

        Args:
            plugin: Instancia del plugin a registrar.
        """
        if plugin.quiz_type in self._plugins:
            logger.warning(
                "Plugin para '%s' ya existe. Sobrescribiendo con '%s'.",
                plugin.quiz_type, plugin.name,
            )
        self._plugins[plugin.quiz_type] = plugin
        logger.debug("Plugin registrado: %s (%s)", plugin.name, plugin.quiz_type)

    def get(self, quiz_type: QuizType) -> BaseQuizPlugin:
        """Obtiene un plugin por tipo de quiz.

        Args:
            quiz_type: Tipo de quiz a buscar.

        Returns:
            El plugin correspondiente.

        Raises:
            PluginNotFoundError: Si no hay plugin registrado para ese tipo.
        """
        plugin = self._plugins.get(quiz_type)
        if plugin is None:
            raise PluginNotFoundError(quiz_type.value)
        return plugin

    def has(self, quiz_type: QuizType) -> bool:
        """Verifica si hay un plugin registrado para un tipo de quiz."""
        return quiz_type in self._plugins

    def list_all(self) -> list[BaseQuizPlugin]:
        """Lista todos los plugins registrados."""
        return list(self._plugins.values())

    def list_types(self) -> list[QuizType]:
        """Lista todos los tipos de quiz con plugin registrado."""
        return list(self._plugins.keys())

    def count(self) -> int:
        """Número de plugins registrados."""
        return len(self._plugins)

    def clear(self) -> None:
        """Limpia todos los plugins (útil para tests)."""
        self._plugins.clear()

    @classmethod
    def reset(cls) -> None:
        """Resetea el singleton (útil para tests)."""
        cls._instance = None


def discover_and_register_builtin_plugins() -> PluginRegistry:
    """Descubre y registra automáticamente todos los plugins built-in.

    Escanea el paquete `quiz_generator.plugins.builtin` e importa
    todos los módulos, que se auto-registran al importarse.

    Returns:
        La instancia del PluginRegistry con los plugins cargados.
    """
    registry = PluginRegistry()

    builtin_package = "quiz_generator.plugins.builtin"

    try:
        package = importlib.import_module(builtin_package)
    except ModuleNotFoundError:
        logger.warning("No se encontró el paquete de plugins built-in: %s", builtin_package)
        return registry

    package_path = getattr(package, "__path__", None)
    if package_path is None:
        return registry

    import sys
    for _importer, module_name, _is_pkg in pkgutil.iter_modules(package_path):
        full_name = f"{builtin_package}.{module_name}"
        try:
            if full_name in sys.modules:
                importlib.reload(sys.modules[full_name])
            else:
                importlib.import_module(full_name)
            logger.debug("Módulo de plugin cargado: %s", full_name)
        except Exception:
            logger.exception("Error al cargar plugin '%s'", full_name)

    logger.info("Plugins registrados: %d", registry.count())
    return registry
