# DentalCare Pro - Site Reliability & Operations Troubleshooting Guide

This guide provides targeted resolution runbooks for common production alerts, errors, and operational incidents.

---

## 1. Database Connection Pool Saturation (`PgBouncerSaturation`)

### Symptoms:
- API latency surges beyond 1000ms.
- 500 error spikes with message: `Remaining connection slots are reserved for non-replication superuser connections`.

### Resolution Steps:
1. Inspect PgBouncer pool status:
   ```bash
   kubectl exec -it deployment/dentalcare-backend -n dentalcare -- psql -h 127.0.0.1 -p 6432 -U postgres -c "SHOW POOLS;"
   ```
2. Identify slow or hanging transactions:
   ```sql
   SELECT pid, now() - xact_start AS duration, query 
   FROM pg_stat_activity 
   WHERE state = 'active' AND (now() - xact_start) > interval '10 seconds';
   ```
3. Terminate runaway query if non-critical:
   ```sql
   SELECT pg_terminate_backend(<pid>);
   ```
4. If connection demand is legitimate traffic surge, scale PgBouncer max connections in `postgres/pgbouncer.ini`.

---

## 2. Pod CrashLoopBackOff Triage

### Symptoms:
- Backend or web pods continuously restart.

### Resolution Steps:
1. Fetch pod termination logs:
   ```bash
   kubectl logs deployment/dentalcare-backend -n dentalcare --previous --tail=50
   ```
2. Verify secret environment variable injection:
   ```bash
   kubectl get secret dentalcare-secrets -n dentalcare -o yaml
   ```
3. Check database migration status:
   ```bash
   kubectl logs job/dentalcare-migration -n dentalcare
   ```

---

## 3. High Memory Utilization on Web Pods (Next.js)

### Symptoms:
- Web pods getting killed by Kubernetes OOMKiller (`OOMKilled`).

### Resolution Steps:
1. Check heap dump allocation in Next.js standalone container.
2. Temporarily increase memory limits in `helm/dentalcare/values.yaml`:
   ```yaml
   web:
     resources:
       limits:
         memory: 2048Mi
   ```
3. Deploy updated Helm release:
   ```bash
   helm upgrade dentalcare-pro helm/dentalcare -n dentalcare
   ```
