# DentalCare Pro - Kubernetes Cluster Architecture & Topology

DentalCare Pro is architected as a resilient, zero-trust microservices deployment running on Kubernetes 1.31+.

---

## 1. Workload Architecture & Pod Topology

The application namespace (`dentalcare`) consists of three decoupled workload controllers:

```
[ Internet Traffic ]
        |
        v
[ AWS NLB / Cloud Load Balancer ]
        |
        v
[ Ingress Controller (TLS 1.3, Rate-Limiting, WAF) ]
        |---------------------------------------|
        | (Host: app.dentalcare.io)             | (Path: /api/*, /metrics)
        v                                       v
[ DentalCare Web Pods ]               [ DentalCare Backend API Pods ]
(Next.js 16 Standalone)               (FastAPI / Python 3.12)
(Replicas: 2 - 10 HPA)                (Replicas: 3 - 20 HPA)
                                                |
        |---------------------------------------|
        |                                       |
        v                                       v
[ Task Worker Pods ]                   [ PgBouncer Connection Pool ]
(Background Celery/Async)                       |
(Replicas: 2 - 6 HPA)                           v
        |                              [ PostgreSQL 17 Multi-AZ ]
        v                               (Primary + Sync Standby)
[ Redis 7 Cluster ]
(Tokens, Locks, Caching)
```

---

## 2. Pod Specifications & Resource Envelopes

| Workload Component | Image Base | Replicas (Min/Max) | CPU Request / Limit | Memory Request / Limit | Security Profile |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Backend API** | `python:3.12-slim` | 3 / 20 | 500m / 2000m | 512Mi / 2048Mi | Non-Root (10001), ReadOnly Root, Drop All Caps |
| **Task Worker** | `python:3.12-slim` | 2 / 6 | 250m / 1000m | 512Mi / 1536Mi | Non-Root (10001), ReadOnly Root, Drop All Caps |
| **Next.js Web** | `node:22-alpine` | 2 / 10 | 250m / 1000m | 256Mi / 1024Mi | Non-Root (10001), ReadOnly Root, Drop All Caps |

---

## 3. High Availability & Resilience Controls

### 3.1 Pod Disruption Budgets (PDB)
PDBs prevent involuntary node draining or upgrades from disrupting live patient traffic:
- `dentalcare-backend-pdb`: `minAvailable: 1`
- `dentalcare-web-pdb`: `minAvailable: 1`

### 3.2 Anti-Affinity Rules
Pod anti-affinity is configured to schedule pods across distinct availability zones:
```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: backend
          topologyKey: "topology.kubernetes.io/zone"
```

### 3.3 Horizontal Pod Autoscaling (HPA)
- **Scale-Up Threshold**: 70% average CPU utilization OR 80% average Memory utilization.
- **Scale-Down Stabilization Window**: 300 seconds (prevents thrashing).
- **Scale-Up Stabilization Window**: 0 seconds (instant response to traffic surges).

---

## 4. Zero-Trust Network Policies

The cluster implements strict network segmentation via Kubernetes NetworkPolicies:

1. **Ingress Isolation**:
   - `dentalcare-web` only accepts ingress traffic from `ingress-nginx` on port 3000.
   - `dentalcare-backend` only accepts ingress traffic from `ingress-nginx` and `dentalcare-web` on port 8000.
2. **Database Isolation**:
   - PostgreSQL (RDS/Cloud) and Redis allow ingress ONLY from `dentalcare-backend` and `dentalcare-worker` pods.
   - `dentalcare-web` pods have ZERO network access to PostgreSQL or Redis.
3. **Egress Restriction**:
   - Pods are prohibited from arbitrary outbound internet access except for authorized external payment gateways (Stripe) and SMS/Email APIs (Twilio/SendGrid).
