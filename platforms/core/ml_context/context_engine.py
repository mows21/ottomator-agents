"""
ML Context Engine
=================

Intelligent context management for LLM agents:
- Dynamic context window optimization
- Relevance-based context selection
- Context compression strategies
- Token budget management
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import hashlib
import json

from platforms.core.logging.structured_logger import StructuredLogger


class ContextStrategy(str, Enum):
    """Strategies for context management."""
    FIFO = "fifo"                    # First in, first out
    LIFO = "lifo"                    # Last in, first out
    RELEVANCE = "relevance"          # Most relevant first
    RECENCY = "recency"              # Most recent with decay
    IMPORTANCE = "importance"        # Importance weighted
    HYBRID = "hybrid"                # Combination of strategies


class ContextType(str, Enum):
    """Types of context items."""
    SYSTEM = "system"                # System prompts
    USER = "user"                    # User messages
    ASSISTANT = "assistant"          # Assistant responses
    TOOL_RESULT = "tool_result"      # Tool execution results
    DOCUMENT = "document"            # RAG documents
    MEMORY = "memory"                # Long-term memory
    INSTRUCTION = "instruction"      # Task instructions


@dataclass
class ContextItem:
    """A single context item with metadata."""
    id: str
    content: str
    context_type: ContextType
    tokens: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    relevance_score: float = 1.0
    importance: float = 1.0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = hashlib.md5(self.content.encode()).hexdigest()[:12]

    @property
    def effective_score(self) -> float:
        """Calculate effective score based on relevance and importance."""
        return self.relevance_score * self.importance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "type": self.context_type.value,
            "tokens": self.tokens,
            "relevance_score": round(self.relevance_score, 3),
            "importance": round(self.importance, 3),
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ContextWindow:
    """
    Represents the current context window state.

    Tracks all context items and provides methods for
    efficient context management.
    """
    max_tokens: int
    items: List[ContextItem] = field(default_factory=list)
    reserved_tokens: int = 0  # Reserved for system prompt, etc.

    @property
    def current_tokens(self) -> int:
        """Get current total tokens."""
        return sum(item.tokens for item in self.items)

    @property
    def available_tokens(self) -> int:
        """Get available tokens."""
        return self.max_tokens - self.current_tokens - self.reserved_tokens

    @property
    def utilization(self) -> float:
        """Get context utilization percentage."""
        return (self.current_tokens / self.max_tokens) * 100 if self.max_tokens > 0 else 0

    def can_fit(self, tokens: int) -> bool:
        """Check if additional tokens can fit."""
        return tokens <= self.available_tokens

    def get_items_by_type(self, context_type: ContextType) -> List[ContextItem]:
        """Get all items of a specific type."""
        return [item for item in self.items if item.context_type == context_type]

    def get_content(self) -> str:
        """Get all context as a single string."""
        return "\n\n".join(item.content for item in self.items)

    def to_messages(self) -> List[Dict[str, str]]:
        """Convert to message format for LLM APIs."""
        messages = []
        for item in self.items:
            role = "system" if item.context_type == ContextType.SYSTEM else \
                   "user" if item.context_type in [ContextType.USER, ContextType.DOCUMENT] else \
                   "assistant"
            messages.append({"role": role, "content": item.content})
        return messages

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "current_tokens": self.current_tokens,
            "available_tokens": self.available_tokens,
            "utilization": round(self.utilization, 2),
            "item_count": len(self.items),
            "items": [item.to_dict() for item in self.items],
        }


class ContextSelector(ABC):
    """Base class for context selection strategies."""

    @abstractmethod
    def select(
        self,
        items: List[ContextItem],
        max_tokens: int,
        query: Optional[str] = None,
    ) -> List[ContextItem]:
        """Select items that fit within the token budget."""
        pass


class FIFOSelector(ContextSelector):
    """First-in-first-out context selection."""

    def select(
        self,
        items: List[ContextItem],
        max_tokens: int,
        query: Optional[str] = None,
    ) -> List[ContextItem]:
        selected = []
        current_tokens = 0

        for item in items:
            if current_tokens + item.tokens <= max_tokens:
                selected.append(item)
                current_tokens += item.tokens

        return selected


class RelevanceSelector(ContextSelector):
    """Relevance-based context selection."""

    def select(
        self,
        items: List[ContextItem],
        max_tokens: int,
        query: Optional[str] = None,
    ) -> List[ContextItem]:
        # Sort by effective score (relevance * importance)
        sorted_items = sorted(items, key=lambda x: x.effective_score, reverse=True)

        selected = []
        current_tokens = 0

        for item in sorted_items:
            if current_tokens + item.tokens <= max_tokens:
                selected.append(item)
                current_tokens += item.tokens

        return selected


class RecencySelector(ContextSelector):
    """Recency-based context selection with decay."""

    def __init__(self, decay_factor: float = 0.95):
        self.decay_factor = decay_factor

    def select(
        self,
        items: List[ContextItem],
        max_tokens: int,
        query: Optional[str] = None,
    ) -> List[ContextItem]:
        now = datetime.now(timezone.utc)

        # Calculate recency scores
        scored_items = []
        for item in items:
            age_seconds = (now - item.created_at).total_seconds()
            recency_score = self.decay_factor ** (age_seconds / 3600)  # Decay per hour
            combined_score = recency_score * item.importance
            scored_items.append((item, combined_score))

        # Sort by combined score
        sorted_items = sorted(scored_items, key=lambda x: x[1], reverse=True)

        selected = []
        current_tokens = 0

        for item, _ in sorted_items:
            if current_tokens + item.tokens <= max_tokens:
                selected.append(item)
                current_tokens += item.tokens

        return selected


class HybridSelector(ContextSelector):
    """Hybrid context selection combining multiple strategies."""

    def __init__(
        self,
        relevance_weight: float = 0.4,
        recency_weight: float = 0.3,
        importance_weight: float = 0.3,
    ):
        self.relevance_weight = relevance_weight
        self.recency_weight = recency_weight
        self.importance_weight = importance_weight

    def select(
        self,
        items: List[ContextItem],
        max_tokens: int,
        query: Optional[str] = None,
    ) -> List[ContextItem]:
        now = datetime.now(timezone.utc)

        # Calculate hybrid scores
        scored_items = []
        for item in items:
            age_seconds = (now - item.created_at).total_seconds()
            recency_score = 0.95 ** (age_seconds / 3600)

            hybrid_score = (
                self.relevance_weight * item.relevance_score +
                self.recency_weight * recency_score +
                self.importance_weight * item.importance
            )
            scored_items.append((item, hybrid_score))

        # Sort by hybrid score
        sorted_items = sorted(scored_items, key=lambda x: x[1], reverse=True)

        selected = []
        current_tokens = 0

        for item, _ in sorted_items:
            if current_tokens + item.tokens <= max_tokens:
                selected.append(item)
                current_tokens += item.tokens

        return selected


class MLContextEngine:
    """
    ML-powered context engine for intelligent context management.

    Features:
    - Dynamic context window optimization
    - Multiple selection strategies
    - Token budget management
    - Relevance scoring with embeddings
    - Context compression

    Example:
        engine = MLContextEngine(max_tokens=8000, strategy=ContextStrategy.HYBRID)

        # Add context items
        engine.add_context("You are a helpful assistant", ContextType.SYSTEM)
        engine.add_context(user_message, ContextType.USER)
        engine.add_context(rag_result, ContextType.DOCUMENT, relevance=0.9)

        # Get optimized context window
        window = engine.optimize(query=user_message)
        messages = window.to_messages()
    """

    def __init__(
        self,
        max_tokens: int = 8000,
        strategy: ContextStrategy = ContextStrategy.HYBRID,
        token_counter: Optional[Callable[[str], int]] = None,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
        logger: Optional[StructuredLogger] = None,
    ):
        self.max_tokens = max_tokens
        self.strategy = strategy
        self._token_counter = token_counter or self._default_token_counter
        self._embedding_fn = embedding_fn
        self.logger = logger or StructuredLogger(name="ml-context-engine")

        # Context storage
        self._items: List[ContextItem] = []
        self._reserved_items: List[ContextItem] = []  # Always included (system prompts)

        # Strategy selectors
        self._selectors: Dict[ContextStrategy, ContextSelector] = {
            ContextStrategy.FIFO: FIFOSelector(),
            ContextStrategy.RELEVANCE: RelevanceSelector(),
            ContextStrategy.RECENCY: RecencySelector(),
            ContextStrategy.HYBRID: HybridSelector(),
        }

    def _default_token_counter(self, text: str) -> int:
        """Default token counter (rough estimate: 4 chars per token)."""
        return len(text) // 4

    def add_context(
        self,
        content: str,
        context_type: ContextType,
        relevance: float = 1.0,
        importance: float = 1.0,
        reserved: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContextItem:
        """
        Add a context item.

        Args:
            content: The context content
            context_type: Type of context
            relevance: Relevance score (0-1)
            importance: Importance score (0-1)
            reserved: If True, always included in context window
            metadata: Additional metadata

        Returns:
            The created ContextItem
        """
        tokens = self._token_counter(content)

        # Generate embedding if function available
        embedding = None
        if self._embedding_fn:
            try:
                embedding = self._embedding_fn(content)
            except Exception as e:
                self.logger.warning(f"Failed to generate embedding: {e}")

        item = ContextItem(
            id="",  # Will be auto-generated
            content=content,
            context_type=context_type,
            tokens=tokens,
            relevance_score=relevance,
            importance=importance,
            embedding=embedding,
            metadata=metadata or {},
        )

        if reserved:
            self._reserved_items.append(item)
        else:
            self._items.append(item)

        self.logger.debug("Added context item", {
            "type": context_type.value,
            "tokens": tokens,
            "relevance": relevance,
            "reserved": reserved,
        })

        return item

    def update_relevance(
        self,
        query: str,
        similarity_fn: Optional[Callable[[List[float], List[float]], float]] = None,
    ) -> None:
        """
        Update relevance scores based on a query.

        Uses embeddings if available, otherwise uses simple text matching.
        """
        if self._embedding_fn and similarity_fn:
            try:
                query_embedding = self._embedding_fn(query)
                for item in self._items:
                    if item.embedding:
                        item.relevance_score = similarity_fn(query_embedding, item.embedding)
            except Exception as e:
                self.logger.warning(f"Failed to update relevance with embeddings: {e}")
        else:
            # Simple keyword matching as fallback
            query_lower = query.lower()
            query_words = set(query_lower.split())

            for item in self._items:
                content_lower = item.content.lower()
                content_words = set(content_lower.split())

                # Calculate Jaccard similarity
                intersection = query_words & content_words
                union = query_words | content_words
                if union:
                    item.relevance_score = len(intersection) / len(union)

    def optimize(
        self,
        query: Optional[str] = None,
        strategy: Optional[ContextStrategy] = None,
    ) -> ContextWindow:
        """
        Optimize the context window for the given query.

        Returns an optimized ContextWindow with selected items.
        """
        strategy = strategy or self.strategy

        # Calculate reserved tokens
        reserved_tokens = sum(item.tokens for item in self._reserved_items)

        # Available tokens for dynamic items
        available_tokens = self.max_tokens - reserved_tokens

        # Update relevance if query provided
        if query:
            self.update_relevance(query)

        # Select items using strategy
        selector = self._selectors.get(strategy, self._selectors[ContextStrategy.HYBRID])
        selected = selector.select(self._items, available_tokens, query)

        # Build context window
        window = ContextWindow(
            max_tokens=self.max_tokens,
            reserved_tokens=reserved_tokens,
        )

        # Add reserved items first
        window.items.extend(self._reserved_items)

        # Add selected items
        window.items.extend(selected)

        self.logger.info("Context optimized", {
            "strategy": strategy.value,
            "total_items": len(self._items),
            "selected_items": len(selected),
            "tokens_used": window.current_tokens,
            "utilization": window.utilization,
        })

        return window

    def compress(
        self,
        compression_ratio: float = 0.5,
        compressor: Optional[Callable[[str], str]] = None,
    ) -> None:
        """
        Compress context items to save tokens.

        Args:
            compression_ratio: Target compression ratio
            compressor: Custom compression function
        """
        if compressor:
            for item in self._items:
                original_content = item.content
                compressed = compressor(original_content)
                item.content = compressed
                item.tokens = self._token_counter(compressed)

                self.logger.debug("Compressed context item", {
                    "original_tokens": self._token_counter(original_content),
                    "compressed_tokens": item.tokens,
                })
        else:
            # Simple truncation-based compression
            for item in self._items:
                target_length = int(len(item.content) * compression_ratio)
                if len(item.content) > target_length:
                    item.content = item.content[:target_length] + "..."
                    item.tokens = self._token_counter(item.content)

    def clear(self, keep_reserved: bool = True) -> None:
        """Clear context items."""
        self._items.clear()
        if not keep_reserved:
            self._reserved_items.clear()

    def remove_oldest(self, count: int = 1) -> List[ContextItem]:
        """Remove oldest items."""
        removed = self._items[:count]
        self._items = self._items[count:]
        return removed

    def get_stats(self) -> Dict[str, Any]:
        """Get context engine statistics."""
        return {
            "max_tokens": self.max_tokens,
            "total_items": len(self._items),
            "reserved_items": len(self._reserved_items),
            "total_tokens": sum(i.tokens for i in self._items + self._reserved_items),
            "strategy": self.strategy.value,
            "items_by_type": {
                ct.value: len([i for i in self._items if i.context_type == ct])
                for ct in ContextType
            },
        }


def create_default_context_engine(
    max_tokens: int = 8000,
    model: str = "gpt-4",
) -> MLContextEngine:
    """
    Create a context engine with default settings.

    Adjusts token limits based on model.
    """
    # Model token limits
    model_limits = {
        "gpt-4": 8192,
        "gpt-4-turbo": 128000,
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "claude-3-opus": 200000,
        "claude-3-sonnet": 200000,
        "claude-3-haiku": 200000,
        "claude-3-5-sonnet": 200000,
        "gemini-1.5-pro": 1000000,
        "gemini-1.5-flash": 1000000,
    }

    # Use 75% of model limit or specified max
    model_max = model_limits.get(model, 8192)
    effective_max = min(max_tokens, int(model_max * 0.75))

    return MLContextEngine(
        max_tokens=effective_max,
        strategy=ContextStrategy.HYBRID,
    )


# Utility functions
def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)
