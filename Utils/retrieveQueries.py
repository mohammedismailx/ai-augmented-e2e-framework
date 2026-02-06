import builtins
import time
from Utils.db_connector import DBConnector
from Logic.API.api_wrapper import APIWrapper
from Utils.query_constants import QUERIES, retrieve_query


def retrieve_and_execute_query(
    query_name, intent, db_connector: DBConnector, max_retries=3, **params
):
    """
    Retrieves, formats, and executes a query with AI self-healing.
    """
    # 1. Get and format base query
    query_template = getattr(QUERIES, query_name, None)
    if not query_template:
        print(
            f"⚠️ Query template '{query_name}' not found. Falling back directly to AI intent."
        )
        query = None
    else:
        try:
            query = query_template.format(**params)
        except Exception as e:
            print(f"❌ Error formatting query: {e}")
            query = None

    last_error = None

    # 2. Performance-based Execution with Retries
    for attempt in range(1, max_retries + 1):
        if not query:
            break

        print(f"Attempt {attempt}/{max_retries} executing query: {query}")
        try:
            results = db_connector.execute_query(query)
            if results is not None:
                return results
        except Exception as e:
            last_error = str(e)
            print(f"❌ Query execution failed: {last_error}")
            time.sleep(1)  # Simple backoff

    # 3. AI Interaction (Self-Healing / Intent-based Retrieval)
    agent_mode = builtins.CONFIG.get("agent_mode", "ENABLED")
    if agent_mode == "ENABLED":
        print(f"Triggering AI Agent for DB intent: '{intent}'")

        # Initialize APIWrapper and Agent locally (Wrapper stays in Wrapper)
        ai_api_wrapper = APIWrapper(builtins.URLS.get("gitlab", {}).get("base_url"))
        ai_agent = ai_api_wrapper.ai_agent

        # Run agent for QUERY_CREATION
        ai_suggested_query = ai_agent.run_agent_based_on_context(
            context="QUERY_CREATION", db_requirement=intent, db_connector=db_connector
        )

        if ai_suggested_query:
            print(f"🤖 AI suggested query: {ai_suggested_query}")
            # Try executing AI query
            try:
                results = db_connector.execute_query(ai_suggested_query)
                if results is not None:
                    print("✓ AI self-healing successful.")
                    return results
            except Exception as e:
                print(f"❌ AI suggested query also failed: {e}")
        else:
            print("❌ AI Agent failed to provide a query.")

    raise Exception(
        f"Failed to retrieve data from DB after {max_retries} retries and AI interaction. Last error: {last_error}"
    )
