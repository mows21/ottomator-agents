"""
Metrics Collector
=================

Comprehensive metrics collection for agent monitoring:
- Request/response metrics
- Latency histograms
- Token usage statistics
- Error rates and types
- Custom business metrics
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from threading import Lock
import statistics
import json


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "labels": self.labels,
        }


@dataclass
class MetricSummary:
    """Statistical summary of metrics."""
    count: int = 0
    sum: float = 0.0
    min: float = float("inf")
    max: float = float("-inf")
    mean: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    values: List[float] = field(default_factory=list)

    def add(self, value: float) -> None:
        """Add a value to the summary."""
        self.count += 1
        self.sum += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        self.values.append(value)

        # Recalculate statistics
        self.mean = self.sum / self.count
        if len(self.values) > 1:
            sorted_values = sorted(self.values)
            self.p50 = self._percentile(sorted_values, 50)
            self.p95 = self._percentile(sorted_values, 95)
            self.p99 = self._percentile(sorted_values, 99)

    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile."""
        if not sorted_values:
            return 0.0
        idx = int(len(sorted_values) * percentile / 100)
        idx = min(idx, len(sorted_values) - 1)
        return sorted_values[idx]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "sum": self.sum,
            "min": self.min if self.min != float("inf") else 0.0,
            "max": self.max if self.max != float("-inf") else 0.0,
            "mean": round(self.mean, 4),
            "p50": round(self.p50, 4),
            "p95": round(self.p95, 4),
            "p99": round(self.p99, 4),
        }


class MetricsCollector:
    """
    Comprehensive metrics collection and aggregation.

    Features:
    - Counter metrics (monotonically increasing)
    - Gauge metrics (point-in-time values)
    - Histogram metrics (distribution analysis)
    - Timer metrics (latency tracking)
    - Label support for dimensional metrics
    - Periodic export capability

    Example:
        metrics = MetricsCollector(name="my-agent")

        # Count requests
        metrics.increment("requests_total", labels={"method": "chat"})

        # Record latency
        with metrics.timer("request_duration"):
            result = await process_request()

        # Track token usage
        metrics.histogram("tokens_used", 1500, labels={"model": "gpt-4"})

        # Get summary
        summary = metrics.get_summary()
    """

    def __init__(
        self,
        name: str,
        max_values_per_metric: int = 10000,
        export_handlers: Optional[List[Callable[[Dict[str, Any]], None]]] = None,
    ):
        self.name = name
        self.max_values = max_values_per_metric
        self._lock = Lock()

        # Metric storage
        self._counters: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._gauges: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._histograms: Dict[str, Dict[str, MetricSummary]] = defaultdict(
            lambda: defaultdict(MetricSummary)
        )
        self._timers: Dict[str, Dict[str, MetricSummary]] = defaultdict(
            lambda: defaultdict(MetricSummary)
        )

        # Time series data
        self._time_series: Dict[str, List[MetricPoint]] = defaultdict(list)

        # Export handlers
        self._export_handlers = export_handlers or []

        # Start time for uptime tracking
        self._start_time = datetime.now(timezone.utc)

    def _labels_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Convert labels to a hashable key."""
        if not labels:
            return ""
        return json.dumps(labels, sort_keys=True)

    def _add_time_series(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Add a point to time series data."""
        point = MetricPoint(
            timestamp=datetime.now(timezone.utc),
            value=value,
            labels=labels or {},
        )
        self._time_series[name].append(point)

        # Trim if too many values
        if len(self._time_series[name]) > self.max_values:
            self._time_series[name] = self._time_series[name][-self.max_values:]

    # Counter metrics
    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a counter metric."""
        with self._lock:
            key = self._labels_key(labels)
            self._counters[name][key] += value
            self._add_time_series(f"counter:{name}", self._counters[name][key], labels)

    def get_counter(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> float:
        """Get current counter value."""
        key = self._labels_key(labels)
        return self._counters[name][key]

    # Gauge metrics
    def gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set a gauge metric."""
        with self._lock:
            key = self._labels_key(labels)
            self._gauges[name][key] = value
            self._add_time_series(f"gauge:{name}", value, labels)

    def get_gauge(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> float:
        """Get current gauge value."""
        key = self._labels_key(labels)
        return self._gauges[name][key]

    # Histogram metrics
    def histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a histogram value."""
        with self._lock:
            key = self._labels_key(labels)
            self._histograms[name][key].add(value)
            self._add_time_series(f"histogram:{name}", value, labels)

    def get_histogram(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> MetricSummary:
        """Get histogram summary."""
        key = self._labels_key(labels)
        return self._histograms[name][key]

    # Timer metrics
    def timer(self, name: str, labels: Optional[Dict[str, str]] = None):
        """
        Context manager for timing operations.

        Example:
            with metrics.timer("request_latency"):
                result = await process()
        """
        return TimerContext(self, name, labels)

    def record_timer(
        self,
        name: str,
        duration_ms: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Manually record a timer value."""
        with self._lock:
            key = self._labels_key(labels)
            self._timers[name][key].add(duration_ms)
            self._add_time_series(f"timer:{name}", duration_ms, labels)

    # Common agent metrics
    def record_request(
        self,
        platform: str,
        agent_id: str,
        success: bool = True,
        latency_ms: float = 0.0,
    ) -> None:
        """Record a request with common labels."""
        labels = {"platform": platform, "agent_id": agent_id}
        self.increment("requests_total", labels=labels)
        if success:
            self.increment("requests_success", labels=labels)
        else:
            self.increment("requests_failed", labels=labels)
        if latency_ms > 0:
            self.histogram("request_latency_ms", latency_ms, labels=labels)

    def record_tokens(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float = 0.0,
    ) -> None:
        """Record token usage."""
        labels = {"model": model}
        self.increment("tokens_prompt", prompt_tokens, labels=labels)
        self.increment("tokens_completion", completion_tokens, labels=labels)
        self.increment("tokens_total", prompt_tokens + completion_tokens, labels=labels)
        if cost_usd > 0:
            self.increment("cost_usd", cost_usd, labels=labels)

    def record_tool_call(
        self,
        tool_name: str,
        success: bool = True,
        latency_ms: float = 0.0,
    ) -> None:
        """Record a tool call."""
        labels = {"tool": tool_name}
        self.increment("tool_calls_total", labels=labels)
        if success:
            self.increment("tool_calls_success", labels=labels)
        else:
            self.increment("tool_calls_failed", labels=labels)
        if latency_ms > 0:
            self.histogram("tool_latency_ms", latency_ms, labels=labels)

    def record_error(
        self,
        error_type: str,
        platform: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> None:
        """Record an error."""
        labels = {"error_type": error_type}
        if platform:
            labels["platform"] = platform
        if agent_id:
            labels["agent_id"] = agent_id
        self.increment("errors_total", labels=labels)

    # Summary and export
    def get_summary(self) -> Dict[str, Any]:
        """Get a complete metrics summary."""
        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

        summary = {
            "collector": self.name,
            "uptime_seconds": uptime,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "counters": {},
            "gauges": {},
            "histograms": {},
            "timers": {},
        }

        # Aggregate counters
        for name, values in self._counters.items():
            summary["counters"][name] = dict(values)

        # Aggregate gauges
        for name, values in self._gauges.items():
            summary["gauges"][name] = dict(values)

        # Aggregate histograms
        for name, values in self._histograms.items():
            summary["histograms"][name] = {
                key: val.to_dict() for key, val in values.items()
            }

        # Aggregate timers
        for name, values in self._timers.items():
            summary["timers"][name] = {
                key: val.to_dict() for key, val in values.items()
            }

        return summary

    def get_time_series(
        self,
        name: str,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get time series data for a metric."""
        points = self._time_series.get(name, [])
        if since:
            points = [p for p in points if p.timestamp >= since]
        return [p.to_dict() for p in points[-limit:]]

    def export(self) -> None:
        """Export metrics to all registered handlers."""
        summary = self.get_summary()
        for handler in self._export_handlers:
            try:
                handler(summary)
            except Exception as e:
                print(f"Metrics export handler error: {e}")

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
            self._time_series.clear()
            self._start_time = datetime.now(timezone.utc)

    def add_export_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Add a metrics export handler."""
        self._export_handlers.append(handler)


class TimerContext:
    """Context manager for timing operations."""

    def __init__(
        self,
        collector: MetricsCollector,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.collector = collector
        self.name = name
        self.labels = labels
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.perf_counter() - self.start_time) * 1000
            self.collector.record_timer(self.name, duration_ms, self.labels)


# Global metrics instance
_global_metrics: Optional[MetricsCollector] = None


def get_global_metrics(name: str = "global") -> MetricsCollector:
    """Get or create the global metrics collector."""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector(name=name)
    return _global_metrics


def create_json_export_handler(file_path: str) -> Callable[[Dict[str, Any]], None]:
    """Create a handler that exports metrics to a JSON file."""
    def handler(metrics: Dict[str, Any]) -> None:
        with open(file_path, "w") as f:
            json.dump(metrics, f, indent=2, default=str)
    return handler


def create_prometheus_handler(push_gateway_url: str) -> Callable[[Dict[str, Any]], None]:
    """
    Create a handler that pushes metrics to Prometheus Pushgateway.

    Note: Requires prometheus_client package.
    """
    def handler(metrics: Dict[str, Any]) -> None:
        try:
            from prometheus_client import CollectorRegistry, Gauge, Counter, push_to_gateway

            registry = CollectorRegistry()

            # Export counters
            for name, values in metrics.get("counters", {}).items():
                counter = Counter(name, f"{name} counter", registry=registry)
                for _, value in values.items():
                    counter._value.set(value)

            # Export gauges
            for name, values in metrics.get("gauges", {}).items():
                gauge = Gauge(name, f"{name} gauge", registry=registry)
                for _, value in values.items():
                    gauge.set(value)

            push_to_gateway(push_gateway_url, job="agent-metrics", registry=registry)
        except ImportError:
            print("prometheus_client not installed, skipping Prometheus export")
        except Exception as e:
            print(f"Prometheus export error: {e}")

    return handler
