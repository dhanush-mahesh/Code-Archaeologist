"""
Tests for IngestionService
Includes unit tests and property-based tests
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings

from ingestion import IngestionService, JobStatus
from parser import TreeSitterParser
from database import KuzuDB


class TestIngestionService:
    """Test suite for IngestionService"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def db(self, temp_dir):
        """Create test database"""
        db_path = temp_dir / "test_db"
        return KuzuDB(str(db_path))
    
    @pytest.fixture
    def parser(self):
        """Create parser instance"""
        return TreeSitterParser()
    
    @pytest.fixture
    def service(self, db, parser, temp_dir):
        """Create ingestion service"""
        repo_dir = temp_dir / "repos"
        return IngestionService(db, parser, str(repo_dir))
    
    # ========== Unit Tests ==========
    
    def test_validate_repo_url_valid(self, service):
        """Test URL validation with valid GitHub URLs"""
        valid_urls = [
            "https://github.com/user/repo",
            "https://github.com/user/repo.git",
            "https://github.com/org/project-name",
        ]
        
        for url in valid_urls:
            assert service.validate_repo_url(url), f"Should accept valid URL: {url}"
    
    def test_validate_repo_url_invalid(self, service):
        """Test URL validation with invalid URLs"""
        invalid_urls = [
            "not-a-url",
            "https://example.com/repo",
            "https://github.com",
            "https://github.com/user",
            "",
        ]
        
        for url in invalid_urls:
            assert not service.validate_repo_url(url), f"Should reject invalid URL: {url}"
    
    def test_get_supported_files(self, service, temp_dir):
        """Test getting supported files from directory"""
        # Create test directory structure
        test_repo = temp_dir / "test_repo"
        test_repo.mkdir()
        
        # Create supported files
        (test_repo / "main.py").write_text("print('hello')")
        (test_repo / "app.js").write_text("console.log('hello')")
        (test_repo / "component.tsx").write_text("export const Component = () => {}")
        
        # Create unsupported files
        (test_repo / "README.md").write_text("# README")
        (test_repo / "data.json").write_text("{}")
        
        # Create subdirectory with files
        subdir = test_repo / "src"
        subdir.mkdir()
        (subdir / "utils.py").write_text("def util(): pass")
        
        # Create node_modules (should be skipped)
        node_modules = test_repo / "node_modules"
        node_modules.mkdir()
        (node_modules / "lib.js").write_text("// library")
        
        # Get supported files
        files = service.get_supported_files(test_repo)
        file_names = [f.name for f in files]
        
        # Verify
        assert "main.py" in file_names
        assert "app.js" in file_names
        assert "component.tsx" in file_names
        assert "utils.py" in file_names
        assert "README.md" not in file_names
        assert "data.json" not in file_names
        assert "lib.js" not in file_names  # node_modules should be skipped
    
    def test_parse_repository(self, service, temp_dir):
        """Test parsing a repository"""
        # Create test repository
        test_repo = temp_dir / "test_repo"
        test_repo.mkdir()
        
        # Create Python file
        python_code = '''
class TestClass:
    def method(self):
        pass

def function():
    pass
'''
        (test_repo / "test.py").write_text(python_code)
        
        # Create JavaScript file
        js_code = '''
class User {
    greet() {
        console.log("Hello");
    }
}
'''
        (test_repo / "user.js").write_text(js_code)
        
        # Parse repository
        files, classes, functions, edges, errors = service.parse_repository(test_repo)
        
        # Verify
        assert len(files) == 2, f"Expected 2 files, got {len(files)}"
        assert len(classes) == 2, f"Expected 2 classes, got {len(classes)}"
        assert len(functions) >= 2, f"Expected at least 2 functions, got {len(functions)}"
        assert len(errors) == 0, f"Expected no errors, got {errors}"
    
    def test_parse_repository_with_errors(self, service, temp_dir):
        """Test that parsing continues after errors"""
        # Create test repository
        test_repo = temp_dir / "test_repo"
        test_repo.mkdir()
        
        # Create valid file
        (test_repo / "valid.py").write_text("def valid(): pass")
        
        # Create malformed file
        (test_repo / "broken.py").write_text("def broken(\n# missing closing paren")
        
        # Create another valid file
        (test_repo / "valid2.py").write_text("def valid2(): pass")
        
        # Parse repository
        files, classes, functions, edges, errors = service.parse_repository(test_repo)
        
        # Should have parsed the valid files
        assert len(files) >= 2, "Should parse valid files despite errors"
        # Errors list may or may not contain the broken file depending on parser behavior
    
    def test_insert_into_database(self, service, temp_dir):
        """Test inserting parsed data into database"""
        # Create test repository and parse it
        test_repo = temp_dir / "test_repo"
        test_repo.mkdir()
        
        code = '''
class MyClass:
    def my_method(self):
        pass
'''
        (test_repo / "test.py").write_text(code)
        
        files, classes, functions, edges, errors = service.parse_repository(test_repo)
        
        # Insert into database
        success, message, nodes_inserted, edges_inserted = service.insert_into_database(
            files, classes, functions, edges
        )
        
        # Verify
        assert success, f"Insertion should succeed: {message}"
        assert nodes_inserted > 0, "Should insert nodes"
        assert edges_inserted > 0, "Should insert edges"
        
        # Verify data is in database
        all_nodes = service.db.get_all_nodes()
        assert len(all_nodes) == nodes_inserted, "Node count should match"
    
    def test_ingest_repository_invalid_url(self, service):
        """Test ingestion with invalid URL"""
        result = service.ingest_repository("not-a-valid-url")
        
        assert result.status == "error"
        assert "Invalid repository URL" in result.message
        assert result.files_processed == 0
        assert result.nodes_created == 0
    
    # ========== Property-Based Tests ==========
    
    @settings(max_examples=50, deadline=500)  # Increase deadline for DB operations
    @given(
        url_path=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=20)
    )
    def test_property_invalid_urls_produce_errors(self, url_path):
        """
        Property 4: Invalid URLs produce error messages
        Validates: Requirements 1.4
        
        For any invalid URL, the service should return an error status.
        """
        temp_dir = Path(tempfile.mkdtemp())
        try:
            db = KuzuDB(str(temp_dir / "db"))
            parser = TreeSitterParser()
            service = IngestionService(db, parser, str(temp_dir / "repos"))
            
            # Create an invalid URL (not a GitHub URL)
            invalid_url = f"https://example.com/{url_path}"
            
            result = service.ingest_repository(invalid_url)
            
            # Should return error status
            assert result.status == "error", f"Invalid URL should produce error status"
            assert len(result.message) > 0, "Error message should not be empty"
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_property_parse_failures_dont_stop_processing(self, service, temp_dir):
        """
        Property 33: Parse failures don't stop processing
        Validates: Requirements 10.2
        
        When one file fails to parse, other files should still be processed.
        """
        # Create test repository
        test_repo = temp_dir / "test_repo"
        test_repo.mkdir()
        
        # Create multiple valid files
        for i in range(5):
            (test_repo / f"valid_{i}.py").write_text(f"def func_{i}(): pass")
        
        # Create a potentially problematic file (empty)
        (test_repo / "empty.py").write_text("")
        
        # Parse repository
        files, classes, functions, edges, errors = service.parse_repository(test_repo)
        
        # Should have parsed the valid files
        assert len(files) >= 5, "Should parse all valid files despite any errors"
    
    def test_property_all_supported_files_are_parsed(self, service, temp_dir):
        """
        Property 2: All supported files are parsed
        Validates: Requirements 1.2
        
        For any repository, all Python and JavaScript files should be parsed.
        """
        # Create test repository with various file types
        test_repo = temp_dir / "test_repo"
        test_repo.mkdir()
        
        # Create supported files
        supported_files = [
            ("file1.py", "def func1(): pass"),
            ("file2.js", "function func2() {}"),
            ("file3.tsx", "export const Component = () => {}"),
        ]
        
        for filename, content in supported_files:
            (test_repo / filename).write_text(content)
        
        # Create unsupported files
        (test_repo / "README.md").write_text("# README")
        (test_repo / "data.json").write_text("{}")
        
        # Parse repository
        files, classes, functions, edges, errors = service.parse_repository(test_repo)
        
        # Should have parsed all supported files
        assert len(files) == len(supported_files), f"Should parse all {len(supported_files)} supported files"
    
    def test_property_parsed_entities_persisted(self, service, temp_dir):
        """
        Property 7: Parsed entities are persisted to database
        Validates: Requirements 2.8
        
        For any parsed repository, all entities should be stored in the database.
        """
        # Create test repository
        test_repo = temp_dir / "test_repo"
        test_repo.mkdir()
        
        code = '''
class DataProcessor:
    def process(self, data):
        return self.clean(data)
    
    def clean(self, data):
        return data.strip()
'''
        (test_repo / "processor.py").write_text(code)
        
        # Parse repository
        files, classes, functions, edges, errors = service.parse_repository(test_repo)
        
        # Insert into database
        success, message, nodes_inserted, edges_inserted = service.insert_into_database(
            files, classes, functions, edges
        )
        
        assert success, "Insertion should succeed"
        
        # Query database to verify persistence
        all_nodes = service.db.get_all_nodes()
        all_edges = service.db.get_all_edges()
        
        # All parsed entities should be in database
        expected_nodes = len(files) + len(classes) + len(functions)
        assert len(all_nodes) == expected_nodes, f"Expected {expected_nodes} nodes in DB, got {len(all_nodes)}"
        assert len(all_edges) == len(edges), f"Expected {len(edges)} edges in DB, got {len(all_edges)}"
