"""
Unit tests for face detection module.
"""

import pytest
import numpy as np
from src.face_detector import FaceDetector


class TestFaceDetector:
    """Test face detector functionality."""
    
    @pytest.fixture
    def detector(self):
        """Create a face detector instance."""
        return FaceDetector()
    
    def test_detector_initialization(self, detector):
        """Test detector initializes correctly."""
        assert detector is not None
        assert detector.min_face_size == 20
        assert detector.confidence_threshold == 0.6
    
    def test_invalid_image_path(self, detector):
        """Test handling of invalid image path."""
        result = detector.process_image("nonexistent.jpg")
        assert not result.get("success")
        assert "error" in result
    
    def test_face_encoding_hash_format(self, detector):
        """Test face encoding hash format."""
        # Create dummy encoding
        dummy_encoding = np.random.randn(128)
        hash_result = detector._encode_to_hash(dummy_encoding)
        
        # Verify it's a hex string of correct length
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
