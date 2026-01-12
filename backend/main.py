"""
Code Archaeologist - Main FastAPI Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
from pathlib import Path

from database import KuzuDB
from parser import TreeSitterParser
from ingestion import IngestionService, JobStatus as IngestionJobStatus
from rag_service import RAGService

from contextlib import asynccontextmanager

# Initialize services (will be done on startup)
db: Optional[KuzuDB] = None
parser: Optional[TreeSitterParser] = None
ingestion_service: Optional[IngestionService] = None
rag_service: Optional[RAGService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global db, parser, ingestion_service, rag_service
    
    # Startup
    db_path = Path("./data/code_graph")
    db = KuzuDB(str(db_path))
    parser = TreeSitterParser()
    ingestion_service = IngestionService(db, parser, "./repos")
    
    # Try to initialize RAG service with Ollama, fall back to mock mode if unavailable
    try:
        rag_service = RAGService(db, model_name="llama3", mock_mode=False)
    except Exception as e:
        print(f"⚠️  Ollama not available, using mock mode: {e}")
        rag_service = RAGService(db, model_name="llama3", mock_mode=True)
    
    print("✓ Services initialized successfully")
    
    yield
    
    # Shutdown
    if db:
        db.close()
    print("✓ Services shut down successfully")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Code Archaeologist API",
    description="Graph-RAG API for code analysis",
    version="1.0.0",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Request/Response Models ==========

class IngestRequest(BaseModel):
    """Request model for repository ingestion"""
    repo_url: str


class JobStatus(BaseModel):
    """Status of an ingestion job"""
    status: str  # "success" | "error" | "in_progress"
    message: str
    job_id: Optional[str] = None
    files_processed: int = 0
    nodes_created: int = 0
    edges_created: int = 0


class GraphNode(BaseModel):
    """Node in the graph visualization"""
    id: str
    type: str  # "file" | "class" | "function"
    data: Dict
    position: Dict[str, float]


class GraphEdge(BaseModel):
    """Edge in the graph visualization"""
    id: str
    source: str
    target: str
    type: str  # "CONTAINS" | "DEFINES" | "CALLS"


class GraphData(BaseModel):
    """Complete graph data for visualization"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class ChatRequest(BaseModel):
    """Request model for chat queries"""
    prompt: str


class ChatResponse(BaseModel):
    """Response model for chat queries"""
    response: str
    node_ids: List[str]


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None


# ========== API Endpoints ==========

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Code Archaeologist API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if db else "disconnected",
        "parser": "ready" if parser else "not ready",
        "ingestion": "ready" if ingestion_service else "not ready",
        "rag": "ready" if rag_service else "not ready"
    }


@app.post("/ingest", response_model=JobStatus)
async def ingest_repository(request: IngestRequest):
    """
    Ingest a GitHub repository into the knowledge graph.
    
    Args:
        request: IngestRequest with repo_url
        
    Returns:
        JobStatus with ingestion results
        
    Raises:
        HTTPException: If ingestion fails
    """
    if not ingestion_service:
        raise HTTPException(status_code=500, detail="Ingestion service not initialized")
    
    try:
        # Run ingestion in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            ingestion_service.ingest_repository,
            request.repo_url
        )
        
        # Convert IngestionJobStatus to JobStatus
        job_status = JobStatus(
            status=result.status,
            message=result.message,
            job_id=result.job_id,
            files_processed=result.files_processed,
            nodes_created=result.nodes_created,
            edges_created=result.edges_created
        )
        
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.message)
        
        return job_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")


@app.get("/graph", response_model=GraphData)
async def get_graph():
    """
    Retrieve the complete knowledge graph for visualization.
    
    Returns:
        GraphData with nodes and edges formatted for React Flow
        
    Raises:
        HTTPException: If graph retrieval fails
    """
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    try:
        # Get all nodes and edges from database
        all_nodes = db.get_all_nodes()
        all_edges = db.get_all_edges()
        
        # Format nodes for React Flow
        graph_nodes = []
        for i, node in enumerate(all_nodes):
            node_type = node.get('_label', 'unknown').lower()
            node_id = node.get('id', f'node_{i}')
            
            # Calculate position (simple grid layout)
            x = (i % 10) * 200
            y = (i // 10) * 150
            
            # Create node data
            graph_node = GraphNode(
                id=node_id,
                type=node_type,
                data={
                    "label": node.get('name', node.get('path', node_id)),
                    **{k: v for k, v in node.items() if k not in ['_label', 'id']}
                },
                position={"x": x, "y": y}
            )
            graph_nodes.append(graph_node)
        
        # Format edges for React Flow
        graph_edges = []
        for i, edge in enumerate(all_edges):
            edge_type = edge.get('_label', 'UNKNOWN')
            source_id = edge.get('_src', f'unknown_src_{i}')
            target_id = edge.get('_dst', f'unknown_dst_{i}')
            
            graph_edge = GraphEdge(
                id=f"edge_{i}",
                source=source_id,
                target=target_id,
                type=edge_type
            )
            graph_edges.append(graph_edge)
        
        return GraphData(nodes=graph_nodes, edges=graph_edges)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph retrieval error: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a natural language query about the codebase using RAG.
    
    Args:
        request: ChatRequest with prompt
        
    Returns:
        ChatResponse with response text and referenced node IDs
        
    Raises:
        HTTPException: If query processing fails
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="RAG service not initialized")
    
    try:
        # Run RAG query processing in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            rag_service.process_query,
            request.prompt
        )
        
        return ChatResponse(
            response=result.response,
            node_ids=result.node_ids
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing error: {str(e)}")


# ========== Error Handlers ==========

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return ErrorResponse(
        error="Internal server error",
        detail=str(exc)
    )

