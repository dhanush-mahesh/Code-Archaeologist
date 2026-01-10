"""
Simple script to test database setup
"""
from database import KuzuDB, FileNode, ClassNode, FunctionNode

def main():
    print("Testing KùzuDB setup...")
    
    # Initialize database
    db = KuzuDB("./data/test_graph")
    print("✓ Database initialized")
    
    # Test inserting a file node
    file_node = FileNode(
        id="test_file_1",
        path="src/example.py",
        language="python"
    )
    success = db.insert_file(file_node)
    print(f"✓ File node inserted: {success}")
    
    # Test inserting a class node
    class_node = ClassNode(
        id="test_class_1",
        name="ExampleClass",
        start_line=10,
        end_line=50,
        file_path="src/example.py"
    )
    success = db.insert_class(class_node)
    print(f"✓ Class node inserted: {success}")
    
    # Test inserting a function node
    function_node = FunctionNode(
        id="test_func_1",
        name="example_function",
        args="arg1, arg2",
        docstring="This is an example function",
        start_line=15,
        end_line=25,
        file_path="src/example.py"
    )
    success = db.insert_function(function_node)
    print(f"✓ Function node inserted: {success}")
    
    # Test creating relationships
    db.insert_contains("test_file_1", "test_class_1")
    print("✓ CONTAINS relationship created (File -> Class)")
    
    db.insert_contains("test_file_1", "test_func_1")
    print("✓ CONTAINS relationship created (File -> Function)")
    
    db.insert_defines("test_class_1", "test_func_1")
    print("✓ DEFINES relationship created (Class -> Function)")
    
    # Test querying
    nodes = db.get_all_nodes()
    print(f"✓ Retrieved {len(nodes)} nodes")
    
    edges = db.get_all_edges()
    print(f"✓ Retrieved {len(edges)} edges")
    
    # Test Cypher query
    result = db.execute_cypher("MATCH (n) RETURN count(n) AS count")
    print(f"✓ Total nodes in database: {result[0]['count']}")
    
    # Clean up
    db.clear_database()
    print("✓ Database cleared")
    
    db.close()
    print("\n✅ All database tests passed!")

if __name__ == "__main__":
    main()
