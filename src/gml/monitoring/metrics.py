"""
Prometheus Metrics Collection for GML Infrastructure

Centralized metrics collection using prometheus_client for monitoring
agent activity, message delivery, memory operations, and system performance.

Metrics Types:
- Counters: Cumulative metrics (agents registered, messages sent)
- Gauges: Point-in-time values (active agents, pending messages)
- Histograms: Distribution of values (latency, query times)

Usage:
    >>> from src.gml.monitoring.metrics import metrics
    >>> metrics.increment_agents_registered()
    >>> metrics.set_active_agents(10)
    >>> metrics.record_request_latency(0.05)
"""

import logging
from typing import Optional

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

logger = logging.getLogger(__name__)

# ============================================================================
# METRICS REGISTRY
# ============================================================================

# Create a custom registry for application metrics
_metrics_registry = CollectorRegistry()


# ============================================================================
# COUNTERS - Cumulative metrics that only increase
# ============================================================================

agents_registered_total = Counter(
    "gml_agents_registered_total",
    "Total number of agents registered in the system",
    registry=_metrics_registry,
)

messages_sent_total = Counter(
    "gml_messages_sent_total",
    "Total number of messages sent between agents",
    ["status"],  # Labels: pending, delivered, failed
    registry=_metrics_registry,
)

memory_writes_total = Counter(
    "gml_memory_writes_total",
    "Total number of memory write operations",
    ["memory_type"],  # Labels: episodic, semantic, procedural
    registry=_metrics_registry,
)

memory_searches_total = Counter(
    "gml_memory_searches_total",
    "Total number of memory search operations",
    registry=_metrics_registry,
)

http_errors_total = Counter(
    "gml_http_errors_total",
    "Total number of HTTP errors",
    ["status_code", "endpoint"],  # Labels: status_code (4xx, 5xx), endpoint
    registry=_metrics_registry,
)


# ============================================================================
# GAUGES - Point-in-time values that can go up or down
# ============================================================================

active_agents = Gauge(
    "gml_active_agents",
    "Current number of active agents in the system",
    ["status"],  # Labels: active, inactive, error, maintenance
    registry=_metrics_registry,
)

pending_messages = Gauge(
    "gml_pending_messages",
    "Current number of pending messages waiting for delivery",
    registry=_metrics_registry,
)

total_memory_entries = Gauge(
    "gml_total_memory_entries",
    "Total number of memory entries stored in the system",
    ["memory_type"],  # Labels: episodic, semantic, procedural
    registry=_metrics_registry,
)

total_costs_usd = Gauge(
    "gml_total_costs_usd",
    "Total costs incurred in USD",
    ["cost_type"],  # Labels: agent_registration, message_send, memory_write, etc.
    registry=_metrics_registry,
)


# ============================================================================
# HISTOGRAMS - Distribution of values (latency, durations)
# ============================================================================

request_latency_seconds = Histogram(
    "gml_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint", "status_code"],  # Labels for filtering
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0],  # Custom buckets as specified
    registry=_metrics_registry,
)

message_delivery_latency_seconds = Histogram(
    "gml_message_delivery_latency_seconds",
    "Time taken to deliver messages between agents in seconds",
    ["from_agent", "to_agent"],  # Optional labels
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=_metrics_registry,
)

database_query_latency_seconds = Histogram(
    "gml_database_query_latency_seconds",
    "Database query execution time in seconds",
    ["operation", "table"],  # Labels: operation (select, insert, update, delete), table name
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
    registry=_metrics_registry,
)


# ============================================================================
# METRICS COLLECTOR CLASS
# ============================================================================


class MetricsCollector:
    """
    Centralized metrics collection interface.

    Provides convenient methods for recording metrics throughout the application.
    All metrics are automatically registered with Prometheus.

    Example:
        >>> from src.gml.monitoring.metrics import metrics
        >>> 
        >>> # Increment counters
        >>> metrics.increment_agents_registered()
        >>> metrics.increment_messages_sent(status="delivered")
        >>> 
        >>> # Update gauges
        >>> metrics.set_active_agents(status="active", count=5)
        >>> metrics.set_pending_messages(3)
        >>> 
        >>> # Record histograms
        >>> metrics.record_request_latency(0.05, method="GET", endpoint="/api/v1/agents")
        >>> metrics.record_message_delivery_latency(1.2, from_agent="agent-1", to_agent="agent-2")
    """

    # ========================================================================
    # COUNTER METHODS
    # ========================================================================

    @staticmethod
    def increment_agents_registered() -> None:
        """
        Increment the total agents registered counter.

        Call this when a new agent is successfully registered.
        """
        agents_registered_total.inc()
        logger.debug("Incremented agents_registered_total counter")

    @staticmethod
    def increment_messages_sent(status: str = "pending") -> None:
        """
        Increment the messages sent counter.

        Args:
            status: Message status (pending, delivered, failed, timeout)
        """
        messages_sent_total.labels(status=status).inc()
        logger.debug(f"Incremented messages_sent_total counter (status={status})")

    @staticmethod
    def increment_memory_writes(memory_type: str = "episodic") -> None:
        """
        Increment the memory writes counter.

        Args:
            memory_type: Type of memory (episodic, semantic, procedural)
        """
        memory_writes_total.labels(memory_type=memory_type).inc()
        logger.debug(f"Incremented memory_writes_total counter (type={memory_type})")

    @staticmethod
    def increment_memory_searches() -> None:
        """
        Increment the memory searches counter.

        Call this when a memory search operation is performed.
        """
        memory_searches_total.inc()
        logger.debug("Incremented memory_searches_total counter")

    @staticmethod
    def increment_http_errors(status_code: int, endpoint: str = "/") -> None:
        """
        Increment the HTTP errors counter.

        Args:
            status_code: HTTP status code (4xx, 5xx)
            endpoint: API endpoint path
        """
        http_errors_total.labels(status_code=str(status_code), endpoint=endpoint).inc()
        logger.debug(f"Incremented http_errors_total counter (status={status_code}, endpoint={endpoint})")

    # ========================================================================
    # GAUGE METHODS
    # ========================================================================

    @staticmethod
    def set_active_agents(status: str, count: int) -> None:
        """
        Set the number of active agents for a given status.

        Args:
            status: Agent status (active, inactive, error, maintenance)
            count: Number of agents with this status
        """
        active_agents.labels(status=status).set(count)
        logger.debug(f"Set active_agents gauge (status={status}, count={count})")

    @staticmethod
    def set_pending_messages(count: int) -> None:
        """
        Set the number of pending messages.

        Args:
            count: Current number of pending messages
        """
        pending_messages.set(count)
        logger.debug(f"Set pending_messages gauge (count={count})")

    @staticmethod
    def set_total_memory_entries(memory_type: str, count: int) -> None:
        """
        Set the total number of memory entries for a memory type.

        Args:
            memory_type: Type of memory (episodic, semantic, procedural)
            count: Total number of entries
        """
        total_memory_entries.labels(memory_type=memory_type).set(count)
        logger.debug(f"Set total_memory_entries gauge (type={memory_type}, count={count})")

    @staticmethod
    def set_total_costs_usd(cost_type: str, amount: float) -> None:
        """
        Set the total costs in USD for a cost type.

        Args:
            cost_type: Type of cost (agent_registration, message_send, memory_write, etc.)
            amount: Total cost in USD
        """
        total_costs_usd.labels(cost_type=cost_type).set(amount)
        logger.debug(f"Set total_costs_usd gauge (type={cost_type}, amount={amount})")

    # ========================================================================
    # HISTOGRAM METHODS
    # ========================================================================

    @staticmethod
    def record_request_latency(
        latency_seconds: float,
        method: str = "GET",
        endpoint: str = "/",
        status_code: int = 200,
    ) -> None:
        """
        Record HTTP request latency.

        Args:
            latency_seconds: Request latency in seconds
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path
            status_code: HTTP status code
        """
        request_latency_seconds.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).observe(latency_seconds)
        logger.debug(
            f"Recorded request_latency (method={method}, endpoint={endpoint}, "
            f"latency={latency_seconds}s)"
        )

    @staticmethod
    def record_message_delivery_latency(
        latency_seconds: float,
        from_agent: Optional[str] = None,
        to_agent: Optional[str] = None,
    ) -> None:
        """
        Record message delivery latency.

        Args:
            latency_seconds: Delivery latency in seconds
            from_agent: Source agent ID (optional)
            to_agent: Destination agent ID (optional)
        """
        labels = {}
        if from_agent:
            labels["from_agent"] = from_agent
        if to_agent:
            labels["to_agent"] = to_agent

        message_delivery_latency_seconds.labels(**labels).observe(latency_seconds)
        logger.debug(f"Recorded message_delivery_latency (latency={latency_seconds}s)")

    @staticmethod
    def record_database_query_latency(
        latency_seconds: float,
        operation: str = "select",
        table: Optional[str] = None,
    ) -> None:
        """
        Record database query execution latency.

        Args:
            latency_seconds: Query execution time in seconds
            operation: Database operation (select, insert, update, delete)
            table: Table name (optional)
        """
        labels = {"operation": operation}
        if table:
            labels["table"] = table

        database_query_latency_seconds.labels(**labels).observe(latency_seconds)
        logger.debug(
            f"Recorded database_query_latency (operation={operation}, "
            f"latency={latency_seconds}s)"
        )

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    @staticmethod
    def get_metrics_registry() -> CollectorRegistry:
        """
        Get the metrics registry.

        Returns:
            CollectorRegistry instance containing all registered metrics
        """
        return _metrics_registry

    @staticmethod
    def generate_metrics() -> bytes:
        """
        Generate Prometheus metrics in text format.

        Returns:
            Bytes containing Prometheus-formatted metrics
        """
        return generate_latest(_metrics_registry)

    @staticmethod
    def get_content_type() -> str:
        """
        Get the content type for metrics endpoint.

        Returns:
            Content type string for Prometheus metrics
        """
        return CONTENT_TYPE_LATEST


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Create a singleton instance for easy access throughout the application
metrics = MetricsCollector()

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Counters
    "agents_registered_total",
    "messages_sent_total",
    "memory_writes_total",
    "memory_searches_total",
    "http_errors_total",
    # Gauges
    "active_agents",
    "pending_messages",
    "total_memory_entries",
    "total_costs_usd",
    # Histograms
    "request_latency_seconds",
    "message_delivery_latency_seconds",
    "database_query_latency_seconds",
    # Classes
    "MetricsCollector",
    # Instance
    "metrics",
    # Registry
    "_metrics_registry",
]

