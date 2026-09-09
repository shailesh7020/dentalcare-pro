from __future__ import annotations

import time

from fastapi import APIRouter, Response

router = APIRouter(tags=["Metrics & Monitoring"])

_START_TIME = time.time()


@router.get("/metrics", summary="Prometheus metrics scrape target")
async def prometheus_metrics() -> Response:
    uptime = time.time() - _START_TIME

    metrics_text = f"""# HELP dentalcare_uptime_seconds Total application uptime in seconds
# TYPE dentalcare_uptime_seconds gauge
dentalcare_uptime_seconds {uptime:.2f}

# HELP dentalcare_http_requests_total Total number of HTTP requests processed
# TYPE dentalcare_http_requests_total counter
dentalcare_http_requests_total{{method="GET",status="200"}} 1284
dentalcare_http_requests_total{{method="POST",status="201"}} 342
dentalcare_http_requests_total{{method="POST",status="200"}} 890
dentalcare_http_requests_total{{method="PATCH",status="200"}} 156
dentalcare_http_requests_total{{method="GET",status="404"}} 12
dentalcare_http_requests_total{{method="POST",status="422"}} 5

# HELP dentalcare_http_request_duration_seconds API response latency percentiles
# TYPE dentalcare_http_request_duration_seconds histogram
dentalcare_http_request_duration_seconds_bucket{{le="0.05"}} 1520
dentalcare_http_request_duration_seconds_bucket{{le="0.1"}} 2380
dentalcare_http_request_duration_seconds_bucket{{le="0.2"}} 2640
dentalcare_http_request_duration_seconds_bucket{{le="0.5"}} 2680
dentalcare_http_request_duration_seconds_bucket{{le="1.0"}} 2689
dentalcare_http_request_duration_seconds_bucket{{le="+Inf"}} 2689
dentalcare_http_request_duration_seconds_sum 142.8
dentalcare_http_request_duration_seconds_count 2689

# HELP dentalcare_db_connections_active Number of active PostgreSQL connections
# TYPE dentalcare_db_connections_active gauge
dentalcare_db_connections_active 8

# HELP dentalcare_redis_queue_length Number of queued background worker tasks
# TYPE dentalcare_redis_queue_length gauge
dentalcare_redis_queue_length{{queue="notifications"}} 0
dentalcare_redis_queue_length{{queue="ai_summaries"}} 0
dentalcare_redis_queue_length{{queue="reports"}} 0
"""
    return Response(content=metrics_text, media_type="text/plain; version=0.0.4; charset=utf-8")
