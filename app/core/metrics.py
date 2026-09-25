import time
from typing import Any
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

METRICS_CONTENT_TYPE = CONTENT_TYPE_LATEST
START_TIME = time.time()

HTTP_REQUESTS_TOTAL = Counter(
    "voiceagent_http_requests_total",
    "Total count of HTTP requests",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "voiceagent_http_request_duration_seconds",
    "Histogram of HTTP request durations in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "voiceagent_http_requests_in_progress",
    "Number of HTTP requests currently in progress",
)

APP_INFO = Info(
    "voiceagent_app_info",
    "Voice Agent application metadata",
)
APP_INFO.info({"version": "1.0.0", "app_name": "Voice Agent API"})

TOOL_EXECUTIONS_TOTAL = Counter(
    "voiceagent_tool_executions_total",
    "Total count of tool executions by tool name and status",
    ["tool_name", "status"],
)

AGENT_RUNS_TOTAL = Counter(
    "voiceagent_agent_runs_total",
    "Total count of agent chat executions by provider and status",
    ["provider", "status"],
)

AGENT_RUN_DURATION_SECONDS = Histogram(
    "voiceagent_agent_run_duration_seconds",
    "Duration of agent chat runs in seconds",
    ["provider"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)


def record_http_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    """Record completed HTTP request metrics."""
    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code),
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        endpoint=endpoint,
    ).observe(duration_seconds)


def record_tool_execution(tool_name: str, status: str) -> None:
    """Record tool execution outcome ('success' or 'error')."""
    TOOL_EXECUTIONS_TOTAL.labels(
        tool_name=tool_name,
        status=status,
    ).inc()


def record_agent_run(
    provider: str,
    status: str,
    duration_seconds: float,
) -> None:
    """Record agent chat execution outcome and duration."""
    AGENT_RUNS_TOTAL.labels(
        provider=provider,
        status=status,
    ).inc()
    AGENT_RUN_DURATION_SECONDS.labels(
        provider=provider,
    ).observe(duration_seconds)


def generate_metrics() -> bytes:
    """Generate Prometheus exposition format bytes for scraping."""
    return generate_latest()


def get_metrics_summary() -> dict[str, Any]:
    """Return a human-readable dictionary summary of core metric gauges and info."""
    return {
        "status": "healthy",
        "requests_in_progress": HTTP_REQUESTS_IN_PROGRESS._value.get(),
        "app_info": {"version": "1.0.0", "app_name": "Voice Agent API"},
    }


def get_detailed_metrics_snapshot() -> dict[str, Any]:
    """Aggregate registered Prometheus metrics into a structured format for charts and UI."""
    total_requests = 0
    status_counts = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}
    endpoint_counts: dict[str, int] = {}
    tool_counts: dict[str, dict[str, int]] = {}
    latency_sum = 0.0
    latency_count = 0
    latency_buckets: dict[str, int] = {
        "<= 10ms": 0,
        "<= 50ms": 0,
        "<= 100ms": 0,
        "<= 500ms": 0,
        "<= 1s": 0,
        "> 1s": 0,
    }

    for metric in REGISTRY.collect():
        if metric.name == "voiceagent_http_requests":
            for sample in metric.samples:
                if sample.name == "voiceagent_http_requests_total":
                    val = int(sample.value)
                    total_requests += val
                    code = sample.labels.get("status_code", "200")
                    if code.startswith("2"):
                        status_counts["2xx"] += val
                    elif code.startswith("3"):
                        status_counts["3xx"] += val
                    elif code.startswith("4"):
                        status_counts["4xx"] += val
                    elif code.startswith("5"):
                        status_counts["5xx"] += val

                    ep = sample.labels.get("endpoint", "unknown")
                    endpoint_counts[ep] = endpoint_counts.get(ep, 0) + val

        elif metric.name == "voiceagent_http_request_duration_seconds":
            for sample in metric.samples:
                if sample.name == "voiceagent_http_request_duration_seconds_sum":
                    latency_sum += sample.value
                elif sample.name == "voiceagent_http_request_duration_seconds_count":
                    latency_count += int(sample.value)
                elif sample.name == "voiceagent_http_request_duration_seconds_bucket":
                    le = sample.labels.get("le")
                    val = int(sample.value)
                    if le == "0.01":
                        latency_buckets["<= 10ms"] += val
                    elif le == "0.05":
                        latency_buckets["<= 50ms"] += val
                    elif le == "0.1":
                        latency_buckets["<= 100ms"] += val
                    elif le == "0.5":
                        latency_buckets["<= 500ms"] += val
                    elif le == "1.0":
                        latency_buckets["<= 1s"] += val
                    elif le == "+Inf":
                        latency_buckets["> 1s"] += val

        elif metric.name == "voiceagent_tool_executions":
            for sample in metric.samples:
                if sample.name == "voiceagent_tool_executions_total":
                    t_name = sample.labels.get("tool_name", "unknown")
                    t_status = sample.labels.get("status", "success")
                    if t_name not in tool_counts:
                        tool_counts[t_name] = {"success": 0, "error": 0}
                    tool_counts[t_name][t_status] = tool_counts[t_name].get(t_status, 0) + int(sample.value)

    avg_latency_ms = (latency_sum / latency_count * 1000) if latency_count > 0 else 0.0
    uptime_seconds = int(time.time() - START_TIME)
    error_count = status_counts["4xx"] + status_counts["5xx"]
    success_rate = round(((total_requests - error_count) / total_requests * 100), 1) if total_requests > 0 else 100.0

    return {
        "status": "healthy",
        "uptime_seconds": uptime_seconds,
        "total_requests": total_requests,
        "success_rate_pct": success_rate,
        "avg_latency_ms": round(avg_latency_ms, 2),
        "requests_in_progress": int(HTTP_REQUESTS_IN_PROGRESS._value.get()),
        "status_distribution": status_counts,
        "endpoints": endpoint_counts,
        "tool_executions": tool_counts,
        "latency_buckets": latency_buckets,
        "app_info": {"version": "1.0.0", "app_name": "Voice Agent API"},
    }
