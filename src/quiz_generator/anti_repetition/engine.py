"""Motor de detección de duplicados basado en embeddings semánticos.

Usa sentence-transformers para generar embeddings y FAISS para
búsquedas eficientes de similitud. Garantiza que nunca se repitan
preguntas, hooks ni estructuras en los quizzes generados.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from quiz_generator.config import Settings
from quiz_generator.core.interfaces import IAntiRepetitionEngine

logger = logging.getLogger(__name__)


class AntiRepetitionEngine(IAntiRepetitionEngine):
    """Motor anti-repetición con embeddings semánticos.

    Características:
    - Genera embeddings con sentence-transformers (all-MiniLM-L6-v2).
    - Almacena vectores en FAISS para búsquedas O(log n).
    - Persiste el índice en disco para memoria entre sesiones.
    - Configurable con umbral de similitud.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._threshold = settings.anti_repeticion.umbral_similitud
        self._store_path = Path(settings.anti_repeticion.ruta_almacen)
        self._store_path.mkdir(parents=True, exist_ok=True)

        self._model = None  # Lazy loading
        self._index = None  # FAISS index
        self._texts: list[str] = []  # Textos almacenados
        self._metadata: list[dict[str, Any]] = []  # Metadata asociada

        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Carga lazy del modelo y el índice persistido."""
        if self._loaded:
            return

        # Importar aquí para evitar carga lenta si no se usa
        from sentence_transformers import SentenceTransformer

        model_name = self._settings.anti_repeticion.modelo_embeddings
        logger.info("Cargando modelo de embeddings: %s", model_name)
        self._model = SentenceTransformer(model_name)

        # Cargar índice existente si hay
        self._load_from_disk()
        self._loaded = True

    def _load_from_disk(self) -> None:
        """Carga el índice FAISS y los textos desde el disco."""
        import faiss

        index_path = self._store_path / "index.faiss"
        texts_path = self._store_path / "texts.json"

        if index_path.exists() and texts_path.exists():
            try:
                self._index = faiss.read_index(str(index_path))
                with open(texts_path, encoding="utf-8") as f:
                    stored = json.load(f)
                self._texts = stored.get("texts", [])
                self._metadata = stored.get("metadata", [])
                logger.info(
                    "Índice anti-repetición cargado: %d entradas", len(self._texts)
                )
            except Exception:
                logger.exception("Error al cargar índice anti-repetición, iniciando vacío")
                self._index = None
                self._texts = []
                self._metadata = []
        else:
            logger.info("Sin índice anti-repetición previo, iniciando vacío")

    def _save_to_disk(self) -> None:
        """Persiste el índice FAISS y los textos al disco."""
        import faiss

        if self._index is None:
            return

        index_path = self._store_path / "index.faiss"
        texts_path = self._store_path / "texts.json"

        faiss.write_index(self._index, str(index_path))
        with open(texts_path, "w", encoding="utf-8") as f:
            json.dump(
                {"texts": self._texts, "metadata": self._metadata},
                f,
                ensure_ascii=False,
                indent=2,
            )
        logger.debug("Índice anti-repetición guardado: %d entradas", len(self._texts))

    def _get_embedding(self, text: str) -> np.ndarray:
        """Genera el embedding de un texto."""
        self._ensure_loaded()
        return self._model.encode([text], normalize_embeddings=True)[0]

    async def is_duplicate(
        self,
        text: str,
        threshold: float | None = None,
    ) -> bool:
        """Verifica si un texto es demasiado similar a uno ya registrado."""
        self._ensure_loaded()
        import faiss

        if self._index is None or self._index.ntotal == 0:
            return False

        effective_threshold = threshold or self._threshold
        embedding = self._get_embedding(text)
        query = np.array([embedding], dtype=np.float32)

        # Buscar el vecino más cercano
        distances, _indices = self._index.search(query, 1)
        similarity = float(distances[0][0])

        is_dup = similarity >= effective_threshold
        if is_dup:
            logger.warning(
                "Duplicado detectado (similitud: %.2f%%): '%s...'",
                similarity * 100, text[:60],
            )

        return is_dup

    async def register(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        """Registra un texto nuevo en el almacén de embeddings."""
        self._ensure_loaded()
        import faiss

        embedding = self._get_embedding(text)

        # Crear índice si no existe
        if self._index is None:
            dimension = len(embedding)
            self._index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine con embeddings normalizados)

        vector = np.array([embedding], dtype=np.float32)
        self._index.add(vector)
        self._texts.append(text)
        self._metadata.append(metadata or {})

        # Persistir cada 10 registros
        if len(self._texts) % 10 == 0:
            self._save_to_disk()

    async def check_batch(
        self,
        texts: list[str],
        threshold: float | None = None,
    ) -> list[bool]:
        """Verifica un lote de textos. Retorna True para cada duplicado."""
        return [await self.is_duplicate(text, threshold) for text in texts]

    async def flush(self) -> None:
        """Fuerza la persistencia del índice actual al disco."""
        self._save_to_disk()

    @property
    def total_entries(self) -> int:
        """Número total de textos registrados."""
        return len(self._texts)
