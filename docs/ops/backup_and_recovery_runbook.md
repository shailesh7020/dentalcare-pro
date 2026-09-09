# DentalCare Pro - Backup, Restoration & Disaster Recovery Runbook

This runbook defines operational procedures for executing backups, Point-In-Time Recovery (PITR), replica failover, and disaster recovery drills.

---

## 1. Recovery Objectives (SLA)

| Metric | Target | Verification Method |
| :--- | :--- | :--- |
| **RPO** (Recovery Point Objective) | **≤ 15 minutes** | Continuous WAL archiving + 60s archive timeout |
| **RTO** (Recovery Time Objective) | **≤ 1 hour** | Automated standby promotion + fast pg_restore |
| **Backup Retention** | 30 Days Daily / 7 Years Yearly | HIPAA Title II Security Rule Compliance |

---

## 2. Automated Daily Backup Execution

Automated backups run daily at 01:00 UTC via Kubernetes CronJob invoking `scripts/backup_postgres.sh`.

### Manual Backup Trigger:
```bash
# Execute ad-hoc full backup
bash scripts/backup_postgres.sh
```

### Backup Verification:
Verify the backup archive exists in the encrypted S3 bucket:
```bash
aws s3 ls s3://dentalcare-production-backups-iad/postgres/daily/ --human-readable
```

---

## 3. Point-In-Time Recovery (PITR) Procedure

Use this procedure if an accidental mass deletion, data corruption, or ransomware incident occurs.

### Step 3.1: Determine Recovery Timestamp
Identify the exact UTC target timestamp immediately preceding the corruption event (e.g., `2026-09-09 14:15:00 UTC`).

### Step 3.2: Isolate Production Database
Prevent active writes:
```bash
kubectl scale deployment dentalcare-backend --replicas=0 -n dentalcare
kubectl scale deployment dentalcare-worker --replicas=0 -n dentalcare
```

### Step 3.3: Execute PITR Engine
Run the automated restore script:
```bash
bash scripts/restore_pitr.sh "2026-09-09 14:15:00 UTC" /tmp/dentalcare_backups/dentalcare_20260909_010000Z.dump.enc
```

### Step 3.4: Verify Restored Data Integrity
Connect to PostgreSQL and verify:
```sql
SELECT count(*) FROM patients;
SELECT count(*) FROM appointments;
SELECT count(*) FROM invoices;
SELECT max(created_at) FROM audit_logs;
```

### Step 3.5: Restore Service Traffic
```bash
kubectl scale deployment dentalcare-backend --replicas=3 -n dentalcare
kubectl scale deployment dentalcare-worker --replicas=2 -n dentalcare
```

---

## 4. Annual Disaster Recovery Drill Procedure

Simulate complete loss of the primary database availability zone using the automated drill engine:

```bash
bash scripts/disaster_recovery_drill.sh
```

This will:
1. Snapshot pre-disaster database record counts.
2. Simulate primary node crash and measure failover latency.
3. Validate WAL replay and verify zero data corruption.
4. Calculate actual RPO and RTO metrics.
5. Generate an executive compliance audit report at `/tmp/dentalcare_dr_audit/dr_drill_report_*.json`.
