import pytest


class TestIntentBasedAPI:
    @pytest.mark.api_intent
    @pytest.mark.id("API-001")
    @pytest.mark.title("Get Book by ID")
    def test_get_book_by_id(self, api_wrapper):
        api_wrapper.execute_by_intent(intent="get book with id 1")

    @pytest.mark.api_intent
    @pytest.mark.id("API-002")
    @pytest.mark.title("Get Activity by ID and verify title")
    def test_get_activity_by_id(self, api_wrapper):
        api_wrapper.execute_by_intent(
            intent="Get Activity with ID 5 and verify that its title is Activity 10"
        )
