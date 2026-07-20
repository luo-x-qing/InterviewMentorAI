import pytest


@pytest.fixture
def mock_openai(mocker):
    mock_client = mocker.MagicMock()
    mock_chat = mocker.MagicMock()
    mock_completion = mocker.MagicMock()
    mock_choice = mocker.MagicMock()
    mock_message = mocker.MagicMock()

    mock_message.content = "测试回复"
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_chat.completions.create.return_value = mock_completion
    mock_client.chat = mock_chat

    mocker.patch("app.services.llm_client.OpenAI", return_value=mock_client)
    return mock_client


class TestLlmClient:
    def test_init_reads_settings(self, mock_openai):
        from app.services.llm_client import LlmClient

        client = LlmClient()
        assert client.model_name is not None
        assert client.api_key is not None

    def test_call_returns_text(self, mock_openai):
        from app.services.llm_client import LlmClient

        client = LlmClient()
        result = client.call("system", "user")
        assert result == "测试回复"

    def test_call_empty_reply(self, mock_openai):
        from app.services.llm_client import LlmClient

        mock_openai.chat.completions.create.return_value.choices[0].message.content = None
        client = LlmClient()
        result = client.call("system", "user")
        assert result == ""

    def test_call_raises_on_api_error(self, mock_openai):
        from app.services.llm_client import LlmClient

        mock_openai.chat.completions.create.side_effect = Exception("API Error")
        client = LlmClient()
        with pytest.raises(Exception, match="千问调用失败"):
            client.call("system", "user")
