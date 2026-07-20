import pytest
from app.models.schemas import (
    AnalysisRequest,
    AnalysisStatus,
    AgentState,
    Speaker,
    DialogueItem,
    EvaluationLevel,
    EvaluationResult,
)


@pytest.fixture
def mock_prompt_service(mocker):
    mock = mocker.MagicMock()
    mock.transcribe_interview.return_value = "面试官：请做自我介绍\n候选人：我叫张三"
    mock.parse_dialogue.return_value = (
        '[{"speaker": "面试官", "content": "请做自我介绍"},'
        '{"speaker": "面试者", "content": "我叫张三"}]'
    )
    mock.generate_report.return_value = "# 面试复盘报告\n\n内容"
    return mock


@pytest.fixture
def mock_rag_mcp(mocker):
    mock = mocker.MagicMock()
    mock.rag_enhance_evaluate.return_value = (
        '{"score": 85, "level": "PROFICIENT", "strengths": "好", "weaknesses": "", "correction": "", "knowledge_points": ""}'
    )
    return mock


@pytest.fixture
def pipeline(mock_prompt_service, mock_rag_mcp):
    from app.services.agent_pipeline import AgentPipeline

    return AgentPipeline(prompt_service=mock_prompt_service, rag_mcp=mock_rag_mcp)


class TestRun:
    def test_success_path(self, pipeline, mock_prompt_service):
        req = AnalysisRequest(interview_id=1, audio_file_path="/path/audio.wav")
        resp = pipeline.run(req)
        assert resp.status == AnalysisStatus.COMPLETED
        assert resp.interview_id == 1
        assert resp.report == "# 面试复盘报告\n\n内容"
        mock_prompt_service.transcribe_interview.assert_called_once()

    def test_failure_path(self, pipeline, mock_prompt_service):
        mock_prompt_service.transcribe_interview.side_effect = Exception("ASR失败")
        req = AnalysisRequest(interview_id=1, audio_file_path="/path/audio.wav")
        resp = pipeline.run(req)
        assert resp.status == AnalysisStatus.FAILED
        assert "ASR失败" in resp.error


class TestParseDialogue:
    def test_valid_json(self, pipeline):
        state = AgentState(interview_id=1, audio_file_path="", raw_transcript="test")
        dialog = pipeline._parse_dialogue(state)
        assert len(dialog) == 2
        assert dialog[0].speaker == Speaker.INTERVIEWER
        assert dialog[1].speaker == Speaker.CANDIDATE

    def test_markdown_wrapped_json(self, pipeline, mock_prompt_service):
        mock_prompt_service.parse_dialogue.return_value = (
            '```json\n[{"speaker": "面试官", "content": "你好"}]\n```'
        )
        state = AgentState(interview_id=1, audio_file_path="", raw_transcript="test")
        dialog = pipeline._parse_dialogue(state)
        assert len(dialog) == 1

    def test_invalid_json_fallback(self, pipeline, mock_prompt_service):
        mock_prompt_service.parse_dialogue.return_value = "不是JSON"
        state = AgentState(interview_id=1, audio_file_path="", raw_transcript="面试官：你好\n候选人：嗨")
        dialog = pipeline._parse_dialogue(state)
        assert len(dialog) == 2
        assert dialog[0].speaker == Speaker.INTERVIEWER


class TestEvaluateAnswers:
    def test_pairing(self, pipeline, mock_rag_mcp):
        state = AgentState(interview_id=1, audio_file_path="")
        state.dialogue_list = [
            DialogueItem(speaker=Speaker.INTERVIEWER, content="什么是Java"),
            DialogueItem(speaker=Speaker.CANDIDATE, content="一种语言"),
            DialogueItem(speaker=Speaker.INTERVIEWER, content="什么是Python"),
            DialogueItem(speaker=Speaker.CANDIDATE, content="另一种语言"),
        ]
        results = pipeline._evaluate_answers(state)
        assert len(results) == 2
        assert results[0].question == "什么是Java"
        assert results[1].question == "什么是Python"

    def test_no_answer_skipped(self, pipeline, mock_rag_mcp):
        state = AgentState(interview_id=1, audio_file_path="")
        state.dialogue_list = [
            DialogueItem(speaker=Speaker.INTERVIEWER, content="什么是Java"),
        ]
        results = pipeline._evaluate_answers(state)
        assert len(results) == 0


class TestEvaluateSingle:
    def test_success(self, pipeline, mock_rag_mcp):
        result = pipeline._evaluate_single("什么是Java", "一种语言")
        assert result is not None
        assert result.score == 85
        assert result.level == EvaluationLevel.PROFICIENT

    def test_invalid_json(self, pipeline, mock_rag_mcp):
        mock_rag_mcp.rag_enhance_evaluate.return_value = "invalid"
        result = pipeline._evaluate_single("什么是Java", "一种语言")
        assert result is None


class TestGenerateReport:
    def test_aggregates_evaluations(self, pipeline, mock_prompt_service):
        state = AgentState(interview_id=1, audio_file_path="")
        state.evaluation_list = [
            EvaluationResult(
                question="q1", answer="a1", score=90, level=EvaluationLevel.PROFICIENT,
                strengths="好", weaknesses="",
            ),
        ]
        report = pipeline._generate_report(state)
        assert report == "# 面试复盘报告\n\n内容"
        called_text = mock_prompt_service.generate_report.call_args[0][0]
        assert "q1" in called_text
        assert "90" in called_text
