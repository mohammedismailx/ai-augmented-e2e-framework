import sys
import builtins
import pytest

# Ensure project root is in path
if not hasattr(builtins, "PROJECT_ROOT"):
    import os

    builtins.PROJECT_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
sys.path.append(builtins.PROJECT_ROOT)

from Utils.db_connector import DBConnector
from Utils.retrieveQueries import retrieve_and_execute_query


class TestDBQueries:
    def test_get_agents_by_user_id(self, db_session):
        """
        Example test case to demonstrate DB connection and AI self-healing.
        """
        # 1. Execute smart query with intent
        # If the query name or execution fails, the AI will use the intent to find the data.
        try:
            results = retrieve_and_execute_query(
                query_name="GET_POSTS_BY_USER_ID",
                intent="Get all agent information for user id 5",
                db_connector=db_session,
                user_id=5,
            )

            if results:
                print(f"✓ Found {len(results)} records")
                for row in results:
                    print(row)
            else:
                print("ℹ No records found.")

        except Exception as e:
            print(f"⚠️ Smart DB retrieval failed: {e}")
