import mysql.connector
from mysql.connector import Error
import builtins
import json
from Utils.logger import FrameworkLogger as log


class DBConnector:
    def __init__(self, host=None, port=None, user=None, password=None, database=None):
        """
        Initialize the database connection using configuration or provided parameters.
        """
        self.host = host or "127.0.0.1"
        self.port = port or "3306"
        self.user = user or "root"
        self.password = password or "22132213"
        self.database = database or "testdb"
        self.connection = None
        self._ai_agent = None
        self._rag_instance = None

    @property
    def ai_agent(self):
        """Lazy load AIAgent with APIWrapper to avoid circular imports."""
        if self._ai_agent is None:
            from Utils.ai_agent import AIAgent
            from Logic.API.api_wrapper import APIWrapper

            # Create APIWrapper for AI communication
            api_wrapper = APIWrapper()
            self._ai_agent = AIAgent(api_wrapper=api_wrapper)
        return self._ai_agent

    @property
    def rag_instance(self):
        """Get RAG instance from builtins (set by conftest fixture)."""
        if self._rag_instance is None:
            self._rag_instance = getattr(builtins, "RAG_DB_INSTANCE", None)
        return self._rag_instance

    def connect(self):
        """Establish the database connection."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
            )
            if self.connection.is_connected():
                log.safe_print(f"[OK] Connected to MySQL database: {self.database}")
                return self.connection
        except Error as e:
            log.safe_print(f"[ERROR] Error connecting to MySQL: {e}")
            return None

    def execute_query(self, query):
        """Execute a query and return results."""
        if not self.connection or not self.connection.is_connected():
            self.connect()

        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as e:
            log.safe_print(f"[ERROR] Error executing query: {e}")
            return None
        finally:
            cursor.close()

    def close(self):
        """Close the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            log.safe_print("[OK] MySQL connection closed")

    # ========================================================================
    # INTENT-BASED QUERY EXECUTION (RAG + GitLab Duo) - TF-IDF FLOW
    # ========================================================================

    def execute_by_intent(
        self, intent, max_retries=2, log_intent=True, assert_success=True
    ):
        """
        Execute database query based on natural language intent using TF-IDF flow.

        This follows the same unified pattern as UI and API:
        1. TF-IDF: Search schema doc by intent → extract table name
        2. RAG: Retrieve stored action from db_learning collection (by table)
        3. DUO: Send BOTH schema_context AND stored_metadata to generate query
        4. EXECUTE: Run the generated SQL query
        5. ANALYZE: AI analyzes the result
        6. STORE: Store action with [correct]/[incorrect] status
        7. ASSERT: Optionally raise AssertionError if AI analysis fails

        Args:
            intent (str): Natural language description of what to query
                         e.g., "verify that the agents table contains an agent name column"
            max_retries (int): Maximum retry attempts on failure
            log_intent (bool): Whether to log intent details
            assert_success (bool): If True, raises AssertionError when AI analysis fails.
                                  Default is True for test convenience.

        Returns:
            dict: {
                "success": bool,
                "reason": str,
                "data": list or None,
                "query": str,
                "error": str or None
            }

        Raises:
            AssertionError: If assert_success=True and the AI analysis indicates failure
        """
        # Initialize logger with DB test type
        from Utils.logger import IntentLogger
        from Resources.prompts import get_db_query_action_prompt

        logger = IntentLogger(test_type="DB")
        logger.start_session(intent=intent)

        separator = "=" * 70
        sub_separator = "-" * 70

        if log_intent:
            logger.log(f"\n{separator}")
            logger.log(f"  DB INTENT-BASED QUERY EXECUTION (TF-IDF FLOW)")
            logger.log(f"{separator}")
            logger.log(f"  Intent: {intent}")
            logger.log(f"{separator}\n")

        # Ensure we have RAG instance
        if not self.rag_instance:
            error_msg = "RAG instance not available. Ensure db_context fixture is used."
            logger.log(f"  [ERROR] {error_msg}")
            logger.end_session()
            return {
                "success": False,
                "reason": error_msg,
                "data": None,
                "query": None,
                "error": error_msg,
            }

        # ============================================================================
        # STEP 1: TF-IDF - Extract Table from Schema by Intent
        # ============================================================================
        logger.log_section("[STEP 1] EXTRACT TABLE FROM SCHEMA BY INTENT")

        table, schema_context = self.rag_instance.extract_table_from_schema_by_intent(
            intent
        )

        logger.log(f"[TABLE] Extracted: {table}")
        if schema_context:
            logger.log(f"[SCHEMA] Found context ({len(schema_context)} chars)")
            logger.log_titled_block("SCHEMA CONTEXT", schema_context, max_chars=2000)
        else:
            logger.log(f"[SCHEMA] No schema context found")

        # ============================================================================
        # STEP 2: RAG - Retrieve Stored Action from Learning Collection
        # ============================================================================
        logger.log_section(
            f"[STEP 2] CHROMADB - RETRIEVING FROM DB LEARNING COLLECTION"
        )

        learning_result = self.rag_instance.retrieve_db_action_for_intent(table, intent)
        stored_metadata = learning_result.get("stored_metadata")
        match_score = learning_result.get("match_score", 0.0)

        if stored_metadata and learning_result.get("status") == "[correct]":
            logger.log(
                f"\n[OK] Found [correct] stored action (match_score: {match_score:.3f})"
            )
            logger.log_titled_block(
                "STORED METADATA", json.dumps(stored_metadata, indent=2), max_chars=3000
            )
        else:
            if stored_metadata:
                logger.log(
                    f"\n[INFO] Found stored action but status is {learning_result.get('status')}"
                )
            else:
                logger.log(f"\n[INFO] No stored action found for this intent")
            logger.log(f"  Will generate query from schema context")

        # ============================================================================
        # STEP 3: Build Prompt with BOTH schema_context AND stored_metadata
        # ============================================================================
        logger.log_section("[STEP 3] BUILDING DUO PROMPT WITH BOTH CONTEXTS")

        prompt = get_db_query_action_prompt(
            table=table,
            intent=intent,
            schema_context=schema_context,
            stored_metadata=stored_metadata,
        )

        logger.log_duo_prompt(prompt)

        # ============================================================================
        # STEP 4: GitLab DUO - Generate Query Action Metadata
        # ============================================================================
        logger.log_section("[STEP 4] GITLAB DUO - GENERATE QUERY ACTION")

        duo_response_raw = self.ai_agent.run_agent_based_on_context(
            context="DB_QUERY_ACTION",
            prompt=prompt,
        )

        logger.log_duo_response(duo_response_raw)

        if not duo_response_raw:
            error_msg = "Failed to get response from GitLab Duo"
            logger.log(f"[ERROR] {error_msg}")
            logger.end_session()
            return {
                "success": False,
                "reason": error_msg,
                "data": None,
                "query": None,
                "error": error_msg,
            }

        # ============================================================================
        # STEP 5: Parse DUO Response
        # ============================================================================
        logger.log_section("[STEP 5] PARSING DUO RESPONSE")

        try:
            duo_response = self._parse_duo_json_response(duo_response_raw)
            sql_query = duo_response.get("query", "")
            action_key = duo_response.get("action_key", "unknown")
            operation = duo_response.get("operation", "SELECT")

            if not sql_query:
                raise ValueError("No query in DUO response")

            sql_query = self._clean_sql_query(sql_query)

            logger.log(f"[ACTION KEY] {action_key}")
            logger.log(f"[OPERATION] {operation}")
            logger.log(f"[QUERY] {sql_query}")

            logger.log(f"\n[OK] Parsed action metadata:")
            logger.log_titled_block(
                "QUERY METADATA", json.dumps(duo_response, indent=2), max_chars=2000
            )

        except Exception as e:
            error_msg = f"Failed to parse DUO response: {e}"
            logger.log(f"[ERROR] {error_msg}")
            logger.end_session()
            return {
                "success": False,
                "reason": error_msg,
                "data": None,
                "query": None,
                "error": error_msg,
            }

        # ============================================================================
        # STEP 6: Execute the Query
        # ============================================================================
        logger.log_section("[STEP 6] EXECUTING SQL QUERY")

        attempt = 0
        result = None
        error_message = None

        while attempt <= max_retries:
            logger.log(f"\n[Attempt {attempt + 1}/{max_retries + 1}]")
            logger.log(f"[Executing query]: {sql_query[:100]}...")

            try:
                result = self.execute_query(sql_query)
                if result is not None:
                    logger.log(f"\n[OK] Query executed successfully!")
                    logger.log(f"[Rows Returned] {len(result)}")
                    if result and len(result) > 0:
                        logger.log(f"[Sample Row] {result[0]}")
                    break
                else:
                    error_message = "Query returned None (possible execution error)"
                    logger.log(f"[ERROR] {error_message}")
            except Exception as e:
                error_message = str(e)
                logger.log(f"[ERROR] Execution failed: {error_message}")

            # Retry logic with AI analysis
            attempt += 1
            if attempt <= max_retries:
                # STEP 1: Get AI analysis of why the query failed
                logger.log(
                    f"\n[RETRY] Attempt {attempt}/{max_retries} - Getting AI analysis..."
                )
                ai_analysis = self.ai_agent.analyze_db_result(
                    intent=intent,
                    sql_query=sql_query,
                    result=f"ERROR: {error_message}",
                )
                ai_analysis_str = str(ai_analysis) if ai_analysis else ""
                logger.log(f"[RETRY] AI Analysis: {ai_analysis_str[:200]}...")

                # STEP 2: Use ENHANCED retry with AI analysis and all original context
                logger.log(f"[RETRY] Regenerating query with AI analysis context...")

                fixed_query = self.ai_agent.run_agent_based_on_context(
                    context="DB_QUERY_RETRY",
                    table=table,
                    intent=intent,
                    failed_query=sql_query,
                    error_output=error_message,
                    ai_analysis=ai_analysis_str,
                    stored_metadata=stored_metadata,  # Original stored metadata
                    schema_context=schema_context,
                    return_prompt=False,
                )

                if fixed_query:
                    sql_query = self._clean_sql_query(fixed_query)
                    logger.log(f"[OK] New Query: {sql_query}")
                else:
                    logger.log("[ERROR] Failed to regenerate query")
                    break

        logger.log_step_separator()

        # ============================================================================
        # STEP 7: Analyze Result with AI
        # ============================================================================
        logger.log_section("[STEP 7] GITLAB DUO - ANALYZING RESULT")

        if result is not None:
            result_str = json.dumps(result, default=str, indent=2)
            analysis = self.ai_agent.analyze_db_result(
                intent=intent, sql_query=sql_query, result=result_str
            )
        else:
            analysis = {
                "success": False,
                "reason": f"Query execution failed: {error_message}",
            }

        ai_success = analysis.get("success", False)
        ai_reason = analysis.get("reason", "N/A")

        logger.log(f"[AI Analysis] Result: {'PASS' if ai_success else 'FAIL'}")
        logger.log(f"[AI Analysis] Reason: {ai_reason}")

        logger.log_step_separator()

        # ============================================================================
        # STEP 8: Store in Learning Collection with Status
        # ============================================================================
        logger.log_section("[STEP 8] STORING RESULT IN DB LEARNING COLLECTION")

        is_correct = analysis.get("success", False)
        status = "[correct]" if is_correct else "[incorrect]"

        # Build DUO response dict for storage
        duo_for_storage = {
            "action_key": duo_response.get(
                "action_key", f"query_{table}_{intent[:20]}"
            ),
            "intent": intent,
            "query": sql_query,
            "expected_columns": duo_response.get("expected_columns", []),
            "expected_row_count": duo_response.get("expected_row_count", "unknown"),
        }

        self.rag_instance.store_db_action_from_duo(
            table=table,
            duo_response=duo_for_storage,
            status=status,
            query_result=str(result)[:500] if result else None,
            error=error_message if not is_correct else None,
        )

        logger.log(f"[Actual Status] {status}")
        logger.log(f"[Table] {table}")
        logger.log(f"[Action Key] {duo_for_storage['action_key']}")
        logger.log(f"[OK] Stored action with status {status}")

        logger.log_step_separator()

        # ============================================================================
        # EXECUTION SUMMARY
        # ============================================================================
        success = analysis.get("success", False) and result is not None
        reason = analysis.get("reason", "No reason provided")

        logger.log_section("EXECUTION SUMMARY")
        logger.log(f"  Intent: {intent}")
        logger.log(f"  Table: {table}")
        logger.log(f"  Query: {sql_query[:80]}...")
        logger.log(f"  Rows Returned: {len(result) if result else 0}")
        logger.log(f"  Learning Status Stored: {status}")
        logger.log(f"  AI Analysis Result: {'PASS' if success else 'FAIL'}")
        logger.log(f"  AI Analysis Reason: {reason[:50]}...")
        logger.log(f"  Error: {error_message if not success else 'None'}")

        # End the logging session
        logger.end_session()

        # Build result dict
        result_dict = {
            "success": success,
            "reason": reason,
            "data": result,
            "query": sql_query,
            "error": error_message if not success else None,
        }

        # ============================================================================
        # STEP 9: ASSERT SUCCESS (if enabled)
        # ============================================================================
        if assert_success and not success:
            raise AssertionError(f"AI Analysis Failed: {reason}")

        return result_dict

    def _parse_duo_json_response(self, response_raw):
        """
        Parse JSON from DUO response, handling markdown code blocks.
        """
        import re

        if not response_raw:
            return {}

        # Clean up the response
        response_text = response_raw.strip()

        # Remove markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        # Try to find JSON object
        response_text = response_text.strip()

        # Look for JSON object pattern
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)

        return json.loads(response_text)

    def _clean_sql_query(self, query):
        """
        Clean SQL query by removing markdown code blocks and extra whitespace.

        Args:
            query (str): Raw query string from AI

        Returns:
            str: Cleaned SQL query
        """
        if not query:
            return query

        # Remove markdown code blocks
        query = query.strip()
        if query.startswith("```sql"):
            query = query[6:]
        elif query.startswith("```"):
            query = query[3:]
        if query.endswith("```"):
            query = query[:-3]

        # Clean up whitespace
        query = query.strip()

        # Remove any leading/trailing quotes
        if (query.startswith('"') and query.endswith('"')) or (
            query.startswith("'") and query.endswith("'")
        ):
            query = query[1:-1]

        return query.strip()

    def _extract_tables_from_query(self, query):
        """
        Extract table names from a SQL query.

        Args:
            query (str): SQL query string

        Returns:
            list: List of table names found in the query
        """
        import re

        if not query:
            return []

        tables = []
        query_upper = query.upper()

        # Pattern to find table names after FROM and JOIN keywords
        # Matches: FROM table_name, JOIN table_name, INNER JOIN table_name, etc.
        patterns = [
            r"FROM\s+`?(\w+)`?",
            r"JOIN\s+`?(\w+)`?",
            r"INTO\s+`?(\w+)`?",
            r"UPDATE\s+`?(\w+)`?",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            tables.extend(matches)

        # Remove duplicates while preserving order
        seen = set()
        unique_tables = []
        for table in tables:
            if table.lower() not in seen:
                seen.add(table.lower())
                unique_tables.append(table)

        return unique_tables

    def get_table_schema(self, table_name):
        """
        Get the schema (column definitions) for a specific table.

        Args:
            table_name (str): Name of the table

        Returns:
            list: List of column definitions
        """
        query = f"DESCRIBE {table_name}"
        return self.execute_query(query)

    def get_all_tables(self):
        """
        Get list of all tables in the database.

        Returns:
            list: List of table names
        """
        query = "SHOW TABLES"
        result = self.execute_query(query)
        if result:
            # Extract table names from result
            return [list(row.values())[0] for row in result]
        return []

    def get_foreign_keys(self, table_name):
        """
        Get foreign key relationships for a table.

        Args:
            table_name (str): Name of the table

        Returns:
            list: List of foreign key definitions
        """
        query = f"""
        SELECT 
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = '{self.database}'
        AND TABLE_NAME = '{table_name}'
        AND REFERENCED_TABLE_NAME IS NOT NULL
        """
        return self.execute_query(query)
