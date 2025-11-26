"""
Quality Management System (QMS)
===============================

Central quality management system for agent platforms:
- Quality gates with pass/fail criteria
- Automated quality reports
- Continuous monitoring
- Issue tracking and remediation
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4
import json

from platforms.core.logging.structured_logger import StructuredLogger
from platforms.core.logging.metrics import MetricsCollector


class QualityLevel(str, Enum):
    """Quality assessment levels."""
    EXCELLENT = "excellent"  # 95-100%
    GOOD = "good"           # 80-94%
    ACCEPTABLE = "acceptable"  # 60-79%
    POOR = "poor"           # 40-59%
    CRITICAL = "critical"   # 0-39%


class GateStatus(str, Enum):
    """Quality gate status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"


@dataclass
class QualityMetric:
    """A single quality metric."""
    name: str
    value: float
    threshold: float
    unit: str = ""
    passed: bool = True
    message: str = ""

    def __post_init__(self):
        self.passed = self.value >= self.threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "threshold": self.threshold,
            "unit": self.unit,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass
class QualityGate:
    """
    A quality gate with pass/fail criteria.

    Quality gates enforce minimum standards that must be met
    before an agent can be deployed or a response can be sent.
    """
    name: str
    description: str
    metrics: List[QualityMetric] = field(default_factory=list)
    status: GateStatus = GateStatus.PENDING
    blocking: bool = True  # If True, failure blocks the pipeline
    evaluated_at: Optional[datetime] = None

    def evaluate(self) -> GateStatus:
        """Evaluate the gate based on all metrics."""
        if not self.metrics:
            self.status = GateStatus.SKIPPED
        elif all(m.passed for m in self.metrics):
            self.status = GateStatus.PASSED
        else:
            self.status = GateStatus.FAILED
        self.evaluated_at = datetime.now(timezone.utc)
        return self.status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "blocking": self.blocking,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
            "metrics": [m.to_dict() for m in self.metrics],
        }


@dataclass
class QualityIssue:
    """A quality issue detected during evaluation."""
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    severity: str = "medium"  # critical, high, medium, low
    category: str = ""
    title: str = ""
    description: str = ""
    source: str = ""
    remediation: str = ""
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "remediation": self.remediation,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class QualityReport:
    """Comprehensive quality report."""
    report_id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    platform: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    overall_score: float = 0.0
    quality_level: QualityLevel = QualityLevel.POOR
    gates: List[QualityGate] = field(default_factory=list)
    issues: List[QualityIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def calculate_score(self) -> float:
        """Calculate overall quality score from gates."""
        if not self.gates:
            return 0.0

        total_metrics = 0
        passed_metrics = 0

        for gate in self.gates:
            for metric in gate.metrics:
                total_metrics += 1
                if metric.passed:
                    passed_metrics += 1

        if total_metrics == 0:
            return 0.0

        self.overall_score = (passed_metrics / total_metrics) * 100
        self._update_quality_level()
        return self.overall_score

    def _update_quality_level(self) -> None:
        """Update quality level based on score."""
        if self.overall_score >= 95:
            self.quality_level = QualityLevel.EXCELLENT
        elif self.overall_score >= 80:
            self.quality_level = QualityLevel.GOOD
        elif self.overall_score >= 60:
            self.quality_level = QualityLevel.ACCEPTABLE
        elif self.overall_score >= 40:
            self.quality_level = QualityLevel.POOR
        else:
            self.quality_level = QualityLevel.CRITICAL

    def is_passing(self) -> bool:
        """Check if all blocking gates pass."""
        for gate in self.gates:
            if gate.blocking and gate.status == GateStatus.FAILED:
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "agent_id": self.agent_id,
            "platform": self.platform,
            "timestamp": self.timestamp.isoformat(),
            "overall_score": round(self.overall_score, 2),
            "quality_level": self.quality_level.value,
            "is_passing": self.is_passing(),
            "gates": [g.to_dict() for g in self.gates],
            "issues": [i.to_dict() for i in self.issues],
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


class QualityManagementSystem:
    """
    Central Quality Management System for agent platforms.

    Features:
    - Define and enforce quality gates
    - Automated quality evaluation
    - Issue detection and tracking
    - Quality reporting and trends
    - Integration with logging and metrics

    Example:
        qms = QualityManagementSystem(agent_id="my-agent", platform="pydantic_ai")

        # Register quality gates
        qms.register_gate("response_quality", [
            ("accuracy", 0.9, 0.85),
            ("latency_ms", 500, 1000),
        ])

        # Evaluate and get report
        report = qms.evaluate()
        if not report.is_passing():
            print("Quality gate failed!")
    """

    def __init__(
        self,
        agent_id: str,
        platform: str,
        logger: Optional[StructuredLogger] = None,
        metrics: Optional[MetricsCollector] = None,
    ):
        self.agent_id = agent_id
        self.platform = platform
        self.logger = logger or StructuredLogger(name=f"qms-{agent_id}")
        self.metrics = metrics or MetricsCollector(name=f"qms-{agent_id}")

        self._gates: Dict[str, QualityGate] = {}
        self._checks: Dict[str, Callable[[], List[QualityMetric]]] = {}
        self._issues: List[QualityIssue] = []
        self._reports: List[QualityReport] = []

        # Register default gates
        self._register_default_gates()

    def _register_default_gates(self) -> None:
        """Register default quality gates for all agents."""
        # Response quality gate
        self.register_gate(
            "response_quality",
            "Ensures response quality meets minimum standards",
            blocking=True,
        )

        # Performance gate
        self.register_gate(
            "performance",
            "Ensures performance meets latency and throughput requirements",
            blocking=True,
        )

        # Safety gate
        self.register_gate(
            "safety",
            "Ensures outputs meet safety and compliance standards",
            blocking=True,
        )

        # Resource gate
        self.register_gate(
            "resources",
            "Ensures resource usage is within acceptable limits",
            blocking=False,
        )

    def register_gate(
        self,
        name: str,
        description: str,
        blocking: bool = True,
    ) -> QualityGate:
        """Register a new quality gate."""
        gate = QualityGate(
            name=name,
            description=description,
            blocking=blocking,
        )
        self._gates[name] = gate
        self.logger.debug(f"Registered quality gate: {name}", {"blocking": blocking})
        return gate

    def add_metric_to_gate(
        self,
        gate_name: str,
        metric_name: str,
        value: float,
        threshold: float,
        unit: str = "",
        message: str = "",
    ) -> None:
        """Add a metric to an existing gate."""
        if gate_name not in self._gates:
            self.logger.warning(f"Gate not found: {gate_name}")
            return

        metric = QualityMetric(
            name=metric_name,
            value=value,
            threshold=threshold,
            unit=unit,
            message=message,
        )
        self._gates[gate_name].metrics.append(metric)

        # Record in metrics collector
        self.metrics.gauge(f"quality_{gate_name}_{metric_name}", value)

    def register_check(
        self,
        name: str,
        check_fn: Callable[[], List[QualityMetric]],
    ) -> None:
        """
        Register a quality check function.

        The check function should return a list of QualityMetric objects.
        """
        self._checks[name] = check_fn
        self.logger.debug(f"Registered quality check: {name}")

    def add_issue(
        self,
        title: str,
        description: str,
        severity: str = "medium",
        category: str = "general",
        source: str = "",
        remediation: str = "",
    ) -> QualityIssue:
        """Add a quality issue."""
        issue = QualityIssue(
            severity=severity,
            category=category,
            title=title,
            description=description,
            source=source,
            remediation=remediation,
        )
        self._issues.append(issue)

        self.logger.warning(f"Quality issue detected: {title}", {
            "severity": severity,
            "category": category,
        })
        self.metrics.increment("quality_issues_total", labels={"severity": severity})

        return issue

    def evaluate_response(
        self,
        response: str,
        latency_ms: float,
        tokens_used: int,
        model: str,
    ) -> QualityReport:
        """
        Evaluate the quality of an agent response.

        This is a convenience method for common response evaluation.
        """
        # Clear previous metrics
        for gate in self._gates.values():
            gate.metrics.clear()

        # Response quality metrics
        self.add_metric_to_gate(
            "response_quality",
            "response_length",
            len(response),
            10,  # Minimum 10 characters
            unit="chars",
            message="Response too short" if len(response) < 10 else "",
        )

        self.add_metric_to_gate(
            "response_quality",
            "is_not_empty",
            1.0 if response.strip() else 0.0,
            1.0,
            message="Response is empty" if not response.strip() else "",
        )

        # Performance metrics
        self.add_metric_to_gate(
            "performance",
            "latency_ms",
            1000 - latency_ms,  # Invert so higher is better
            0,  # Threshold of 1000ms
            unit="ms",
            message=f"Latency {latency_ms}ms exceeds threshold" if latency_ms > 1000 else "",
        )

        self.add_metric_to_gate(
            "performance",
            "tokens_efficiency",
            10000 - tokens_used,  # Invert so higher is better
            0,  # Threshold of 10000 tokens
            unit="tokens",
            message="Token usage too high" if tokens_used > 10000 else "",
        )

        # Resource metrics
        self.add_metric_to_gate(
            "resources",
            "token_count",
            tokens_used,
            0,  # No minimum
            unit="tokens",
        )

        return self.evaluate()

    def evaluate(self) -> QualityReport:
        """
        Evaluate all quality gates and generate a report.

        Returns a QualityReport with all gate evaluations and issues.
        """
        self.logger.info("Starting quality evaluation")

        # Run all registered checks
        for name, check_fn in self._checks.items():
            try:
                metrics = check_fn()
                # Distribute metrics to appropriate gates
                for metric in metrics:
                    # Find matching gate or add to first gate
                    gate_found = False
                    for gate in self._gates.values():
                        if name.startswith(gate.name):
                            gate.metrics.append(metric)
                            gate_found = True
                            break
                    if not gate_found and self._gates:
                        first_gate = list(self._gates.values())[0]
                        first_gate.metrics.append(metric)
            except Exception as e:
                self.logger.error(f"Quality check failed: {name}", e)
                self.add_issue(
                    title=f"Check failed: {name}",
                    description=str(e),
                    severity="high",
                    category="check_failure",
                )

        # Evaluate all gates
        for gate in self._gates.values():
            gate.evaluate()

        # Generate report
        report = QualityReport(
            agent_id=self.agent_id,
            platform=self.platform,
            gates=list(self._gates.values()),
            issues=self._issues.copy(),
        )
        report.calculate_score()

        # Store report
        self._reports.append(report)
        if len(self._reports) > 100:
            self._reports.pop(0)

        # Record metrics
        self.metrics.gauge("quality_score", report.overall_score)
        self.metrics.increment(
            "quality_evaluations",
            labels={"level": report.quality_level.value, "passing": str(report.is_passing())},
        )

        self.logger.info("Quality evaluation complete", {
            "score": report.overall_score,
            "level": report.quality_level.value,
            "passing": report.is_passing(),
            "issues": len(report.issues),
        })

        return report

    def get_trend(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get quality score trend from recent reports."""
        reports = self._reports[-limit:]
        return [
            {
                "timestamp": r.timestamp.isoformat(),
                "score": r.overall_score,
                "level": r.quality_level.value,
                "passing": r.is_passing(),
            }
            for r in reports
        ]

    def get_issues(
        self,
        severity: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[QualityIssue]:
        """Get filtered list of issues."""
        issues = self._issues
        if severity:
            issues = [i for i in issues if i.severity == severity]
        if category:
            issues = [i for i in issues if i.category == category]
        return issues

    def clear_issues(self) -> None:
        """Clear all tracked issues."""
        self._issues.clear()
        self.logger.debug("Cleared all quality issues")

    def reset_gates(self) -> None:
        """Reset all gate metrics for a new evaluation cycle."""
        for gate in self._gates.values():
            gate.metrics.clear()
            gate.status = GateStatus.PENDING
            gate.evaluated_at = None


# Pre-built quality checks
def create_response_length_check(
    min_length: int = 10,
    max_length: int = 10000,
) -> Callable[[str], List[QualityMetric]]:
    """Create a response length check."""
    def check(response: str) -> List[QualityMetric]:
        length = len(response)
        return [
            QualityMetric(
                name="min_length",
                value=length,
                threshold=min_length,
                unit="chars",
                message=f"Response length {length} below minimum {min_length}",
            ),
            QualityMetric(
                name="max_length",
                value=max_length - length,
                threshold=0,
                unit="chars",
                message=f"Response length {length} exceeds maximum {max_length}",
            ),
        ]
    return check


def create_latency_check(max_latency_ms: float = 1000) -> Callable[[float], List[QualityMetric]]:
    """Create a latency check."""
    def check(latency_ms: float) -> List[QualityMetric]:
        return [
            QualityMetric(
                name="latency",
                value=max_latency_ms - latency_ms,
                threshold=0,
                unit="ms",
                message=f"Latency {latency_ms}ms exceeds threshold {max_latency_ms}ms",
            ),
        ]
    return check


def create_content_safety_check() -> Callable[[str], List[QualityMetric]]:
    """Create a basic content safety check."""
    # Basic unsafe patterns (extend as needed)
    UNSAFE_PATTERNS = [
        "password",
        "api_key",
        "secret",
        "private_key",
    ]

    def check(content: str) -> List[QualityMetric]:
        content_lower = content.lower()
        issues_found = [p for p in UNSAFE_PATTERNS if p in content_lower]
        return [
            QualityMetric(
                name="content_safety",
                value=1.0 if not issues_found else 0.0,
                threshold=1.0,
                message=f"Unsafe patterns detected: {issues_found}" if issues_found else "",
            ),
        ]
    return check
