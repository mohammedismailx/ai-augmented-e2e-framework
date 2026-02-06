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


class TestAPIAgent:
    """Test suite for API Agent"""

    posts_controller = PostsController()

    def test_create_posts(self):
        """
        Test API Agent functionality.
        """
        self.posts_controller.createPosts()


class TestIntentBasedAPI:
    # """
    # Test suite for Intent-Based API Execution using RAG + GitLab Duo.

    # These tests demonstrate the AI-powered API testing capability where:
    # 1. Natural language intent is converted to API calls
    # 2. Swagger documentation is used via RAG for context
    # 3. GitLab Duo generates and analyzes curl commands
    # """

    # # Base URL for FakeRESTAPI
    BASE_URL = "https://fakerestapi.azurewebsites.net"

    # def test_get_all_books(self, api_wrapper, api_context):
    #     """
    #     Test: Get all books using natural language intent.
    #     Intent: "get all books" -> GET /api/v1/Books
    #     """
    #     result = api_wrapper.execute_by_intent(
    #         intent="get all books", base_url=self.BASE_URL, rag_instance=api_context
    #     )

    #     assert result["success"], f"API call failed: {result.get('error')}"
    #     assert (
    #         result["status_code"] == 200
    #     ), f"Expected status 200, got {result['status_code']}"
    #     print(f"\n[TEST] Get all books - PASSED")
    #     print(f"[Response preview] {result['response_body'][:200]}...")

    def test_get_book_by_id(self, api_wrapper, api_context):
        """
        Test: Get a specific book by ID.
        Intent: "get book with id 1" -> GET /api/v1/Books/1

        The assertion is based on GitLab Duo's AI analysis of the response,
        not hard-coded status code checks.
        """
        result = api_wrapper.execute_by_intent(
            intent="get book with id 1",
            base_url=self.BASE_URL,
            rag_instance=api_context,
        )

        # Assert based on AI analysis result
        assert result[
            "success"
        ], f"AI Analysis Failed: {result.get('reason', 'No reason provided')}"
        print(f"\n[TEST] Get book by ID - PASSED")
        print(f"[AI Analysis] {result.get('reason', 'N/A')}")

    # def test_delete_book(self, api_wrapper, api_context):
    #     """
    #     Test: Delete a book by ID.
    #     Intent: "delete book number 5" -> DELETE /api/v1/Books/5
    #     """
    #     result = api_wrapper.execute_by_intent(
    #         intent="delete book number 5",
    #         base_url=self.BASE_URL,
    #         rag_instance=api_context,
    #     )

    #     assert result["success"], f"API call failed: {result.get('error')}"
    #     # DELETE typically returns 200 with empty body
    #     assert (
    #         result["status_code"] == 200
    #     ), f"Expected status 200, got {result['status_code']}"
    #     print(f"\n[TEST] Delete book - PASSED")

    # def test_create_new_activity(self, api_wrapper, api_context):
    #     """
    #     Test: Create a new activity.
    #     Intent: "create a new activity with title 'Test Activity'" -> POST /api/v1/Activities
    #     """
    #     result = api_wrapper.execute_by_intent(
    #         intent="create a new activity with title 'Test Activity' and mark it as completed",
    #         base_url=self.BASE_URL,
    #         rag_instance=api_context,
    #     )

    #     assert result["success"], f"API call failed: {result.get('error')}"
    #     assert (
    #         result["status_code"] == 200
    #     ), f"Expected status 200, got {result['status_code']}"
    #     print(f"\n[TEST] Create activity - PASSED")

    # def test_get_all_users(self, api_wrapper, api_context):
    #     """
    #     Test: Get all users.
    #     Intent: "list all users" -> GET /api/v1/Users
    #     """
    #     result = api_wrapper.execute_by_intent(
    #         intent="list all users", base_url=self.BASE_URL, rag_instance=api_context
    #     )

    #     assert result["success"], f"API call failed: {result.get('error')}"
    #     assert (
    #         result["status_code"] == 200
    #     ), f"Expected status 200, got {result['status_code']}"
    #     print(f"\n[TEST] Get all users - PASSED")

    # def test_update_user(self, api_wrapper, api_context):
    #     """
    #     Test: Update a user.
    #     Intent: "update user 3 with username 'updated_user'" -> PUT /api/v1/Users/3
    #     """
    #     result = api_wrapper.execute_by_intent(
    #         intent="update user with id 3 with username 'updated_user' and password 'pass123'",
    #         base_url=self.BASE_URL,
    #         rag_instance=api_context,
    #     )

    #     assert result["success"], f"API call failed: {result.get('error')}"
    #     assert (
    #         result["status_code"] == 200
    #     ), f"Expected status 200, got {result['status_code']}"
    #     print(f"\n[TEST] Update user - PASSED")

    # def test_get_authors_for_book(self, api_wrapper, api_context):
    #     """
    #     Test: Get authors for a specific book.
    #     Intent: "get authors for book 1" -> GET /api/v1/Authors/authors/books/1
    #     """
    #     result = api_wrapper.execute_by_intent(
    #         intent="get all authors for book number 1",
    #         base_url=self.BASE_URL,
    #         rag_instance=api_context,
    #     )

    #     # This may or may not succeed depending on API structure
    #     print(f"\n[TEST] Get authors for book")
    #     print(f"[Result] Success: {result['success']}, Status: {result['status_code']}")
    #     print(f"[Analysis] {result.get('analysis', 'N/A')[:300]}...")
