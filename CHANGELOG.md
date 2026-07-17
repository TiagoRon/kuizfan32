# Changelog

Todos los cambios notables en este proyecto se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

## [0.2.0] — 2026-07-17

### Agregado

- 🧩 24 nuevos plugins de quiz (total: 30 tipos):
  - Adivina: Personaje, País, Logo, Película, Canción, Animal, Marca,
    Comida, Celebridad, Futbolista, Auto, Voz, Sonido
  - Conocimiento: ¿Quién es más?
  - Decisiones: Decisión Rápida, Elección de Supervivencia
  - Desafíos mentales: Desafío de Memoria, Encuentra la Diferencia,
    Encuentra el Error, Acertijo Mental, Quiz Imposible, Test de IQ,
    Adivinanza, Ilusión Óptica
- 🎨 Módulo de efectos visuales avanzados (`video/effects.py`):
  - Confeti para respuestas correctas
  - Shake para momentos de tensión
  - Glow para resaltar respuestas
  - Flash para revelaciones
  - Viñeta cinematográfica para hooks
  - Zoom pulse para transiciones
  - Color overlay para feedback visual
- 🖼️ Generador de miniaturas virales (`video/thumbnail.py`):
  - Texto con outline para máxima legibilidad
  - Fondos gradiente vibrantes
  - Emojis decorativos gigantes
  - Generación automática en el pipeline
- 🎬 Integración de efectos en el motor de video:
  - Confeti automático al revelar respuestas correctas
  - Viñeta en la escena del hook
  - Color overlay suave en revelaciones
- 🧪 Tests unitarios completos:
  - `test_builtin_plugins.py`: 30 plugins verificados
  - `test_effects.py`: Todos los efectos visuales
  - `test_thumbnail.py`: Generación de miniaturas
- 📝 README actualizado con los 30 tipos de quiz

## [0.1.0] — 2026-07-17

### Agregado

- 🏗️ Arquitectura base con Clean Architecture y sistema de plugins
- 🤖 Integración con Google Gemini para generación de contenido
- 🗣️ Motor de TTS con Edge TTS (gratuito, sin API key)
- 🎬 Motor de composición de video con Pillow + MoviePy
- 🔄 Sistema anti-repetición con sentence-transformers + FAISS
- 🧩 6 plugins de quiz iniciales:
  - Trivia de Cultura General
  - Verdadero o Falso
  - ¿Qué Prefieres?
  - Emoji Quiz
  - Adivina la Bandera
  - Adivina el Pokémon
- ⚡ Pipeline de generación completo (IA → TTS → Video → MP4)
- 📐 Sistema de configuración con YAML + variables de entorno
- 🖥️ CLI con Click y Rich
- 🔧 GitHub Actions workflow para generación remota
- 🧪 Tests unitarios
- 📝 README profesional y documentación
