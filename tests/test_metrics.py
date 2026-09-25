from fastapi.testclient import TestClient

from app.main import app
from app.core.metrics import HTTP_REQUESTS_TOTAL, TOOL_EXECUTIONS_TOTAL, record_tool_execution

client = TestClient(app)


def test_metrics_endpoint_returns_prometheus_format():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text
    assert "voiceagent_app_info" in body
    assert "voiceagent_http_requests_total" in body
    assert "python_info" in body


def test_http_requests_tracked_by_middleware():
    health_res = client.get("/health")
    assert health_res.status_code == 200

    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200
    body = metrics_res.text
    assert 'endpoint="/health"' in body
    assert 'status_code="200"' in body


def test_metrics_json_format():
    response = client.get("/metrics?format=json")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_info" in data
    assert data["app_info"]["app_name"] == "Voice Agent API"


def test_unmatched_route_metric_labeled_safe():
    res_404 = client.get("/random-route-that-does-not-exist-12345")
    assert res_404.status_code == 404

    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200
    body = metrics_res.text
    assert 'endpoint="not_found"' in body
    assert 'status_code="404"' in body


def test_tool_execution_metric_recorded():
    record_tool_execution("test_tool", "success")
    record_tool_execution("test_tool", "error")

    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200
    body = metrics_res.text
    assert 'voiceagent_tool_executions_total{status="success",tool_name="test_tool"}' in body
    assert 'voiceagent_tool_executions_total{status="error",tool_name="test_tool"}' in body
