"""
Test Suite for API Agent
Uses Pytest fixtures
"""

import sys
import builtins

# Add project root to path
sys.path.append(builtins.PROJECT_ROOT)
from Logic.API.PostsService.PostsController.builder import PostsController


class TestAPIAgent:
    """Test suite for API Agent"""

    posts_controller = PostsController()

    def test_create_posts(self):
        """
        Test API Agent functionality.
        """
        self.posts_controller.createPosts()

