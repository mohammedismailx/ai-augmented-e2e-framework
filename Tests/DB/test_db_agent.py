import pytest


class TestDBIntentExecution:
    @pytest.mark.db_intent
    @pytest.mark.id("DB-001")
    @pytest.mark.title("Verify Agents Table Schema")
    def test_get_all_agents(self, db_context):
        db_context.execute_by_intent(
            intent="verify that ther is an agent like name Rowen and that his address like emirates"
        )

    @pytest.mark.db_intent
    @pytest.mark.id("DB-002")
    @pytest.mark.title("Verify Agents Table Schema")
    def test_get_all_agents(self, db_context):
        db_context.execute_by_intent(
            intent="verify that Reumaysa email domain is yahoo"
        )

    @pytest.mark.db_intent
    @pytest.mark.id("DB-002")
    @pytest.mark.title("Verify Agents Table Schema")
    def test_get_all_agents(self, db_context):
        db_context.execute_by_intent(intent="verify that Shawn action is a Principle")
