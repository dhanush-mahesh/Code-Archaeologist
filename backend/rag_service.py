"""
RAG Service for Code Archaeologist
Handles natural language query processing using LangChain and Ollama
"""
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
import re

from langchain_community.llms import Ollama
from langchain_community.graphs import KuzuGraph
from langchain.chains import GraphCypherQAChain
from langchain.prompts import PromptTemplate

from database import KuzuDB


class QueryResponse(BaseModel):
    """Response from RAG query processing"""
    response: str
    node_ids: List[str]
    cypher_query: Optional[str] = None


class RAGService:
    """Service for processing natural language queries using Graph-RAG"""
    
    def __init__(self, db: KuzuDB, model_name: str = "llama3", mock_mode: bool = False):
        """
        Initialize the RAG service.
        
        Args:
            db: KuzuDB database instance
            model_name: Ollama model name (default: llama3)
            mock_mode: If True, use mock responses instead of Ollama (for testing)
        """
        self.db = db
        self.model_name = model_name
        self.mock_mode = mock_mode
        
        if not mock_mode:
            try:
                # Initialize Ollama LLM
                self.llm = Ollama(
                    model=model_name,
                    temperature=0.0,  # Deterministic for Cypher generation
                )
                print(f"✓ Ollama initialized with model: {model_name}")
            except Exception as e:
                print(f"⚠️  Ollama initialization failed: {e}")
                print("⚠️  Falling back to mock mode")
                self.mock_mode = True
                self.llm = None
        else:
            self.llm = None
            print("✓ RAG Service initialized in mock mode")
        
        # Create KuzuGraph wrapper for LangChain
        # Note: LangChain's KuzuGraph expects a database path, not a connection
        # We'll use our own database wrapper instead
        
        # Few-shot examples for Cypher generation
        self.cypher_examples = """
# Example 1: Find all functions in a file
Question: What functions are in the calculator.py file?
Cypher: MATCH (f:File {path: 'calculator.py'})-[:CONTAINS_FUNCTION]->(fn:Function) RETURN fn.name, fn.args

# Example 2: Find all classes
Question: What classes are in the codebase?
Cypher: MATCH (c:Class) RETURN c.name, c.file_path

# Example 3: Find functions that call a specific function
Question: What functions call the add function?
Cypher: MATCH (caller:Function)-[:CALLS]->(callee:Function {name: 'add'}) RETURN caller.name, caller.file_path

# Example 4: Find methods in a class
Question: What methods does the Calculator class have?
Cypher: MATCH (c:Class {name: 'Calculator'})-[:DEFINES]->(fn:Function) RETURN fn.name, fn.args, fn.docstring

# Example 5: Find all files
Question: What files are in the repository?
Cypher: MATCH (f:File) RETURN f.path, f.language
"""
        
        # Cypher generation prompt
        self.cypher_prompt = PromptTemplate(
            input_variables=["question", "schema", "examples"],
            template="""You are a Cypher query expert for KùzuDB graph database.

Database Schema:
{schema}

Few-shot Examples:
{examples}

Important Rules:
1. Use MATCH patterns to find nodes and relationships
2. Node types: File, Class, Function
3. Relationship types: CONTAINS_CLASS (File->Class), CONTAINS_FUNCTION (File->Function), DEFINES (Class->Function), CALLS (Function->Function)
4. Always use RETURN to specify what to return
5. Use WHERE clauses for filtering
6. Property access: node.property (e.g., f.path, fn.name)
7. Do not use Neo4j-specific syntax
8. Keep queries simple and focused

Question: {question}

Generate ONLY the Cypher query, nothing else:
Cypher:"""
        )
        
        # Response generation prompt - enhanced for better responses
        self.response_prompt = PromptTemplate(
            input_variables=["question", "context"],
            template="""You are an expert code analyst helping developers understand their codebase. 
Your goal is to provide clear, detailed, and actionable insights.

Question: {question}

Query Results:
{context}

Instructions:
1. Analyze the query results carefully
2. Provide a comprehensive answer that explains:
   - What was found (files, classes, functions, relationships)
   - Key details about each entity (location, purpose, connections)
   - How these entities relate to each other
   - Any patterns or insights you notice
3. Use natural, conversational language
4. Structure your response with bullet points or numbered lists when appropriate
5. If results are empty, suggest alternative queries or what to look for
6. Be specific about file paths, line numbers, and function signatures when available

Answer:"""
        )
    
    def _get_schema(self) -> str:
        """Get database schema description"""
        return """
Node Types:
- File: {id, path, language}
- Class: {id, name, start_line, end_line, file_path}
- Function: {id, name, args, docstring, start_line, end_line, file_path}

Relationship Types:
- CONTAINS_CLASS: File -> Class
- CONTAINS_FUNCTION: File -> Function
- DEFINES: Class -> Function
- CALLS: Function -> Function
"""
    
    def generate_cypher(self, question: str) -> str:
        """
        Generate a Cypher query from a natural language question.
        
        Args:
            question: Natural language question
            
        Returns:
            Cypher query string
        """
        if self.mock_mode or self.llm is None:
            # Enhanced mock Cypher generation with better pattern matching
            question_lower = question.lower()
            
            # Pattern: files
            if "file" in question_lower and "how many" in question_lower:
                return "MATCH (f:File) RETURN count(f) AS count"
            elif "file" in question_lower:
                return "MATCH (f:File) RETURN f.path, f.language, f.id"
            
            # Pattern: classes
            elif "class" in question_lower and "how many" in question_lower:
                return "MATCH (c:Class) RETURN count(c) AS count"
            elif "class" in question_lower and ("method" in question_lower or "function" in question_lower):
                # Looking for methods in a class - extract class name preserving case
                words = question.split()  # Use original question to preserve case
                for i, word in enumerate(words):
                    if word.lower() in ["class", "the"] and i + 1 < len(words):
                        class_name = words[i + 1].strip("?.,")
                        if class_name.lower() not in ["have", "has", "contain", "contains", "class"]:
                            return f"MATCH (c:Class)-[:DEFINES]->(fn:Function) WHERE c.name = '{class_name}' RETURN fn.name, fn.args, fn.start_line, fn.end_line, fn.file_path"
                return "MATCH (c:Class)-[:DEFINES]->(fn:Function) RETURN c.name, fn.name, fn.args"
            elif "class" in question_lower and ("in" in question_lower or "from" in question_lower):
                # Try to extract file name
                words = question_lower.split()
                for i, word in enumerate(words):
                    if word in ["in", "from"] and i + 1 < len(words):
                        filename = words[i + 1].strip("?.,")
                        if filename not in ["the", "a", "an", "codebase", "repository", "repo", "code"]:
                            return f"MATCH (f:File)-[:CONTAINS_CLASS]->(c:Class) WHERE f.path CONTAINS '{filename}' RETURN c.name, c.start_line, c.end_line, c.file_path"
                return "MATCH (c:Class) RETURN c.name, c.file_path, c.start_line, c.end_line"
            elif "class" in question_lower:
                return "MATCH (c:Class) RETURN c.name, c.file_path, c.start_line, c.end_line"
            
            # Pattern: functions/methods
            elif ("function" in question_lower or "method" in question_lower) and "how many" in question_lower:
                return "MATCH (fn:Function) RETURN count(fn) AS count"
            elif ("function" in question_lower or "method" in question_lower) and ("in" in question_lower or "from" in question_lower):
                # Try to extract class or file name
                words = question_lower.split()
                for i, word in enumerate(words):
                    if word in ["in", "from"] and i + 1 < len(words):
                        name = words[i + 1].strip("?.,")
                        # Check if it's a class
                        if "class" in question_lower:
                            return f"MATCH (c:Class)-[:DEFINES]->(fn:Function) WHERE c.name CONTAINS '{name}' RETURN fn.name, fn.args, fn.start_line, fn.end_line"
                        else:
                            return f"MATCH (f:File)-[:CONTAINS_FUNCTION]->(fn:Function) WHERE f.path CONTAINS '{name}' RETURN fn.name, fn.args, fn.start_line, fn.end_line"
                return "MATCH (fn:Function) RETURN fn.name, fn.args, fn.file_path, fn.start_line, fn.end_line"
            elif "function" in question_lower or "method" in question_lower:
                return "MATCH (fn:Function) RETURN fn.name, fn.args, fn.file_path, fn.start_line, fn.end_line"
            
            # Pattern: calls/dependencies
            elif "call" in question_lower:
                words = question_lower.split()
                # Look for function name after "call" or "calls"
                for i, word in enumerate(words):
                    if word in ["call", "calls", "calling", "called"] and i + 1 < len(words):
                        func_name = words[i + 1].strip("?.,")
                        if func_name not in ["the", "a", "an"]:
                            return f"MATCH (caller:Function)-[:CALLS]->(callee:Function) WHERE callee.name CONTAINS '{func_name}' RETURN caller.name, caller.file_path, callee.name"
                # Look for function name before "call"
                for i, word in enumerate(words):
                    if word in ["call", "calls", "calling", "called"] and i > 0:
                        func_name = words[i - 1].strip("?.,")
                        if func_name not in ["what", "which", "who", "functions", "function"]:
                            return f"MATCH (caller:Function)-[:CALLS]->(callee:Function) WHERE callee.name CONTAINS '{func_name}' RETURN caller.name, caller.file_path, callee.name"
                return "MATCH (caller:Function)-[:CALLS]->(callee:Function) RETURN caller.name, callee.name, caller.file_path"
            
            # Pattern: structure/overview
            elif "structure" in question_lower or "overview" in question_lower or "summary" in question_lower:
                return "MATCH (f:File) OPTIONAL MATCH (f)-[:CONTAINS_CLASS]->(c:Class) OPTIONAL MATCH (f)-[:CONTAINS_FUNCTION]->(fn:Function) RETURN f.path, count(c) AS classes, count(fn) AS functions"
            
            # Default: show some nodes
            else:
                return "MATCH (n) RETURN n LIMIT 20"
        
        try:
            prompt = self.cypher_prompt.format(
                question=question,
                schema=self._get_schema(),
                examples=self.cypher_examples
            )
            
            # Generate Cypher query
            cypher = self.llm.invoke(prompt)
            
            # Clean up the response
            cypher = cypher.strip()
            
            # Extract just the Cypher query if there's extra text
            # Look for lines that start with MATCH or RETURN
            lines = cypher.split('\n')
            cypher_lines = []
            in_query = False
            
            for line in lines:
                line = line.strip()
                if line.upper().startswith(('MATCH', 'RETURN', 'WHERE', 'WITH', 'CREATE', 'MERGE')):
                    in_query = True
                if in_query and line:
                    cypher_lines.append(line)
                elif in_query and not line:
                    break  # End of query
            
            if cypher_lines:
                cypher = ' '.join(cypher_lines)
            
            return cypher
        except Exception as e:
            print(f"⚠️  LLM invocation failed: {e}")
            print("⚠️  Falling back to mock mode")
            self.mock_mode = True
            self.llm = None
            # Retry with mock mode
            return self.generate_cypher(question)
    
    def execute_cypher(self, cypher: str) -> Tuple[bool, List[Dict], str]:
        """
        Execute a Cypher query against the database.
        
        Args:
            cypher: Cypher query string
            
        Returns:
            Tuple of (success, results, error_message)
        """
        try:
            results = self.db.execute_cypher(cypher)
            return True, results, ""
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  Cypher execution error: {error_msg}")
            return False, [], error_msg
    
    def extract_node_ids(self, results: List[Dict]) -> List[str]:
        """
        Extract node IDs from query results.
        
        Args:
            results: Query results from database
            
        Returns:
            List of node IDs
        """
        node_ids = []
        
        for row in results:
            # Results can be lists or tuples from KuzuDB
            if isinstance(row, (list, tuple)):
                for item in row:
                    # Check if item is a dict with 'id' field
                    if isinstance(item, dict) and 'id' in item:
                        node_ids.append(item['id'])
                    # Check if item is a string that looks like an ID
                    elif isinstance(item, str) and ('/' in item or '_' in item):
                        node_ids.append(item)
            elif isinstance(row, dict):
                # Check all values in the dict
                for key, value in row.items():
                    if key == 'id' or key.endswith('.id'):
                        node_ids.append(str(value))
                    elif isinstance(value, dict) and 'id' in value:
                        node_ids.append(value['id'])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for node_id in node_ids:
            if node_id not in seen:
                seen.add(node_id)
                unique_ids.append(node_id)
        
        return unique_ids
    
    def _format_results_detailed(self, results: List[Dict]) -> str:
        """
        Format query results into detailed, readable text.
        
        Args:
            results: Query results from database
            
        Returns:
            Formatted string with detailed information
        """
        if not results:
            return "No results found."
        
        formatted_lines = []
        
        for i, row in enumerate(results, 1):
            if isinstance(row, (list, tuple)):
                # Handle tuple/list results
                parts = []
                for item in row:
                    if isinstance(item, dict):
                        # Format dict items nicely
                        item_parts = []
                        for k, v in item.items():
                            if k not in ['id', '_label'] and v:  # Skip internal fields
                                item_parts.append(f"{k}: {v}")
                        if item_parts:
                            parts.append(", ".join(item_parts))
                    else:
                        parts.append(str(item))
                formatted_lines.append(f"{i}. {' | '.join(parts)}")
            elif isinstance(row, dict):
                # Handle dict results
                parts = []
                for k, v in row.items():
                    if k not in ['id', '_label'] and v:  # Skip internal fields
                        parts.append(f"{k}: {v}")
                if parts:
                    formatted_lines.append(f"{i}. {', '.join(parts)}")
            else:
                formatted_lines.append(f"{i}. {row}")
        
        return '\n'.join(formatted_lines)
    
    def _generate_smart_response(self, question: str, results: List[Dict]) -> str:
        """
        Generate an intelligent response without LLM (fallback mode).
        
        Args:
            question: Original question
            results: Query results from database
            
        Returns:
            Natural language response
        """
        if not results:
            return "I couldn't find any matching entities in the codebase. Try asking about files, classes, or functions in the repository."
        
        question_lower = question.lower()
        count = len(results)
        
        # Analyze what type of entities we found
        has_files = any('path' in str(r) or 'language' in str(r) for r in results)
        has_classes = any('class' in str(r).lower() for r in results)
        has_functions = any('function' in str(r).lower() or 'args' in str(r) for r in results)
        
        # Build contextual response
        response_parts = []
        
        # Opening statement
        if "what" in question_lower or "which" in question_lower or "list" in question_lower:
            if has_files:
                response_parts.append(f"I found {count} file(s) in the repository:")
            elif has_classes:
                response_parts.append(f"I found {count} class(es) in the codebase:")
            elif has_functions:
                response_parts.append(f"I found {count} function(s):")
            else:
                response_parts.append(f"Here are the {count} result(s) I found:")
        elif "how many" in question_lower or "count" in question_lower:
            response_parts.append(f"There are {count} matching entities.")
        else:
            response_parts.append(f"Based on your query, I found {count} result(s):")
        
        # Format the actual results
        formatted = self._format_results_detailed(results)
        response_parts.append("\n" + formatted)
        
        # Add helpful context
        if count > 10:
            response_parts.append(f"\n(Showing all {count} results)")
        
        return "\n".join(response_parts)
    
    def generate_response(self, question: str, results: List[Dict]) -> str:
        """
        Generate a natural language response from query results.
        
        Args:
            question: Original question
            results: Query results from database
            
        Returns:
            Natural language response
        """
        # Format results as context
        context = self._format_results_detailed(results)
        
        if self.mock_mode or self.llm is None:
            # Use smart fallback response generation
            return self._generate_smart_response(question, results)
        
        try:
            # Generate response with LLM
            prompt = self.response_prompt.format(
                question=question,
                context=context
            )
            
            response = self.llm.invoke(prompt)
            return response.strip()
        except Exception as e:
            print(f"⚠️  LLM invocation failed: {e}")
            print("⚠️  Falling back to smart response mode")
            self.mock_mode = True
            self.llm = None
            # Use smart fallback
            return self._generate_smart_response(question, results)
    
    def process_query(self, question: str, max_retries: int = 2) -> QueryResponse:
        """
        Process a natural language query end-to-end.
        
        Args:
            question: Natural language question
            max_retries: Maximum number of retries for invalid Cypher
            
        Returns:
            QueryResponse with answer and node IDs
        """
        cypher = None
        results = []
        error_msg = ""
        
        # Try to generate and execute Cypher query
        for attempt in range(max_retries + 1):
            try:
                # Generate Cypher query
                cypher = self.generate_cypher(question)
                print(f"📝 Generated Cypher (attempt {attempt + 1}): {cypher}")
                
                # Execute query
                success, results, error_msg = self.execute_cypher(cypher)
                
                if success:
                    break
                else:
                    print(f"⚠️  Cypher execution failed: {error_msg}")
                    if attempt < max_retries:
                        # Add error feedback to the question for retry
                        question = f"{question}\n\nPrevious query failed with error: {error_msg}\nPlease generate a corrected query."
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️  Query processing error: {error_msg}")
                if attempt >= max_retries:
                    break
        
        # Generate response
        if results:
            response_text = self.generate_response(question, results)
            node_ids = self.extract_node_ids(results)
        else:
            # Fallback response if query failed
            response_text = f"I encountered an issue processing your query. {error_msg if error_msg else 'Please try rephrasing your question.'}"
            node_ids = []
        
        return QueryResponse(
            response=response_text,
            node_ids=node_ids,
            cypher_query=cypher
        )
