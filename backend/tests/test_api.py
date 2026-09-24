"""Tests for FastAPI endpoints — health, status, usage, ask (with mocked LLM)."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def mock_google_clients(monkeypatch):
    """Isolate constructors as well as queries, including fallback imports."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-used")
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    # Never load a developer's real credentials into the test process.
    with patch("dotenv.load_dotenv"):
        import main

    monkeypatch.setattr(main, "AI_PROVIDER", "gemini")
    with (
        patch("llama_index.llms.google_genai.GoogleGenAI") as llm,
        patch("llama_index.embeddings.google_genai.GoogleGenAIEmbedding") as embedding,
        patch.object(main, "LlamaSettings"),
        patch.object(main, "ChromaVectorStore"),
    ):
        # Settings setters normally validate concrete LlamaIndex objects. Keep
        # these per-test mocks out of the process-wide real Settings singleton.
        yield llm, embedding


@pytest.fixture(autouse=True)
def reset_tracker():
    """Reset the usage tracker singleton before each test."""
    from usage_tracker import tracker
    tracker._reset()
    yield


@pytest.fixture
def client():
    """Create a test client with mocked vector store."""
    from main import app
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "notice" in data


class TestDebugConfigEndpoint:
    def test_debug_config_returns_settings(self, client):
        r = client.get("/debug-config")
        assert r.status_code == 200
        data = r.json()
        assert "ai_provider" in data
        assert "chroma_db_path" in data
        assert "regulations" in data
        assert "default_regulation" in data
        assert "google_key_present" in data


class TestUsageEndpoint:
    def test_usage_returns_dashboard(self, client):
        r = client.get("/usage")
        assert r.status_code == 200
        data = r.json()
        assert "active_model" in data
        assert "summary" in data
        assert "models" in data
        assert data["fallback_enabled"] is True

    def test_usage_starts_at_zero(self, client):
        r = client.get("/usage")
        data = r.json()
        assert data["summary"]["total_requests"] == 0


class TestStatusEndpoint:
    def test_status_returns_model_info(self, client):
        r = client.get("/status")
        assert r.status_code == 200
        data = r.json()
        assert "active_model" in data
        assert "model_tier" in data
        assert "fallback_available" in data
        assert "requests_used" in data
        assert "requests_remaining" in data
        assert "models" in data

    def test_status_shows_all_models(self, client):
        from usage_tracker import MODEL_CHAIN
        r = client.get("/status")
        data = r.json()
        assert len(data["models"]) == len(MODEL_CHAIN)
        for model_info in data["models"]:
            assert "name" in model_info
            assert "tier" in model_info
            assert "active" in model_info
            assert "requests_used" in model_info
            assert "requests_limit" in model_info


class TestAskEndpoint:
    def test_ask_rejects_empty_question(self, client):
        r = client.post("/ask", json={"question": ""})
        assert r.status_code == 400

    def test_ask_rejects_whitespace_question(self, client):
        r = client.post("/ask", json={"question": "   "})
        assert r.status_code == 400

    def test_ask_requires_question_field(self, client):
        r = client.post("/ask", json={})
        assert r.status_code == 422  # Pydantic validation error

    @patch("main.chromadb")
    @patch("main.VectorStoreIndex")
    @patch("main.os.path.exists", return_value=True)
    def test_ask_returns_expected_format(self, mock_exists, mock_index_cls, mock_chroma, client, mock_google_clients):
        """Test /ask with fully mocked LLM — no real API call."""
        # Mock the ChromaDB chain
        mock_collection = MagicMock()
        mock_chroma_client = MagicMock()
        mock_chroma_client.get_collection.return_value = mock_collection
        mock_chroma.PersistentClient.return_value = mock_chroma_client

        # Mock source node
        mock_node = MagicMock()
        mock_node.node.get_content.return_value = "Article 17 provides the right to erasure."
        mock_node.node.metadata = {"source": "gdpr.txt"}
        mock_node.score = 0.92

        # Mock query response
        mock_response = MagicMock()
        mock_response.__str__ = lambda self: "The right to erasure is defined in Article 17."
        mock_response.source_nodes = [mock_node]

        # Mock index and query engine
        mock_index = MagicMock()
        mock_query_engine = MagicMock()
        mock_query_engine.query.return_value = mock_response
        mock_index.as_query_engine.return_value = mock_query_engine
        mock_index_cls.from_vector_store.return_value = mock_index

        r = client.post("/ask", json={"question": "What is the right to erasure?"})
        assert r.status_code == 200
        data = r.json()

        # Verify response structure
        assert "answer" in data
        assert "question" in data
        assert "model_used" in data
        assert "fallback_used" in data
        assert "sources" in data
        assert "usage" in data
        assert "notice" in data

        # Verify content
        assert data["question"] == "What is the right to erasure?"
        assert "Article 17" in data["answer"]
        assert data["fallback_used"] is False
        assert len(data["sources"]) == 1
        assert data["sources"][0]["score"] == 0.92

        # Verify usage was tracked
        assert data["usage"]["requests_today"] == 1

        llm, embedding = mock_google_clients
        llm.assert_called_once()
        assert llm.call_args.kwargs["api_key"] == "test-key-not-used"
        embedding.assert_called_once_with(
            model_name="gemini-embedding-001", api_key="test-key-not-used"
        )

    @patch("main.chromadb")
    @patch("main.VectorStoreIndex")
    @patch("main.os.path.exists", return_value=True)
    def test_ask_tracks_usage_across_requests(self, mock_exists, mock_index_cls, mock_chroma, client):
        """Multiple requests should increment usage counter."""
        mock_collection = MagicMock()
        mock_chroma_client = MagicMock()
        mock_chroma_client.get_collection.return_value = mock_collection
        mock_chroma.PersistentClient.return_value = mock_chroma_client

        mock_node = MagicMock()
        mock_node.node.get_content.return_value = "Test content"
        mock_node.node.metadata = {}
        mock_node.score = 0.8

        mock_response = MagicMock()
        mock_response.__str__ = lambda self: "Test answer"
        mock_response.source_nodes = [mock_node]

        mock_index = MagicMock()
        mock_query_engine = MagicMock()
        mock_query_engine.query.return_value = mock_response
        mock_index.as_query_engine.return_value = mock_query_engine
        mock_index_cls.from_vector_store.return_value = mock_index

        # Make 3 requests
        for i in range(3):
            r = client.post("/ask", json={"question": f"Question {i}"})
            assert r.status_code == 200

        # Check usage
        r = client.get("/usage")
        assert r.json()["summary"]["total_requests"] == 3

    @patch("main.os.path.exists", return_value=False)
    def test_ask_returns_503_when_no_vectordb(self, mock_exists, client):
        r = client.post("/ask", json={"question": "test"})
        assert r.status_code == 503
        assert "Vector DB" in r.json()["detail"]


class TestAskFallbackBehavior:
    @patch("main.chromadb")
    @patch("main.VectorStoreIndex")
    @patch("main.os.path.exists", return_value=True)
    def test_ask_succeeds_after_mocked_model_fallback(self, mock_exists, mock_index_cls, mock_chroma, client, mock_google_clients):
        """A fallback must construct another mock, never a real Google client."""
        from usage_tracker import MODEL_CHAIN

        response = MagicMock()
        response.__str__ = lambda self: "A cited answer from the fallback model."
        response.source_nodes = []
        engine = mock_index_cls.from_vector_store.return_value.as_query_engine.return_value
        engine.query.side_effect = [Exception("429 Resource exhausted"), response]

        r = client.post("/ask", json={"question": "What is HIPAA?"})

        assert r.status_code == 200
        data = r.json()
        assert data["fallback_used"] is True
        assert data["model_used"] == MODEL_CHAIN[1]["name"]
        assert data["usage"]["requests_today"] == 1
        assert engine.query.call_count == 2
        llm, embedding = mock_google_clients
        assert [call.kwargs["model"] for call in llm.call_args_list] == [
            MODEL_CHAIN[0]["name"], MODEL_CHAIN[1]["name"]
        ]
        assert all(call.kwargs["api_key"] == "test-key-not-used" for call in llm.call_args_list)
        embedding.assert_called_once()

    @patch("main.chromadb")
    @patch("main.VectorStoreIndex")
    @patch("main.os.path.exists", return_value=True)
    def test_ask_returns_429_on_rate_limit_all_exhausted(self, mock_exists, mock_index_cls, mock_chroma, client):
        """When LLM raises 429 and no fallback works, return 429."""
        mock_collection = MagicMock()
        mock_chroma_client = MagicMock()
        mock_chroma_client.get_collection.return_value = mock_collection
        mock_chroma.PersistentClient.return_value = mock_chroma_client

        mock_index = MagicMock()
        mock_query_engine = MagicMock()
        mock_query_engine.query.side_effect = Exception("429 Resource exhausted")
        mock_index.as_query_engine.return_value = mock_query_engine
        mock_index_cls.from_vector_store.return_value = mock_index

        r = client.post("/ask", json={"question": "test question"})
        # Should get 429 (either direct or after fallback also fails)
        assert r.status_code == 429

    @patch("main.chromadb")
    @patch("main.VectorStoreIndex")
    @patch("main.os.path.exists", return_value=True)
    def test_ask_returns_500_on_non_rate_limit_error(self, mock_exists, mock_index_cls, mock_chroma, client):
        """Non-rate-limit errors should return 500."""
        mock_collection = MagicMock()
        mock_chroma_client = MagicMock()
        mock_chroma_client.get_collection.return_value = mock_collection
        mock_chroma.PersistentClient.return_value = mock_chroma_client

        mock_index = MagicMock()
        mock_query_engine = MagicMock()
        mock_query_engine.query.side_effect = Exception("Connection timeout")
        mock_index.as_query_engine.return_value = mock_query_engine
        mock_index_cls.from_vector_store.return_value = mock_index

        r = client.post("/ask", json={"question": "test question"})
        assert r.status_code == 500
