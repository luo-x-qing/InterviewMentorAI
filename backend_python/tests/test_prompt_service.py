import pytest


@pytest.fixture
def mock_llm(mocker):
    mock = mocker.MagicMock()
    mock.call = mocker.AsyncMock(return_value="llm_reply")
    return mock


@pytest.fixture
def prompt_service(mock_llm):
    from app.services.prompt_service import PromptService

    return PromptService(llm_client=mock_llm)


class TestPromptService:
    @pytest.mark.asyncio
    async def test_transcribe_interview(self, prompt_service, mock_llm):
        result = await prompt_service.transcribe_interview("/path/audio.wav")
        assert result == "llm_reply"
        system, user = mock_llm.call.call_args[0]
        assert "转录" in system
        assert "/path/audio.wav" in user

    @pytest.mark.asyncio
    async def test_parse_dialogue(self, prompt_service, mock_llm):
        result = await prompt_service.parse_dialogue("面试官：你好")
        assert result == "llm_reply"
        system, user = mock_llm.call.call_args[0]
        assert "JSON" in system or "json" in system
        assert "面试官" in user

    @pytest.mark.asyncio
    async def test_evaluate_answer_without_ref(self, prompt_service, mock_llm):
        result = await prompt_service.evaluate_answer("什么是Java", "Java是一种语言")
        assert result == "llm_reply"
        system, user = mock_llm.call.call_args[0]
        assert "评估" in system
        assert "什么是Java" in user

    @pytest.mark.asyncio
    async def test_evaluate_answer_with_ref(self, prompt_service, mock_llm):
        result = await prompt_service.evaluate_answer("什么是Java", "Java是一种语言", ref_text="参考资料内容")
        assert result == "llm_reply"
        system, user = mock_llm.call.call_args[0]
        assert "参考资料内容" in user

    @pytest.mark.asyncio
    async def test_generate_report(self, prompt_service, mock_llm):
        result = await prompt_service.generate_report("评估结果文本")
        assert result == "llm_reply"
        system, user = mock_llm.call.call_args[0]
        assert "报告" in system
        assert "评估结果文本" in user
