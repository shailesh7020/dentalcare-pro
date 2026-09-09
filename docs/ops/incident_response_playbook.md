# DentalCare Pro - Incident Response & On-Call Playbook

This playbook outlines the operational steps for triaging, mitigating, and documenting production incidents for DentalCare Pro.

---

## 1. Incident Severity Matrix

| Severity | Definition | Response Time (SLA) | Escalation Path |
| :--- | :--- | :--- | :--- |
| **SEV-1 (Critical)** | Total outage, data corruption, API failure > 5%, patient data compromised. | **Immediate (< 15 mins)** | Primary On-Call -> Engineering Lead -> CTO -> Clinical Director |
| **SEV-2 (Major)** | Core feature degraded (Odontogram unavailable, billing offline, latency > 1s). | **< 30 mins** | Primary On-Call -> Secondary On-Call -> Engineering Lead |
| **SEV-3 (Minor)** | Non-critical feature degraded (SMS delay, report download slow, minor UI glitch). | **< 2 hours** | Primary On-Call |
| **SEV-4 (Low)** | Cosmestic issues, minor admin warning. | Next Business Day | Backlog triage |

---

## 2. Standard Triage Workflow

```
[ Alert Fires (PagerDuty / Slack) ]
                |
                v
[ Acknowledge Alert (< 15m for SEV-1) ]
                |
                v
[ Declare Incident in #incident-prod ]
                |
        ---------------------------------
        |                               |
        v                               v
[ Check Grafana SLO Dashboards ]   [ Check Loki Logs ]
(5xx rate, latency, DB connections) (grep error, exception trace)
                |
                v
[ Identify Root Cause: Code vs Infra vs DB ]
                |
        ---------------------------------
        |                               |
        v                               v
[ Infrastructure Rollback / Scale ]  [ Database Failover / PITR ]
(helm rollback dentalcare-pro)       (scripts/restore_pitr.sh)
                |
                v
[ Verify Healthcheck & Synthetic Probes ]
                |
                v
[ Resolve Incident & Publish Post-Mortem ]
```

---

## 3. Quick Mitigation Commands

### High API Latency or CPU Exhaustion
Scale up backend pods immediately:
```bash
kubectl scale deployment dentalcare-backend --replicas=15 -n dentalcare
```

### Faulty Code Release
Rollback to previous known good Helm release:
```bash
helm rollback dentalcare-pro -n dentalcare 0
```

### PgBouncer Connection Saturation
Inspect active client connections:
```bash
kubectl exec -it deployment/dentalcare-backend -n dentalcare -- psql -h 127.0.0.1 -p 6432 -U postgres -c "SHOW POOLS;"
```

### Redis Cache Reset
Evict temporary cache keys (does NOT affect sessions if separated):
```bash
redis-cli -u $REDIS_URL MEMORY PURGE
```

---

## 4. Root Cause Analysis (RCA) Post-Mortem Template

Every SEV-1 and SEV-2 incident requires a published Post-Mortem within 48 hours containing:
1. **Summary**: Brief description of what happened and business impact.
2. **Timeline (UTC)**: Detailed sequence of events from injection to detection, triage, and resolution.
3. **Root Cause**: 5-Whys analysis explaining technical and process deficiencies.
4. **Corrective Actions**: Specific Jira tasks assigned to engineers with completion deadlines.
