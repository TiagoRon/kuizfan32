"""Paquete de integración con proveedores de IA."""

from quiz_generator.ai.gemini_provider import GeminiProvider
from quiz_generator.ai.groq_provider import GroqProvider
from quiz_generator.ai.offline_provider import OfflineQuizProvider
from quiz_generator.ai.prompt_manager import PromptManager

__all__ = [
    "GeminiProvider",
    "GroqProvider",
    "OfflineQuizProvider",
    "PromptManager",
]
