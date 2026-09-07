"""
Integration tests for the complete pipeline.
"""

import pytest
from src.utils import validate_image_path, load_env_vars


class TestPipelineIntegration:
    """Integration tests for the pipeline."""
    
    def test_env_vars_loading(self):
        """Test loading environment variables."""
        # Note: This requires .env file to be present
        env_vars = load_env_vars()
        
        # Should at least load the function without error
        assert isinstance(env_vars, dict)
    
    def test_image_validation(self):
        """Test image path validation."""
        # Valid extensions
        assert not validate_image_path("nonexistent.jpg")
        
        # Invalid extension
        assert not validate_image_path("test.txt")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
