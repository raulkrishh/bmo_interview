import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Point the app at a throwaway JSON file so tests never touch real data.
os.environ["TASK_STORE_PATH"] = tempfile.mktemp(suffix=".json")

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_tools():
    response = client.get("/api/tools")
    assert response.status_code == 200
    names = {tool["name"] for tool in response.json()}
    assert {"CalculatorTool", "TextProcessorTool", "WeatherMockTool"}.issubset(names)


def test_submit_and_fetch_history():
    response = client.post("/api/tasks", json={"task": "3 + 5"})
    assert response.status_code == 200
    body = response.json()
    assert body["final_output"] == "8"
    assert body["tools_used"] == ["CalculatorTool"]
    assert len(body["steps"]) > 0

    history = client.get("/api/tasks")
    assert history.status_code == 200
    assert any(t["id"] == body["id"] for t in history.json())


def test_get_single_task():
    submitted = client.post("/api/tasks", json={"task": "weather in Chicago"}).json()
    fetched = client.get(f"/api/tasks/{submitted['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == submitted["id"]


def test_get_missing_task_404():
    response = client.get("/api/tasks/does-not-exist")
    assert response.status_code == 404


def test_empty_task_rejected():
    response = client.post("/api/tasks", json={"task": ""})
    assert response.status_code == 422
