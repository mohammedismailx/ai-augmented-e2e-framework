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
    # INTENT-BASED QUERY EXECUTION (RAG + GitLab Duo)
    # ========================================================================

    def execute_by_intent(self, intent, max_retries=2, log_intent=True):
        """
        Execute database query based on natural language intent.

        This is the main orchestrator method that:
        1. Retrieves relevant schema context from RAG
        2. Retrieves learning examples (correct/incorrect queries)
        3. Generates SQL query using GitLab Duo
        4. Executes the query
        5. Analyzes the result with AI
        6. Stores the query as correct/incorrect for future learning

        Args:
            intent (str): Natural language description of what to query
                         e.g., "get all posts by user with id 5"
            max_retries (int): Maximum retry attempts on failure
            log_intent (bool): Whether to log intent details

        Returns:
            dict: {
                "success": bool,
                "reason": str,
                "data": list or None,
                "query": str,
                "error": str or None
            }
        """
        # Initialize logger with DB test type (reads test ID from builtins automatically)
        from Utils.logger import IntentLogger

        logger = IntentLogger(test_type="DB")
        logger.start_session(intent=intent)

        separator = "=" * 70
        sub_separator = "-" * 70

        if log_intent:
            logger.log(f"\n{separator}")
            logger.log(f"  DB INTENT-BASED QUERY EXECUTION")
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

        # ----------------------------------------------------------------
        # STEP 1: Retrieve Context from RAG
        # ----------------------------------------------------------------
        logger.log(f"{sub_separator}")
        logger.log(f"  STEP 1: Retrieving Context from RAG")
        logger.log(f"{sub_separator}")

        rag_result = self.rag_instance.retrieve_db_context_by_intent(intent)

        schema_context = rag_result.get("schema_context", "")
        correct_examples = rag_result.get("correct_examples", "")
        incorrect_examples = rag_result.get("incorrect_examples", "")

        if not schema_context:
            logger.log(
                f"  [WARNING] No schema context found. Query generation may be less accurate."
            )

        logger.log(f"  Schema Context:      {len(schema_context)} characters")
        logger.log(f"  Correct Examples:    {len(correct_examples)} characters")
        logger.log(f"  Incorrect Examples:  {len(incorrect_examples)} characters")
        logger.log("")

        # ----------------------------------------------------------------
        # STEP 2: Generate SQL Query with GitLab Duo
        # ----------------------------------------------------------------
        logger.log(f"{sub_separator}")
        logger.log(f"  STEP 2: Generating SQL Query with GitLab Duo")
        logger.log(f"{sub_separator}")

        sql_query = self.ai_agent.generate_db_query(
            intent=intent,
            schema_context=schema_context,
            correct_examples=correct_examples,
            incorrect_examples=incorrect_examples,
        )

        if not sql_query:
            error_msg = "Failed to generate SQL query from AI agent"
            logger.log(f"  [ERROR] {error_msg}")
            logger.end_session()
            return {
                "success": False,
                "reason": error_msg,
                "data": None,
                "query": None,
                "error": error_msg,
            }

        # Clean up the query (remove markdown code blocks if present)
        sql_query = self._clean_sql_query(sql_query)
        logger.log(f"  Generated Query:")
        logger.log(f"  >>> {sql_query}")
        logger.log("")

        # ----------------------------------------------------------------
        # STEP 3: Execute the Query
        # ----------------------------------------------------------------
        logger.log(f"{sub_separator}")
        logger.log(f"  STEP 3: Executing Query")
        logger.log(f"{sub_separator}")

        attempt = 0
        result = None
        error_message = None

        while attempt <= max_retries:
            try:
                result = self.execute_query(sql_query)
                if result is not None:
                    logger.log(f"  [OK] Query executed successfully")
                    logger.log(f"  Rows Returned: {len(result)}")
                    if result and len(result) > 0:
                        logger.log(f"  Sample Row: {result[0]}")
                    break
                else:
                    error_message = "Query returned None (possible execution error)"
                    logger.log(f"  [ERROR] {error_message}")
            except Exception as e:
                error_message = str(e)
                logger.log(f"  [ERROR] Execution failed: {error_message}")

            # Retry logic
            attempt += 1
            if attempt <= max_retries:
                logger.log(
                    f"\n  [RETRY] Attempt {attempt}/{max_retries} - Regenerating query..."
                )
                sql_query = self.ai_agent.retry_db_query(
                    intent=intent,
                    original_query=sql_query,
                    error_message=error_message,
                    schema_context=schema_context,
                )
                if sql_query:
                    sql_query = self._clean_sql_query(sql_query)
                    logger.log(f"  New Query: {sql_query}")
                else:
                    logger.log("  [ERROR] Failed to regenerate query")
                    break
        logger.log("")

        # ----------------------------------------------------------------
        # STEP 4: Analyze Result with AI
        # ----------------------------------------------------------------
        logger.log(f"{sub_separator}")
        logger.log(f"  STEP 4: Analyzing Result with GitLab Duo")
        logger.log(f"{sub_separator}")

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

        logger.log(f"  AI Analysis Result: {'PASS' if ai_success else 'FAIL'}")
        logger.log(f"  AI Reason: {ai_reason}")
        logger.log("")

        # ----------------------------------------------------------------
        # STEP 5: Store in Learning Collection
        # ----------------------------------------------------------------
        logger.log(f"{sub_separator}")
        logger.log(f"  STEP 5: Storing Query in Learning Collection")
        logger.log(f"{sub_separator}")

        is_correct = analysis.get("success", False)
        error_msg = None if is_correct else analysis.get("reason", "Query failed")

        # Extract table names from query (simple extraction)
        tables_used = self._extract_tables_from_query(sql_query)

        self.rag_instance.store_query_learning(
            intent=intent,
            query=sql_query,
            tables_used=tables_used,
            is_correct=is_correct,
            error_message=error_msg,
        )
        logger.log(f"  Status: [{'CORRECT' if is_correct else 'INCORRECT'}]")
        logger.log(f"  Tables Used: {tables_used}")
        logger.log(f"  Stored for future learning")
        logger.log("")

        # ----------------------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------------------
        success = analysis.get("success", False) and result is not None
        reason = analysis.get("reason", "No reason provided")

        logger.log(f"{separator}")
        logger.log(f"  FINAL RESULT: {'SUCCESS' if success else 'FAILED'}")
        logger.log(f"{separator}")
        logger.log(f"  Success: {success}")
        logger.log(f"  Reason:  {reason}")
        logger.log(f"  Query:   {sql_query}")
        logger.log(f"  Rows:    {len(result) if result else 0}")
        logger.log(f"{separator}\n")

        # End the logging session
        logger.end_session()

        return {
            "success": success,
            "reason": reason,  # Top-level reason like API
            "data": result,
            "query": sql_query,
            "error": error_message if not success else None,
        }

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
