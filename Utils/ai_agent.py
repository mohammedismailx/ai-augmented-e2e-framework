import json
import os
import builtins
import requests
from Resources.Constants import endpoints, headers
from Utils.utils import load_test_data
from Utils.logger import FrameworkLogger as log
from Logic.API.ai.builder import AIAgentBuilder
from Resources.prompts import (
    get_self_healing_prompt,
    get_db_context_prompt,
    get_response_body_validation_prompt,
    get_logs_analyzing_prompt,
    get_curl_generation_prompt,
    get_api_response_analysis_prompt,
    get_curl_retry_prompt,
)
from Libs.IntentLocatorLibrary import IntentLocatorLibrary
from Libs.IntentQueriesLibrary import IntentQueriesLibrary
from Utils.db_connector import DBConnector
from Utils.query_constants import QUERIES


class AIAgent:
    def __init__(self, agent_type=None, base_url=None, api_wrapper=None):
        """
        Initialize AIAgent.
        Accepts an api_wrapper instance (Dependency Injection).
        Does NOT import APIWrapper to avoid circular dependency.
        """
        self.agent_type = agent_type or builtins.CONFIG.get("agent_type", "LOCAL")

        # Try to get base_url from:
        # 1. Parameter
        # 2. URLS (new structure)
        # 3. CONFIG (deprecated structure)
        self.base_url = base_url
        if not self.base_url:
            if self.agent_type == "GITLAB_DUO":
                self.base_url = builtins.URLS.get("gitlab", {}).get("base_url")

            if not self.base_url:
                self.base_url = builtins.CONFIG.get("base_url")
        self.chat_history = []

        # Reference to the injected wrapper
        self.api_wrapper = api_wrapper

        # Initialize builder with the wrapper
        self.builder = AIAgentBuilder(self.api_wrapper)

        self.intent_locator_lib = IntentLocatorLibrary()
        self.intent_queries_lib = IntentQueriesLibrary()

    def run_agent_based_on_context(self, context, **kwargs):
        if context == "SELF_HEALING":
            return self.execute_self_healing_context(
                kwargs.get("locator_name"),
                kwargs.get("locator_value"),
                kwargs.get("html_content"),
            )
        elif context == "QUERY_CREATION":
            return self.execute_db_context(
                kwargs.get("db_requirement"), kwargs.get("db_connector")
            )
        elif context == "RESPONSE_BODY_VALIDATION":
            return self.execute_response_body_validation_context(
                kwargs.get("response"), kwargs.get("exp_response")
            )
        elif context == "LOGS_ANALYZING":
            return self.execute_logs_analyzing_context(kwargs.get("logs"))
        elif context == "SWAGGER_INTENT":
            return self.execute_swagger_intent_context(
                kwargs.get("intent"),
                kwargs.get("swagger_context"),
                kwargs.get("base_url"),
                kwargs.get("return_prompt", False),
            )
        return None

    def execute_self_healing_context(
        self, locator_name, locator_value, html_content=None
    ):
        self._initialize_conversation("You are an expert in DOM analysis...")
        html = html_content if html_content else "<html>...</html>"

        matches = self.intent_locator_lib.find_elements_outerhtml_by_intent(
            html_or_path=html,
            intent_str=locator_name,
            top_k=5,
            min_score=0.1,
            locator_value=locator_value,
        )

        if not matches:
            raise Exception("No matches found")

        goal = get_self_healing_prompt(locator_name, locator_value, matches)

        return self._prompt_agent(
            goal,
            file_name="file.html",
            constraints="CSS selectors preferred",
            backstory="You are an expert in DOM analysis...",
        )

    def execute_db_context(self, db_requirement, db_connector=None):
        """
        Fetches the current database schema from INFORMATION_SCHEMA,
        updates schemaAnalysis.md, and then runs the AI agent to create a query.
        """
        # 1. Fetch Schema from DB
        schema_query = QUERIES.FETCH_SCHEMA

        # Use the passed db_connector (the fixture) or create a new one if not provided
        if not db_connector:
            db_connector = DBConnector()

        log.safe_print(
            f"DEBUG: Fetching schema information for 'testdb' using provided connector..."
        )
        schema_data = db_connector.execute_query(schema_query)

        # 2. Format schema as Markdown
        schema_md = "# Database Schema Analysis (Auto-generated)\n\n"
        if schema_data:
            current_table = ""
            for row in schema_data:
                if row["TABLE_NAME"] != current_table:
                    current_table = row["TABLE_NAME"]
                    schema_md += f"\n### Table: {current_table}\n"
                    schema_md += (
                        "| Column | Data Type | Nullable | Key | Extra | Default |\n"
                    )
                    schema_md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"

                schema_md += f"| {row['COLUMN_NAME']} | {row['COLUMN_TYPE']} | {row['IS_NULLABLE']} | {row['COLUMN_KEY']} | {row['EXTRA']} | {row['COLUMN_DEFAULT']} |\n"
        else:
            schema_md += "[WARNING] No schema data found or connection failed."

        # 3. Save to schemaAnalysis.md
        schema_path = os.path.join(
            builtins.PROJECT_ROOT, "Resources", "schemaAnalysis.md"
        )
        os.makedirs(os.path.dirname(schema_path), exist_ok=True)
        with open(schema_path, "w", encoding="utf-8") as f:
            f.write(schema_md)
        log.safe_print(f"✓ Schema analysis updated in {schema_path}")

        # 4. Proceed with AI analysis
        self._initialize_conversation("You are an expert in MySQL...")
        schema_analysis = schema_md

        res = self.intent_queries_lib.get_queries_schemas_relationships_by_intent(
            content_text=schema_analysis,
            intent_str=db_requirement,
            top_k_each=3,
            min_score=0.0,
        )
        goal = get_db_context_prompt(res, db_requirement)

        return self._prompt_agent(
            goal,
            file_name="query.sql",
            constraints="MySQL",
            backstory="You are an expert in MySQL...",
        )

    def execute_response_body_validation_context(self, response, exp_response):
        self._initialize_conversation("Your expertise: Precise JSON path resolution...")
        goal = get_response_body_validation_prompt(response, exp_response)
        return self._prompt_agent(goal, file_name="file.json")

    def execute_logs_analyzing_context(self, logs):
        self._initialize_conversation("Analyze logs and provide solutions...")
        goal = get_logs_analyzing_prompt(logs)
        return self._prompt_agent(goal, file_name="file.log")

    def execute_swagger_intent_context(
        self,
        intent: str,
        swagger_context: str,
        base_url: str,
        return_prompt: bool = False,
    ):
        """
        Generate a curl command based on user intent and swagger context.

        Args:
            intent (str): User's natural language intent (e.g., "delete book with id 5")
            swagger_context (str): Retrieved swagger API documentation from RAG
            base_url (str): Base URL for the API
            return_prompt (bool): If True, returns tuple (response, prompt)

        Returns:
            str or tuple: Generated curl command, or (curl_command, prompt) if return_prompt=True
        """
        self._initialize_conversation(
            "You are an expert in REST API integration, curl command generation, and API request construction."
        )

        goal = get_curl_generation_prompt(intent, swagger_context, base_url)

        curl_command = self._prompt_agent(
            goal,
            file_name="curl_command.sh",
            constraints="Generate executable curl command",
            backstory="You are an expert in REST API integration and curl command generation.",
        )

        if return_prompt:
            return curl_command, goal
        return curl_command

    def analyze_api_response(
        self,
        intent: str,
        curl_command: str,
        response_body: str,
        status_code: int,
        stderr: str = "",
        return_prompt: bool = False,
    ):
        """
        Analyze API response using GitLab Duo.

        Args:
            intent (str): Original user intent
            curl_command (str): The curl command that was executed
            response_body (str): The response body from the API
            status_code (int): HTTP status code
            stderr (str): Any error output from curl execution
            return_prompt (bool): If True, returns tuple (response, prompt)

        Returns:
            str or tuple: Analysis result, or (analysis, prompt) if return_prompt=True
        """
        self._initialize_conversation(
            "You are an expert in REST API response analysis, HTTP status interpretation, and test result evaluation."
        )

        goal = get_api_response_analysis_prompt(
            intent, curl_command, response_body, status_code, stderr
        )

        # Use .json file extension to hint that we want JSON output
        # Use a direct instruction that asks for the analysis result
        analysis = self._prompt_agent(
            goal,
            file_name="analysis_result.json",
            constraints="Return ONLY the JSON object with success and reason fields",
            backstory="Analyze the API response and return JSON: ",
        )

        if return_prompt:
            return analysis, goal
        return analysis

    def retry_curl_generation(
        self,
        intent: str,
        original_curl: str,
        error_output: str,
        swagger_context: str,
        base_url: str,
        return_prompt: bool = False,
    ):
        """
        Retry curl generation after a failed attempt.

        Args:
            intent (str): Original user intent
            original_curl (str): The curl command that failed
            error_output (str): Error message from the failed execution
            swagger_context (str): API documentation for reference
            base_url (str): Base URL for the API
            return_prompt (bool): If True, returns tuple (response, prompt)

        Returns:
            str or tuple: Fixed curl command, or (fixed_curl, prompt) if return_prompt=True
        """
        self._initialize_conversation(
            "You are an expert in REST API debugging, curl command troubleshooting, and error resolution."
        )

        goal = get_curl_retry_prompt(
            intent, original_curl, error_output, swagger_context, base_url
        )

        fixed_curl = self._prompt_agent(
            goal,
            file_name="curl_command_fixed.sh",
            constraints="Fix the curl command based on error analysis",
            backstory="You are an expert in curl troubleshooting.",
        )

        if return_prompt:
            return fixed_curl, goal
        return fixed_curl

    def _initialize_conversation(self, content):
        if self.agent_type == "LOCAL":
            self.chat_history = [{"role": "system", "content": content}]
        elif self.agent_type == "GITLAB_DUO":
            self.chat_history = content

    def _prompt_agent(self, prompt, file_name=None, constraints=None, backstory=None):
        if not self.api_wrapper:
            log.safe_print(
                "Error: No APIWrapper provided to AIAgent. Cannot communicate with AI."
            )
            return None

        if self.agent_type == "LOCAL":
            self.chat_history.append({"role": "user", "content": prompt})
            test_data = load_test_data("LocalModel")
            try:
                test_data["success"]["input"]["body"]["messages"] = self.chat_history
            except KeyError as e:
                log.safe_print(f"Error updating test data: {e}")
                return None

            response = self.builder.communicate_with_agent(
                agent_type=self.agent_type,
                scenario="success",
                override_test_data=test_data,
                base_url=self.base_url,
            )

            if response and response.status_code == 200:
                try:
                    answer = response.json()["choices"][0]["message"]["content"]
                    self.chat_history.append({"role": "assistant", "content": answer})
                    return answer
                except (KeyError, IndexError) as e:
                    log.safe_print(f"Error parsing response: {e}")
                    return None
            return None

        elif self.agent_type == "GITLAB_DUO":
            test_data = load_test_data("GitlabDuo")
            try:
                body = test_data["success"]["input"]["body"]
                if "context" in body and len(body["context"]) > 0:
                    body["context"][0]["content"] = prompt
                    body["context"][0]["name"] = file_name or ""
                body["user_instruction"] = constraints or ""
                if "current_file" in body:
                    body["current_file"]["file_name"] = file_name or ""
                    body["current_file"]["content_above_cursor"] = backstory or ""
            except KeyError as e:
                log.safe_print(f"Error updating test data: {e}")
                return None

            response = self.builder.communicate_with_agent(
                agent_type=self.agent_type,
                scenario="success",
                override_test_data=test_data,
                base_url=self.base_url,
            )

            if response and response.status_code == 200:
                try:
                    answer = response.json()["choices"][0]["text"]
                    return answer
                except (KeyError, IndexError) as e:
                    log.safe_print(f"Error parsing response: {e}")
                    return None
            return None

        return None
