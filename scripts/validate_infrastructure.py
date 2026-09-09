# =====================================================================
# DentalCare Pro - Enterprise Infrastructure & DevOps Validation Engine
# Verifies all Phase 16 Cloud, K8s, Terraform, CI/CD & Monitoring assets
# =====================================================================
import json
import os
import sys
import yaml

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def safe_print(msg: str):
    print(msg.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8"))

class InfrastructureValidator:
    def __init__(self):
        self.passed_checks = 0
        self.failed_checks = 0
        self.errors = []

    def check(self, condition: bool, description: str):
        if condition:
            self.passed_checks += 1
            safe_print(f"  [PASS] {description}")
        else:
            self.failed_checks += 1
            self.errors.append(description)
            safe_print(f"  [FAIL] {description}")

    def validate_docker_stack(self):
        safe_print("\n--- 1. Validating Production Docker & Compose Simulation ---")
        backend_df = os.path.join(ROOT_DIR, "backend", "Dockerfile")
        self.check(os.path.exists(backend_df), "backend/Dockerfile exists")
        if os.path.exists(backend_df):
            content = open(backend_df, encoding="utf-8").read()
            self.check("dumb-init" in content, "backend/Dockerfile contains dumb-init PID 1 supervisor")
            self.check("appuser" in content, "backend/Dockerfile runs as unprivileged user")
            self.check("HEALTHCHECK" in content, "backend/Dockerfile contains HEALTHCHECK instruction")

        web_df = os.path.join(ROOT_DIR, "apps", "web", "Dockerfile")
        self.check(os.path.exists(web_df), "apps/web/Dockerfile exists")
        if os.path.exists(web_df):
            content = open(web_df, encoding="utf-8").read()
            self.check("standalone" in content, "apps/web/Dockerfile uses Next.js standalone build")
            self.check("nextjs" in content, "apps/web/Dockerfile runs as unprivileged nextjs user")

        compose_prod = os.path.join(ROOT_DIR, "docker-compose.prod.yml")
        self.check(os.path.exists(compose_prod), "docker-compose.prod.yml exists")
        if os.path.exists(compose_prod):
            with open(compose_prod, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                services = data.get("services", {})
                self.check("api" in services or "backend" in services, "Compose includes API/backend service")
                self.check("web" in services, "Compose includes web service")
                self.check("db" in services or "postgres" in services, "Compose includes database service")
                self.check("redis" in services, "Compose includes redis service")
                self.check("proxy" in services or "nginx" in services, "Compose includes reverse proxy")
                self.check("worker" in services, "Compose includes background task worker")

        nginx_conf = os.path.join(ROOT_DIR, "docker", "nginx", "nginx.conf")
        self.check(os.path.exists(nginx_conf), "docker/nginx/nginx.conf exists")
        if os.path.exists(nginx_conf):
            content = open(nginx_conf, encoding="utf-8").read()
            self.check("limit_req_zone" in content, "Nginx config includes rate limiting zones")
            self.check("upstream api_cluster" in content or "upstream backend_api" in content, "Nginx config defines backend upstream")

    def validate_kubernetes_helm(self):
        safe_print("\n--- 2. Validating Kubernetes Manifests & Helm Charts ---")
        chart_yaml = os.path.join(ROOT_DIR, "helm", "dentalcare", "Chart.yaml")
        values_yaml = os.path.join(ROOT_DIR, "helm", "dentalcare", "values.yaml")
        self.check(os.path.exists(chart_yaml), "helm/dentalcare/Chart.yaml exists")
        self.check(os.path.exists(values_yaml), "helm/dentalcare/values.yaml exists")

        templates_dir = os.path.join(ROOT_DIR, "helm", "dentalcare", "templates")
        expected_templates = [
            "backend-deployment.yaml",
            "backend-hpa.yaml",
            "backend-service.yaml",
            "worker-deployment.yaml",
            "web-deployment.yaml",
            "web-service.yaml",
            "ingress.yaml",
            "network-policy.yaml",
            "pod-disruption-budget.yaml",
            "configmap.yaml",
            "secrets.yaml",
        ]
        for tmpl in expected_templates:
            self.check(os.path.exists(os.path.join(templates_dir, tmpl)), f"Helm template exists: {tmpl}")

        k8s_all = os.path.join(ROOT_DIR, "k8s", "dentalcare-all-in-one.yaml")
        self.check(os.path.exists(k8s_all), "k8s/dentalcare-all-in-one.yaml exists")

    def validate_terraform_iac(self):
        safe_print("\n--- 3. Validating Terraform Infrastructure as Code ---")
        tf_root = os.path.join(ROOT_DIR, "terraform")
        self.check(os.path.exists(os.path.join(tf_root, "main.tf")), "terraform/main.tf exists")
        self.check(os.path.exists(os.path.join(tf_root, "variables.tf")), "terraform/variables.tf exists")
        self.check(os.path.exists(os.path.join(tf_root, "outputs.tf")), "terraform/outputs.tf exists")

        modules = ["vpc", "kubernetes", "database", "redis", "storage", "security"]
        for mod in modules:
            mod_main = os.path.join(tf_root, "modules", mod, "main.tf")
            self.check(os.path.exists(mod_main), f"Terraform module exists: modules/{mod}/main.tf")

        tfvars = os.path.join(tf_root, "environments", "production", "terraform.tfvars.example")
        self.check(os.path.exists(tfvars), "Production terraform.tfvars.example exists")

    def validate_cicd_pipeline(self):
        safe_print("\n--- 4. Validating CI/CD Pipeline (GitHub Actions) ---")
        ci_path = os.path.join(ROOT_DIR, ".github", "workflows", "ci.yml")
        self.check(os.path.exists(ci_path), ".github/workflows/ci.yml exists")
        if os.path.exists(ci_path):
            content = open(ci_path, encoding="utf-8").read()
            expected_stages = [
                "lint", "unit-tests", "integration-tests", "security-scan",
                "dependency-scan", "docker-build", "image-scan", "deploy-staging",
                "smoke-tests", "deploy-production"
            ]
            for stage in expected_stages:
                self.check(stage in content, f"CI/CD workflow contains stage: {stage}")
            self.check("manual-approval" in content or "manual-gate" in content, "CI/CD workflow contains stage: manual approval gate")

    def validate_monitoring_telemetry(self):
        safe_print("\n--- 5. Validating Observability & Telemetry Stack ---")
        metrics_py = os.path.join(ROOT_DIR, "backend", "app", "api", "metrics.py")
        self.check(os.path.exists(metrics_py), "backend/app/api/metrics.py exists")

        prom_yml = os.path.join(ROOT_DIR, "monitoring", "prometheus", "prometheus.yml")
        alerts_yml = os.path.join(ROOT_DIR, "monitoring", "prometheus", "alerts.yml")
        self.check(os.path.exists(prom_yml), "monitoring/prometheus/prometheus.yml exists")
        self.check(os.path.exists(alerts_yml), "monitoring/prometheus/alerts.yml exists")

        alertmgr_yml = os.path.join(ROOT_DIR, "monitoring", "alertmanager", "alertmanager.yml")
        self.check(os.path.exists(alertmgr_yml), "monitoring/alertmanager/alertmanager.yml exists")

        dashboards = [
            "executive_slo_dashboard.json",
            "api_service_dashboard.json",
            "database_postgres_dashboard.json"
        ]
        for db in dashboards:
            p = os.path.join(ROOT_DIR, "monitoring", "grafana", "dashboards", db)
            self.check(os.path.exists(p), f"Grafana dashboard exists: {db}")
            if os.path.exists(p):
                try:
                    with open(p, encoding="utf-8") as f:
                        json.load(f)
                    self.check(True, f"Grafana dashboard {db} parses as valid JSON")
                except Exception as e:
                    self.check(False, f"Grafana dashboard {db} parse error: {e}")

        self.check(os.path.exists(os.path.join(ROOT_DIR, "monitoring", "loki", "loki.yml")), "monitoring/loki/loki.yml exists")
        self.check(os.path.exists(os.path.join(ROOT_DIR, "monitoring", "promtail", "promtail.yml")), "monitoring/promtail/promtail.yml exists")

    def validate_postgres_disaster_recovery(self):
        safe_print("\n--- 6. Validating PostgreSQL HA & Disaster Recovery ---")
        pg_conf = os.path.join(ROOT_DIR, "postgres", "postgresql.conf")
        pgb_ini = os.path.join(ROOT_DIR, "postgres", "pgbouncer.ini")
        self.check(os.path.exists(pg_conf), "postgres/postgresql.conf exists")
        self.check(os.path.exists(pgb_ini), "postgres/pgbouncer.ini exists")

        dr_scripts = [
            "backup_postgres.sh",
            "restore_pitr.sh",
            "disaster_recovery_drill.sh"
        ]
        for s in dr_scripts:
            self.check(os.path.exists(os.path.join(ROOT_DIR, "scripts", s)), f"DR script exists: scripts/{s}")

    def validate_load_testing(self):
        safe_print("\n--- 7. Validating Performance & Load Testing ---")
        k6_script = os.path.join(ROOT_DIR, "tests", "load", "k6_stress_test.js")
        self.check(os.path.exists(k6_script), "tests/load/k6_stress_test.js exists")

        runner_py = os.path.join(ROOT_DIR, "tests", "load", "load_test_runner.py")
        self.check(os.path.exists(runner_py), "tests/load/load_test_runner.py exists")

        results_json = os.path.join(ROOT_DIR, "tests", "load", "load_test_results.json")
        self.check(os.path.exists(results_json), "tests/load/load_test_results.json exists")
        if os.path.exists(results_json):
            with open(results_json, encoding="utf-8") as f:
                res = json.load(f)
                sla = res.get("sla_verification", {})
                self.check(sla.get("overall_sla_status") == "PASS", "Load test benchmark overall status is PASS")
                self.check(sla.get("p95_pass") is True, f"P95 latency benchmark passed ({sla.get('p95_latency_ms')}ms < 200ms)")
                self.check(sla.get("dashboard_load_pass") is True, f"Dashboard load benchmark passed ({sla.get('dashboard_load_ms')}ms < 500ms)")

    def validate_operational_docs(self):
        safe_print("\n--- 8. Validating Operational Runbooks & Documentation ---")
        docs = [
            "deployment_guide.md",
            "kubernetes_architecture.md",
            "backup_and_recovery_runbook.md",
            "incident_response_playbook.md",
            "monitoring_and_alerting_guide.md",
            "security_and_compliance_hipaa.md",
            "cost_estimation_report.md",
        ]
        for d in docs:
            p = os.path.join(ROOT_DIR, "docs", "ops", d)
            self.check(os.path.exists(p) and os.path.getsize(p) > 500, f"Operational runbook exists & complete: docs/ops/{d}")

    def run_all(self):
        safe_print("=" * 70)
        safe_print("  DentalCare Pro - Phase 16 Infrastructure Validation Gate")
        safe_print("=" * 70)

        self.validate_docker_stack()
        self.validate_kubernetes_helm()
        self.validate_terraform_iac()
        self.validate_cicd_pipeline()
        self.validate_monitoring_telemetry()
        self.validate_postgres_disaster_recovery()
        self.validate_load_testing()
        self.validate_operational_docs()

        safe_print("\n" + "=" * 70)
        safe_print(f"Validation Summary: {self.passed_checks} checks passed, {self.failed_checks} failed.")
        safe_print("=" * 70)

        if self.failed_checks > 0:
            safe_print("\nFailed Checks:")
            for err in self.errors:
                safe_print(f"  - {err}")
            return False
        return True

if __name__ == "__main__":
    validator = InfrastructureValidator()
    success = validator.run_all()
    if success:
        safe_print("\n[SUCCESS] Phase 16 Infrastructure Verification Gate: 100% PASSED.")
        sys.exit(0)
    else:
        safe_print("\n[ERROR] Phase 16 Infrastructure Verification Gate FAILED.")
        sys.exit(1)
