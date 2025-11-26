"""
Prompt Optimizer
================

ML-powered prompt optimization:
- Prompt effectiveness learning
- A/B testing for prompts
- Automatic prompt improvement
- Performance tracking
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4
import json
import hashlib
import random

from platforms.core.logging.structured_logger import StructuredLogger
from platforms.core.logging.metrics import MetricsCollector


class OptimizationType(str, Enum):
    """Types of prompt optimization."""
    CLARITY = "clarity"           # Improve instruction clarity
    CONCISENESS = "conciseness"   # Reduce token usage
    SPECIFICITY = "specificity"   # Add more specific instructions
    EXAMPLES = "examples"         # Add/improve examples
    FORMATTING = "formatting"     # Improve output formatting
    TONE = "tone"                 # Adjust tone/style
    STRUCTURE = "structure"       # Improve structure


@dataclass
class PromptVariant:
    """A variant of a prompt for A/B testing."""
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    content: str = ""
    optimization_type: Optional[OptimizationType] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Performance metrics
    uses: int = 0
    successes: int = 0
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    feedback_scores: List[float] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return self.successes / self.uses if self.uses > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.uses if self.uses > 0 else 0.0

    @property
    def avg_tokens(self) -> float:
        return self.total_tokens / self.uses if self.uses > 0 else 0.0

    @property
    def avg_feedback(self) -> float:
        return sum(self.feedback_scores) / len(self.feedback_scores) if self.feedback_scores else 0.0

    @property
    def score(self) -> float:
        """Calculate overall performance score."""
        if self.uses < 5:
            return 0.5  # Not enough data

        # Weighted score: success rate (40%), feedback (30%), efficiency (30%)
        success_component = self.success_rate * 0.4
        feedback_component = (self.avg_feedback / 5.0) * 0.3  # Assuming 1-5 scale
        efficiency_component = max(0, 1 - (self.avg_tokens / 1000)) * 0.3  # Lower tokens = better

        return success_component + feedback_component + efficiency_component

    def record_use(
        self,
        success: bool,
        latency_ms: float,
        tokens: int,
        feedback: Optional[float] = None,
    ) -> None:
        """Record a use of this variant."""
        self.uses += 1
        if success:
            self.successes += 1
        self.total_latency_ms += latency_ms
        self.total_tokens += tokens
        if feedback is not None:
            self.feedback_scores.append(feedback)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "optimization_type": self.optimization_type.value if self.optimization_type else None,
            "uses": self.uses,
            "success_rate": round(self.success_rate, 3),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "avg_tokens": round(self.avg_tokens, 1),
            "avg_feedback": round(self.avg_feedback, 2),
            "score": round(self.score, 3),
        }


@dataclass
class OptimizationResult:
    """Result of a prompt optimization."""
    original_prompt: str
    optimized_prompt: str
    optimization_type: OptimizationType
    improvements: List[str] = field(default_factory=list)
    token_change: int = 0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "optimization_type": self.optimization_type.value,
            "improvements": self.improvements,
            "token_change": self.token_change,
            "confidence": round(self.confidence, 3),
            "original_length": len(self.original_prompt),
            "optimized_length": len(self.optimized_prompt),
        }


@dataclass
class PromptExperiment:
    """An A/B testing experiment for prompts."""
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    description: str = ""
    variants: List[PromptVariant] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    winner_id: Optional[str] = None

    def add_variant(self, content: str, optimization_type: Optional[OptimizationType] = None) -> PromptVariant:
        """Add a variant to the experiment."""
        variant = PromptVariant(
            content=content,
            optimization_type=optimization_type,
        )
        self.variants.append(variant)
        return variant

    def select_variant(self, strategy: str = "epsilon_greedy", epsilon: float = 0.1) -> PromptVariant:
        """
        Select a variant for use.

        Strategies:
        - random: Random selection
        - epsilon_greedy: Explore with probability epsilon, exploit otherwise
        - thompson: Thompson sampling
        """
        if not self.variants:
            raise ValueError("No variants in experiment")

        if strategy == "random":
            return random.choice(self.variants)

        elif strategy == "epsilon_greedy":
            if random.random() < epsilon:
                return random.choice(self.variants)
            else:
                return max(self.variants, key=lambda v: v.score)

        elif strategy == "thompson":
            # Thompson sampling with Beta distribution approximation
            scores = []
            for variant in self.variants:
                alpha = variant.successes + 1
                beta = (variant.uses - variant.successes) + 1
                sample = random.betavariate(alpha, beta)
                scores.append((variant, sample))
            return max(scores, key=lambda x: x[1])[0]

        else:
            return self.variants[0]

    def get_winner(self, min_uses: int = 100, significance_threshold: float = 0.1) -> Optional[PromptVariant]:
        """
        Determine the winning variant.

        Returns the winner if statistically significant, None otherwise.
        """
        eligible = [v for v in self.variants if v.uses >= min_uses]
        if len(eligible) < 2:
            return None

        sorted_variants = sorted(eligible, key=lambda v: v.score, reverse=True)
        best = sorted_variants[0]
        second_best = sorted_variants[1]

        # Simple significance check (score difference threshold)
        if best.score - second_best.score >= significance_threshold:
            self.winner_id = best.id
            return best

        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "variant_count": len(self.variants),
            "total_uses": sum(v.uses for v in self.variants),
            "winner_id": self.winner_id,
            "variants": [v.to_dict() for v in self.variants],
        }


class PromptOptimizer:
    """
    ML-powered prompt optimizer for continuous improvement.

    Features:
    - Automatic prompt optimization suggestions
    - A/B testing for prompt variants
    - Performance tracking and learning
    - Multi-armed bandit for variant selection

    Example:
        optimizer = PromptOptimizer()

        # Create an experiment
        exp = optimizer.create_experiment("chat_prompt")
        exp.add_variant("You are a helpful assistant.")
        exp.add_variant("You are an expert assistant. Be concise and accurate.")

        # Select and use a variant
        variant = optimizer.select_for_use("chat_prompt")
        result = await process_with_prompt(variant.content)

        # Record feedback
        optimizer.record_result("chat_prompt", variant.id, success=True, latency_ms=500)
    """

    def __init__(
        self,
        logger: Optional[StructuredLogger] = None,
        metrics: Optional[MetricsCollector] = None,
        selection_strategy: str = "epsilon_greedy",
    ):
        self.logger = logger or StructuredLogger(name="prompt-optimizer")
        self.metrics = metrics or MetricsCollector(name="prompt-optimizer")
        self.selection_strategy = selection_strategy

        self._experiments: Dict[str, PromptExperiment] = {}
        self._prompt_history: Dict[str, List[Tuple[str, float]]] = {}  # prompt_hash -> [(response, score)]

    def create_experiment(
        self,
        name: str,
        description: str = "",
        base_prompt: Optional[str] = None,
    ) -> PromptExperiment:
        """Create a new prompt experiment."""
        experiment = PromptExperiment(
            name=name,
            description=description,
        )

        if base_prompt:
            experiment.add_variant(base_prompt)

        self._experiments[name] = experiment

        self.logger.info("Created prompt experiment", {
            "name": name,
            "has_base_prompt": base_prompt is not None,
        })

        return experiment

    def get_experiment(self, name: str) -> Optional[PromptExperiment]:
        """Get an experiment by name."""
        return self._experiments.get(name)

    def select_for_use(
        self,
        experiment_name: str,
        strategy: Optional[str] = None,
    ) -> PromptVariant:
        """Select a variant for use from an experiment."""
        experiment = self._experiments.get(experiment_name)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_name}")

        strategy = strategy or self.selection_strategy
        variant = experiment.select_variant(strategy)

        self.logger.debug("Selected prompt variant", {
            "experiment": experiment_name,
            "variant_id": variant.id,
            "strategy": strategy,
        })

        return variant

    def record_result(
        self,
        experiment_name: str,
        variant_id: str,
        success: bool,
        latency_ms: float = 0.0,
        tokens: int = 0,
        feedback: Optional[float] = None,
    ) -> None:
        """Record the result of using a variant."""
        experiment = self._experiments.get(experiment_name)
        if not experiment:
            return

        variant = next((v for v in experiment.variants if v.id == variant_id), None)
        if variant:
            variant.record_use(success, latency_ms, tokens, feedback)

            self.metrics.increment(
                "prompt_uses",
                labels={"experiment": experiment_name, "variant": variant_id},
            )
            if success:
                self.metrics.increment(
                    "prompt_successes",
                    labels={"experiment": experiment_name, "variant": variant_id},
                )

            self.logger.debug("Recorded prompt result", {
                "experiment": experiment_name,
                "variant_id": variant_id,
                "success": success,
                "current_score": variant.score,
            })

    def optimize(
        self,
        prompt: str,
        optimization_types: Optional[List[OptimizationType]] = None,
        target_tokens: Optional[int] = None,
    ) -> List[OptimizationResult]:
        """
        Generate optimization suggestions for a prompt.

        This is a rule-based optimizer. For ML-based optimization,
        integrate with an LLM for prompt rewriting.
        """
        results = []
        optimization_types = optimization_types or list(OptimizationType)

        for opt_type in optimization_types:
            result = self._apply_optimization(prompt, opt_type, target_tokens)
            if result:
                results.append(result)

        return results

    def _apply_optimization(
        self,
        prompt: str,
        opt_type: OptimizationType,
        target_tokens: Optional[int],
    ) -> Optional[OptimizationResult]:
        """Apply a specific optimization type."""
        optimized = prompt
        improvements = []
        confidence = 0.5

        if opt_type == OptimizationType.CONCISENESS:
            # Remove redundant whitespace
            import re
            optimized = re.sub(r'\s+', ' ', prompt).strip()

            # Remove filler phrases
            filler_phrases = [
                "please note that",
                "it is important to",
                "keep in mind that",
                "make sure to",
                "be sure to",
            ]
            for phrase in filler_phrases:
                if phrase in optimized.lower():
                    optimized = optimized.replace(phrase, "").replace(phrase.capitalize(), "")
                    improvements.append(f"Removed filler phrase: '{phrase}'")

            if len(optimized) < len(prompt) * 0.9:
                confidence = 0.7

        elif opt_type == OptimizationType.CLARITY:
            # Check for ambiguous terms
            ambiguous_terms = ["it", "this", "that", "they", "them"]
            for term in ambiguous_terms:
                if f" {term} " in prompt.lower():
                    improvements.append(f"Consider replacing ambiguous pronoun: '{term}'")

            # Check for passive voice indicators
            passive_indicators = ["was", "were", "been", "being"]
            for indicator in passive_indicators:
                if f" {indicator} " in prompt.lower():
                    improvements.append("Consider using active voice")
                    break

            confidence = 0.6

        elif opt_type == OptimizationType.STRUCTURE:
            # Check for list structure opportunities
            if prompt.count(",") >= 3 and "\n" not in prompt:
                improvements.append("Consider using bullet points for lists")
                confidence = 0.65

            # Check for section headers
            if len(prompt) > 500 and prompt.count(":") < 2:
                improvements.append("Consider adding section headers for long prompts")

        elif opt_type == OptimizationType.SPECIFICITY:
            # Check for vague instructions
            vague_terms = ["good", "nice", "better", "proper", "appropriate"]
            for term in vague_terms:
                if term in prompt.lower():
                    improvements.append(f"Consider replacing vague term '{term}' with specific criteria")

            confidence = 0.55

        elif opt_type == OptimizationType.EXAMPLES:
            # Check if examples might help
            if "example" not in prompt.lower() and len(prompt) > 200:
                improvements.append("Consider adding examples to clarify expected output")
                confidence = 0.6

        elif opt_type == OptimizationType.FORMATTING:
            # Check output format instructions
            format_keywords = ["json", "markdown", "list", "table", "format"]
            has_format = any(kw in prompt.lower() for kw in format_keywords)
            if not has_format:
                improvements.append("Consider specifying desired output format")
                confidence = 0.5

        if not improvements:
            return None

        return OptimizationResult(
            original_prompt=prompt,
            optimized_prompt=optimized,
            optimization_type=opt_type,
            improvements=improvements,
            token_change=len(prompt) // 4 - len(optimized) // 4,
            confidence=confidence,
        )

    def learn_from_feedback(
        self,
        prompt: str,
        response: str,
        score: float,
    ) -> None:
        """
        Learn from user feedback on prompt effectiveness.

        This data can be used for future ML-based optimization.
        """
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]

        if prompt_hash not in self._prompt_history:
            self._prompt_history[prompt_hash] = []

        self._prompt_history[prompt_hash].append((response[:500], score))

        # Keep only recent history
        if len(self._prompt_history[prompt_hash]) > 100:
            self._prompt_history[prompt_hash] = self._prompt_history[prompt_hash][-100:]

        self.metrics.histogram("prompt_feedback_score", score)

        self.logger.debug("Recorded prompt feedback", {
            "prompt_hash": prompt_hash,
            "score": score,
            "history_size": len(self._prompt_history[prompt_hash]),
        })

    def get_best_practices(self) -> List[str]:
        """Get prompt engineering best practices based on collected data."""
        practices = [
            "Be specific about the task and expected output format",
            "Use clear, unambiguous language",
            "Provide examples when possible",
            "Structure long prompts with sections or bullet points",
            "Specify constraints and requirements upfront",
            "Use active voice for clearer instructions",
            "Include context relevant to the task",
            "Test and iterate on prompts using A/B experiments",
        ]
        return practices

    def get_experiment_stats(self) -> Dict[str, Any]:
        """Get statistics for all experiments."""
        return {
            "total_experiments": len(self._experiments),
            "active_experiments": sum(1 for e in self._experiments.values() if e.is_active),
            "total_variants": sum(len(e.variants) for e in self._experiments.values()),
            "total_uses": sum(
                sum(v.uses for v in e.variants)
                for e in self._experiments.values()
            ),
            "experiments": {
                name: exp.to_dict()
                for name, exp in self._experiments.items()
            },
        }


def create_prompt_optimizer(
    enable_metrics: bool = True,
    enable_logging: bool = True,
) -> PromptOptimizer:
    """Create a prompt optimizer with standard configuration."""
    logger = StructuredLogger(name="prompt-optimizer") if enable_logging else None
    metrics = MetricsCollector(name="prompt-optimizer") if enable_metrics else None

    return PromptOptimizer(
        logger=logger,
        metrics=metrics,
        selection_strategy="epsilon_greedy",
    )
