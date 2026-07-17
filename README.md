# 🧠 AI Viral Quiz Generator

<div align="center">

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=github-actions&logoColor=white)](.github/workflows/ci.yml)
[![Code Style: Ruff](https://img.shields.io/badge/Code_Style-Ruff-D7FF64?logo=ruff&logoColor=black)](https://github.com/astral-sh/ruff)

**Plataforma profesional de generación automática de videos virales de quizzes
para YouTube Shorts, TikTok e Instagram Reels.**

[Inicio Rápido](#-inicio-rápido) •
[Tipos de Quiz](#-tipos-de-quiz) •
[Arquitectura](#-arquitectura) •
[Configuración](#%EF%B8%8F-configuración) •
[Plugins](#-plugins) •
[GitHub Actions](#-uso-con-github-actions)

</div>

---

## ✨ Características

- 🤖 **Generación con IA** — Usa Google Gemini para crear preguntas únicas, hooks virales y metadatos optimizados
- 🎬 **Renderizado automático** — Video completo en formato 9:16 (1080×1920) a 60 FPS
- 🗣️ **Narración por TTS** — Edge TTS gratuito con subtítulos sincronizados palabra por palabra
- 🔄 **Anti-repetición** — Embeddings semánticos + FAISS para nunca repetir contenido
- 🧩 **Sistema de plugins** — Agrega nuevos tipos de quiz sin tocar el núcleo
- 🎨 **Estilo viral** — Diseño inspirado en MrBeast, con colores, timers y efectos
- ⚡ **GitHub Actions** — Genera videos directamente desde GitHub, sin setup local
- 📐 **100% configurable** — Todo personalizable via YAML sin modificar código
- 🧠 **Psicología viral** — Hooks, FOMO, competencia, curiosidad y más

## 🚀 Inicio Rápido

### Opción 1: Desde GitHub Actions (Recomendado)

1. Haz fork de este repositorio
2. Ve a **Settings → Secrets → Actions** y agrega `GEMINI_API_KEY`
3. Ve a **Actions → 🎬 Generar Video de Quiz**
4. Click en **Run workflow**, selecciona tipo y dificultad
5. Descarga el video desde los artefactos del workflow

### Opción 2: Ejecución Local

```bash
# Clonar
git clone https://github.com/tu-usuario/ai-viral-quiz-generator.git
cd ai-viral-quiz-generator

# Instalar dependencias
pip install -e ".[dev]"

# Configurar API key
export GEMINI_API_KEY="tu_clave_aqui"

# Generar un video
python -m quiz_generator generate --type trivia --difficulty medio --questions 8
```

## 🎮 Tipos de Quiz (30 tipos)

| Tipo | Descripción | Estado |
|:---|:---|:---|
| 🧠 Trivia | Cultura general con 4 opciones | ✅ |
| ✅❌ Verdadero o Falso | Afirmaciones verdaderas o falsas | ✅ |
| 🤔 ¿Qué Prefieres? | Elige entre dos opciones extremas | ✅ |
| 😀 Emoji Quiz | Adivina por secuencia de emojis | ✅ |
| 🏳️ Adivina la Bandera | Identifica el país por su bandera | ✅ |
| ⚡ Adivina el Pokémon | Identifica Pokémon por pistas | ✅ |
| 🎬 Adivina la Película | Adivina por trama, emojis o escenas | ✅ |
| 🎵 Adivina la Canción | Adivina por letra o pistas musicales | ✅ |
| ⚽ Adivina el Futbolista | Identifica futbolistas por stats/pistas | ✅ |
| 🚗 Adivina el Auto | Identifica autos por silueta o datos | ✅ |
| 🧩 Acertijo Mental | Lógica y pensamiento lateral | ✅ |
| 💀 Quiz Imposible | Preguntas trampa y absurdas | ✅ |
| 🎭 Adivina el Personaje | Personajes de ficción, anime, series | ✅ |
| 🌍 Adivina el País | Países por datos geográficos/culturales | ✅ |
| 🏷️ Adivina el Logo | Marcas por su logo | ✅ |
| 🐾 Adivina el Animal | Animales por características | ✅ |
| 🏢 Adivina la Marca | Marcas por eslogan o datos | ✅ |
| 🍕 Adivina la Comida | Platos por ingredientes u origen | ✅ |
| ⭐ Adivina la Celebridad | Celebridades por datos biográficos | ✅ |
| 🎙️ Adivina la Voz | Identifica voces famosas | ✅ |
| 🔊 Adivina el Sonido | Sonidos de naturaleza/instrumentos | ✅ |
| ⚖️ ¿Quién es más...? | Comparaciones sorprendentes | ✅ |
| ⚡ Decisión Rápida | 3 segundos para elegir | ✅ |
| 🏕️ Elección de Supervivencia | Escenarios extremos | ✅ |
| 🧠 Desafío de Memoria | Recuerda patrones y secuencias | ✅ |
| 👀 Encuentra la Diferencia | Encuentra el elemento diferente | ✅ |
| 🔍 Encuentra el Error | Detecta errores en datos | ✅ |
| 🧪 Test de IQ | Patrones, secuencias y lógica | ✅ |
| 💡 Adivinanza | Acertijos clásicos con giro moderno | ✅ |
| 👁️ Ilusión Óptica | Percepción visual y trucos | ✅ |

## 🏗️ Arquitectura

```
Arquitectura Hexagonal (Puertos y Adaptadores)
├── Core (Dominio)        → Modelos, enums, interfaces abstractas
├── AI Engine             → Gemini provider (intercambiable)
├── Plugin System         → Quiz types como plugins independientes
├── Audio Engine          → Edge TTS con timestamps
├── Video Engine          → Pillow + MoviePy compositor
├── Anti-Repetition       → sentence-transformers + FAISS
├── Pipeline Orchestrator → Coordina todo el flujo
└── CLI / GitHub Actions  → Puntos de entrada
```

## ⚙️ Configuración

Todo se configura en `config/config.yaml` (o variables de entorno):

```yaml
# Ejemplo: Cambiar voz y dificultad por defecto
general:
  dificultad_default: "dificil"

tts:
  voz: "es-AR-ElenaNeural"
  velocidad: 1.2

video:
  colores:
    primario: "#FF6B6B"
    fondo: "#1A1A2E"
  tiempos:
    tiempo_por_pregunta: 8
```

## 🧩 Plugins

Crear un nuevo tipo de quiz es simple:

```python
# src/quiz_generator/plugins/builtin/mi_quiz.py
from quiz_generator.plugins.base_plugin import BaseQuizPlugin
from quiz_generator.plugins.registry import PluginRegistry
from quiz_generator.core.enums import QuizType

class MiQuizPlugin(BaseQuizPlugin):
    @property
    def quiz_type(self) -> QuizType:
        return QuizType.TRIVIA  # Usa un tipo existente o crea uno nuevo

    @property
    def name(self) -> str:
        return "Mi Quiz Personalizado"

    @property
    def description(self) -> str:
        return "Descripción de mi quiz"

    def build_prompt_instructions(self) -> str:
        return "Instrucciones para que la IA genere este tipo de quiz..."

# Auto-registrar
PluginRegistry().register(MiQuizPlugin())
```

## 🔧 GitHub Actions

### Generar Video Manualmente

Ve a **Actions → 🎬 Generar Video de Quiz → Run workflow** y selecciona:

- **Tipo de quiz**: trivia, emoji_quiz, guess_pokemon, etc.
- **Dificultad**: facil, medio, dificil, imposible
- **Preguntas**: 3-20
- **Tema**: (opcional) "Pokémon Gen 1", "Historia de México", etc.

El video se descarga como artefacto del workflow.

### Secrets Necesarios

| Secret | Descripción | Requerido |
|:---|:---|:---|
| `GEMINI_API_KEY` | Clave API de Google Gemini | ✅ Sí |
| `ELEVENLABS_API_KEY` | Clave de ElevenLabs (TTS premium) | ❌ Opcional |

## 📁 Estructura del Proyecto

```
├── src/quiz_generator/      # Código fuente principal
│   ├── core/                # Modelos, enums, interfaces
│   ├── ai/                  # Proveedor de IA (Gemini)
│   ├── plugins/             # Sistema de plugins
│   ├── audio/               # Motor de TTS
│   ├── video/               # Motor de composición de video
│   ├── anti_repetition/     # Sistema anti-duplicados
│   ├── orchestrator/        # Pipeline de generación
│   └── config/              # Sistema de configuración
├── config/                  # Archivos YAML de configuración
├── assets/                  # Sonidos, fuentes, imágenes
├── tests/                   # Tests unitarios e integración
├── .github/workflows/       # GitHub Actions
└── output/                  # Videos generados
```

## 🧪 Desarrollo

```bash
# Instalar en modo desarrollo
pip install -e ".[dev]"

# Ejecutar tests
pytest tests/unit/ -v

# Linting
ruff check src/
ruff format src/

# Type checking
mypy src/quiz_generator/
```

## 🗺️ Roadmap

- [x] Fase 1: Core + 6 tipos de quiz + pipeline completo
- [x] Fase 2: 30 tipos de quiz + efectos avanzados + miniaturas
- [ ] Fase 3: Panel web (FastAPI + React)
- [ ] Fase 4: Auto-publicación + analítica + A/B testing

## 📄 Licencia

[MIT](LICENSE)

---

<div align="center">
  <sub>Hecho con 🧠 IA y ❤️ por el equipo de AI Viral Quiz Generator</sub>
</div>
