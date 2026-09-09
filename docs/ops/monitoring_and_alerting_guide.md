# DentalCare Pro - Monitoring, Alerting & Observability Guide

DentalCare Pro incorporates full-stack observability across Prometheus, Grafana, Loki, and Alertmanager.

---

## 1. Observability Architecture

```
[ Application Pods ]  -->  [ Prometheus Scraper (Port 8000 /metrics) ]
[ Node Exporter ]     -->  [ Prometheus Server (Port 9090) ]
[ Postgres Exporter ] -->       |
[ Promtail Agent ]    -->  [ Loki Log Store (Port 3100) ]
                                |
                                v
                       [ Grafana Dashboards (Port 3001) ]
                                |
                                v
                       [ Alertmanager (Port 9093) ]
                                |
                   ---------------------------
                   |            |            |
                   v            v            v
              [PagerDuty]    [Slack]      [Email]
```

---

## 2. Core Prometheus Metrics Dictionary

| Metric Name | Type | Description | Alert Condition |
| :--- | :--- | :--- | :--- |
| `dentalcare_http_requests_total` | Counter | Total incoming HTTP requests by route, method, status | 5xx rate > 1% |
| `dentalcare_http_request_duration_seconds` | Histogram | Request latency distribution | P95 > 200ms |
| `dentalcare_db_connections_active` | Gauge | Active connections to PostgreSQL | Pool saturation > 85% |
| `dentalcare_worker_queue_depth` | Gauge | Outstanding background jobs in queue | Queue depth > 500 jobs |
| `dentalcare_uptime_seconds` | Counter | Continuous pod process uptime | Unexpected restarts |

---

## 3. Grafana Dashboards Overview

Dashboards are stored in `monitoring/grafana/dashboards/`:

1. **Executive SLO & Practice Performance Dashboard (`executive_slo_dashboard.json`)**:
   - 99.9% Uptime SLA Tracker
   - Error Budget Burn Rate (30-day trailing)
   - Total System Throughput (RPS)
   - Cross-Branch Performance Overview
2. **Backend API Microservices Dashboard (`api_service_dashboard.json`)**:
   - P50, P90, P95, and P99 Latency percentiles
   - Request distribution by HTTP status code (2xx, 4xx, 5xx)
   - Pod CPU and Memory consumption per replica
3. **PostgreSQL Database & PgBouncer Dashboard (`database_postgres_dashboard.json`)**:
   - Active client connections vs server pool limits
   - Transaction volume (Commits / Rollbacks)
   - Buffer Cache Hit Ratio (target > 99%)
   - Slow query tracker (> 250ms)

---

## 4. Alerting Thresholds & Notification Routing

Alerts are defined in `monitoring/prometheus/alerts.yml` and routed via `monitoring/alertmanager/alertmanager.yml`:

- **Critical Alerts (PagerDuty + High-Priority Slack)**:
  - `DentalCareApiHigh5xxErrorRate`: 5xx errors > 1% for 2 consecutive minutes.
  - `DentalCareApiP95LatencyExceeded`: P95 latency > 500ms for 5 minutes.
  - `DentalCareDatabaseConnectionsSaturated`: Active connections > 85% of max pool.
  - `DentalCarePodCrashLooping`: Pod restarting > 3 times in 10 minutes.
- **Warning Alerts (Standard Slack #alerts-prod)**:
  - `DentalCareLowDiskSpace`: Node filesystem utilization > 85%.
  - `DentalCareBackgroundQueueLag`: Worker backlog > 500 jobs for 10 minutes.
