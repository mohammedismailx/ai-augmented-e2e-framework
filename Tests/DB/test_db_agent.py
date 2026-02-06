"""
Intent-Based Database Testing with RAG + GitLab Duo

This module demonstrates the DB intent execution flow:
1. User provides natural language intent
2. RAG retrieves relevant schema context + learning examples
3. GitLab Duo generates SQL query
4. Query is executed and analyzed
5. Result is stored for future learning (correct/incorrect)

Usage:
    pytest Tests/DB/test_db_agent.py -v -s
"""

import pytest


class TestDBIntentExecution:
    """
    Test class for intent-based database query execution.

    Uses the db_context fixture which:
    - Embeds database schema into ChromaDB
    - Provides DBConnector with execute_by_intent() method
    - Stores query results for learning
    """

    @pytest.mark.db_intent
    @pytest.mark.id("DB-001")
    @pytest.mark.title("Verify Agents Table Schema")
    def test_get_all_agents(self, db_context):
        result = db_context.execute_by_intent(
            intent="verify that the agents table contains an agent name column"
        )
        # Assert based on AI analysis result
        assert result[
            "success"
        ], f"AI Analysis Failed: {result.get('reason', 'No reason provided')}"
