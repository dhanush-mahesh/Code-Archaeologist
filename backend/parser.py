"""
Tree-sitter based code parser for extracting graph entities from source code.
Supports Python and JavaScript/TypeScript files.
"""
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from tree_sitter import Language, Parser, Node, Tree
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
from database import FileNode, ClassNode, FunctionNode, Edge


class TreeSitterParser:
    """Parser for extracting code structure using tree-sitter."""
    
    def __init__(self):
        """Initialize parsers for Python and JavaScript."""
        # Initialize Python parser
        self.python_lang = Language(tspython.language(), 'python')
        self.python_parser = Parser()
        self.python_parser.set_language(self.python_lang)
        
        # Initialize JavaScript parser
        self.js_lang = Language(tsjavascript.language(), 'javascript')
        self.js_parser = Parser()
        self.js_parser.set_language(self.js_lang)
        
        # Supported file extensions
        self.python_extensions = {'.py'}
        self.js_extensions = {'.js', '.jsx', '.ts', '.tsx', '.mjs'}
    
    def detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension."""
        ext = file_path.suffix.lower()
        if ext in self.python_extensions:
            return 'python'
        elif ext in self.js_extensions:
            return 'javascript'
        return None
    
    def parse_file(self, file_path: Path) -> Tuple[List[FileNode], List[ClassNode], List[FunctionNode], List[Edge]]:
        """
        Parse a single file and extract all nodes and edges.
        
        Returns:
            Tuple of (file_nodes, class_nodes, function_nodes, edges)
        """
        language = self.detect_language(file_path)
        if not language:
            return [], [], [], []
        
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            # Parse based on language
            if language == 'python':
                tree = self.python_parser.parse(source_code)
            else:  # javascript
                tree = self.js_parser.parse(source_code)
            
            # Create file node
            file_id = f"file:{file_path}"
            file_node = FileNode(
                id=file_id,
                path=str(file_path),
                language=language
            )
            
            # Extract entities
            classes = self.extract_classes(tree, file_path, language)
            functions = self.extract_functions(tree, file_path, language)
            edges = self.extract_edges(tree, file_path, language, classes, functions)
            
            return [file_node], classes, functions, edges
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return [], [], [], []

    def extract_classes(self, tree: Tree, file_path: Path, language: str) -> List[ClassNode]:
        """Extract class definitions from AST."""
        classes = []
        
        if language == 'python':
            query_str = "(class_definition name: (identifier) @class_name) @class_def"
        else:  # javascript
            query_str = "(class_declaration name: (identifier) @class_name) @class_def"
        
        try:
            lang = self.python_lang if language == 'python' else self.js_lang
            query = lang.query(query_str)
            captures = query.captures(tree.root_node)
            
            # Group captures by class definition
            class_defs = {}
            for node, capture_name in captures:
                if capture_name == 'class_def':
                    class_defs[node.id] = {'node': node}
                elif capture_name == 'class_name':
                    # Find parent class_def
                    parent = node.parent
                    while parent and parent.type not in ['class_definition', 'class_declaration']:
                        parent = parent.parent
                    if parent and parent.id in class_defs:
                        class_defs[parent.id]['name'] = node.text.decode('utf-8')
            
            # Create ClassNode objects
            for class_id, class_data in class_defs.items():
                if 'name' in class_data:
                    node = class_data['node']
                    class_name = class_data['name']
                    
                    class_node = ClassNode(
                        id=f"class:{file_path}:{class_name}:{node.start_point[0]}",
                        name=class_name,
                        start_line=node.start_point[0] + 1,  # Convert to 1-indexed
                        end_line=node.end_point[0] + 1,
                        file_path=str(file_path)
                    )
                    classes.append(class_node)
        
        except Exception as e:
            print(f"Error extracting classes from {file_path}: {e}")
        
        return classes
    
    def extract_functions(self, tree: Tree, file_path: Path, language: str) -> List[FunctionNode]:
        """Extract function definitions from AST."""
        functions = []
        
        if language == 'python':
            # Query for function definitions
            query_str = """
            (function_definition
                name: (identifier) @func_name
                parameters: (parameters) @params
                body: (block) @body) @func_def
            """
        else:  # javascript
            # Query for various function types in JavaScript
            query_str = """
            [
                (function_declaration
                    name: (identifier) @func_name
                    parameters: (formal_parameters) @params) @func_def
                (method_definition
                    name: (property_identifier) @func_name
                    parameters: (formal_parameters) @params) @func_def
            ]
            """
        
        try:
            lang = self.python_lang if language == 'python' else self.js_lang
            query = lang.query(query_str)
            captures = query.captures(tree.root_node)
            
            # Group captures by function definition
            func_defs = {}
            for node, capture_name in captures:
                if capture_name == 'func_def':
                    func_defs[node.id] = {'node': node, 'params': '', 'docstring': ''}
                elif capture_name == 'func_name':
                    # Find parent function
                    parent = node.parent
                    while parent and parent.type not in ['function_definition', 'function_declaration', 'method_definition']:
                        parent = parent.parent
                    if parent and parent.id in func_defs:
                        func_defs[parent.id]['name'] = node.text.decode('utf-8')
                elif capture_name == 'params':
                    parent = node.parent
                    while parent and parent.type not in ['function_definition', 'function_declaration', 'method_definition']:
                        parent = parent.parent
                    if parent and parent.id in func_defs:
                        func_defs[parent.id]['params'] = node.text.decode('utf-8')
                elif capture_name == 'body':
                    parent = node.parent
                    if parent and parent.id in func_defs:
                        # Try to extract docstring (first string in body)
                        docstring = self._extract_docstring(node, language)
                        func_defs[parent.id]['docstring'] = docstring
            
            # Create FunctionNode objects
            for func_id, func_data in func_defs.items():
                if 'name' in func_data:
                    node = func_data['node']
                    func_name = func_data['name']
                    
                    function_node = FunctionNode(
                        id=f"func:{file_path}:{func_name}:{node.start_point[0]}",
                        name=func_name,
                        args=func_data['params'],
                        docstring=func_data['docstring'],
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        file_path=str(file_path)
                    )
                    functions.append(function_node)
        
        except Exception as e:
            print(f"Error extracting functions from {file_path}: {e}")
        
        return functions
    
    def _extract_docstring(self, body_node: Node, language: str) -> str:
        """Extract docstring from function body."""
        try:
            if language == 'python':
                # Look for first expression_statement containing a string
                for child in body_node.children:
                    if child.type == 'expression_statement':
                        for subchild in child.children:
                            if subchild.type == 'string':
                                # Remove quotes
                                text = subchild.text.decode('utf-8')
                                return text.strip('"""').strip("'''").strip('"').strip("'").strip()
            else:  # javascript
                # Look for first comment or string
                for child in body_node.children:
                    if child.type == 'comment':
                        return child.text.decode('utf-8').strip('//').strip('/*').strip('*/').strip()
        except:
            pass
        return ''

    def extract_edges(self, tree: Tree, file_path: Path, language: str, 
                     classes: List[ClassNode], functions: List[FunctionNode]) -> List[Edge]:
        """Extract relationships (CONTAINS, DEFINES, CALLS) from AST."""
        edges = []
        file_id = f"file:{file_path}"
        
        # Create lookup maps
        class_map = {cls.name: cls for cls in classes}
        func_map = {func.name: func for func in functions}
        
        # 1. CONTAINS edges: File -> Classes and File -> Functions (top-level only)
        edges.extend(self._extract_contains_edges(tree, file_id, classes, functions, language))
        
        # 2. DEFINES edges: Class -> Methods
        edges.extend(self._extract_defines_edges(tree, classes, functions, language))
        
        # 3. CALLS edges: Function -> Function
        edges.extend(self._extract_calls_edges(tree, functions, language))
        
        return edges
    
    def _extract_contains_edges(self, tree: Tree, file_id: str, 
                                classes: List[ClassNode], 
                                functions: List[FunctionNode],
                                language: str) -> List[Edge]:
        """Extract CONTAINS relationships (File -> Class/Function)."""
        edges = []
        
        # Get top-level nodes (direct children of module/program)
        root = tree.root_node
        
        # Find which classes and functions are top-level
        for cls in classes:
            # Check if class is at top level
            if self._is_top_level(root, cls.start_line - 1, language):
                edge = Edge(
                    id=f"{file_id}->CONTAINS_CLASS->{cls.id}",
                    source=file_id,
                    target=cls.id,
                    edge_type="CONTAINS_CLASS"
                )
                edges.append(edge)
        
        for func in functions:
            # Check if function is at top level (not inside a class)
            if self._is_top_level(root, func.start_line - 1, language):
                edge = Edge(
                    id=f"{file_id}->CONTAINS_FUNCTION->{func.id}",
                    source=file_id,
                    target=func.id,
                    edge_type="CONTAINS_FUNCTION"
                )
                edges.append(edge)
        
        return edges
    
    def _is_top_level(self, root: Node, line: int, language: str) -> bool:
        """Check if a node at given line is at top level (not nested in class)."""
        # For simplicity, check if the node is a direct child of module/program
        # This is a heuristic - in production, we'd track the actual AST structure
        
        if language == 'python':
            target_types = ['class_definition', 'function_definition']
        else:
            target_types = ['class_declaration', 'function_declaration', 'method_definition']
        
        for child in root.children:
            if child.type in target_types and child.start_point[0] == line:
                return True
        
        return False
    
    def _extract_defines_edges(self, tree: Tree, 
                              classes: List[ClassNode], 
                              functions: List[FunctionNode],
                              language: str) -> List[Edge]:
        """Extract DEFINES relationships (Class -> Method)."""
        edges = []
        
        # For each class, find methods defined within it
        for cls in classes:
            for func in functions:
                # Check if function is within class line range
                if (func.start_line > cls.start_line and 
                    func.end_line <= cls.end_line and
                    func.file_path == cls.file_path):
                    edge = Edge(
                        id=f"{cls.id}->DEFINES->{func.id}",
                        source=cls.id,
                        target=func.id,
                        edge_type="DEFINES"
                    )
                    edges.append(edge)
        
        return edges
    
    def _extract_calls_edges(self, tree: Tree, 
                            functions: List[FunctionNode],
                            language: str) -> List[Edge]:
        """Extract CALLS relationships (Function -> Function)."""
        edges = []
        
        # Build function name lookup
        func_by_name = {}
        for func in functions:
            func_by_name[func.name] = func
        
        # Query for call expressions
        if language == 'python':
            query_str = "(call function: (identifier) @callee) @call_expr"
        else:  # javascript
            query_str = "(call_expression function: (identifier) @callee) @call_expr"
        
        try:
            lang = self.python_lang if language == 'python' else self.js_lang
            query = lang.query(query_str)
            captures = query.captures(tree.root_node)
            
            # Track calls
            calls = []
            for node, capture_name in captures:
                if capture_name == 'callee':
                    callee_name = node.text.decode('utf-8')
                    call_line = node.start_point[0] + 1
                    calls.append((callee_name, call_line))
            
            # Match calls to caller functions
            for callee_name, call_line in calls:
                # Find which function contains this call
                caller_func = None
                for func in functions:
                    if func.start_line <= call_line <= func.end_line:
                        caller_func = func
                        break
                
                # Find callee function
                callee_func = func_by_name.get(callee_name)
                
                if caller_func and callee_func and caller_func.id != callee_func.id:
                    edge = Edge(
                        id=f"{caller_func.id}->CALLS->{callee_func.id}",
                        source=caller_func.id,
                        target=callee_func.id,
                        edge_type="CALLS"
                    )
                    edges.append(edge)
        
        except Exception as e:
            print(f"Error extracting calls: {e}")
        
        return edges
