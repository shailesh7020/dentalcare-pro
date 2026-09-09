from fastapi.testclient import TestClient

from app.main import app


def test_live_probe_and_request_id_headers() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health/live", headers={"X-Request-ID": "trace-123"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"] == "trace-123"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_validation_error_uses_standard_envelope() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login", json={"email": "not-an-email", "password": "x"}
        )
    body = response.json()
    assert response.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["path"] == "/api/v1/auth/login"
    assert body["request_id"]


def test_cors_allows_configured_origin_only() -> None:
    with TestClient(app) as client:
        allowed = client.options(
            "/api/v1/health/live",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
        )
        rejected = client.options(
            "/api/v1/health/live",
            headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "GET"},
        )
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-origin" not in rejected.headers
