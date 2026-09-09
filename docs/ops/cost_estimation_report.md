# DentalCare Pro - Cloud Infrastructure Cost Estimation & Sizing Report

This report provides estimated monthly cloud infrastructure costs across AWS production reference deployments for DentalCare Pro.

---

## 1. Environment Tiers & Sizing

### Tier 1: Development & Testing (Single Clinic / CI)
- EKS Cluster: 1 t3.medium node
- RDS PostgreSQL: Single-AZ `db.t4g.medium` (2 vCPU, 4GB RAM, 50GB gp3)
- ElastiCache Redis: `cache.t4g.micro`
- S3 Storage: 100GB Standard
- **Estimated Monthly Cost**: **~$180 - $250 / month**

### Tier 2: Staging / Pre-Production (Simulated Multi-Branch)
- EKS Cluster: 2 m6i.large nodes
- RDS PostgreSQL: Multi-AZ `db.r6g.large` (2 vCPU, 16GB RAM, 200GB gp3)
- ElastiCache Redis: Multi-AZ `cache.m6g.large`
- S3 Storage: 500GB Standard + KMS
- **Estimated Monthly Cost**: **~$650 - $850 / month**

### Tier 3: Enterprise Production (Supports 500+ Clinics, 10,000+ Concurrent Users)
- **EKS Managed Cluster**: 3-10 m6i.xlarge nodes (4 vCPU, 16GB RAM each) with Cluster Autoscaler
- **RDS PostgreSQL 17**: Multi-AZ `db.r6g.2xlarge` (8 vCPU, 64GB RAM, 1TB gp3 with 12,000 IOPS) + 1 Read Replica
- **ElastiCache Redis HA**: 2-node cluster `cache.r6g.large` (Multi-AZ with automatic failover)
- **AWS S3 & CloudFront**: 5TB diagnostic images + Glacier lifecycle archiving
- **AWS WAF & Shield Standard**: 1 Web ACL with Managed Rule Groups (SQLi, XSS, Common)
- **Data Transfer & NAT Gateways**: Dual-AZ NAT Gateways + 5TB egress
- **Estimated Monthly Cost**: **~$2,400 - $3,200 / month**

---

## 2. Itemized Production Cost Breakdown (Tier 3)

| Component | AWS Resource | Monthly Unit Cost | Qty / Usage | Total Monthly (USD) |
| :--- | :--- | :--- | :--- | :--- |
| **Kubernetes Control Plane** | Amazon EKS Cluster | $73.00 / month | 1 Cluster | $73.00 |
| **Compute Nodes** | EC2 `m6i.xlarge` (4 vCPU, 16GB) | $140.16 / month | 4 nodes (avg) | $560.64 |
| **Database Primary** | RDS Multi-AZ `db.r6g.2xlarge` | $1,022.00 / month | 1 instance | $1,022.00 |
| **Database Read Replica** | RDS Single-AZ `db.r6g.xlarge` | $255.50 / month | 1 instance | $255.50 |
| **Database Storage** | RDS gp3 (1TB, 12,000 IOPS) | $185.00 / month | 1.5 TB | $277.50 |
| **In-Memory Cache** | ElastiCache `cache.r6g.large` Multi-AZ | $198.00 / month | 1 cluster (2 nodes) | $396.00 |
| **Object Storage (X-Rays/Media)** | S3 Standard (5TB) + Glacier | $0.023 / GB | 5,000 GB | $115.00 |
| **Network & Ingress** | Dual NAT Gateways + NLB | $72.00 / month | 2 NAT + 1 NLB | $144.00 |
| **WAF & Security** | AWS WAFv2 + Rules | $30.00 / month | 1 WebACL + Rules | $45.00 |
| **KMS Key Management** | KMS Customer Managed Keys | $1.00 / key + requests | 3 keys | $15.00 |
| **Total Estimated Spend** | | | | **~$2,903.64 / month** |

---

## 3. Cost Optimization Strategies

1. **Savings Plans & Reserved Instances**: Committing to 1-year or 3-year Compute Savings Plans reduces EC2 and RDS compute costs by 35% - 55%.
2. **S3 Intelligent-Tiering & Glacier Lifecycle**: Automatically transition X-rays and 3D dental scans older than 90 days to Glacier Instant Retrieval, cutting storage costs by 68%.
3. **Karpenter / Horizontal Pod Autoscaling**: Scale down worker and non-critical pods during non-business clinic hours (8 PM - 6 AM local time), saving up to 25% on compute node hours.
