import os
import shutil
import pytest
from datetime import datetime

# Test directories
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "test_output")
TEST_ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "test_artifacts")

def pytest_configure(config):
    """Configure test environment."""
    # Create test directories if they don't exist
    for directory in [TEST_DATA_DIR, TEST_OUTPUT_DIR, TEST_ARTIFACTS_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    # Set test mode environment variable
    os.environ["FOS_TEST_MODE"] = "1"

def pytest_unconfigure(config):
    """Clean up after all tests."""
    # Move test output to artifacts with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    artifacts_dir = os.path.join(TEST_ARTIFACTS_DIR, f"test_run_{timestamp}")
    os.makedirs(artifacts_dir, exist_ok=True)
    
    # Move test output files to artifacts
    for item in os.listdir(TEST_OUTPUT_DIR):
        src = os.path.join(TEST_OUTPUT_DIR, item)
        dst = os.path.join(artifacts_dir, item)
        if os.path.isfile(src):
            shutil.move(src, dst)
        elif os.path.isdir(src):
            shutil.move(src, dst)
    
    # Clean test data directory
    for item in os.listdir(TEST_DATA_DIR):
        item_path = os.path.join(TEST_DATA_DIR, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)
    
    # Remove test mode environment variable
    if "FOS_TEST_MODE" in os.environ:
        del os.environ["FOS_TEST_MODE"]

@pytest.fixture(autouse=True)
def test_environment():
    """Ensure test environment is properly configured."""
    # Verify test directories exist
    for directory in [TEST_DATA_DIR, TEST_OUTPUT_DIR, TEST_ARTIFACTS_DIR]:
        assert os.path.exists(directory), f"Test directory {directory} does not exist"
    
    # Verify test mode is enabled
    assert os.environ.get("FOS_TEST_MODE") == "1", "Test mode not enabled"
    
    yield
    
    # Clean test output after each test
    for item in os.listdir(TEST_OUTPUT_DIR):
        item_path = os.path.join(TEST_OUTPUT_DIR, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path) 