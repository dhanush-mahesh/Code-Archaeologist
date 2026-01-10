"""
Property-based tests for KùzuDB database operations
Feature: code-archaeologist
"""
import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path
import shutil
from database import KuzuDB, FileNode, ClassNode, FunctionNode


# Test database path
TEST_DB_PATH = "./test_data/test_graph"


@pytest.fixture
def db():
    """Create a test database instance"""
    # Clean up any existing test database
    if Path(TEST_DB_PATH).exists():
        shutil.rmtree(Path(TEST_DB_PATH).parent)
    
    # Create new test database
    test_db = KuzuDB(TEST_DB_PATH)
    yield test_db
    
    # Cleanup after test
    test_db.close()
    if Path(TEST_DB_PATH).exists():
        shutil.rmtree(Path(TEST_DB_PATH).parent)


# Strategies for generating test data
file_node_strategy = st.builds(
    FileNode,
    id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-')),
    path=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='/_.-')),
    language=st.sampled_from(['python', 'javascript'])
)

class_node_strategy = st.builds(
    ClassNode,
    id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-')),
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters='_')),
    start_line=st.integers(min_value=1, max_value=1000),
    end_line=st.integers(min_value=1, max_value=1000),
    file_path=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='/_.-'))
).filter(lambda c: c.start_line <= c.end_line)

function_node_strategy = st.builds(
    FunctionNode,
    id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-')),
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters='_')),
    args=st.text(max_size=200),
    docstring=st.one_of(st.none(), st.text(max_size=500)),
    start_line=st.integers(min_value=1, max_value=1000),
    end_line=st.integers(min_value=1, max_value=1000),
    file_path=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='/_.-'))
).filter(lambda f: f.start_line <= f.end_line)


@settings(max_examples=100)
@given(file_node=file_node_strategy)
def test_property_file_node_round_trip(file_node):
    """
    Property 8: Graph persistence round-trip
    Validates: Requirements 3.1, 3.2
    
    For any valid FileNode, storing it to KùzuDB and then retrieving it
    should produce an equivalent node with the same attributes.
    """
    # Create a fresh database for this test
    if Path(TEST_DB_PATH).exists():
        shutil.rmtree(Path(TEST_DB_PATH).parent)
    
    db = KuzuDB(TEST_DB_PATH)
    
    try:
        # Insert the file node
        success = db.insert_file(file_node)
        assert success, "Failed to insert file node"
        
        # Retrieve the node
        result = db.execute_cypher(
            "MATCH (f:File {id: $id}) RETURN f.id AS id, f.path AS path, f.language AS language",
            {"id": file_node.id}
        )
        
        # Verify we got exactly one result
        assert len(result) == 1, f"Expected 1 result, got {len(result)}"
        
        # Verify all attributes match
        retrieved = result[0]
        assert retrieved['id'] == file_node.id, "ID mismatch"
        assert retrieved['path'] == file_node.path, "Path mismatch"
        assert retrieved['language'] == file_node.language, "Language mismatch"
        
    finally:
        db.close()
        if Path(TEST_DB_PATH).exists():
            shutil.rmtree(Path(TEST_DB_PATH).parent)


@settings(max_examples=100)
@given(class_node=class_node_strategy)
def test_property_class_node_round_trip(class_node):
    """
    Property 8: Graph persistence round-trip (Class nodes)
    Validates: Requirements 3.1, 3.2
    
    For any valid ClassNode, storing it to KùzuDB and then retrieving it
    should produce an equivalent node with the same attributes.
    """
    # Create a fresh database for this test
    if Path(TEST_DB_PATH).exists():
        shutil.rmtree(Path(TEST_DB_PATH).parent)
    
    db = KuzuDB(TEST_DB_PATH)
    
    try:
        # Insert the class node
        success = db.insert_class(class_node)
        assert success, "Failed to insert class node"
        
        # Retrieve the node
        result = db.execute_cypher(
            """MATCH (c:Class {id: $id}) 
               RETURN c.id AS id, c.name AS name, c.start_line AS start_line, 
                      c.end_line AS end_line, c.file_path AS file_path""",
            {"id": class_node.id}
        )
        
        # Verify we got exactly one result
        assert len(result) == 1, f"Expected 1 result, got {len(result)}"
        
        # Verify all attributes match
        retrieved = result[0]
        assert retrieved['id'] == class_node.id, "ID mismatch"
        assert retrieved['name'] == class_node.name, "Name mismatch"
        assert retrieved['start_line'] == class_node.start_line, "Start line mismatch"
        assert retrieved['end_line'] == class_node.end_line, "End line mismatch"
        assert retrieved['file_path'] == class_node.file_path, "File path mismatch"
        
    finally:
        db.close()
        if Path(TEST_DB_PATH).exists():
            shutil.rmtree(Path(TEST_DB_PATH).parent)


@settings(max_examples=100)
@given(function_node=function_node_strategy)
def test_property_function_node_round_trip(function_node):
    """
    Property 8: Graph persistence round-trip (Function nodes)
    Validates: Requirements 3.1, 3.2
    
    For any valid FunctionNode, storing it to KùzuDB and then retrieving it
    should produce an equivalent node with the same attributes.
    """
    # Create a fresh database for this test
    if Path(TEST_DB_PATH).exists():
        shutil.rmtree(Path(TEST_DB_PATH).parent)
    
    db = KuzuDB(TEST_DB_PATH)
    
    try:
        # Insert the function node
        success = db.insert_function(function_node)
        assert success, "Failed to insert function node"
        
        # Retrieve the node
        result = db.execute_cypher(
            """MATCH (f:Function {id: $id}) 
               RETURN f.id AS id, f.name AS name, f.args AS args, f.docstring AS docstring,
                      f.start_line AS start_line, f.end_line AS end_line, f.file_path AS file_path""",
            {"id": function_node.id}
        )
        
        # Verify we got exactly one result
        assert len(result) == 1, f"Expected 1 result, got {len(result)}"
        
        # Verify all attributes match
        retrieved = result[0]
        assert retrieved['id'] == function_node.id, "ID mismatch"
        assert retrieved['name'] == function_node.name, "Name mismatch"
        assert retrieved['args'] == function_node.args, "Args mismatch"
        assert retrieved['docstring'] == (function_node.docstring or ""), "Docstring mismatch"
        assert retrieved['start_line'] == function_node.start_line, "Start line mismatch"
        assert retrieved['end_line'] == function_node.end_line, "End line mismatch"
        assert retrieved['file_path'] == function_node.file_path, "File path mismatch"
        
    finally:
        db.close()
        if Path(TEST_DB_PATH).exists():
            shutil.rmtree(Path(TEST_DB_PATH).parent)


def test_basic_database_initialization(db):
    """Test that database initializes correctly with schema"""
    # Database should be initialized by the fixture
    assert db is not None
    assert db.conn is not None
    
    # Test basic query execution
    result = db.execute_cypher("MATCH (n) RETURN count(n) AS count")
    assert len(result) == 1
    assert result[0]['count'] == 0  # Should be empty initially


def test_file_node_insertion(db):
    """Test inserting a File node"""
    file_node = FileNode(
        id="file_1",
        path="src/main.py",
        language="python"
    )
    
    success = db.insert_file(file_node)
    assert success
    
    # Verify insertion
    result = db.execute_cypher("MATCH (f:File {id: 'file_1'}) RETURN f")
    assert len(result) == 1


def test_class_node_insertion(db):
    """Test inserting a Class node"""
    class_node = ClassNode(
        id="class_1",
        name="MyClass",
        start_line=10,
        end_line=50,
        file_path="src/main.py"
    )
    
    success = db.insert_class(class_node)
    assert success
    
    # Verify insertion
    result = db.execute_cypher("MATCH (c:Class {id: 'class_1'}) RETURN c")
    assert len(result) == 1


def test_function_node_insertion(db):
    """Test inserting a Function node"""
    function_node = FunctionNode(
        id="func_1",
        name="my_function",
        args="arg1, arg2",
        docstring="This is a test function",
        start_line=5,
        end_line=15,
        file_path="src/main.py"
    )
    
    success = db.insert_function(function_node)
    assert success
    
    # Verify insertion
    result = db.execute_cypher("MATCH (f:Function {id: 'func_1'}) RETURN f")
    assert len(result) == 1


def test_contains_relationship(db):
    """Test creating CONTAINS relationship"""
    # Insert file and function
    file_node = FileNode(id="file_1", path="src/main.py", language="python")
    function_node = FunctionNode(
        id="func_1", name="test", args="", docstring=None,
        start_line=1, end_line=5, file_path="src/main.py"
    )
    
    db.insert_file(file_node)
    db.insert_function(function_node)
    
    # Create relationship
    success = db.insert_contains("file_1", "func_1")
    assert success
    
    # Verify relationship
    result = db.execute_cypher(
        "MATCH (f:File)-[:CONTAINS]->(fn:Function) RETURN f.id AS file_id, fn.id AS func_id"
    )
    assert len(result) == 1
    assert result[0]['file_id'] == "file_1"
    assert result[0]['func_id'] == "func_1"


def test_defines_relationship(db):
    """Test creating DEFINES relationship"""
    # Insert class and function
    class_node = ClassNode(
        id="class_1", name="MyClass", start_line=1, end_line=10, file_path="src/main.py"
    )
    function_node = FunctionNode(
        id="func_1", name="method", args="self", docstring=None,
        start_line=2, end_line=5, file_path="src/main.py"
    )
    
    db.insert_class(class_node)
    db.insert_function(function_node)
    
    # Create relationship
    success = db.insert_defines("class_1", "func_1")
    assert success
    
    # Verify relationship
    result = db.execute_cypher(
        "MATCH (c:Class)-[:DEFINES]->(f:Function) RETURN c.id AS class_id, f.id AS func_id"
    )
    assert len(result) == 1
    assert result[0]['class_id'] == "class_1"
    assert result[0]['func_id'] == "func_1"


def test_calls_relationship(db):
    """Test creating CALLS relationship"""
    # Insert two functions
    func1 = FunctionNode(
        id="func_1", name="caller", args="", docstring=None,
        start_line=1, end_line=5, file_path="src/main.py"
    )
    func2 = FunctionNode(
        id="func_2", name="callee", args="", docstring=None,
        start_line=10, end_line=15, file_path="src/main.py"
    )
    
    db.insert_function(func1)
    db.insert_function(func2)
    
    # Create relationship
    success = db.insert_calls("func_1", "func_2")
    assert success
    
    # Verify relationship
    result = db.execute_cypher(
        "MATCH (f1:Function)-[:CALLS]->(f2:Function) RETURN f1.id AS caller, f2.id AS callee"
    )
    assert len(result) == 1
    assert result[0]['caller'] == "func_1"
    assert result[0]['callee'] == "func_2"
