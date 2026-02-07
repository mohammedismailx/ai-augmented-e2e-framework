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
    get_db_query_generation_prompt,
    get_db_query_analysis_prompt,
    get_db_query_retry_prompt,
    get_db_query_action_prompt,
    get_db_query_retry_prompt_enhanced,
    get_ui_step_action_prompt,
    get_ui_step_verification_prompt,
    get_ui_step_retry_prompt,
    get_ui_step_failure_analysis_prompt,
    get_ui_module_action_prompt,
    get_ui_module_retry_prompt,
    get_api_endpoint_action_prompt,
    get_api_endpoint_retry_prompt,
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
        elif context == "DB_QUERY_INTENT":
            return self.execute_db_query_intent_context(
                kwargs.get("intent"),
                kwargs.get("schema_context"),
                kwargs.get("correct_examples", ""),
                kwargs.get("incorrect_examples", ""),
                kwargs.get("return_prompt", False),
            )
        elif context == "UI_STEP_ACTION":
            return self.execute_ui_step_action_context(
                kwargs.get("step_intent"),
                kwargs.get("step_type"),
                kwargs.get("relevant_elements"),
                kwargs.get("page_url"),
                kwargs.get("previous_steps"),
                kwargs.get("return_prompt", False),
            )
        elif context == "UI_STEP_VERIFICATION":
            return self.execute_ui_step_verification_context(
                kwargs.get("step_intent"),
                kwargs.get("relevant_elements"),
                kwargs.get("page_url"),
                kwargs.get("page_title", ""),
                kwargs.get("return_prompt", False),
            )
        elif context == "UI_STEP_RETRY":
            return self.execute_ui_step_retry_context(
                kwargs.get("step_intent"),
                kwargs.get("failed_action"),
                kwargs.get("error"),
                kwargs.get("relevant_elements"),
                kwargs.get("page_url"),
                kwargs.get("return_prompt", False),
            )
        elif context == "UI_STEP_FAILURE_ANALYSIS":
            return self.execute_ui_step_failure_analysis_context(
                kwargs.get("step_intent"),
                kwargs.get("step_type"),
                kwargs.get("failed_action"),
                kwargs.get("error"),
                kwargs.get("relevant_elements"),
                kwargs.get("page_url"),
                kwargs.get("page_title", ""),
                kwargs.get("previous_steps"),
                kwargs.get("return_prompt", False),
            )
        elif context == "UI_MODULE_ACTION":
            return self.execute_ui_module_action_context(
                kwargs.get("step_intent"),
                kwargs.get("step_type"),
                kwargs.get("module"),
                kwargs.get("page_url"),
                kwargs.get("stored_metadata"),
                kwargs.get("relevant_elements"),
                kwargs.get("previous_steps"),
                kwargs.get("return_prompt", False),
            )
        elif context == "UI_MODULE_RETRY":
            return self.execute_ui_module_retry_context(
                kwargs.get("step_intent"),
                kwargs.get("step_type"),
                kwargs.get("module"),
                kwargs.get("page_url"),
                kwargs.get("failed_action"),
                kwargs.get("error"),
                kwargs.get("ai_analysis"),
                kwargs.get("stored_metadata"),
                kwargs.get("relevant_elements"),
                kwargs.get("previous_steps"),
                kwargs.get("return_prompt", False),
            )
        elif context == "API_ENDPOINT_ACTION":
            return self.execute_api_endpoint_action_context(
                kwargs.get("prompt"),
                kwargs.get("return_prompt", False),
            )
        elif context == "API_ENDPOINT_RETRY":
            return self.execute_api_endpoint_retry_context(
                kwargs.get("resource"),
                kwargs.get("intent"),
                kwargs.get("failed_curl"),
                kwargs.get("error_output"),
                kwargs.get("ai_analysis"),
                kwargs.get("stored_metadata"),
                kwargs.get("swagger_context"),
                kwargs.get("base_url"),
                kwargs.get("return_prompt", False),
            )
        elif context == "DB_QUERY_ACTION":
            return self.execute_db_query_action_context(
                kwargs.get("prompt"),
                kwargs.get("return_prompt", False),
            )
        elif context == "DB_QUERY_RETRY":
            return self.execute_db_query_retry_context(
                kwargs.get("table"),
                kwargs.get("intent"),
                kwargs.get("failed_query"),
                kwargs.get("error_message"),
                kwargs.get("ai_analysis"),
                kwargs.get("stored_metadata"),
                kwargs.get("schema_context"),
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

    # ========================================================================
    # DB QUERY GENERATION METHODS (Intent-based SQL generation)
    # ========================================================================

    def generate_db_query(
        self,
        intent,
        schema_context,
        correct_examples="",
        incorrect_examples="",
        return_prompt=False,
    ):
        """
        Generate SQL query based on user intent using GitLab Duo.

        Args:
            intent (str): User's natural language intent (e.g., "get all posts by user 5")
            schema_context (str): Database schema documentation from RAG
            correct_examples (str): Previously successful queries for similar intents
            incorrect_examples (str): Previously failed queries to avoid
            return_prompt (bool): If True, returns tuple (query, prompt)

        Returns:
            str or tuple: Generated SQL query, or (query, prompt) if return_prompt=True
        """
        self._initialize_conversation(
            "You are an expert MySQL database engineer specializing in query generation."
        )

        goal = get_db_query_generation_prompt(
            intent, schema_context, correct_examples, incorrect_examples
        )

        sql_query = self._prompt_agent(
            goal,
            file_name="generated_query.sql",
            constraints="Generate a single, optimized SQL query for the given intent",
            backstory="You are an expert MySQL query generator.",
        )

        if return_prompt:
            return sql_query, goal
        return sql_query

    def analyze_db_result(self, intent, sql_query, result, return_prompt=False):
        """
        Analyze database query result to determine if it meets the intent.

        Args:
            intent (str): Original user intent
            sql_query (str): The SQL query that was executed
            result (str): Query result (JSON stringified or error message)
            return_prompt (bool): If True, returns tuple (analysis, prompt)

        Returns:
            dict or tuple: Analysis result {"success": bool, "reason": str},
                          or (analysis, prompt) if return_prompt=True
        """
        self._initialize_conversation(
            "You are an expert database analyst specializing in query result validation."
        )

        goal = get_db_query_analysis_prompt(intent, sql_query, result)

        analysis_response = self._prompt_agent(
            goal,
            file_name="query_analysis.json",
            constraints='Return ONLY {"success": true/false, "reason": "explanation"}',
            backstory="You are an expert in database result analysis.",
        )

        # Parse the analysis response
        try:
            if analysis_response:
                # Try to extract JSON from the response
                import re

                # Find the last occurrence of {"success" - this is the actual AI response
                json_start = analysis_response.rfind('{"success"')
                if json_start != -1:
                    # Extract from {"success" to end and find the closing brace
                    json_str = analysis_response[json_start:]
                    brace_count = 0
                    json_end = 0
                    for i, char in enumerate(json_str):
                        if char == "{":
                            brace_count += 1
                        elif char == "}":
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    if json_end > 0:
                        try:
                            analysis = json.loads(json_str[:json_end])
                            # Validate the analysis has required keys
                            if "success" not in analysis:
                                analysis["success"] = False
                            # Check if AI returned placeholder text instead of actual analysis
                            placeholder_phrases = [
                                "explanation",
                                "Describe exactly WHY",
                                "YOUR specific analysis",
                            ]
                            reason = analysis.get("reason", "")
                            if not reason or any(
                                p in reason for p in placeholder_phrases
                            ):
                                # Generate a meaningful reason based on the result
                                analysis["reason"] = (
                                    "AI did not provide detailed analysis"
                                )
                        except json.JSONDecodeError:
                            # Fallback regex pattern for simpler cases
                            simple_pattern = r'"success"\s*:\s*(true|false)'
                            reason_pattern = r'"reason"\s*:\s*"([^"]+)"'

                            success_match = re.search(
                                simple_pattern, json_str, re.IGNORECASE
                            )
                            reason_match = re.search(
                                reason_pattern, json_str, re.IGNORECASE
                            )

                            analysis = {
                                "success": (
                                    success_match.group(1).lower() == "true"
                                    if success_match
                                    else False
                                ),
                                "reason": (
                                    reason_match.group(1)
                                    if reason_match
                                    else "Could not parse reason from response"
                                ),
                            }
                    else:
                        analysis = {
                            "success": False,
                            "reason": "Could not find complete JSON in response",
                        }
                else:
                    # Last resort: try direct JSON parse
                    try:
                        analysis = json.loads(analysis_response)
                    except json.JSONDecodeError:
                        analysis = {
                            "success": False,
                            "reason": f"No JSON found in response: {analysis_response[:200]}",
                        }
            else:
                analysis = {"success": False, "reason": "No response from AI agent"}
        except json.JSONDecodeError:
            analysis = {
                "success": False,
                "reason": f"Could not parse AI response: {analysis_response[:200] if analysis_response else 'None'}",
            }

        if return_prompt:
            return analysis, goal
        return analysis

    def retry_db_query(
        self,
        intent,
        original_query,
        error_message,
        schema_context,
        return_prompt=False,
    ):
        """
        Retry SQL query generation after a failed attempt.

        Args:
            intent (str): Original user intent
            original_query (str): The SQL query that failed
            error_message (str): Error message from the failed execution
            schema_context (str): Database schema for reference
            return_prompt (bool): If True, returns tuple (query, prompt)

        Returns:
            str or tuple: Fixed SQL query, or (query, prompt) if return_prompt=True
        """
        self._initialize_conversation(
            "You are an expert in MySQL debugging and query troubleshooting."
        )

        goal = get_db_query_retry_prompt(
            intent, original_query, error_message, schema_context
        )

        fixed_query = self._prompt_agent(
            goal,
            file_name="query_fixed.sql",
            constraints="Fix the SQL query based on error analysis",
            backstory="You are an expert in SQL troubleshooting.",
        )

        if return_prompt:
            return fixed_query, goal
        return fixed_query

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

    # =========================================================================
    # UI INTENT-BASED EXECUTION METHODS
    # =========================================================================

    def execute_ui_step_action_context(
        self,
        step_intent: str,
        step_type: str,
        relevant_elements: list,
        page_url: str,
        previous_steps: list = None,
        return_prompt: bool = False,
    ):
        """
        Generate action for a single UI step using GitLab Duo.

        Args:
            step_intent: The step text (e.g., "fill username with standard_user")
            step_type: Given/When/Then/And
            relevant_elements: Elements retrieved by IntentLocatorLibrary
            page_url: Current page URL
            previous_steps: List of previously executed steps for context
            return_prompt: If True, return the prompt instead of executing

        Returns:
            JSON action object or prompt string
        """
        prompt = get_ui_step_action_prompt(
            step_intent=step_intent,
            step_type=step_type,
            relevant_elements=relevant_elements or [],
            page_url=page_url,
            previous_steps=previous_steps,
        )

        if return_prompt:
            return prompt

        self._initialize_conversation(
            "You are an expert Playwright automation engineer..."
        )

        response = self._prompt_agent(
            prompt,
            file_name="ui_step.json",
            constraints="Return ONLY valid JSON action object",
            backstory="You are an expert in browser automation...",
        )

        return self._parse_json_response(response)

    def execute_ui_step_verification_context(
        self,
        step_intent: str,
        relevant_elements: list,
        page_url: str,
        page_title: str = "",
        return_prompt: bool = False,
    ):
        """
        Verify a 'Then' step using GitLab Duo.

        Args:
            step_intent: The verification intent
            relevant_elements: Elements retrieved by IntentLocatorLibrary
            page_url: Current page URL
            page_title: Current page title
            return_prompt: If True, return the prompt instead of executing

        Returns:
            Verification result dict or prompt string
        """
        prompt = get_ui_step_verification_prompt(
            step_intent=step_intent,
            relevant_elements=relevant_elements or [],
            page_url=page_url,
            page_title=page_title,
        )

        if return_prompt:
            return prompt

        self._initialize_conversation("You are an expert QA validation engineer...")

        response = self._prompt_agent(
            prompt,
            file_name="ui_verification.json",
            constraints="Return ONLY valid JSON verification result",
            backstory="You are an expert in UI testing...",
        )

        return self._parse_json_response(response)

    def execute_ui_step_retry_context(
        self,
        step_intent: str,
        failed_action: dict,
        error: str,
        relevant_elements: list,
        page_url: str,
        return_prompt: bool = False,
    ):
        """
        Fix a failed UI step using GitLab Duo.

        Args:
            step_intent: Original step intent
            failed_action: The action that failed
            error: Error message
            relevant_elements: Fresh elements from current page
            page_url: Current page URL
            return_prompt: If True, return the prompt instead of executing

        Returns:
            Fixed action dict or prompt string
        """
        prompt = get_ui_step_retry_prompt(
            step_intent=step_intent,
            failed_action=failed_action,
            error=error,
            relevant_elements=relevant_elements or [],
            page_url=page_url,
        )

        if return_prompt:
            return prompt

        self._initialize_conversation(
            "You are an expert Playwright debugging engineer..."
        )

        response = self._prompt_agent(
            prompt,
            file_name="ui_retry.json",
            constraints="Return ONLY valid JSON corrected action",
            backstory="You are an expert in fixing selectors...",
        )

        return self._parse_json_response(response)

    def execute_ui_step_failure_analysis_context(
        self,
        step_intent: str,
        step_type: str,
        action_attempted: dict,
        error_message: str,
        relevant_elements: list,
        page_url: str,
        page_html_snippet: str = None,
        previous_steps: list = None,
        return_prompt: bool = False,
    ):
        """
        Analyze a failed UI step comprehensively using GitLab Duo.

        This is an extra analysis layer called when a step fails after retry,
        providing detailed insights into why the step failed and how to fix it.

        Args:
            step_intent: The original step intent (e.g., "Then I should see 'Swag Labs' on the page")
            step_type: The type of step (Given/When/Then/And)
            action_attempted: The action that was attempted (dict with action_type, selector, etc.)
            error_message: The error message from the failed execution
            relevant_elements: Elements retrieved by IntentLocatorLibrary
            page_url: Current page URL
            page_html_snippet: Optional snippet of page HTML for context (used as page_title fallback)
            previous_steps: List of previously executed steps for context
            return_prompt: If True, return the prompt instead of executing

        Returns:
            Analysis dict with root_cause, suggestions, element_analysis, etc.
            or prompt string if return_prompt=True
        """
        prompt = get_ui_step_failure_analysis_prompt(
            step_intent=step_intent,
            step_type=step_type,
            failed_action=action_attempted,
            error=error_message,
            relevant_elements=relevant_elements or [],
            page_url=page_url,
            page_title=page_html_snippet or "",  # Use snippet as title fallback
            previous_steps=previous_steps or [],
        )

        if return_prompt:
            return prompt

        self._initialize_conversation(
            "You are an expert test automation failure analyst with deep knowledge of "
            "Playwright, web technologies, and debugging techniques. You analyze failed "
            "UI test steps and provide comprehensive insights."
        )

        response = self._prompt_agent(
            prompt,
            file_name="ui_failure_analysis.json",
            constraints="Return ONLY valid JSON analysis with root_cause, suggestions, and element_analysis",
            backstory="You are a senior QA engineer specializing in diagnosing test failures...",
        )

        return self._parse_json_response(response)

    # =========================================================================
    # UI MODULE-BASED LEARNING (DUO returns full metadata dict)
    # =========================================================================

    def execute_ui_module_action_context(
        self,
        step_intent: str,
        step_type: str,
        module: str,
        page_url: str,
        stored_metadata: dict = None,
        relevant_elements: list = None,
        previous_steps: list = None,
        return_prompt: bool = False,
    ):
        """
        Generate action for a UI step, returning FULL METADATA dict for storage.

        DUO receives either:
        - stored_metadata: Previous [correct] action from ChromaDB (to validate/reuse)
        - relevant_elements: Live HTML elements (when no stored action or was [incorrect])

        DUO returns the SAME metadata format that will be stored:
        {
            "action_key": "click_login",
            "intent": "click login button",
            "action_type": "click",
            "locator": "#login-btn",
            "action_json": {...},
            "playwright_code": "page.click('#login-btn')"
        }

        Args:
            step_intent: The step text (e.g., "fill username with standard_user")
            step_type: Given/When/Then/And
            module: Current module name (e.g., "inventory", "login")
            page_url: Current page URL
            stored_metadata: Previous stored action from ChromaDB (optional)
            relevant_elements: Fresh HTML elements from IntentLocatorLibrary (optional)
            previous_steps: List of previously executed steps for context
            return_prompt: If True, return the prompt instead of executing

        Returns:
            Full metadata dict for storage or prompt string
        """
        prompt = get_ui_module_action_prompt(
            step_intent=step_intent,
            step_type=step_type,
            module=module,
            page_url=page_url,
            stored_metadata=stored_metadata,
            relevant_elements=relevant_elements or [],
            previous_steps=previous_steps,
        )

        if return_prompt:
            return prompt

        self._initialize_conversation(
            "You are an expert Playwright automation engineer. You analyze UI steps "
            "and return complete action metadata objects that can be stored and reused. "
            "Your responses must be valid JSON with all required fields."
        )

        response = self._prompt_agent(
            prompt,
            file_name="ui_module_action.json",
            constraints="Return ONLY valid JSON with action_key, intent, action_type, locator, action_json, and playwright_code",
            backstory="You are an expert in browser automation and test learning systems...",
        )

        return self._parse_json_response(response)

    def _parse_json_response(self, response: str) -> dict:
        """
        Parse JSON from AI response, handling markdown code blocks.

        Args:
            response: Raw AI response string

        Returns:
            Parsed dict or None if parsing fails
        """
        if not response:
            return None

        try:
            # Clean up response
            cleaned = response.strip()

            # Remove markdown code blocks
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            cleaned = cleaned.strip()

            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            log.warning(f"Failed to parse JSON response: {e}")
            log.debug(f"Raw response: {response[:200]}...")
            return None

    # ==================== API ENDPOINT ACTION CONTEXT ====================

    def execute_api_endpoint_action_context(
        self,
        prompt: str,
        return_prompt: bool = False,
    ):
        """
        Generate API endpoint action metadata from GitLab Duo.

        This is the API equivalent of execute_ui_module_action_context.
        DUO receives a prompt (built by get_api_endpoint_action_prompt) containing:
        - Intent (e.g., "get all users")
        - Resource (e.g., "users")
        - Either stored_metadata from learning collection OR swagger_context
        - Base URL

        DUO returns full action metadata for storage:
        {
            "action_key": "get_all_users",
            "intent": "get all users",
            "resource": "users",
            "method": "GET",
            "endpoint": "/api/users",
            "curl": "curl -X GET 'http://...'/api/users' -H '...'",
            "expected_status": 200,
            "request_body": {},
            "headers": {"Content-Type": "application/json"}
        }

        Args:
            prompt: Pre-built prompt from get_api_endpoint_action_prompt
            return_prompt: If True, return the prompt instead of executing

        Returns:
            Raw AI response string (parsing done by caller)
        """
        if return_prompt:
            return prompt

        self._initialize_conversation(
            "You are an expert API automation engineer. You analyze API intents "
            "and return complete action metadata objects with curl commands that can be "
            "stored and reused. Your responses must be valid JSON with all required fields."
        )

        response = self._prompt_agent(
            prompt,
            file_name="api_endpoint_action.json",
            constraints="Return ONLY valid JSON with action_key, intent, resource, method, endpoint, curl, expected_status, request_body, and headers",
            backstory="You are an expert in REST API automation and test learning systems...",
        )

        return response

    # ==================== DB QUERY ACTION CONTEXT ====================

    def execute_db_query_action_context(
        self,
        prompt: str,
        return_prompt: bool = False,
    ):
        """
        Generate DB query action metadata from GitLab Duo.

        This is the DB equivalent of execute_ui_module_action_context and
        execute_api_endpoint_action_context.

        DUO receives a prompt (built by get_db_query_action_prompt) containing:
        - Intent (e.g., "get all agents")
        - Table (e.g., "agents")
        - BOTH stored_metadata from learning collection AND schema_context

        DUO returns full action metadata for storage:
        {
            "action_key": "get_all_agents",
            "intent": "get all agents",
            "table": "agents",
            "operation": "SELECT",
            "query": "SELECT * FROM agents;",
            "expected_columns": ["id", "name", "status"],
            "expected_row_count": "multiple",
            "description": "Retrieves all agents from the table"
        }

        Args:
            prompt: Pre-built prompt from get_db_query_action_prompt
            return_prompt: If True, return the prompt instead of executing

        Returns:
            Raw AI response string (parsing done by caller)
        """
        if return_prompt:
            return prompt

        self._initialize_conversation(
            "You are an expert database engineer. You analyze database intents "
            "and return complete SQL query metadata objects that can be "
            "stored and reused. Your responses must be valid JSON with all required fields."
        )

        response = self._prompt_agent(
            prompt,
            file_name="db_query_action.json",
            constraints="Return ONLY valid JSON with action_key, intent, table, operation, query, expected_columns, expected_row_count, and description",
            backstory="You are an expert in MySQL database automation and test learning systems...",
        )

        return response

    # ==================== ENHANCED RETRY CONTEXTS ====================

    def execute_ui_module_retry_context(
        self,
        step_intent: str,
        step_type: str,
        module: str,
        page_url: str,
        failed_action: dict,
        error: str,
        ai_analysis: str,
        stored_metadata: dict,
        relevant_elements: list,
        previous_steps: list = None,
        return_prompt: bool = False,
    ):
        """
        Generate corrected UI action using AI analysis and all original context.

        This is the ENHANCED retry that includes:
        - AI analysis from first attempt
        - Original stored_metadata
        - Fresh live HTML elements
        - All context from original prompt
        """
        prompt = get_ui_module_retry_prompt(
            step_intent=step_intent,
            step_type=step_type,
            module=module,
            page_url=page_url,
            failed_action=failed_action,
            error=error,
            ai_analysis=ai_analysis,
            stored_metadata=stored_metadata,
            relevant_elements=relevant_elements,
            previous_steps=previous_steps,
        )

        if return_prompt:
            return prompt

        self._initialize_conversation(
            "You are an expert UI automation engineer. You analyze failed actions "
            "and AI feedback to generate corrected Playwright actions with better locators."
        )

        response = self._prompt_agent(
            prompt,
            file_name="ui_retry_action.json",
            constraints="Return ONLY valid JSON with corrected action. Do NOT change value/text fields.",
            backstory="You are an expert in Playwright and UI test self-healing...",
        )

        return response

    def execute_api_endpoint_retry_context(
        self,
        resource: str,
        intent: str,
        failed_curl: str,
        error_output: str,
        ai_analysis: str,
        stored_metadata: dict,
        swagger_context: str,
        base_url: str,
        return_prompt: bool = False,
    ):
        """
        Generate corrected API curl command using AI analysis and all original context.

        This is the ENHANCED retry that includes:
        - AI analysis from first attempt
        - Original stored_metadata
        - Original swagger_context
        - Error details
        """
        prompt = get_api_endpoint_retry_prompt(
            resource=resource,
            intent=intent,
            failed_curl=failed_curl,
            error_output=error_output,
            ai_analysis=ai_analysis,
            stored_metadata=stored_metadata,
            swagger_context=swagger_context,
            base_url=base_url,
        )

        if return_prompt:
            return prompt

        self._initialize_conversation(
            "You are an expert API automation engineer. You analyze failed API requests "
            "and AI feedback to generate corrected curl commands."
        )

        response = self._prompt_agent(
            prompt,
            file_name="api_retry_curl.txt",
            constraints="Return ONLY the corrected curl command, single line, no explanations.",
            backstory="You are an expert in REST API debugging and automation...",
        )

        return response

    def execute_db_query_retry_context(
        self,
        table: str,
        intent: str,
        failed_query: str,
        error_message: str,
        ai_analysis: str,
        stored_metadata: dict,
        schema_context: str,
        return_prompt: bool = False,
    ):
        """
        Generate corrected DB query using AI analysis and all original context.

        This is the ENHANCED retry that includes:
        - AI analysis from first attempt
        - Original stored_metadata
        - Original schema_context
        - Error details
        """
        prompt = get_db_query_retry_prompt_enhanced(
            table=table,
            intent=intent,
            failed_query=failed_query,
            error_message=error_message,
            ai_analysis=ai_analysis,
            stored_metadata=stored_metadata,
            schema_context=schema_context,
        )

        if return_prompt:
            return prompt

        self._initialize_conversation(
            "You are an expert database engineer. You analyze failed SQL queries "
            "and AI feedback to generate corrected queries with proper syntax."
        )

        response = self._prompt_agent(
            prompt,
            file_name="db_retry_query.json",
            constraints="Return ONLY valid JSON with corrected query action metadata.",
            backstory="You are an expert in MySQL debugging and query optimization...",
        )

        return response
