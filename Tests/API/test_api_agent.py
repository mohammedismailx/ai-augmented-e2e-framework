"""
Test Suite for API Agent
Uses Pytest fixtures
"""

import sys
import builtins
import pytest

# Add project root to path
sys.path.append(builtins.PROJECT_ROOT)
from Logic.API.PostsService.PostsController.builder import PostsController


class TestIntentBasedAPI:
    @pytest.mark.api_intent
    @pytest.mark.id("API-001")
    @pytest.mark.title("Get Book by ID")
    def test_get_book_by_id(self, api_wrapper):
        result = api_wrapper.execute_by_intent(intent="get book with id 1")
        # Assert based on AI analysis result
        assert result[
            "success"
        ], f"AI Analysis Failed: {result.get('reason', 'No reason provided')}"

   