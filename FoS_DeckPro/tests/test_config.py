import os
import pytest
from pathlib import Path
from FoS_DeckPro.logic.config import Config

def test_test_mode_detection():
    """Test that test mode is correctly detected."""
    config = Config()
    assert config.is_test_mode == True  # Should be True in test environment
    
    # Temporarily disable test mode
    old_value = os.environ.get("FOS_TEST_MODE")
    os.environ["FOS_TEST_MODE"] = "0"
    config = Config()
    assert config.is_test_mode == False
    if old_value:
        os.environ["FOS_TEST_MODE"] = old_value
    else:
        del os.environ["FOS_TEST_MODE"]

def test_test_path_detection():
    """Test that test paths are correctly identified."""
    config = Config()
    test_root = Path(__file__).parent
    
    # Test valid test paths
    assert config.is_test_path(test_root / "test_data" / "test.db")
    assert config.is_test_path(test_root / "test_output" / "output.txt")
    assert config.is_test_path(test_root / "test_artifacts" / "artifact.json")
    
    # Test invalid test paths
    assert not config.is_test_path(Path.home() / ".fos_deckpro" / "data.db")
    assert not config.is_test_path(Path.home() / "Documents" / "output.txt")

def test_path_validation():
    """Test that path validation works correctly."""
    config = Config()
    test_root = Path(__file__).parent
    
    # Should allow test paths in test mode
    config.validate_path(test_root / "test_data" / "test.db")
    
    # Temporarily disable test mode
    old_value = os.environ.get("FOS_TEST_MODE")
    os.environ["FOS_TEST_MODE"] = "0"
    config = Config()
    
    # Should raise error for test paths in production mode
    with pytest.raises(RuntimeError):
        config.validate_path(test_root / "test_data" / "test.db")
    
    # Should allow non-test paths in production mode
    config.validate_path(Path.home() / ".fos_deckpro" / "data.db")
    
    if old_value:
        os.environ["FOS_TEST_MODE"] = old_value
    else:
        del os.environ["FOS_TEST_MODE"]

def test_directory_access():
    """Test that directory access works correctly."""
    config = Config()
    
    # Should allow access to test directories in test mode
    assert config.get_test_dir("test_data").exists()
    assert config.get_test_dir("test_output").exists()
    assert config.get_test_dir("test_artifacts").exists()
    
    # Should raise error for invalid test directory
    with pytest.raises(ValueError):
        config.get_test_dir("invalid_dir")
    
    # Temporarily disable test mode
    old_value = os.environ.get("FOS_TEST_MODE")
    os.environ["FOS_TEST_MODE"] = "0"
    config = Config()
    
    # Should raise error for test directory access in production mode
    with pytest.raises(RuntimeError):
        config.get_test_dir("test_data")
    
    if old_value:
        os.environ["FOS_TEST_MODE"] = old_value
    else:
        del os.environ["FOS_TEST_MODE"] 