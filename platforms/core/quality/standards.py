"""
Quality Standards
=================

Define and enforce quality standards across agent platforms:
- Predefined compliance levels
- Industry standards (SOC2, GDPR, etc.)
- Custom organizational standards
- Automated compliance checking
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import json


class ComplianceLevel(str, Enum):
    """Compliance levels for quality standards."""
    BASIC = "basic"           # Minimum viable standards
    STANDARD = "standard"     # Industry standard
    ENHANCED = "enhanced"     # Above average
    ENTERPRISE = "enterprise" # Maximum security and compliance
    CUSTOM = "custom"         # Organization-specific


class StandardCategory(str, Enum):
    """Categories of quality standards."""
    SECURITY = "security"
    PRIVACY = "privacy"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    ACCESSIBILITY = "accessibility"
    COMPLIANCE = "compliance"
    OBSERVABILITY = "observability"
    DOCUMENTATION = "documentation"


@dataclass
class StandardRequirement:
    """A single requirement within a standard."""
    id: str
    name: str
    description: str
    category: StandardCategory
    check: Callable[[Any], bool]
    severity: str = "required"  # required, recommended, optional
    remediation: str = ""
    references: List[str] = field(default_factory=list)

    def evaluate(self, context: Any) -> "RequirementResult":
        """Evaluate this requirement against a context."""
        try:
            passed = self.check(context)
            return RequirementResult(
                requirement_id=self.id,
                requirement_name=self.name,
                passed=passed,
                severity=self.severity,
                message="" if passed else f"Requirement not met: {self.name}",
                remediation=self.remediation if not passed else "",
            )
        except Exception as e:
            return RequirementResult(
                requirement_id=self.id,
                requirement_name=self.name,
                passed=False,
                severity=self.severity,
                message=f"Evaluation error: {str(e)}",
                error=str(e),
            )


@dataclass
class RequirementResult:
    """Result of evaluating a single requirement."""
    requirement_id: str
    requirement_name: str
    passed: bool
    severity: str
    message: str = ""
    remediation: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.requirement_id,
            "name": self.requirement_name,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
            "remediation": self.remediation,
            "error": self.error,
        }


@dataclass
class Standard:
    """
    A quality standard with multiple requirements.

    Standards group related requirements and provide
    overall compliance evaluation.
    """
    id: str
    name: str
    description: str
    version: str
    category: StandardCategory
    compliance_level: ComplianceLevel
    requirements: List[StandardRequirement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_requirement(self, requirement: StandardRequirement) -> "Standard":
        """Add a requirement to this standard."""
        self.requirements.append(requirement)
        return self

    def evaluate(self, context: Any) -> "StandardResult":
        """Evaluate all requirements against a context."""
        results = [req.evaluate(context) for req in self.requirements]

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        required_passed = sum(
            1 for r in results
            if r.passed and r.severity == "required"
        )
        required_total = sum(
            1 for r in results
            if r.severity == "required"
        )

        # Standard is compliant if all required requirements pass
        is_compliant = required_passed == required_total

        return StandardResult(
            standard_id=self.id,
            standard_name=self.name,
            version=self.version,
            is_compliant=is_compliant,
            total_requirements=total,
            passed_requirements=passed,
            compliance_percentage=(passed / total * 100) if total > 0 else 0,
            results=results,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category.value,
            "compliance_level": self.compliance_level.value,
            "requirements_count": len(self.requirements),
            "metadata": self.metadata,
        }


@dataclass
class StandardResult:
    """Result of evaluating a complete standard."""
    standard_id: str
    standard_name: str
    version: str
    is_compliant: bool
    total_requirements: int
    passed_requirements: int
    compliance_percentage: float
    results: List[RequirementResult] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_failures(self) -> List[RequirementResult]:
        """Get all failed requirements."""
        return [r for r in self.results if not r.passed]

    def get_required_failures(self) -> List[RequirementResult]:
        """Get failed requirements that are marked as required."""
        return [r for r in self.results if not r.passed and r.severity == "required"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "standard_id": self.standard_id,
            "standard_name": self.standard_name,
            "version": self.version,
            "is_compliant": self.is_compliant,
            "total_requirements": self.total_requirements,
            "passed_requirements": self.passed_requirements,
            "compliance_percentage": round(self.compliance_percentage, 2),
            "failures": [r.to_dict() for r in self.get_failures()],
            "evaluated_at": self.evaluated_at.isoformat(),
        }


class QualityStandards:
    """
    Quality standards manager for agent platforms.

    Features:
    - Predefined industry standards
    - Custom standard creation
    - Batch compliance evaluation
    - Compliance reporting

    Example:
        standards = QualityStandards()

        # Add a custom standard
        standards.add_standard(my_standard)

        # Evaluate compliance
        report = standards.evaluate_all(agent_context)
        if report.is_fully_compliant:
            print("All standards met!")
    """

    def __init__(self):
        self._standards: Dict[str, Standard] = {}
        self._register_default_standards()

    def _register_default_standards(self) -> None:
        """Register default quality standards."""
        # Agent Security Standard
        self.add_standard(self._create_security_standard())

        # Performance Standard
        self.add_standard(self._create_performance_standard())

        # Observability Standard
        self.add_standard(self._create_observability_standard())

        # Data Privacy Standard
        self.add_standard(self._create_privacy_standard())

    def _create_security_standard(self) -> Standard:
        """Create the agent security standard."""
        standard = Standard(
            id="SEC-001",
            name="Agent Security Standard",
            description="Security requirements for AI agents",
            version="1.0.0",
            category=StandardCategory.SECURITY,
            compliance_level=ComplianceLevel.STANDARD,
        )

        standard.add_requirement(StandardRequirement(
            id="SEC-001-01",
            name="Input Sanitization",
            description="All user inputs must be sanitized before processing",
            category=StandardCategory.SECURITY,
            check=lambda ctx: ctx.get("input_sanitization_enabled", False),
            severity="required",
            remediation="Enable input sanitization in the validation engine",
        ))

        standard.add_requirement(StandardRequirement(
            id="SEC-001-02",
            name="Output Validation",
            description="All agent outputs must be validated before delivery",
            category=StandardCategory.SECURITY,
            check=lambda ctx: ctx.get("output_validation_enabled", False),
            severity="required",
            remediation="Enable output validation in the QMS",
        ))

        standard.add_requirement(StandardRequirement(
            id="SEC-001-03",
            name="API Authentication",
            description="API endpoints must require authentication",
            category=StandardCategory.SECURITY,
            check=lambda ctx: ctx.get("api_auth_enabled", False),
            severity="required",
            remediation="Configure API bearer token authentication",
        ))

        standard.add_requirement(StandardRequirement(
            id="SEC-001-04",
            name="Secrets Management",
            description="Secrets should not be exposed in logs or outputs",
            category=StandardCategory.SECURITY,
            check=lambda ctx: ctx.get("secrets_protected", False),
            severity="required",
            remediation="Enable secret filtering in logging",
        ))

        standard.add_requirement(StandardRequirement(
            id="SEC-001-05",
            name="Rate Limiting",
            description="API endpoints should implement rate limiting",
            category=StandardCategory.SECURITY,
            check=lambda ctx: ctx.get("rate_limiting_enabled", False),
            severity="recommended",
            remediation="Configure rate limiting middleware",
        ))

        return standard

    def _create_performance_standard(self) -> Standard:
        """Create the performance standard."""
        standard = Standard(
            id="PERF-001",
            name="Agent Performance Standard",
            description="Performance requirements for AI agents",
            version="1.0.0",
            category=StandardCategory.PERFORMANCE,
            compliance_level=ComplianceLevel.STANDARD,
        )

        standard.add_requirement(StandardRequirement(
            id="PERF-001-01",
            name="Response Latency",
            description="Average response latency should be under 2 seconds",
            category=StandardCategory.PERFORMANCE,
            check=lambda ctx: ctx.get("avg_latency_ms", 5000) < 2000,
            severity="required",
            remediation="Optimize agent processing or use faster models",
        ))

        standard.add_requirement(StandardRequirement(
            id="PERF-001-02",
            name="Token Efficiency",
            description="Token usage should be optimized",
            category=StandardCategory.PERFORMANCE,
            check=lambda ctx: ctx.get("avg_tokens_per_request", 10000) < 5000,
            severity="recommended",
            remediation="Optimize prompts and context management",
        ))

        standard.add_requirement(StandardRequirement(
            id="PERF-001-03",
            name="Error Rate",
            description="Error rate should be below 5%",
            category=StandardCategory.PERFORMANCE,
            check=lambda ctx: ctx.get("error_rate", 10) < 5,
            severity="required",
            remediation="Investigate and fix common error causes",
        ))

        standard.add_requirement(StandardRequirement(
            id="PERF-001-04",
            name="Concurrent Handling",
            description="Agent should handle concurrent requests",
            category=StandardCategory.PERFORMANCE,
            check=lambda ctx: ctx.get("async_enabled", False),
            severity="recommended",
            remediation="Enable async request handling",
        ))

        return standard

    def _create_observability_standard(self) -> Standard:
        """Create the observability standard."""
        standard = Standard(
            id="OBS-001",
            name="Agent Observability Standard",
            description="Observability requirements for AI agents",
            version="1.0.0",
            category=StandardCategory.OBSERVABILITY,
            compliance_level=ComplianceLevel.STANDARD,
        )

        standard.add_requirement(StandardRequirement(
            id="OBS-001-01",
            name="Structured Logging",
            description="Agent must use structured logging",
            category=StandardCategory.OBSERVABILITY,
            check=lambda ctx: ctx.get("structured_logging_enabled", False),
            severity="required",
            remediation="Initialize StructuredLogger for the agent",
        ))

        standard.add_requirement(StandardRequirement(
            id="OBS-001-02",
            name="Trace Propagation",
            description="Request traces should be propagated",
            category=StandardCategory.OBSERVABILITY,
            check=lambda ctx: ctx.get("trace_propagation_enabled", False),
            severity="required",
            remediation="Enable trace context propagation",
        ))

        standard.add_requirement(StandardRequirement(
            id="OBS-001-03",
            name="Metrics Collection",
            description="Agent metrics should be collected",
            category=StandardCategory.OBSERVABILITY,
            check=lambda ctx: ctx.get("metrics_enabled", False),
            severity="required",
            remediation="Initialize MetricsCollector for the agent",
        ))

        standard.add_requirement(StandardRequirement(
            id="OBS-001-04",
            name="LLM Observability",
            description="LLM calls should be traced with Langfuse",
            category=StandardCategory.OBSERVABILITY,
            check=lambda ctx: ctx.get("langfuse_enabled", False),
            severity="recommended",
            remediation="Configure Langfuse integration",
        ))

        standard.add_requirement(StandardRequirement(
            id="OBS-001-05",
            name="Error Tracking",
            description="Errors should be tracked and reported",
            category=StandardCategory.OBSERVABILITY,
            check=lambda ctx: ctx.get("error_tracking_enabled", False),
            severity="required",
            remediation="Enable error tracking in logging",
        ))

        return standard

    def _create_privacy_standard(self) -> Standard:
        """Create the data privacy standard."""
        standard = Standard(
            id="PRIV-001",
            name="Data Privacy Standard",
            description="Data privacy requirements for AI agents",
            version="1.0.0",
            category=StandardCategory.PRIVACY,
            compliance_level=ComplianceLevel.STANDARD,
        )

        standard.add_requirement(StandardRequirement(
            id="PRIV-001-01",
            name="PII Protection",
            description="Personally identifiable information must be protected",
            category=StandardCategory.PRIVACY,
            check=lambda ctx: ctx.get("pii_protection_enabled", False),
            severity="required",
            remediation="Enable PII detection and masking",
        ))

        standard.add_requirement(StandardRequirement(
            id="PRIV-001-02",
            name="Data Retention",
            description="Data retention policies must be enforced",
            category=StandardCategory.PRIVACY,
            check=lambda ctx: ctx.get("data_retention_policy", False),
            severity="required",
            remediation="Configure data retention policies",
        ))

        standard.add_requirement(StandardRequirement(
            id="PRIV-001-03",
            name="Consent Management",
            description="User consent should be tracked",
            category=StandardCategory.PRIVACY,
            check=lambda ctx: ctx.get("consent_management_enabled", False),
            severity="recommended",
            remediation="Implement consent management",
        ))

        return standard

    def add_standard(self, standard: Standard) -> None:
        """Add a standard to the manager."""
        self._standards[standard.id] = standard

    def get_standard(self, standard_id: str) -> Optional[Standard]:
        """Get a standard by ID."""
        return self._standards.get(standard_id)

    def list_standards(
        self,
        category: Optional[StandardCategory] = None,
        level: Optional[ComplianceLevel] = None,
    ) -> List[Standard]:
        """List all standards, optionally filtered."""
        standards = list(self._standards.values())
        if category:
            standards = [s for s in standards if s.category == category]
        if level:
            standards = [s for s in standards if s.compliance_level == level]
        return standards

    def evaluate(self, standard_id: str, context: Dict[str, Any]) -> Optional[StandardResult]:
        """Evaluate a specific standard."""
        standard = self.get_standard(standard_id)
        if standard:
            return standard.evaluate(context)
        return None

    def evaluate_all(self, context: Dict[str, Any]) -> "ComplianceReport":
        """Evaluate all standards and generate a report."""
        results = []
        for standard in self._standards.values():
            result = standard.evaluate(context)
            results.append(result)

        return ComplianceReport(results=results)


@dataclass
class ComplianceReport:
    """Complete compliance report across all standards."""
    results: List[StandardResult] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_fully_compliant(self) -> bool:
        """Check if all standards are met."""
        return all(r.is_compliant for r in self.results)

    @property
    def total_standards(self) -> int:
        return len(self.results)

    @property
    def compliant_standards(self) -> int:
        return sum(1 for r in self.results if r.is_compliant)

    @property
    def overall_compliance_percentage(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.compliance_percentage for r in self.results) / len(self.results)

    def get_non_compliant(self) -> List[StandardResult]:
        """Get all non-compliant standards."""
        return [r for r in self.results if not r.is_compliant]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_fully_compliant": self.is_fully_compliant,
            "total_standards": self.total_standards,
            "compliant_standards": self.compliant_standards,
            "overall_compliance_percentage": round(self.overall_compliance_percentage, 2),
            "generated_at": self.generated_at.isoformat(),
            "standards": [r.to_dict() for r in self.results],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# Factory functions for common standard configurations
def create_basic_standards() -> QualityStandards:
    """Create quality standards with basic level requirements only."""
    standards = QualityStandards()
    # Filter to basic level only (default standards are already basic-compatible)
    return standards


def create_enterprise_standards() -> QualityStandards:
    """Create quality standards with enterprise level requirements."""
    standards = QualityStandards()

    # Add additional enterprise requirements
    enterprise_security = Standard(
        id="SEC-ENT-001",
        name="Enterprise Security Standard",
        description="Additional enterprise security requirements",
        version="1.0.0",
        category=StandardCategory.SECURITY,
        compliance_level=ComplianceLevel.ENTERPRISE,
    )

    enterprise_security.add_requirement(StandardRequirement(
        id="SEC-ENT-001-01",
        name="Audit Logging",
        description="All actions must be audit logged",
        category=StandardCategory.SECURITY,
        check=lambda ctx: ctx.get("audit_logging_enabled", False),
        severity="required",
        remediation="Enable comprehensive audit logging",
    ))

    enterprise_security.add_requirement(StandardRequirement(
        id="SEC-ENT-001-02",
        name="Encryption at Rest",
        description="Sensitive data must be encrypted at rest",
        category=StandardCategory.SECURITY,
        check=lambda ctx: ctx.get("encryption_at_rest", False),
        severity="required",
        remediation="Configure encryption for stored data",
    ))

    enterprise_security.add_requirement(StandardRequirement(
        id="SEC-ENT-001-03",
        name="Multi-Factor Authentication",
        description="MFA should be available for admin access",
        category=StandardCategory.SECURITY,
        check=lambda ctx: ctx.get("mfa_enabled", False),
        severity="required",
        remediation="Enable MFA for administrative access",
    ))

    standards.add_standard(enterprise_security)
    return standards
