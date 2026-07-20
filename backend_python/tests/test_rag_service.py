import pytest
from app.models.schemas import RagDoc, RagRetrievalResult


@pytest.fixture
def mock_vector_db(mocker):
    mock = mocker.MagicMock()
    mock.search_hybrid.return_value = [
        RagDoc(doc_id=1, title="t1", content="Java HashMap底层原理", source="src", score=0.85),
    ]
    mock.search_vector.return_value = [
        RagDoc(doc_id=1, title="t1", content="Java HashMap底层原理", source="src", score=0.85),
    ]
    return mock


@pytest.fixture
def mock_llm_client(mocker):
    mock = mocker.MagicMock()
    mock.client.embeddings.create.return_value.data = [
        mocker.MagicMock(embedding=[0.1] * 1024)
    ]
    return mock


@pytest.fixture
def rag_service(mock_vector_db, mock_llm_client):
    from app.services.rag_service import RagService

    return RagService(vector_db=mock_vector_db, llm_service=mock_llm_client)


class TestSplitChunks:
    def test_fixed_chunk(self, rag_service):
        text = "A" * 200
        chunks = rag_service.split_fixed_chunk(text, chunk_size=50, chunk_overlap=10)
        assert len(chunks) == 5

    def test_paragraph_chunk(self, rag_service):
        text = "\n\n".join(["第{}段内容".format(i) for i in range(10)])
        chunks = rag_service.split_paragraph_chunk(text, chunk_size=20)
        assert len(chunks) >= 2

    def test_semantic_chunk(self, rag_service):
        text = "句子一。句子二。句子三。"
        chunks = rag_service.split_semantic_chunk(text, chunk_size=50)
        assert len(chunks) >= 1

    def test_split_chunks_dispatcher(self, rag_service):
        text = "第一段。第二段。第三段。"
        assert len(rag_service.split_chunks(text, "fixed")) >= 1
        assert len(rag_service.split_chunks(text, "paragraph")) >= 1
        assert len(rag_service.split_chunks(text, "semantic")) >= 1


class TestGetTextEmbedding:
    def test_embedding_calls_api(self, rag_service, mock_llm_client):
        emb = rag_service.get_text_embedding("测试文本")
        assert len(emb) == 1024
        mock_llm_client.client.embeddings.create.assert_called_once()

    def test_embedding_cache_hit(self, rag_service, mock_llm_client):
        emb1 = rag_service.get_text_embedding("测试文本")
        emb2 = rag_service.get_text_embedding("测试文本")
        assert emb1 == emb2
        assert mock_llm_client.client.embeddings.create.call_count == 1


class TestRetrieveByQuestion:
    def test_hybrid_retrieval(self, rag_service, mock_vector_db):
        result = rag_service.retrieve_by_question("Java HashMap", use_hybrid=True)
        assert len(result.docs) == 1
        mock_vector_db.search_hybrid.assert_called_once()

    def test_vector_only_retrieval(self, rag_service, mock_vector_db):
        result = rag_service.retrieve_by_question("Java HashMap", use_hybrid=False)
        assert len(result.docs) == 1
        mock_vector_db.search_vector.assert_called_once()

    def test_close_clears_cache(self, rag_service):
        rag_service.get_text_embedding("测试文本")
        assert len(rag_service._embedding_cache) > 0
        rag_service.close()
        assert len(rag_service._embedding_cache) == 0
