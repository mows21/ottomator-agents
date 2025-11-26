"""
ML Context Engineering Module
=============================

Machine learning for intelligent prompt context engineering:
- Context optimization and compression
- Prompt effectiveness learning
- Embedding management
- Semantic similarity for context selection
"""

from platforms.core.ml_context.context_engine import MLContextEngine, ContextWindow, ContextStrategy
from platforms.core.ml_context.prompt_optimizer import PromptOptimizer, OptimizationResult
from platforms.core.ml_context.embedding_manager import EmbeddingManager, EmbeddingCache

__all__ = [
    "MLContextEngine",
    "ContextWindow",
    "ContextStrategy",
    "PromptOptimizer",
    "OptimizationResult",
    "EmbeddingManager",
    "EmbeddingCache",
]
