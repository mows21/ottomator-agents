"""
Embedding Manager
=================

Centralized embedding management for ML context:
- Multi-provider embedding support
- Embedding caching
- Batch processing
- Similarity search
"""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from threading import Lock
import os

from platforms.core.logging.structured_logger import StructuredLogger
from platforms.core.logging.metrics import MetricsCollector


@dataclass
class EmbeddingResult:
    """Result of an embedding operation."""
    text: str
    embedding: List[float]
    model: str
    dimensions: int
    tokens_used: int = 0
    cached: bool = False
    latency_ms: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text[:50] + "..." if len(self.text) > 50 else self.text,
            "model": self.model,
            "dimensions": self.dimensions,
            "tokens_used": self.tokens_used,
            "cached": self.cached,
            "latency_ms": round(self.latency_ms, 2),
        }


class EmbeddingCache:
    """
    LRU cache for embeddings with TTL support.

    Features:
    - Thread-safe caching
    - TTL-based expiration
    - LRU eviction
    - Memory-efficient storage
    """

    def __init__(
        self,
        max_size: int = 10000,
        ttl_seconds: int = 3600,
    ):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[List[float], datetime]] = {}
        self._access_order: List[str] = []
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def _compute_key(self, text: str, model: str) -> str:
        """Compute cache key from text and model."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, text: str, model: str) -> Optional[List[float]]:
        """Get embedding from cache."""
        key = self._compute_key(text, model)

        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            embedding, created_at = self._cache[key]

            # Check TTL
            if datetime.now(timezone.utc) - created_at > timedelta(seconds=self.ttl_seconds):
                del self._cache[key]
                self._access_order.remove(key)
                self._misses += 1
                return None

            # Update access order (LRU)
            self._access_order.remove(key)
            self._access_order.append(key)
            self._hits += 1

            return embedding

    def set(self, text: str, model: str, embedding: List[float]) -> None:
        """Store embedding in cache."""
        key = self._compute_key(text, model)

        with self._lock:
            # Evict oldest if at capacity
            while len(self._cache) >= self.max_size:
                oldest_key = self._access_order.pop(0)
                del self._cache[oldest_key]

            self._cache[key] = (embedding, datetime.now(timezone.utc))
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()

    @property
    def hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self.hit_rate, 3),
            "ttl_seconds": self.ttl_seconds,
        }


class EmbeddingProvider(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    def embed(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for a list of texts."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the model name."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def dimensions(self) -> int:
        return self._dimensions.get(self.model, 1536)

    def embed(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings using OpenAI API."""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)

            start_time = time.perf_counter()
            response = client.embeddings.create(
                model=self.model,
                input=texts,
            )
            latency_ms = (time.perf_counter() - start_time) * 1000

            results = []
            for i, embedding_data in enumerate(response.data):
                results.append(EmbeddingResult(
                    text=texts[i],
                    embedding=embedding_data.embedding,
                    model=self.model,
                    dimensions=len(embedding_data.embedding),
                    tokens_used=response.usage.total_tokens // len(texts),
                    latency_ms=latency_ms / len(texts),
                ))

            return results

        except ImportError:
            raise ImportError("openai package required for OpenAI embeddings")


class VoyageEmbeddingProvider(EmbeddingProvider):
    """Voyage AI embedding provider (Claude-recommended)."""

    def __init__(
        self,
        model: str = "voyage-3",
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        self._dimensions = {
            "voyage-3": 1024,
            "voyage-3-lite": 512,
            "voyage-code-3": 1024,
        }

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def dimensions(self) -> int:
        return self._dimensions.get(self.model, 1024)

    def embed(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings using Voyage API."""
        try:
            import voyageai
            client = voyageai.Client(api_key=self.api_key)

            start_time = time.perf_counter()
            result = client.embed(texts, model=self.model)
            latency_ms = (time.perf_counter() - start_time) * 1000

            results = []
            for i, embedding in enumerate(result.embeddings):
                results.append(EmbeddingResult(
                    text=texts[i],
                    embedding=embedding,
                    model=self.model,
                    dimensions=len(embedding),
                    tokens_used=result.total_tokens // len(texts) if hasattr(result, 'total_tokens') else 0,
                    latency_ms=latency_ms / len(texts),
                ))

            return results

        except ImportError:
            raise ImportError("voyageai package required for Voyage embeddings")


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers."""

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        self.model = model
        self._model_instance = None
        self._model_dimensions = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "paraphrase-MiniLM-L6-v2": 384,
        }

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def dimensions(self) -> int:
        return self._model_dimensions.get(self.model, 384)

    def _get_model(self):
        """Lazy load the model."""
        if self._model_instance is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model_instance = SentenceTransformer(self.model)
            except ImportError:
                raise ImportError("sentence-transformers package required for local embeddings")
        return self._model_instance

    def embed(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings locally."""
        model = self._get_model()

        start_time = time.perf_counter()
        embeddings = model.encode(texts, convert_to_numpy=True)
        latency_ms = (time.perf_counter() - start_time) * 1000

        results = []
        for i, embedding in enumerate(embeddings):
            results.append(EmbeddingResult(
                text=texts[i],
                embedding=embedding.tolist(),
                model=self.model,
                dimensions=len(embedding),
                tokens_used=0,
                latency_ms=latency_ms / len(texts),
            ))

        return results


class EmbeddingManager:
    """
    Centralized embedding manager with multi-provider support.

    Features:
    - Multiple embedding providers
    - Automatic caching
    - Batch processing
    - Similarity search
    - Provider fallback

    Example:
        manager = EmbeddingManager(provider="openai")

        # Generate embeddings
        results = manager.embed(["Hello world", "How are you?"])

        # Search for similar texts
        query = "Hi there"
        similar = manager.search(query, corpus, top_k=5)
    """

    def __init__(
        self,
        provider: str = "openai",
        cache_size: int = 10000,
        cache_ttl: int = 3600,
        logger: Optional[StructuredLogger] = None,
        metrics: Optional[MetricsCollector] = None,
        fallback_providers: Optional[List[str]] = None,
    ):
        self.logger = logger or StructuredLogger(name="embedding-manager")
        self.metrics = metrics or MetricsCollector(name="embedding-manager")
        self.cache = EmbeddingCache(max_size=cache_size, ttl_seconds=cache_ttl)

        # Initialize providers
        self._providers: Dict[str, EmbeddingProvider] = {}
        self._primary_provider = provider
        self._fallback_providers = fallback_providers or []

        self._register_provider(provider)
        for fallback in self._fallback_providers:
            self._register_provider(fallback)

    def _register_provider(self, name: str) -> None:
        """Register an embedding provider."""
        if name in self._providers:
            return

        provider_map = {
            "openai": lambda: OpenAIEmbeddingProvider(),
            "openai-large": lambda: OpenAIEmbeddingProvider(model="text-embedding-3-large"),
            "voyage": lambda: VoyageEmbeddingProvider(),
            "voyage-lite": lambda: VoyageEmbeddingProvider(model="voyage-3-lite"),
            "voyage-code": lambda: VoyageEmbeddingProvider(model="voyage-code-3"),
            "local": lambda: LocalEmbeddingProvider(),
            "local-mpnet": lambda: LocalEmbeddingProvider(model="all-mpnet-base-v2"),
        }

        if name in provider_map:
            try:
                self._providers[name] = provider_map[name]()
                self.logger.info(f"Registered embedding provider: {name}")
            except Exception as e:
                self.logger.warning(f"Failed to register provider {name}: {e}")

    @property
    def provider(self) -> EmbeddingProvider:
        """Get the primary provider."""
        return self._providers.get(self._primary_provider)

    def embed(
        self,
        texts: List[str],
        use_cache: bool = True,
        batch_size: int = 100,
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed
            use_cache: Whether to use caching
            batch_size: Batch size for processing

        Returns:
            List of EmbeddingResult objects
        """
        if not texts:
            return []

        results = []
        uncached_texts = []
        uncached_indices = []

        # Check cache first
        if use_cache:
            for i, text in enumerate(texts):
                cached = self.cache.get(text, self.provider.model_name)
                if cached:
                    results.append(EmbeddingResult(
                        text=text,
                        embedding=cached,
                        model=self.provider.model_name,
                        dimensions=len(cached),
                        cached=True,
                    ))
                    self.metrics.increment("embedding_cache_hits")
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
                    self.metrics.increment("embedding_cache_misses")
        else:
            uncached_texts = texts
            uncached_indices = list(range(len(texts)))

        # Generate embeddings for uncached texts
        if uncached_texts:
            new_results = self._embed_with_fallback(uncached_texts, batch_size)

            # Cache new embeddings
            if use_cache:
                for result in new_results:
                    self.cache.set(result.text, result.model, result.embedding)

            # Insert results at correct positions
            result_iter = iter(new_results)
            final_results = []
            cached_iter = iter(results)

            for i in range(len(texts)):
                if i in uncached_indices:
                    final_results.append(next(result_iter))
                else:
                    final_results.append(next(cached_iter))

            results = final_results

        self.logger.debug("Generated embeddings", {
            "total": len(texts),
            "cached": len(texts) - len(uncached_texts),
            "generated": len(uncached_texts),
        })

        return results

    def _embed_with_fallback(
        self,
        texts: List[str],
        batch_size: int,
    ) -> List[EmbeddingResult]:
        """Embed texts with fallback to other providers on failure."""
        providers_to_try = [self._primary_provider] + self._fallback_providers

        for provider_name in providers_to_try:
            if provider_name not in self._providers:
                continue

            provider = self._providers[provider_name]

            try:
                results = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    batch_results = provider.embed(batch)
                    results.extend(batch_results)

                self.metrics.increment(
                    "embeddings_generated",
                    len(texts),
                    labels={"provider": provider_name},
                )

                return results

            except Exception as e:
                self.logger.warning(f"Embedding failed with {provider_name}: {e}")
                self.metrics.increment(
                    "embedding_errors",
                    labels={"provider": provider_name},
                )
                continue

        raise RuntimeError("All embedding providers failed")

    def embed_single(self, text: str, use_cache: bool = True) -> EmbeddingResult:
        """Embed a single text."""
        results = self.embed([text], use_cache=use_cache)
        return results[0] if results else None

    def similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        if len(embedding1) != len(embedding2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def search(
        self,
        query: str,
        corpus: List[str],
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[Tuple[str, float]]:
        """
        Search for similar texts in a corpus.

        Args:
            query: Query text
            corpus: List of texts to search
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of (text, similarity) tuples
        """
        if not corpus:
            return []

        # Get embeddings
        query_result = self.embed_single(query)
        corpus_results = self.embed(corpus)

        # Calculate similarities
        similarities = []
        for i, corpus_result in enumerate(corpus_results):
            sim = self.similarity(query_result.embedding, corpus_result.embedding)
            if sim >= threshold:
                similarities.append((corpus[i], sim))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            "primary_provider": self._primary_provider,
            "fallback_providers": self._fallback_providers,
            "registered_providers": list(self._providers.keys()),
            "cache": self.cache.get_stats(),
        }


def create_embedding_manager(
    provider: str = "openai",
    enable_cache: bool = True,
    cache_size: int = 10000,
) -> EmbeddingManager:
    """Create an embedding manager with standard configuration."""
    return EmbeddingManager(
        provider=provider,
        cache_size=cache_size if enable_cache else 0,
        fallback_providers=["local"] if provider != "local" else [],
    )
