import os
from pathlib import Path

class Config:
    """Configuration manager with test mode safety checks."""
    
    def __init__(self):
        self.is_test_mode = os.environ.get("FOS_TEST_MODE") == "1"
        self.test_dirs = [
            "test_data",
            "test_output",
            "test_artifacts"
        ]
    
    def get_test_dir(self, dir_name: str) -> Path:
        """Get path to a test directory."""
        if not self.is_test_mode:
            raise RuntimeError("Cannot access test directories outside of test mode")
        if dir_name not in self.test_dirs:
            raise ValueError(f"Invalid test directory: {dir_name}")
        return Path(__file__).parent.parent / "tests" / dir_name
    
    def is_test_path(self, path: str | Path) -> bool:
        """Check if a path is within test directories."""
        path = Path(path)
        test_root = Path(__file__).parent.parent / "tests"
        return any(
            str(path).startswith(str(test_root / test_dir))
            for test_dir in self.test_dirs
        )
    
    def validate_path(self, path: str | Path) -> None:
        """Validate that a path is safe to use."""
        path = Path(path)
        if not self.is_test_mode and self.is_test_path(path):
            raise RuntimeError(
                f"Attempted to access test path in production mode: {path}\n"
                "This is not allowed for safety reasons."
            )
    
    def get_app_data_dir(self) -> Path:
        """Get the application data directory."""
        if self.is_test_mode:
            return self.get_test_dir("test_data")
        return Path.home() / ".fos_deckpro"
    
    def get_output_dir(self) -> Path:
        """Get the output directory."""
        if self.is_test_mode:
            return self.get_test_dir("test_output")
        return self.get_app_data_dir() / "output"

# Global config instance
config = Config() 