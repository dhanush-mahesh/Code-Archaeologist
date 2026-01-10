"""
KùzuDB Database Wrapper
Handles graph database operations for Code Archaeologist
"""
import kuzu
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel


# Data Models
class FileNode(BaseModel):
    id: str
    path: str
    language: str


class ClassNode(BaseModel):
    id: str
    name: str
    start_line: int
    end_line: int
    file_path: str


class FunctionNode(BaseModel):
    id: str
    name: str
    args: str
    docstring: Optional[str] = None
    start_line: int
    end_line: int
    file_path: str


class Edge(BaseModel):
    id: str
    source: str
    target: str
    edge_type: str  # CONTAINS, DEFINES, CALLS


class KuzuDB:
    """Wrapper class for KùzuDB operations"""
    
    def __init__(self, db_path: str = "./data/code_graph"):
        """
        Initialize KùzuDB connection and create schema if needed.
        
        Args:
            db_path: Path to the database directory
        """
        # Create database directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        
        # Initialize schema
        self._init_schema()
    
    def _init_schema(self):
        """Create node and relationship tables if they don't exist"""
        try:
            # Create File node table
            try:
                self.conn.execute("MATCH (f:File) RETURN f LIMIT 1")
            except:
                self.conn.execute("""
                    CREATE NODE TABLE File(
                        id STRING,
                        path STRING,
                        language STRING,
                        PRIMARY KEY (id)
                    )
                """)
            
            # Create Class node table
            try:
                self.conn.execute("MATCH (c:Class) RETURN c LIMIT 1")
            except:
                self.conn.execute("""
                    CREATE NODE TABLE Class(
                        id STRING,
                        name STRING,
                        start_line INT64,
                        end_line INT64,
                        file_path STRING,
                        PRIMARY KEY (id)
                    )
                """)
            
            # Create Function node table
            try:
                self.conn.execute("MATCH (f:Function) RETURN f LIMIT 1")
            except:
                self.conn.execute("""
                    CREATE NODE TABLE Function(
                        id STRING,
                        name STRING,
                        args STRING,
                        docstring STRING,
                        start_line INT64,
                        end_line INT64,
                        file_path STRING,
                        PRIMARY KEY (id)
                    )
                """)
            
            # Create CONTAINS relationship table (File -> Class)
            try:
                self.conn.execute("MATCH (f:File)-[r:CONTAINS_CLASS]->(c:Class) RETURN r LIMIT 1")
            except:
                self.conn.execute("""
                    CREATE REL TABLE CONTAINS_CLASS(FROM File TO Class)
                """)
            
            # Create CONTAINS relationship table (File -> Function)
            try:
                self.conn.execute("MATCH (f:File)-[r:CONTAINS_FUNCTION]->(fn:Function) RETURN r LIMIT 1")
            except:
                self.conn.execute("""
                    CREATE REL TABLE CONTAINS_FUNCTION(FROM File TO Function)
                """)
            
            # Create DEFINES relationship table (Class -> Function)
            try:
                self.conn.execute("MATCH (c:Class)-[r:DEFINES]->(f:Function) RETURN r LIMIT 1")
            except:
                self.conn.execute("""
                    CREATE REL TABLE DEFINES(FROM Class TO Function)
                """)
            
            # Create CALLS relationship table (Function -> Function)
            try:
                self.conn.execute("MATCH (f1:Function)-[r:CALLS]->(f2:Function) RETURN r LIMIT 1")
            except:
                self.conn.execute("""
                    CREATE REL TABLE CALLS(FROM Function TO Function)
                """)
            
            print("✓ Database schema initialized successfully")
            
        except Exception as e:
            print(f"Error initializing schema: {e}")
            raise
    
    def insert_file(self, file_node: FileNode) -> bool:
        """
        Insert a File node into the database.
        
        Args:
            file_node: FileNode object with id, path, and language
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.conn.execute(
                "CREATE (f:File {id: $id, path: $path, language: $language})",
                {
                    "id": file_node.id,
                    "path": file_node.path,
                    "language": file_node.language
                }
            )
            return True
        except Exception as e:
            print(f"Error inserting file node: {e}")
            return False
    
    def insert_class(self, class_node: ClassNode) -> bool:
        """
        Insert a Class node into the database.
        
        Args:
            class_node: ClassNode object with id, name, line numbers, and file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.conn.execute(
                """CREATE (c:Class {
                    id: $id,
                    name: $name,
                    start_line: $start_line,
                    end_line: $end_line,
                    file_path: $file_path
                })""",
                {
                    "id": class_node.id,
                    "name": class_node.name,
                    "start_line": class_node.start_line,
                    "end_line": class_node.end_line,
                    "file_path": class_node.file_path
                }
            )
            return True
        except Exception as e:
            print(f"Error inserting class node: {e}")
            return False
    
    def insert_function(self, function_node: FunctionNode) -> bool:
        """
        Insert a Function node into the database.
        
        Args:
            function_node: FunctionNode object with id, name, args, docstring, line numbers, and file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.conn.execute(
                """CREATE (f:Function {
                    id: $id,
                    name: $name,
                    args: $args,
                    docstring: $docstring,
                    start_line: $start_line,
                    end_line: $end_line,
                    file_path: $file_path
                })""",
                {
                    "id": function_node.id,
                    "name": function_node.name,
                    "args": function_node.args,
                    "docstring": function_node.docstring or "",
                    "start_line": function_node.start_line,
                    "end_line": function_node.end_line,
                    "file_path": function_node.file_path
                }
            )
            return True
        except Exception as e:
            print(f"Error inserting function node: {e}")
            return False
    
    def insert_contains(self, source_id: str, target_id: str, target_type: str = "Function") -> bool:
        """
        Create a CONTAINS relationship between a File and a Class/Function.
        
        Args:
            source_id: ID of the File node
            target_id: ID of the Class or Function node
            target_type: Type of target node ("Class" or "Function")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if target_type == "Class":
                self.conn.execute(
                    """MATCH (source:File {id: $source_id}), (target:Class {id: $target_id})
                       CREATE (source)-[:CONTAINS_CLASS]->(target)""",
                    {"source_id": source_id, "target_id": target_id}
                )
            else:  # Function
                self.conn.execute(
                    """MATCH (source:File {id: $source_id}), (target:Function {id: $target_id})
                       CREATE (source)-[:CONTAINS_FUNCTION]->(target)""",
                    {"source_id": source_id, "target_id": target_id}
                )
            return True
        except Exception as e:
            print(f"Error creating CONTAINS relationship: {e}")
            return False
    
    def insert_defines(self, source_id: str, target_id: str) -> bool:
        """
        Create a DEFINES relationship between a Class and a Function.
        
        Args:
            source_id: ID of the Class node
            target_id: ID of the Function node
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.conn.execute(
                """MATCH (source:Class {id: $source_id}), (target:Function {id: $target_id})
                   CREATE (source)-[:DEFINES]->(target)""",
                {"source_id": source_id, "target_id": target_id}
            )
            return True
        except Exception as e:
            print(f"Error creating DEFINES relationship: {e}")
            return False
    
    def insert_calls(self, source_id: str, target_id: str) -> bool:
        """
        Create a CALLS relationship between two Functions.
        
        Args:
            source_id: ID of the calling Function node
            target_id: ID of the called Function node
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.conn.execute(
                """MATCH (source:Function {id: $source_id}), (target:Function {id: $target_id})
                   CREATE (source)-[:CALLS]->(target)""",
                {"source_id": source_id, "target_id": target_id}
            )
            return True
        except Exception as e:
            print(f"Error creating CALLS relationship: {e}")
            return False
    
    def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Execute a Cypher query and return results.
        
        Args:
            query: Cypher query string
            parameters: Optional query parameters
            
        Returns:
            List of result dictionaries
        """
        try:
            if parameters:
                result = self.conn.execute(query, parameters)
            else:
                result = self.conn.execute(query)
            
            # Convert result to list of dictionaries
            results = []
            while result.has_next():
                row = result.get_next()
                results.append(row)
            
            return results
        except Exception as e:
            print(f"Error executing Cypher query: {e}")
            raise
    
    def get_all_nodes(self) -> List[Dict]:
        """
        Retrieve all nodes from the database.
        
        Returns:
            List of all nodes with their properties
        """
        try:
            # Get all File nodes
            files = self.execute_cypher("MATCH (f:File) RETURN f")
            
            # Get all Class nodes
            classes = self.execute_cypher("MATCH (c:Class) RETURN c")
            
            # Get all Function nodes
            functions = self.execute_cypher("MATCH (fn:Function) RETURN fn")
            
            return files + classes + functions
        except Exception as e:
            print(f"Error retrieving nodes: {e}")
            return []
    
    def get_all_edges(self) -> List[Dict]:
        """
        Retrieve all relationships from the database.
        
        Returns:
            List of all edges with their properties
        """
        try:
            result = []
            
            # Get all CONTAINS_CLASS relationships
            contains_class = self.conn.execute(
                "MATCH (a:File)-[r:CONTAINS_CLASS]->(b:Class) RETURN a.id AS source, b.id AS target, 'CONTAINS' AS type"
            )
            while contains_class.has_next():
                result.append(contains_class.get_next())
            
            # Get all CONTAINS_FUNCTION relationships
            contains_func = self.conn.execute(
                "MATCH (a:File)-[r:CONTAINS_FUNCTION]->(b:Function) RETURN a.id AS source, b.id AS target, 'CONTAINS' AS type"
            )
            while contains_func.has_next():
                result.append(contains_func.get_next())
            
            # Get all DEFINES relationships
            defines = self.conn.execute(
                "MATCH (a:Class)-[r:DEFINES]->(b:Function) RETURN a.id AS source, b.id AS target, 'DEFINES' AS type"
            )
            while defines.has_next():
                result.append(defines.get_next())
            
            # Get all CALLS relationships
            calls = self.conn.execute(
                "MATCH (a:Function)-[r:CALLS]->(b:Function) RETURN a.id AS source, b.id AS target, 'CALLS' AS type"
            )
            while calls.has_next():
                result.append(calls.get_next())
            
            return result
        except Exception as e:
            print(f"Error retrieving edges: {e}")
            return []
    
    def clear_database(self):
        """Clear all data from the database (useful for testing)"""
        try:
            self.conn.execute("MATCH (n) DETACH DELETE n")
            print("✓ Database cleared")
        except Exception as e:
            print(f"Error clearing database: {e}")
            raise
    
    def close(self):
        """Close the database connection"""
        # KùzuDB connections don't need explicit closing
        print("✓ Database connection closed")


# Singleton instance
_db_instance: Optional[KuzuDB] = None


def get_db() -> KuzuDB:
    """Get or create the database singleton instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = KuzuDB()
    return _db_instance
