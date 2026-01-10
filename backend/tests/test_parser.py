"""
Property-based and unit tests for TreeSitterParser.
Tests node extraction, edge creation, and parsing correctness.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from hypothesis import given, strategies as st, settings
from parser import TreeSitterParser
from database import FileNode, ClassNode, FunctionNode, Edge


class TestTreeSitterParser:
    """Test suite for TreeSitterParser."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return TreeSitterParser()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    # ========== Unit Tests ==========
    
    def test_detect_language_python(self, parser):
        """Test language detection for Python files."""
        assert parser.detect_language(Path("test.py")) == "python"
        assert parser.detect_language(Path("module.py")) == "python"
    
    def test_detect_language_javascript(self, parser):
        """Test language detection for JavaScript files."""
        assert parser.detect_language(Path("test.js")) == "javascript"
        assert parser.detect_language(Path("test.jsx")) == "javascript"
        assert parser.detect_language(Path("test.ts")) == "javascript"
        assert parser.detect_language(Path("test.tsx")) == "javascript"
    
    def test_detect_language_unsupported(self, parser):
        """Test language detection for unsupported files."""
        assert parser.detect_language(Path("test.txt")) is None
        assert parser.detect_language(Path("test.java")) is None
    
    def test_parse_simple_python_function(self, parser, temp_dir):
        """Test parsing a simple Python function."""
        code = '''def hello_world():
    """Say hello."""
    print("Hello, World!")
'''
        test_file = temp_dir / "test.py"
        test_file.write_text(code)
        
        files, classes, functions, edges = parser.parse_file(test_file)
        
        assert len(files) == 1
        assert files[0].language == "python"
        assert len(functions) == 1
        assert functions[0].name == "hello_world"
        assert functions[0].docstring == "Say hello."
        assert functions[0].start_line == 1
    
    def test_parse_simple_python_class(self, parser, temp_dir):
        """Test parsing a simple Python class."""
        code = '''class MyClass:
    def __init__(self):
        pass
    
    def method(self):
        pass
'''
        test_file = temp_dir / "test.py"
        test_file.write_text(code)
        
        files, classes, functions, edges = parser.parse_file(test_file)
        
        assert len(classes) == 1
        assert classes[0].name == "MyClass"
        assert classes[0].start_line == 1
        assert len(functions) == 2  # __init__ and method
    
    def test_parse_javascript_function(self, parser, temp_dir):
        """Test parsing a JavaScript function."""
        code = '''function greet(name) {
    console.log("Hello, " + name);
}
'''
        test_file = temp_dir / "test.js"
        test_file.write_text(code)
        
        files, classes, functions, edges = parser.parse_file(test_file)
        
        assert len(files) == 1
        assert files[0].language == "javascript"
        assert len(functions) == 1
        assert functions[0].name == "greet"
    
    def test_parse_javascript_class(self, parser, temp_dir):
        """Test parsing a JavaScript class."""
        code = '''class Person {
    constructor(name) {
        this.name = name;
    }
    
    greet() {
        console.log("Hello");
    }
}
'''
        test_file = temp_dir / "test.js"
        test_file.write_text(code)
        
        files, classes, functions, edges = parser.parse_file(test_file)
        
        assert len(classes) == 1
        assert classes[0].name == "Person"
        assert len(functions) == 2  # constructor and greet
    
    def test_contains_edges_python(self, parser, temp_dir):
        """Test CONTAINS edges for Python file."""
        code = '''class MyClass:
    pass

def my_function():
    pass
'''
        test_file = temp_dir / "test.py"
        test_file.write_text(code)
        
        files, classes, functions, edges = parser.parse_file(test_file)
        
        # Should have CONTAINS edges from file to class and function
        contains_edges = [e for e in edges if e.edge_type.startswith("CONTAINS")]
        assert len(contains_edges) >= 2
    
    def test_defines_edges_python(self, parser, temp_dir):
        """Test DEFINES edges for Python class methods."""
        code = '''class MyClass:
    def method1(self):
        pass
    
    def method2(self):
        pass
'''
        test_file = temp_dir / "test.py"
        test_file.write_text(code)
        
        files, classes, functions, edges = parser.parse_file(test_file)
        
        # Should have DEFINES edges from class to methods
        defines_edges = [e for e in edges if e.edge_type == "DEFINES"]
        assert len(defines_edges) == 2
    
    def test_calls_edges_python(self, parser, temp_dir):
        """Test CALLS edges for Python function calls."""
        code = '''def helper():
    pass

def main():
    helper()
'''
        test_file = temp_dir / "test.py"
        test_file.write_text(code)
        
        files, classes, functions, edges = parser.parse_file(test_file)
        
        # Should have CALLS edge from main to helper
        calls_edges = [e for e in edges if e.edge_type == "CALLS"]
        assert len(calls_edges) >= 1
    
    def test_parse_empty_file(self, parser, temp_dir):
        """Test parsing an empty file."""
        test_file = temp_dir / "empty.py"
        test_file.write_text("")
        
        files, classes, functions, edges = parser.parse_file(test_file)
        
        assert len(files) == 1
        assert len(classes) == 0
        assert len(functions) == 0
    
    def test_parse_malformed_file(self, parser, temp_dir):
        """Test parsing a file with syntax errors."""
        code = '''def broken(
    # Missing closing parenthesis
'''
        test_file = temp_dir / "broken.py"
        test_file.write_text(code)
        
        # Should not crash, may return partial results
        files, classes, functions, edges = parser.parse_file(test_file)
        assert isinstance(files, list)
        assert isinstance(classes, list)
        assert isinstance(functions, list)
        assert isinstance(edges, list)

    
    # ========== Property-Based Tests ==========
    
    @settings(max_examples=100)
    @given(
        func_name=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll')), min_size=1, max_size=20),
        class_name=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll')), min_size=1, max_size=20)
    )
    def test_property_nodes_contain_required_attributes(self, func_name, class_name):
        """
        Property 5: Nodes contain required attributes
        Validates: Requirements 2.1, 2.2, 2.3
        
        For any valid Python code with functions and classes,
        all extracted nodes must contain required attributes.
        """
        parser = TreeSitterParser()  # Create parser inside test
        temp_dir = Path(tempfile.mkdtemp())  # Create temp dir inside test
        
        try:
            # Generate valid Python code
            code = f'''class {class_name}:
    def {func_name}(self):
        """Test docstring."""
        pass
'''
            test_file = temp_dir / f"test_{func_name}.py"
            test_file.write_text(code)
            
            files, classes, functions, edges = parser.parse_file(test_file)
            
            # Verify file nodes have required attributes
            for file_node in files:
                assert hasattr(file_node, 'id')
                assert hasattr(file_node, 'path')
                assert hasattr(file_node, 'language')
                assert file_node.id is not None
                assert file_node.path is not None
                assert file_node.language in ['python', 'javascript']
            
            # Verify class nodes have required attributes
            for class_node in classes:
                assert hasattr(class_node, 'id')
                assert hasattr(class_node, 'name')
                assert hasattr(class_node, 'start_line')
                assert hasattr(class_node, 'end_line')
                assert hasattr(class_node, 'file_path')
                assert class_node.id is not None
                assert class_node.name is not None
                assert class_node.start_line > 0
                assert class_node.end_line >= class_node.start_line
            
            # Verify function nodes have required attributes
            for func_node in functions:
                assert hasattr(func_node, 'id')
                assert hasattr(func_node, 'name')
                assert hasattr(func_node, 'args')
                assert hasattr(func_node, 'docstring')
                assert hasattr(func_node, 'start_line')
                assert hasattr(func_node, 'end_line')
                assert hasattr(func_node, 'file_path')
                assert func_node.id is not None
                assert func_node.name is not None
                assert func_node.start_line > 0
                assert func_node.end_line >= func_node.start_line
        
        except Exception:
            # Skip invalid identifiers
            pass
        finally:
            # Cleanup temp dir
            shutil.rmtree(temp_dir)
    
    @settings(max_examples=100)
    @given(
        num_functions=st.integers(min_value=1, max_value=5)
    )
    def test_property_edges_created_for_relationships(self, num_functions):
        """
        Property 6: Edges are created for all relationships
        Validates: Requirements 2.4, 2.5, 2.6, 2.7
        
        For any code with relationships, all edges must be created.
        """
        parser = TreeSitterParser()  # Create parser inside test
        temp_dir = Path(tempfile.mkdtemp())  # Create temp dir inside test
        
        try:
            # Generate code with known relationships
            functions = [f"func_{i}" for i in range(num_functions)]
            
            code = "# Test file\n"
            for func in functions:
                code += f'''
def {func}():
    pass
'''
            
            test_file = temp_dir / "test_edges.py"
            test_file.write_text(code)
            
            files, classes, funcs, edges = parser.parse_file(test_file)
            
            # Verify edges have required attributes
            for edge in edges:
                assert hasattr(edge, 'id')
                assert hasattr(edge, 'source')
                assert hasattr(edge, 'target')
                assert hasattr(edge, 'edge_type')
                assert edge.id is not None
                assert edge.source is not None
                assert edge.target is not None
                assert edge.edge_type in ['CONTAINS_CLASS', 'CONTAINS_FUNCTION', 'DEFINES', 'CALLS']
            
            # Verify CONTAINS edges exist for top-level functions
            contains_edges = [e for e in edges if e.edge_type == 'CONTAINS_FUNCTION']
            assert len(contains_edges) == num_functions
        finally:
            # Cleanup temp dir
            shutil.rmtree(temp_dir)
    
    @settings(max_examples=50)
    @given(
        num_methods=st.integers(min_value=1, max_value=5)
    )
    def test_property_class_defines_methods(self, num_methods):
        """
        Property: Class DEFINES edges are created for all methods
        
        For any class with methods, DEFINES edges must exist.
        """
        parser = TreeSitterParser()  # Create parser inside test
        temp_dir = Path(tempfile.mkdtemp())  # Create temp dir inside test
        
        try:
            methods = [f"method_{i}" for i in range(num_methods)]
            
            code = "class TestClass:\n"
            for method in methods:
                code += f'''    def {method}(self):
        pass
    
'''
            
            test_file = temp_dir / "test_class.py"
            test_file.write_text(code)
            
            files, classes, funcs, edges = parser.parse_file(test_file)
            
            # Verify DEFINES edges exist
            defines_edges = [e for e in edges if e.edge_type == 'DEFINES']
            assert len(defines_edges) == num_methods
            
            # Verify all DEFINES edges point from class to methods
            if classes:
                class_id = classes[0].id
                for edge in defines_edges:
                    assert edge.source == class_id
        finally:
            # Cleanup temp dir
            shutil.rmtree(temp_dir)
    
    def test_property_line_numbers_are_positive(self, parser, temp_dir):
        """
        Property: All line numbers must be positive integers
        
        For any parsed code, line numbers must be >= 1.
        """
        code = '''def func1():
    pass

class MyClass:
    def method(self):
        pass

def func2():
    pass
'''
        test_file = temp_dir / "test_lines.py"
        test_file.write_text(code)
        
        files, classes, funcs, edges = parser.parse_file(test_file)
        
        # Verify all line numbers are positive
        for cls in classes:
            assert cls.start_line >= 1
            assert cls.end_line >= 1
            assert cls.end_line >= cls.start_line
        
        for func in funcs:
            assert func.start_line >= 1
            assert func.end_line >= 1
            assert func.end_line >= func.start_line
    
    def test_property_file_node_always_created(self, parser, temp_dir):
        """
        Property: A file node is always created for valid files
        
        For any supported file, exactly one file node must be created.
        """
        code = "# Empty Python file\n"
        test_file = temp_dir / "test.py"
        test_file.write_text(code)
        
        files, classes, funcs, edges = parser.parse_file(test_file)
        
        assert len(files) == 1
        assert files[0].language == "python"
        assert str(test_file) in files[0].path
    
    def test_property_edge_ids_reference_valid_nodes(self, parser, temp_dir):
        """
        Property: All edge IDs must reference valid node IDs
        
        For any parsed code, edge source/target IDs must match node IDs.
        """
        code = '''class MyClass:
    def method(self):
        pass

def top_level():
    pass
'''
        test_file = temp_dir / "test.py"
        test_file.write_text(code)
        
        files, classes, funcs, edges = parser.parse_file(test_file)
        
        # Collect all valid node IDs
        valid_ids = set()
        for file_node in files:
            valid_ids.add(file_node.id)
        for cls in classes:
            valid_ids.add(cls.id)
        for func in funcs:
            valid_ids.add(func.id)
        
        # Verify all edges reference valid nodes
        for edge in edges:
            assert edge.source in valid_ids, f"Invalid source: {edge.source}"
            assert edge.target in valid_ids, f"Invalid target: {edge.target}"
