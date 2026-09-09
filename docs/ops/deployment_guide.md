# DentalCare Pro - Enterprise Cloud Deployment Guide

This guide provides end-to-end instructions for deploying DentalCare Pro to production Kubernetes clusters (AWS EKS, GCP GKE, Azure AKS, or bare-metal Kubernetes) using Terraform and Helm.

---

## 1. Prerequisites

Ensure your deployment workstation or CI/CD runner has the following tools installed:

- **Terraform**: `v1.9.0` or higher
- **kubectl**: `v1.31.0` or higher
- **Helm**: `v3.15.0` or higher
- **AWS CLI** (or cloud provider equivalent CLI): `v2.17.0`
- **Docker**: `v26.0` or higher with Buildx support

---

## 2. Infrastructure Provisioning via Terraform

All cloud resources (VPC, Subnets, EKS, RDS Multi-AZ, ElastiCache Redis, S3 media storage, WAF) are defined declaratively in `terraform/`.

### Step 2.1: Initialize Terraform
Navigate to the terraform directory and initialize the remote backend:

```bash
cd terraform
terraform init -backend-config="bucket=dentalcare-tfstate-production" \
               -backend-config="key=production/dentalcare.tfstate" \
               -backend-config="region=us-east-1"
```

### Step 2.2: Plan Infrastructure Changes
Review the execution plan against `environments/production/terraform.tfvars`:

```bash
terraform plan -var-file=environments/production/terraform.tfvars.example -out=prod.tfplan
```

### Step 2.3: Apply Infrastructure
Apply the verified plan:

```bash
terraform apply prod.tfplan
```

Upon completion, note the exported outputs:
- `kubernetes_cluster_name`: `dentalcare-production-eks`
- `rds_postgres_endpoint`: Primary database endpoint
- `redis_replication_group_primary_endpoint`: Redis cache endpoint
- `s3_media_bucket_name`: `dentalcare-production-media-iad`

### Step 2.4: Update Local Kubeconfig
Connect `kubectl` to the newly provisioned EKS cluster:

```bash
aws eks update-kubeconfig --name dentalcare-production-eks --region us-east-1
kubectl get nodes
```

---

## 3. Kubernetes Ingress & TLS Setup

DentalCare Pro utilizes `cert-manager` for automatic Let's Encrypt TLS certificate provisioning and renewal.

### Step 3.1: Install Ingress Controller
Deploy ingress-nginx:

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/aws-load-balancer-type"="nlb"
```

### Step 3.2: Install Cert-Manager
Deploy cert-manager for automated ACME Let's Encrypt certificates:

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

---

## 4. Application Deployment via Helm

DentalCare Pro packaging is consolidated into `helm/dentalcare/`.

### Step 4.1: Prepare Production Secrets
Secrets can be injected from AWS Secrets Manager / HashiCorp Vault or passed via Helm values:

```bash
kubectl create namespace dentalcare --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic dentalcare-secrets \
  --namespace dentalcare \
  --from-literal=database-url="postgresql://app_user:YourSecurePassword@rds-endpoint:5432/dentalcare" \
  --from-literal=redis-url="rediss://:YourRedisAuthToken@redis-endpoint:6379/0" \
  --from-literal=secret-key="YourEnterprise64ByteSecretKey" \
  --from-literal=encryption-key="Your32ByteHIPAAAESKey" \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Step 4.2: Lint Helm Chart
Validate chart syntax and templates:

```bash
helm lint helm/dentalcare
```

### Step 4.3: Execute Zero-Downtime Deployment
Deploy DentalCare Pro stack to production:

```bash
helm upgrade --install dentalcare-pro helm/dentalcare \
  --namespace dentalcare \
  --values helm/dentalcare/values.yaml \
  --set backend.image.tag="v1.0.0" \
  --set web.image.tag="v1.0.0" \
  --wait --timeout 10m
```

### Step 4.4: Verify Deployment Health
```bash
kubectl get pods -n dentalcare
kubectl get ingress -n dentalcare
kubectl get hpa -n dentalcare
```

---

## 5. Rollback Procedure

If any health check or smoke test fails after deployment:

```bash
# View deployment release history
helm history dentalcare-pro -n dentalcare

# Roll back to the previous release
helm rollback dentalcare-pro -n dentalcare 0

# Verify rollout status
kubectl rollout status deployment/dentalcare-backend -n dentalcare
kubectl rollout status deployment/dentalcare-web -n dentalcare
```
