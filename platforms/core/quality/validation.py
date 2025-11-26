"""
Validation Engine
=================

Comprehensive validation for agent inputs and outputs:
- Schema validation with Pydantic
- Custom validation rules
- Sanitization and normalization
- Validation pipelines
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union
from uuid import uuid4

try:
    from pydantic import BaseModel, ValidationError as PydanticValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object
    PydanticValidationError = Exception


T = TypeVar("T")


class ValidationSeverity(str, Enum):
    """Severity level for validation issues."""
    ERROR = "error"      # Blocks processing
    WARNING = "warning"  # Allows processing with notification
    INFO = "info"        # Informational only


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    field: str = ""
    message: str = ""
    severity: ValidationSeverity = ValidationSeverity.ERROR
    rule_name: str = ""
    input_value: Any = None
    sanitized_value: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "rule_name": self.rule_name,
            "input_value": str(self.input_value)[:100] if self.input_value else None,
            "sanitized_value": str(self.sanitized_value)[:100] if self.sanitized_value else None,
            "metadata": self.metadata,
        }


@dataclass
class ValidationReport:
    """Complete validation report for an input/output."""
    report_id: str = field(default_factory=lambda: str(uuid4())[:8])
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_valid: bool = True
    results: List[ValidationResult] = field(default_factory=list)
    errors: List[ValidationResult] = field(default_factory=list)
    warnings: List[ValidationResult] = field(default_factory=list)
    sanitized_data: Any = None

    def add_result(self, result: ValidationResult) -> None:
        """Add a validation result to the report."""
        self.results.append(result)
        if not result.is_valid:
            if result.severity == ValidationSeverity.ERROR:
                self.errors.append(result)
                self.is_valid = False
            elif result.severity == ValidationSeverity.WARNING:
                self.warnings.append(result)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp.isoformat(),
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "results": [r.to_dict() for r in self.results],
        }


class ValidationRule(ABC):
    """Base class for validation rules."""

    def __init__(
        self,
        name: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        message: Optional[str] = None,
    ):
        self.name = name
        self.severity = severity
        self._message = message

    @abstractmethod
    def validate(self, value: Any, field: str = "") -> ValidationResult:
        """Validate a value and return the result."""
        pass

    def _create_result(
        self,
        is_valid: bool,
        value: Any,
        field: str,
        message: str = "",
        sanitized: Any = None,
    ) -> ValidationResult:
        return ValidationResult(
            is_valid=is_valid,
            field=field,
            message=message or self._message or "",
            severity=self.severity,
            rule_name=self.name,
            input_value=value,
            sanitized_value=sanitized,
        )


class RequiredRule(ValidationRule):
    """Validates that a value is not None or empty."""

    def __init__(self, severity: ValidationSeverity = ValidationSeverity.ERROR):
        super().__init__("required", severity, "Value is required")

    def validate(self, value: Any, field: str = "") -> ValidationResult:
        is_valid = value is not None and (not isinstance(value, str) or value.strip())
        return self._create_result(is_valid, value, field)


class TypeRule(ValidationRule):
    """Validates that a value is of a specific type."""

    def __init__(
        self,
        expected_type: type,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ):
        super().__init__("type", severity)
        self.expected_type = expected_type
        self._message = f"Expected type {expected_type.__name__}"

    def validate(self, value: Any, field: str = "") -> ValidationResult:
        is_valid = isinstance(value, self.expected_type)
        return self._create_result(is_valid, value, field)


class LengthRule(ValidationRule):
    """Validates string or list length."""

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ):
        super().__init__("length", severity)
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value: Any, field: str = "") -> ValidationResult:
        if value is None:
            return self._create_result(True, value, field)

        length = len(value) if hasattr(value, "__len__") else 0

        if self.min_length is not None and length < self.min_length:
            return self._create_result(
                False, value, field,
                f"Length {length} is less than minimum {self.min_length}",
            )

        if self.max_length is not None and length > self.max_length:
            # Attempt to sanitize by truncating
            sanitized = value[:self.max_length] if isinstance(value, str) else value
            return self._create_result(
                False, value, field,
                f"Length {length} exceeds maximum {self.max_length}",
                sanitized=sanitized,
            )

        return self._create_result(True, value, field)


class PatternRule(ValidationRule):
    """Validates against a regex pattern."""

    def __init__(
        self,
        pattern: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        message: Optional[str] = None,
    ):
        super().__init__("pattern", severity, message or f"Value must match pattern: {pattern}")
        self.pattern = re.compile(pattern)

    def validate(self, value: Any, field: str = "") -> ValidationResult:
        if not isinstance(value, str):
            return self._create_result(False, value, field, "Value must be a string")

        is_valid = bool(self.pattern.match(value))
        return self._create_result(is_valid, value, field)


class RangeRule(ValidationRule):
    """Validates numeric values are within a range."""

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ):
        super().__init__("range", severity)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: Any, field: str = "") -> ValidationResult:
        if not isinstance(value, (int, float)):
            return self._create_result(False, value, field, "Value must be numeric")

        if self.min_value is not None and value < self.min_value:
            return self._create_result(
                False, value, field,
                f"Value {value} is less than minimum {self.min_value}",
                sanitized=self.min_value,
            )

        if self.max_value is not None and value > self.max_value:
            return self._create_result(
                False, value, field,
                f"Value {value} exceeds maximum {self.max_value}",
                sanitized=self.max_value,
            )

        return self._create_result(True, value, field)


class EnumRule(ValidationRule):
    """Validates value is one of allowed values."""

    def __init__(
        self,
        allowed_values: List[Any],
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ):
        super().__init__("enum", severity)
        self.allowed_values = allowed_values
        self._message = f"Value must be one of: {allowed_values}"

    def validate(self, value: Any, field: str = "") -> ValidationResult:
        is_valid = value in self.allowed_values
        return self._create_result(is_valid, value, field)


class CustomRule(ValidationRule):
    """Custom validation with a callable."""

    def __init__(
        self,
        name: str,
        validator: Callable[[Any], bool],
        sanitizer: Optional[Callable[[Any], Any]] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        message: str = "Custom validation failed",
    ):
        super().__init__(name, severity, message)
        self.validator = validator
        self.sanitizer = sanitizer

    def validate(self, value: Any, field: str = "") -> ValidationResult:
        is_valid = self.validator(value)
        sanitized = self.sanitizer(value) if self.sanitizer and not is_valid else None
        return self._create_result(is_valid, value, field, sanitized=sanitized)


class SanitizationRule(ValidationRule):
    """Always passes but sanitizes the input."""

    def __init__(
        self,
        name: str,
        sanitizer: Callable[[Any], Any],
    ):
        super().__init__(name, ValidationSeverity.INFO)
        self.sanitizer = sanitizer

    def validate(self, value: Any, field: str = "") -> ValidationResult:
        sanitized = self.sanitizer(value)
        return self._create_result(True, value, field, sanitized=sanitized)


class ValidationEngine:
    """
    Comprehensive validation engine for agent inputs and outputs.

    Features:
    - Chain multiple validation rules
    - Support for Pydantic models
    - Automatic sanitization
    - Detailed validation reports

    Example:
        engine = ValidationEngine()

        # Add rules
        engine.add_rule("message", RequiredRule())
        engine.add_rule("message", LengthRule(min_length=1, max_length=10000))

        # Validate
        result = engine.validate({"message": "Hello world"})
        if result.is_valid:
            print("Valid!")
    """

    def __init__(self, auto_sanitize: bool = True):
        self.auto_sanitize = auto_sanitize
        self._rules: Dict[str, List[ValidationRule]] = {}
        self._global_rules: List[ValidationRule] = []

    def add_rule(self, field: str, rule: ValidationRule) -> "ValidationEngine":
        """Add a validation rule for a specific field."""
        if field not in self._rules:
            self._rules[field] = []
        self._rules[field].append(rule)
        return self

    def add_global_rule(self, rule: ValidationRule) -> "ValidationEngine":
        """Add a rule that applies to the entire input."""
        self._global_rules.append(rule)
        return self

    def validate(self, data: Dict[str, Any]) -> ValidationReport:
        """Validate data against all registered rules."""
        report = ValidationReport()
        sanitized_data = data.copy() if self.auto_sanitize else data

        # Apply field-specific rules
        for field, rules in self._rules.items():
            value = data.get(field)

            for rule in rules:
                result = rule.validate(value, field)
                report.add_result(result)

                # Apply sanitization if available
                if self.auto_sanitize and result.sanitized_value is not None:
                    sanitized_data[field] = result.sanitized_value
                    value = result.sanitized_value  # Use sanitized value for subsequent rules

        # Apply global rules
        for rule in self._global_rules:
            result = rule.validate(data, "")
            report.add_result(result)

        if self.auto_sanitize:
            report.sanitized_data = sanitized_data

        return report

    def validate_pydantic(
        self,
        data: Dict[str, Any],
        model: type,
    ) -> ValidationReport:
        """Validate data against a Pydantic model."""
        report = ValidationReport()

        if not PYDANTIC_AVAILABLE:
            report.add_result(ValidationResult(
                is_valid=False,
                message="Pydantic not available for validation",
                severity=ValidationSeverity.ERROR,
            ))
            return report

        try:
            validated = model(**data)
            report.sanitized_data = validated.model_dump() if hasattr(validated, "model_dump") else dict(validated)
            report.add_result(ValidationResult(
                is_valid=True,
                message="Pydantic validation passed",
                rule_name="pydantic",
            ))
        except PydanticValidationError as e:
            for error in e.errors():
                report.add_result(ValidationResult(
                    is_valid=False,
                    field=".".join(str(loc) for loc in error.get("loc", [])),
                    message=error.get("msg", "Validation error"),
                    severity=ValidationSeverity.ERROR,
                    rule_name="pydantic",
                    metadata={"type": error.get("type")},
                ))

        return report

    def create_pipeline(self, name: str) -> "ValidationPipeline":
        """Create a new validation pipeline."""
        return ValidationPipeline(name, self)


class ValidationPipeline:
    """
    A pipeline of validation steps for complex validation flows.

    Example:
        pipeline = engine.create_pipeline("chat_input")
        pipeline.add_step("sanitize", sanitize_fn)
        pipeline.add_step("validate_content", validate_content_fn)
        pipeline.add_step("check_safety", check_safety_fn)

        result = pipeline.execute(input_data)
    """

    def __init__(self, name: str, engine: ValidationEngine):
        self.name = name
        self.engine = engine
        self._steps: List[tuple[str, Callable[[Any], ValidationReport]]] = []

    def add_step(
        self,
        name: str,
        validator: Callable[[Any], ValidationReport],
    ) -> "ValidationPipeline":
        """Add a validation step to the pipeline."""
        self._steps.append((name, validator))
        return self

    def execute(self, data: Any) -> ValidationReport:
        """Execute all validation steps in order."""
        final_report = ValidationReport()
        current_data = data

        for step_name, validator in self._steps:
            try:
                step_report = validator(current_data)

                # Add all results with step prefix
                for result in step_report.results:
                    result.metadata["step"] = step_name
                    final_report.add_result(result)

                # Use sanitized data for next step
                if step_report.sanitized_data is not None:
                    current_data = step_report.sanitized_data

                # Stop on blocking errors
                if not step_report.is_valid:
                    break

            except Exception as e:
                final_report.add_result(ValidationResult(
                    is_valid=False,
                    message=f"Pipeline step '{step_name}' failed: {str(e)}",
                    severity=ValidationSeverity.ERROR,
                    rule_name="pipeline",
                    metadata={"step": step_name, "error": str(e)},
                ))
                break

        final_report.sanitized_data = current_data
        return final_report


# Pre-built validators
def create_message_validator(
    max_length: int = 100000,
    min_length: int = 1,
) -> ValidationEngine:
    """Create a validator for chat messages."""
    engine = ValidationEngine()
    engine.add_rule("message", RequiredRule())
    engine.add_rule("message", TypeRule(str))
    engine.add_rule("message", LengthRule(min_length=min_length, max_length=max_length))
    return engine


def create_session_validator() -> ValidationEngine:
    """Create a validator for session data."""
    engine = ValidationEngine()
    engine.add_rule("session_id", RequiredRule())
    engine.add_rule("session_id", TypeRule(str))
    engine.add_rule("session_id", LengthRule(min_length=1, max_length=100))
    engine.add_rule("user_id", TypeRule(str, severity=ValidationSeverity.WARNING))
    return engine


# Common sanitizers
def strip_whitespace(value: Any) -> Any:
    """Strip whitespace from strings."""
    if isinstance(value, str):
        return value.strip()
    return value


def normalize_newlines(value: Any) -> Any:
    """Normalize newlines to Unix style."""
    if isinstance(value, str):
        return value.replace("\r\n", "\n").replace("\r", "\n")
    return value


def truncate_string(max_length: int) -> Callable[[Any], Any]:
    """Create a truncation sanitizer."""
    def sanitizer(value: Any) -> Any:
        if isinstance(value, str) and len(value) > max_length:
            return value[:max_length] + "..."
        return value
    return sanitizer


def remove_control_chars(value: Any) -> Any:
    """Remove control characters from strings."""
    if isinstance(value, str):
        return "".join(c for c in value if ord(c) >= 32 or c in "\n\t\r")
    return value
