"""
Unit tests for image search module.
"""

import pytest
from src.image_search import ReverseImageSearcher


class TestReverseImageSearcher:
    """Test reverse image search functionality."""
    
    @pytest.fixture
    def searcher(self):
        """Create an image searcher instance."""
        return ReverseImageSearcher("test_api_key")
    
    def test_searcher_initialization(self, searcher):
        """Test searcher initializes correctly."""
        assert searcher is not None
        assert searcher.api_key == "test_api_key"
        assert searcher.similarity_threshold == 0.85
    
    def test_handle_missing_image(self, searcher):
        """Test handling of missing image file."""
        results = searcher.search_image("nonexistent.jpg")
        assert results == []
    
    def test_social_media_domain_extraction(self):
        """Test extracting social media handles from URLs."""
        url = "https://twitter.com/username/status/123456"
        handle = ReverseImageSearcher.extract_social_media_handle(url)
        assert handle == "username" or handle == "twitter.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
