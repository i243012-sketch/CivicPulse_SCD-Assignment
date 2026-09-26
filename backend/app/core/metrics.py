"""Prometheus metrics for monitoring."""
from prometheus_client import Counter, Gauge, Histogram

# Request metrics
request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

request_latency = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

# Triage metrics
triage_latency = Histogram(
    "triage_duration_milliseconds",
    "Triage operation latency in milliseconds",
    ["provider"],
    buckets=(10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000),
)

triage_fallback_count = Counter(
    "triage_fallback_total",
    "Total number of triage fallbacks to rules engine",
    ["provider", "reason"],
)

triage_cache_hit = Counter(
    "triage_cache_hits_total",
    "Total number of triage cache hits",
)

triage_cache_miss = Counter(
    "triage_cache_misses_total",
    "Total number of triage cache misses",
)

# Stats cache metrics
stats_cache_hit = Counter(
    "stats_cache_hits_total",
    "Total number of stats cache hits",
)

stats_cache_miss = Counter(
    "stats_cache_misses_total",
    "Total number of stats cache misses",
)

# Database connection pool
db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

# Rate limiting
rate_limit_exceeded = Counter(
    "rate_limit_exceeded_total",
    "Total number of rate limit exceedances",
    ["client_ip"],
)
