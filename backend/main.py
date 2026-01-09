"""
Code Archaeologist - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Code Archaeologist API",
    description="Graph-RAG API for code analysis",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Code Archaeologist API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
