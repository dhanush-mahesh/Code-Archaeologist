"""
Ingestion Service for Code Archaeologist
Handles repository cloning, parsing, and database insertion
"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
from urllib.parse import urlparse
from pydantic import BaseModel

from parser import TreeSitterParser
from database import KuzuDB, FileNode, ClassNode, FunctionNode, Edge


class JobStatus(BaseModel):
    """Status of an ingestion job"""
    status: str  # "success" | "error" | "in_progress"
    message: str
    job_id: Optional[str] = None
    files_processed: int = 0
    nodes_created: int = 0
    edges_created: int = 0


class IngestionService:
    """Service for ingesting GitHub repositories into the knowledge graph"""
    
    def __init__(self, db: KuzuDB, parser: TreeSitterParser, repo_dir: str = "./repos"):
        """
        Initialize the ingestion service.
        
        Args:
            db: KuzuDB database instance
            parser: TreeSitterParser instance
            repo_dir: Directory to store cloned repositories
        """
        self.db = db
        self.parser = parser
        self.repo_dir = Path(repo_dir)
        self.repo_dir.mkdir(exist_ok=True)
    
    def validate_repo_url(self, repo_url: str) -> bool:
        """
        Validate that a repository URL is valid.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            True if valid, False otherwise
        """
        try:
            parsed = urlparse(repo_url)
            
            # Check if it's a valid URL
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Check if it's a GitHub URL
            if 'github.com' not in parsed.netloc:
                return False
            
            # Check if path looks like a repo (owner/repo)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                return False
            
            return True
            
        except Exception:
            return False
    
    def clone_repo(self, repo_url: str) -> Tuple[bool, Optional[Path], str]:
        """
        Clone a GitHub repository to local storage.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Tuple of (success, repo_path, message)
        """
        # Validate URL
        if not self.validate_repo_url(repo_url):
            return False, None, f"Invalid repository URL: {repo_url}"
        
        try:
            # Extract repo name from URL
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip('/').split('/')
            repo_name = path_parts[-1].replace('.git', '')
            
            # Create local path
            local_path = self.repo_dir / repo_name
            
            # Remove existing directory if it exists
            if local_path.exists():
                shutil.rmtree(local_path)
            
            # Clone the repository
            result = subprocess.run(
                ['git', 'clone', repo_url, str(local_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error during cloning"
                return False, None, f"Failed to clone repository: {error_msg}"
            
            return True, local_path, f"Successfully cloned repository to {local_path}"
            
        except subprocess.TimeoutExpired:
            return False, None, "Repository cloning timed out (5 minutes)"
        except Exception as e:
            return False, None, f"Error cloning repository: {str(e)}"
    
    def get_supported_files(self, repo_path: Path) -> List[Path]:
        """
        Get all supported files (Python and JavaScript) from repository.
        
        Args:
            repo_path: Path to cloned repository
            
        Returns:
            List of file paths
        """
        supported_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.mjs'}
        supported_files = []
        
        # Walk through directory tree
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories and common non-code directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__', 'dist', 'build']]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in supported_extensions:
                    supported_files.append(file_path)
        
        return supported_files
    
    def parse_repository(self, repo_path: Path) -> Tuple[List[FileNode], List[ClassNode], List[FunctionNode], List[Edge], List[str]]:
        """
        Parse all supported files in a repository.
        
        Args:
            repo_path: Path to cloned repository
            
        Returns:
            Tuple of (all_files, all_classes, all_functions, all_edges, errors)
        """
        all_files = []
        all_classes = []
        all_functions = []
        all_edges = []
        errors = []
        
        # Get all supported files
        supported_files = self.get_supported_files(repo_path)
        
        # Parse each file
        for file_path in supported_files:
            try:
                files, classes, functions, edges = self.parser.parse_file(file_path)
                
                all_files.extend(files)
                all_classes.extend(classes)
                all_functions.extend(functions)
                all_edges.extend(edges)
                
            except Exception as e:
                error_msg = f"Error parsing {file_path}: {str(e)}"
                errors.append(error_msg)
                print(f"⚠️  {error_msg}")
                # Continue processing other files
                continue
        
        return all_files, all_classes, all_functions, all_edges, errors
    
    def insert_into_database(self, files: List[FileNode], classes: List[ClassNode], 
                            functions: List[FunctionNode], edges: List[Edge]) -> Tuple[bool, str, int, int]:
        """
        Insert parsed nodes and edges into database.
        
        Args:
            files: List of file nodes
            classes: List of class nodes
            functions: List of function nodes
            edges: List of edges
            
        Returns:
            Tuple of (success, message, nodes_inserted, edges_inserted)
        """
        nodes_inserted = 0
        edges_inserted = 0
        
        try:
            # Insert file nodes
            for file_node in files:
                if self.db.insert_file(file_node):
                    nodes_inserted += 1
                else:
                    print(f"⚠️  Failed to insert file: {file_node.id}")
            
            # Insert class nodes
            for class_node in classes:
                if self.db.insert_class(class_node):
                    nodes_inserted += 1
                else:
                    print(f"⚠️  Failed to insert class: {class_node.id}")
            
            # Insert function nodes
            for func_node in functions:
                if self.db.insert_function(func_node):
                    nodes_inserted += 1
                else:
                    print(f"⚠️  Failed to insert function: {func_node.id}")
            
            # Insert edges
            for edge in edges:
                success = False
                if edge.edge_type == "CONTAINS_CLASS":
                    success = self.db.insert_contains(edge.source, edge.target, "Class")
                elif edge.edge_type == "CONTAINS_FUNCTION":
                    success = self.db.insert_contains(edge.source, edge.target, "Function")
                elif edge.edge_type == "DEFINES":
                    success = self.db.insert_defines(edge.source, edge.target)
                elif edge.edge_type == "CALLS":
                    success = self.db.insert_calls(edge.source, edge.target)
                
                if success:
                    edges_inserted += 1
                else:
                    print(f"⚠️  Failed to insert edge: {edge.edge_type} from {edge.source} to {edge.target}")
            
            message = f"Inserted {nodes_inserted} nodes and {edges_inserted} edges"
            return True, message, nodes_inserted, edges_inserted
            
        except Exception as e:
            return False, f"Database insertion error: {str(e)}", nodes_inserted, edges_inserted
    
    def ingest_repository(self, repo_url: str) -> JobStatus:
        """
        Main ingestion method: clone, parse, and store repository.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            JobStatus with results
        """
        # Step 1: Clone repository
        success, repo_path, message = self.clone_repo(repo_url)
        if not success:
            return JobStatus(
                status="error",
                message=message,
                files_processed=0,
                nodes_created=0,
                edges_created=0
            )
        
        try:
            # Step 2: Parse repository
            files, classes, functions, edges, errors = self.parse_repository(repo_path)
            
            files_processed = len(self.get_supported_files(repo_path))
            
            # Step 3: Insert into database
            success, db_message, nodes_inserted, edges_inserted = self.insert_into_database(
                files, classes, functions, edges
            )
            
            if not success:
                return JobStatus(
                    status="error",
                    message=db_message,
                    files_processed=files_processed,
                    nodes_created=nodes_inserted,
                    edges_created=edges_inserted
                )
            
            # Build final message
            final_message = f"Successfully ingested repository. {db_message}. Processed {files_processed} files."
            if errors:
                final_message += f" {len(errors)} files had parsing errors."
            
            return JobStatus(
                status="success",
                message=final_message,
                files_processed=files_processed,
                nodes_created=nodes_inserted,
                edges_created=edges_inserted
            )
            
        except Exception as e:
            return JobStatus(
                status="error",
                message=f"Ingestion error: {str(e)}",
                files_processed=0,
                nodes_created=0,
                edges_created=0
            )
        finally:
            # Cleanup: optionally remove cloned repo
            # For now, we keep it for debugging
            pass
