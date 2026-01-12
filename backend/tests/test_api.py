"""
Tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil

# Import app and initialize services before creating client
import main


@pytest.fixture(scope="module")
def client():
    """Create test client with initialized services"""
    # Initialize services manually for testing
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test_db"
    
    from database import KuzuDB
    from parser import TreeSitterParser
    from ingestion import IngestionService
    from rag_service import RAGService
    
    main.db = KuzuDB(str(db_path))
    main.parser = TreeSitterParser()
    main.ingestion_service = IngestionService(main.db, main.parser, str(temp_dir / "repos"))
    main.rag_service = RAGService(main.db, mock_mode=True)  # Use mock mode for testing
    
    client = TestClient(main.app)
    
    yield client
    
    # Cleanup
    main.db.close()
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


class TestAPIEndpoints:
    """Test suite for API endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "running"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "parser" in data
        assert "ingestion" in data
        assert "rag" in data
    
    def test_graph_endpoint_empty(self, client):
        """Test graph endpoint with empty database"""
        response = client.get("/graph")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)
    
    def test_chat_endpoint(self, client):
        """Test chat endpoint"""
        response = client.post(
            "/chat",
            json={"prompt": "What is in the codebase?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "node_ids" in data
        assert isinstance(data["response"], str)
        assert isinstance(data["node_ids"], list)
    
    def test_ingest_endpoint_invalid_url(self, client):
        """Test ingest endpoint with invalid URL"""
        response = client.post(
            "/ingest",
            json={"repo_url": "not-a-valid-url"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid repository URL" in data["detail"]
    
    def test_ingest_endpoint_non_github_url(self, client):
        """Test ingest endpoint with non-GitHub URL"""
        response = client.post(
            "/ingest",
            json={"repo_url": "https://example.com/repo"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_chat_endpoint_missing_prompt(self, client):
        """Test chat endpoint with missing prompt"""
        response = client.post("/chat", json={})
        assert response.status_code == 422  # Validation error
    
    def test_ingest_endpoint_missing_repo_url(self, client):
        """Test ingest endpoint with missing repo_url"""
        response = client.post("/ingest", json={})
        assert response.status_code == 422  # Validation error
    
    def test_graph_endpoint_response_format(self, client):
        """Test that graph endpoint returns correct format"""
        response = client.get("/graph")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "nodes" in data
        assert "edges" in data
        
        # If there are nodes, verify their structure
        if data["nodes"]:
            node = data["nodes"][0]
            assert "id" in node
            assert "type" in node
            assert "data" in node
            assert "position" in node
            assert "x" in node["position"]
            assert "y" in node["position"]
        
        # If there are edges, verify their structure
        if data["edges"]:
            edge = data["edges"][0]
            assert "id" in edge
            assert "source" in edge
            assert "target" in edge
            assert "type" in edge
    
    def test_chat_endpoint_response_format(self, client):
        """Test that chat endpoint returns correct format"""
        response = client.post(
            "/chat",
            json={"prompt": "test query"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "response" in data
        assert "node_ids" in data
        assert isinstance(data["response"], str)
        assert isinstance(data["node_ids"], list)
        assert len(data["response"]) > 0
