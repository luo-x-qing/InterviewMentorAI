import pytest
from fastapi.testclient import TestClient

from app.models.schemas import AnalysisResponse, AnalysisStatus, EvaluationResult, EvaluationLevel


@pytest.fixture
def mock_agent_pipeline(mocker):
    mock = mocker.MagicMock()
    mock.run = mocker.AsyncMock(return_value=AnalysisResponse(
        status=AnalysisStatus.COMPLETED,
        interview_id=1,
        report="# 报告",
        evaluations=[
            EvaluationResult(
                question="q1", answer="a1", score=85, level=EvaluationLevel.PROFICIENT,
                strengths="好", weaknesses="",
            ),
        ],
    ))
    return mock


@pytest.fixture
def client(mock_agent_pipeline):
    from app.main import app

    app.dependency_overrides.clear()
    from app.main import get_agent_pipeline

    app.dependency_overrides[get_agent_pipeline] = lambda: mock_agent_pipeline
    return TestClient(app)


class TestAnalysisAPI:
    def test_analyze_success(self, client, mock_agent_pipeline):
        resp = client.post("/api/v1/analysis/analyze", json={
            "interview_id": 1,
            "audio_file_path": "/path/audio.wav",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "COMPLETED"
        assert data["report"] == "# 报告"
        mock_agent_pipeline.run.assert_called_once()

    def test_analyze_failure(self, client, mock_agent_pipeline):
        mock_agent_pipeline.run.return_value = AnalysisResponse(
            status=AnalysisStatus.FAILED,
            interview_id=1,
            error="流水线异常",
        )
        resp = client.post("/api/v1/analysis/analyze", json={
            "interview_id": 1,
            "audio_file_path": "/path/audio.wav",
        })
        assert resp.status_code == 500

    def test_analyze_invalid_request(self, client):
        resp = client.post("/api/v1/analysis/analyze", json={})
        assert resp.status_code == 422

    def test_health_check(self, client):
        resp = client.get("/api/v1/analysis/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
