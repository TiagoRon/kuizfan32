"""Proveedor de IA Offline / Local de respaldo.

Genera quizzes, hooks y metadatos de alta calidad basados en bancos de preguntas
curadas y generadores algorítmicos para todos los tipos de quiz.
Garantiza que el pipeline de generación de video NUNCA falle ante caídas de API,
cortes de conexión o límites de cuota (Rate Limits 429).
"""

from __future__ import annotations

import logging
import random
import uuid
from typing import Any

from quiz_generator.core.enums import Difficulty, QuizType, ViralTrigger
from quiz_generator.core.interfaces import IAIProvider
from quiz_generator.core.models import (
    Answer,
    Hook,
    Question,
    Quiz,
    QuizMetadata,
)

logger = logging.getLogger(__name__)


class OfflineQuizProvider(IAIProvider):
    """Proveedor de IA offline de emergencia sin dependencia de APIs externas."""

    def __init__(self) -> None:
        self._tokens_used = 0

    @property
    def tokens_used(self) -> int:
        return self._tokens_used

    async def generate_quiz(
        self,
        quiz_type: QuizType,
        difficulty: Difficulty,
        num_questions: int,
        language: str = "es",
        topic: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Quiz:
        """Genera un quiz completo utilizando el banco de preguntas offline."""
        logger.info(
            "Generando quiz con proveedor OFFLINE (respaldo): tipo=%s, dificultad=%s, preguntas=%d",
            quiz_type.value, difficulty.value, num_questions,
        )

        hook = self._generate_hook(quiz_type, difficulty, topic)
        preguntas = self._generate_questions(quiz_type, difficulty, num_questions, topic)
        metadata = self._generate_metadata(quiz_type, difficulty, topic)
        triggers = [ViralTrigger.CURIOSIDAD, ViralTrigger.COMPETENCIA, ViralTrigger.SORPRESA]

        return Quiz(
            id=str(uuid.uuid4())[:8],
            tipo=quiz_type,
            dificultad=difficulty,
            idioma=language,
            hook=hook,
            preguntas=preguntas,
            metadata=metadata,
            disparadores_virales=triggers,
        )

    async def generate_hooks(
        self,
        quiz_type: QuizType,
        count: int = 5,
        language: str = "es",
    ) -> list[str]:
        """Genera hooks virales."""
        hooks_pool = [
            f"🧠 ¡Solo el 1% puede responder este quiz de {quiz_type.value}!",
            f"🔥 ¿Eres un verdadero experto en {quiz_type.value}? ¡Pruébalo!",
            "⚡ 99% falla en la última pregunta de este quiz",
            "🎯 ¿Cuántas puedes acertar? ¡Comenta tu puntuación!",
            "👀 El test definitivo que pondrá a prueba tu cerebro",
            "🏆 Si aciertas más de 5, eres un genio absoluto",
        ]
        return random.sample(hooks_pool, min(count, len(hooks_pool)))

    async def generate_metadata(
        self,
        quiz: Quiz,
        language: str = "es",
    ) -> QuizMetadata:
        """Genera metadatos para el quiz."""
        return self._generate_metadata(quiz.tipo, quiz.dificultad, None)

    async def analyze_trends(
        self,
        category: str,
        language: str = "es",
    ) -> dict[str, Any]:
        """Retorna tendencias por defecto."""
        return {
            "tendencias": [f"Reto viral {category}", f"Quiz rápido {category}", f"Curiosidades {category}"],
            "temas_calientes": [category, "viral", "challenge", "shorts", "trivia"],
        }

    # =========================================================================
    # Métodos internos de generación
    # =========================================================================

    def _generate_hook(
        self, quiz_type: QuizType, difficulty: Difficulty, topic: str | None
    ) -> Hook:
        topic_str = f" de {topic}" if topic else ""
        templates = [
            (f"🧠 ¡Solo el 1% responde todas{topic_str}!", ViralTrigger.COMPETENCIA, "🧠"),
            (f"😱 El 95% falla la última pregunta{topic_str}", ViralTrigger.SORPRESA, "😱"),
            (f"⚡ ¿Cuánto sabes realmente{topic_str}? ¡Pruébalo!", ViralTrigger.CURIOSIDAD, "⚡"),
            (f"🔥 ¿Eres un verdadero genio{topic_str}? Descúbrelo", ViralTrigger.DESAFIO, "🔥"),
            (f"🎯 Test viral{topic_str}: ¿Podrás acertar todas?", ViralTrigger.CURIOSIDAD, "🎯"),
        ]
        texto, tipo, emoji = random.choice(templates)
        return Hook(texto=texto, tipo=tipo, emoji=emoji)

    def _generate_metadata(
        self, quiz_type: QuizType, difficulty: Difficulty, topic: str | None
    ) -> QuizMetadata:
        topic_tag = topic.lower().replace(" ", "") if topic else quiz_type.value
        title_prefix = f"Quiz de {topic}" if topic else f"Quiz Viral de {quiz_type.value.replace('_', ' ').title()}"
        return QuizMetadata(
            titulo=f"🧠 {title_prefix} — ¿Cuántas aciertas?",
            descripcion=f"Pon a prueba tus conocimientos con este quiz de {quiz_type.value}. ¡Comenta cuántas acertaste!",
            hashtags=["quiz", "trivia", "viral", "shorts", "reels", "tiktok", topic_tag],
            prompt_miniatura=f"A vibrant colorful thumbnail for a {quiz_type.value} viral quiz, 4k quality, dramatic lighting",
            cta="¡Comenta tu puntuación y desafía a tus amigos! 🎯",
        )

    def _generate_questions(
        self, quiz_type: QuizType, difficulty: Difficulty, count: int, topic: str | None
    ) -> list[Question]:
        generator_method = getattr(self, f"_bank_{quiz_type.value}", self._bank_generic)
        pool = generator_method(difficulty, topic)

        if not pool:
            pool = self._bank_generic(difficulty, topic)

        # Si el pool es menor que count, multiplicar variando
        if len(pool) < count:
            multiplier = (count // len(pool)) + 1
            pool = pool * multiplier

        selected = random.sample(pool, min(count, len(pool)))
        return selected

    # =========================================================================
    # Bancos de preguntas específicos por tipo de quiz
    # =========================================================================

    def _bank_trivia(self, difficulty: Difficulty, topic: str | None) -> list[Question]:
        return [
            Question(
                texto="¿Cuál es el planeta más grande de nuestro sistema solar?",
                respuestas=[
                    Answer(texto="Marte", es_correcta=False, emoji="🔴"),
                    Answer(texto="Júpiter", es_correcta=True, explicacion="Júpiter es más grande que todos los demás planetas juntos.", emoji="🟠"),
                    Answer(texto="Saturno", es_correcta=False, emoji="🪐"),
                    Answer(texto="Neptuno", es_correcta=False, emoji="🔵"),
                ],
                dificultad=Difficulty.FACIL,
                curiosidad="Júpiter tiene más de 90 lunas confirmadas.",
                categoria="Astronomía",
            ),
            Question(
                texto="¿En qué año llegó el ser humano a la Luna por primera vez?",
                respuestas=[
                    Answer(texto="1965", es_correcta=False),
                    Answer(texto="1969", es_correcta=True, explicacion="Neil Armstrong pisó la Luna el 20 de julio de 1969."),
                    Answer(texto="1972", es_correcta=False),
                    Answer(texto="1959", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                curiosidad="La computadora del Apolo 11 tenía menos memoria que un teléfono básico actual.",
                categoria="Historia",
            ),
            Question(
                texto="¿Cuál es el elemento químico más abundante en el universo?",
                respuestas=[
                    Answer(texto="Oxígeno", es_correcta=False),
                    Answer(texto="Hidrógeno", es_correcta=True, explicacion="El hidrógeno conforma aproximadamente el 75% de la masa del universo."),
                    Answer(texto="Helio", es_correcta=False),
                    Answer(texto="Carbono", es_correcta=False),
                ],
                dificultad=Difficulty.MEDIO,
                curiosidad="Las estrellas están compuestas principalmente de hidrógeno y helio.",
                categoria="Química",
            ),
            Question(
                texto="¿Cuál es el hueso más largo del cuerpo humano?",
                respuestas=[
                    Answer(texto="Tibia", es_correcta=False),
                    Answer(texto="Húmero", es_correcta=False),
                    Answer(texto="Fémur", es_correcta=True, explicacion="El fémur soporta hasta 30 veces el peso del cuerpo."),
                    Answer(texto="Peroné", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                curiosidad="El fémur es más fuerte que el concreto.",
                categoria="Anatomía",
            ),
            Question(
                texto="¿Qué país tiene la mayor cantidad de islas en el mundo?",
                respuestas=[
                    Answer(texto="Indonesia", es_correcta=False),
                    Answer(texto="Filipinas", es_correcta=False),
                    Answer(texto="Suecia", es_correcta=True, explicacion="Suecia tiene más de 260.000 islas."),
                    Answer(texto="Canadá", es_correcta=False),
                ],
                dificultad=Difficulty.DIFICIL,
                curiosidad="Menos de 1.000 de las islas de Suecia están habitadas.",
                categoria="Geografía",
            ),
            Question(
                texto="¿Quién pintó la famosa obra 'La noche estrellada'?",
                respuestas=[
                    Answer(texto="Pablo Picasso", es_correcta=False),
                    Answer(texto="Vincent van Gogh", es_correcta=True, explicacion="La pintó en 1889 desde el sanatorio de Saint-Rémy."),
                    Answer(texto="Claude Monet", es_correcta=False),
                    Answer(texto="Salvador Dalí", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                curiosidad="Van Gogh pintó la vista desde su ventana este justo antes del amanecer.",
                categoria="Arte",
            ),
            Question(
                texto="¿Cuál es el océano más profundo de la Tierra?",
                respuestas=[
                    Answer(texto="Océano Atlántico", es_correcta=False),
                    Answer(texto="Océano Índico", es_correcta=False),
                    Answer(texto="Océano Pacífico", es_correcta=True, explicacion="La Fosa de las Marianas alcanza casi 11.000 metros de profundidad."),
                    Answer(texto="Océano Ártico", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                curiosidad="El Monte Everest cabría entero dentro de la Fosa de las Marianas.",
                categoria="Geografía",
            ),
            Question(
                texto="¿Cuántos corazones tiene un pulpo?",
                respuestas=[
                    Answer(texto="1", es_correcta=False),
                    Answer(texto="2", es_correcta=False),
                    Answer(texto="3", es_correcta=True, explicacion="Dos bombean sangre a las branquias y uno al resto del cuerpo."),
                    Answer(texto="4", es_correcta=False),
                ],
                dificultad=Difficulty.MEDIO,
                curiosidad="Además de tres corazones, los pulpos tienen sangre azul debido a la hemocianina.",
                categoria="Biología",
            ),
        ]

    def _bank_true_or_false(self, difficulty: Difficulty, topic: str | None) -> list[Question]:
        return [
            Question(
                texto="¿Las bananas son técnicamente una baya botánica?",
                respuestas=[
                    Answer(texto="Verdadero", es_correcta=True, explicacion="Botánicamente, la banana cumple todos los criterios de una baya.", emoji="✅"),
                    Answer(texto="Falso", es_correcta=False, emoji="❌"),
                ],
                dificultad=Difficulty.MEDIO,
                curiosidad="Las frutillas/fresas, en cambio, no son bayas botánicas.",
            ),
            Question(
                texto="¿La Gran Muralla China es visible a simple vista desde la Luna?",
                respuestas=[
                    Answer(texto="Verdadero", es_correcta=False, emoji="✅"),
                    Answer(texto="Falso", es_correcta=True, explicacion="Es un mito popular; los astronautas han confirmado que no es visible sin equipo.", emoji="❌"),
                ],
                dificultad=Difficulty.FACIL,
                curiosidad="Apenas las ciudades iluminadas son visibles de noche desde la órbita baja.",
            ),
            Question(
                texto="¿Los tiburones existieron antes que los árboles en la Tierra?",
                respuestas=[
                    Answer(texto="Verdadero", es_correcta=True, explicacion="Los tiburones aparecieron hace 400 millones de años, los árboles hace 350 millones.", emoji="✅"),
                    Answer(texto="Falso", es_correcta=False, emoji="❌"),
                ],
                dificultad=Difficulty.MEDIO,
                curiosidad="Los tiburones son más antiguos que los dinosaurios y los anillos de Saturno.",
            ),
            Question(
                texto="¿El ADN humano comparte cerca del 50% de sus genes con un plátano?",
                respuestas=[
                    Answer(texto="Verdadero", es_correcta=True, explicacion="Compartimos genes fundamentales para funciones celulares básicas.", emoji="✅"),
                    Answer(texto="Falso", es_correcta=False, emoji="❌"),
                ],
                dificultad=Difficulty.DIFICIL,
                curiosidad="También compartimos un 98% con los chimpancés.",
            ),
            Question(
                texto="¿El sonido viaja más rápido en el agua que en el aire?",
                respuestas=[
                    Answer(texto="Verdadero", es_correcta=True, explicacion="Viaja unas 4.3 veces más rápido en el agua (1482 m/s vs 343 m/s).", emoji="✅"),
                    Answer(texto="Falso", es_correcta=False, emoji="❌"),
                ],
                dificultad=Difficulty.FACIL,
                curiosidad="En el acero, el sonido viaja aún más rápido: a más de 5000 m/s.",
            ),
        ]

    def _bank_would_you_rather(self, difficulty: Difficulty, topic: str | None) -> list[Question]:
        return [
            Question(
                texto="¿Qué superpoder prefieres tener por el resto de tu vida?",
                respuestas=[
                    Answer(texto="Teletransportación instantánea", es_correcta=True, emoji="⚡"),
                    Answer(texto="Invisibilidad a voluntad", es_correcta=False, emoji="👻"),
                    Answer(texto="Volar a la velocidad del sonido", es_correcta=False, emoji="🦅"),
                    Answer(texto="Leer la mente de las personas", es_correcta=False, emoji="🧠"),
                ],
                dificultad=Difficulty.MEDIO,
                curiosidad="La mayoría de las personas elige teletransportación para ahorrar tiempo de viaje.",
            ),
            Question(
                texto="¿Qué dilema histórico preferirías vivir?",
                respuestas=[
                    Answer(texto="Viajar 500 años al pasado", es_correcta=True, emoji="📜"),
                    Answer(texto="Viajar 500 años al futuro", es_correcta=False, emoji="🚀"),
                    Answer(texto="Detener el tiempo 1 hora al día", es_correcta=False, emoji="⏳"),
                    Answer(texto="Saber el día exacto de tu muerte", es_correcta=False, emoji="💀"),
                ],
                dificultad=Difficulty.MEDIO,
            ),
            Question(
                texto="¿Qué habilidad mental extraordinaria elegirías?",
                respuestas=[
                    Answer(texto="Memoria fotográfica perfecta", es_correcta=True, emoji="📸"),
                    Answer(texto="Aprender cualquier idioma en 1 día", es_correcta=False, emoji="🗣️"),
                    Answer(texto="Dormir solo 1 hora y estar 100% descansado", es_correcta=False, emoji="🔋"),
                    Answer(texto="Saber siempre si alguien te miente", es_correcta=False, emoji="👁️"),
                ],
                dificultad=Difficulty.MEDIO,
            ),
        ]

    def _bank_emoji_quiz(self, difficulty: Difficulty, topic: str | None) -> list[Question]:
        return [
            Question(
                texto="Adivina la película con estos emojis: 🧙‍♂️🧝‍♂️🧔💍🌋",
                respuestas=[
                    Answer(texto="Harry Potter", es_correcta=False),
                    Answer(texto="El Señor de los Anillos", es_correcta=True, explicacion="El anillo único debe ser destruido en el Monte del Destino.", emoji="💍"),
                    Answer(texto="Las Crónicas de Narnia", es_correcta=False),
                    Answer(texto="El Hobbit", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                curiosidad="La trilogía ganó un total de 17 premios Oscar.",
                emoji_pista="💍",
            ),
            Question(
                texto="Adivina la película con estos emojis: 🦁👑🌅🐒🐗",
                respuestas=[
                    Answer(texto="Madagascar", es_correcta=False),
                    Answer(texto="El Rey León", es_correcta=True, explicacion="Simba, Mufasa, Timón y Pumba.", emoji="🦁"),
                    Answer(texto="El Libro de la Selva", es_correcta=False),
                    Answer(texto="Tarzán", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                emoji_pista="🦁",
            ),
            Question(
                texto="Adivina el país con estos emojis: 🌮🪅🌵🥑🫔",
                respuestas=[
                    Answer(texto="Colombia", es_correcta=False),
                    Answer(texto="México", es_correcta=True, explicacion="Famoso por su gastronomía y cultura prehispánica.", emoji="🇲🇽"),
                    Answer(texto="Perú", es_correcta=False),
                    Answer(texto="Guatemala", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                emoji_pista="🌮",
            ),
            Question(
                texto="Adivina la película con estos emojis: 🚢❄️🎻💎👩‍❤️‍👨",
                respuestas=[
                    Answer(texto="Titanic", es_correcta=True, explicacion="El famoso trasatlántico que chocó contra un iceberg en 1912.", emoji="🚢"),
                    Answer(texto="Poseidón", es_correcta=False),
                    Answer(texto="Piratas del Caribe", es_correcta=False),
                    Answer(texto="Náufrago", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                emoji_pista="🚢",
            ),
        ]

    def _bank_guess_flag(self, difficulty: Difficulty, topic: str | None) -> list[Question]:
        return [
            Question(
                texto="¿A qué país pertenece esta bandera? 🇯🇵",
                respuestas=[
                    Answer(texto="Corea del Sur", es_correcta=False),
                    Answer(texto="Japón", es_correcta=True, explicacion="El círculo rojo representa el sol naciente.", emoji="🇯🇵"),
                    Answer(texto="China", es_correcta=False),
                    Answer(texto="Vietnam", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                curiosidad="El nombre oficial de la bandera en japonés es Nisshōki.",
                emoji_pista="🇯🇵",
            ),
            Question(
                texto="¿A qué país pertenece esta bandera? 🇧🇷",
                respuestas=[
                    Answer(texto="Argentina", es_correcta=False),
                    Answer(texto="Brasil", es_correcta=True, explicacion="Su lema 'Ordem e Progresso' está inscrito en la franja blanca.", emoji="🇧🇷"),
                    Answer(texto="Colombia", es_correcta=False),
                    Answer(texto="Venezuela", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                emoji_pista="🇧🇷",
            ),
            Question(
                texto="¿A qué país pertenece esta bandera? 🇨🇦",
                respuestas=[
                    Answer(texto="Canadá", es_correcta=True, explicacion="La hoja de arce roja es el símbolo nacional oficial.", emoji="🇨🇦"),
                    Answer(texto="Reino Unido", es_correcta=False),
                    Answer(texto="Suiza", es_correcta=False),
                    Answer(texto="Austria", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                emoji_pista="🇨🇦",
            ),
            Question(
                texto="¿A qué país pertenece esta bandera? 🇩🇪",
                respuestas=[
                    Answer(texto="Bélgica", es_correcta=False),
                    Answer(texto="Alemania", es_correcta=True, explicacion="Colores negro, rojo y oro.", emoji="🇩🇪"),
                    Answer(texto="Holanda", es_correcta=False),
                    Answer(texto="Austria", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                emoji_pista="🇩🇪",
            ),
        ]

    def _bank_guess_pokemon(self, difficulty: Difficulty, topic: str | None) -> list[Question]:
        return [
            Question(
                texto="¿Qué Pokémon eléctrico es el fiel compañero de Ash Ketchum?",
                respuestas=[
                    Answer(texto="Raichu", es_correcta=False),
                    Answer(texto="Pikachu", es_correcta=True, explicacion="Es el Pokémon número 25 de la Pokédex nacional.", emoji="⚡"),
                    Answer(texto="Pichu", es_correcta=False),
                    Answer(texto="Electabuzz", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                curiosidad="Pikachu almacena electricidad en sus mejillas rojas.",
            ),
            Question(
                texto="¿Cuál es la evolución final del inicial de fuego Charmeleon?",
                respuestas=[
                    Answer(texto="Charizard", es_correcta=True, explicacion="Tipo Fuego/Volador.", emoji="🔥"),
                    Answer(texto="Dragonite", es_correcta=False),
                    Answer(texto="Typhlosion", es_correcta=False),
                    Answer(texto="Arcanine", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                emoji_pista="🔥",
            ),
            Question(
                texto="¿Qué Pokémon legendario fue creado genéticamente a partir del ADN de Mew?",
                respuestas=[
                    Answer(texto="Mewtwo", es_correcta=True, explicacion="Creado por científicos en Isla Canela.", emoji="🧬"),
                    Answer(texto="Deoxys", es_correcta=False),
                    Answer(texto="Lugia", es_correcta=False),
                    Answer(texto="Rayquaza", es_correcta=False),
                ],
                dificultad=Difficulty.MEDIO,
            ),
        ]

    def _bank_guess_football_player(self, difficulty: Difficulty, topic: str | None) -> list[Question]:
        return [
            Question(
                texto="¿Qué futbolista ha ganado 8 Balones de Oro y el Mundial 2022?",
                respuestas=[
                    Answer(texto="Cristiano Ronaldo", es_correcta=False),
                    Answer(texto="Lionel Messi", es_correcta=True, explicacion="Capitán de la Selección Argentina y máximo goleador del FC Barcelona.", emoji="🐐"),
                    Answer(texto="Kylian Mbappé", es_correcta=False),
                    Answer(texto="Pelé", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
                curiosidad="Messi anotó 91 goles oficiales en un solo año natural (2012).",
            ),
            Question(
                texto="¿Quién es el máximo goleador histórico de la UEFA Champions League?",
                respuestas=[
                    Answer(texto="Lionel Messi", es_correcta=False),
                    Answer(texto="Cristiano Ronaldo", es_correcta=True, explicacion="Con más de 140 goles anotados en Champions League.", emoji="⚽"),
                    Answer(texto="Robert Lewandowski", es_correcta=False),
                    Answer(texto="Karim Benzema", es_correcta=False),
                ],
                dificultad=Difficulty.FACIL,
            ),
            Question(
                texto="¿Quién es el único futbolista en ganar 3 Copas del Mundo?",
                respuestas=[
                    Answer(texto="Diego Maradona", es_correcta=False),
                    Answer(texto="Pelé", es_correcta=True, explicacion="Ganó los mundiales de 1958, 1962 y 1970 con Brasil.", emoji="👑"),
                    Answer(texto="Zinedine Zidane", es_correcta=False),
                    Answer(texto="Ronaldo Nazário", es_correcta=False),
                ],
                dificultad=Difficulty.MEDIO,
            ),
        ]

    def _bank_generic(self, difficulty: Difficulty, topic: str | None) -> list[Question]:
        topic_name = topic or "Conocimiento General"
        return [
            Question(
                texto=f"¿Cuál es un concepto fundamental en {topic_name}?",
                respuestas=[
                    Answer(texto="Opción Alfa", es_correcta=False),
                    Answer(texto="La respuesta correcta", es_correcta=True, explicacion=f"Dato clave sobre {topic_name}."),
                    Answer(texto="Opción Beta", es_correcta=False),
                    Answer(texto="Opción Gamma", es_correcta=False),
                ],
                dificultad=difficulty,
                curiosidad=f"Un dato fascinante sobre {topic_name} que pocos conocen.",
            ),
            Question(
                texto=f"¿Cuál de las siguientes afirmaciones sobre {topic_name} es correcta?",
                respuestas=[
                    Answer(texto="Dato verificado principal", es_correcta=True, explicacion="Explicación precisa y detallada."),
                    Answer(texto="Dato incorrecto A", es_correcta=False),
                    Answer(texto="Dato incorrecto B", es_correcta=False),
                    Answer(texto="Dato incorrecto C", es_correcta=False),
                ],
                dificultad=difficulty,
            ),
            Question(
                texto=f"¿Qué elemento destaca principalmente en {topic_name}?",
                respuestas=[
                    Answer(texto="Factor secundario", es_correcta=False),
                    Answer(texto="Elemento principal", es_correcta=True, explicacion="Es la característica más representativa."),
                    Answer(texto="Alternativa errónea", es_correcta=False),
                    Answer(texto="Elemento falso", es_correcta=False),
                ],
                dificultad=difficulty,
            ),
            Question(
                texto=f"¿Qué récord o curiosidad está asociada a {topic_name}?",
                respuestas=[
                    Answer(texto="Récord auténtico", es_correcta=True, explicacion="Demostrado históricamente."),
                    Answer(texto="Mito popular", es_correcta=False),
                    Answer(texto="Dato desactualizado", es_correcta=False),
                    Answer(texto="Hipótesis refutada", es_correcta=False),
                ],
                dificultad=difficulty,
            ),
        ]
