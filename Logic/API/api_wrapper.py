import requests
import json
import builtins
import subprocess
import platform
import re
import os
from datetime import datetime
from Resources.Constants import constants, endpoints, headers
from Resources.prompts import get_api_endpoint_action_prompt
from Utils.ai_agent import AIAgent

# Import centralized logger
from Utils.logger import FrameworkLogger as log, IntentLogger


class APIWrapper:

    def __init__(self, base_url=None, rag_instance=None):
        """
        Initialize APIWrapper.

        Args:
            base_url: Base URL for API calls (can be set via fixture)
            rag_instance: RAG instance with embedded swagger (can be set via fixture)
        """
        self.base_url = base_url
        self.rag_instance = rag_instance
        self.session = requests.Session()
        self.timeout = 30  # Default timeout
        self.config = getattr(builtins, "CONFIG", {})
        self.agent_mode = self.config.get("agent_mode", "ENABLED")

        # Dependency Injection: Wrapper creates the Agent and passes itself
        self.ai_agent = AIAgent(api_wrapper=self)

    def initialize_api_session(self, base_url):
        self.base_url = base_url
        return self.session

    def prepare_api_request(
        self,
        base_url=None,
        endpoint=None,
        headers=None,
        request_model=None,
        test_data=None,
    ):
        url = f"{base_url or self.base_url}{endpoint}"
        request_body = test_data if test_data else {}
        return url, request_body

    def process_api_response(self, response, exp_status_code=None, exp_body=None):
        log.safe_print(f"Response Status: {response.status_code}")
        log.safe_print(f"Response Body: {response.text}")

        if exp_status_code:
            assert (
                response.status_code == exp_status_code
            ), f"Expected status {exp_status_code}, got {response.status_code}"

        if exp_body:
            try:
                resp_json = response.json()
                for key, value in exp_body.items():
                    try:
                        assert key in resp_json, f"Key {key} not found in response"
                        assert (
                            resp_json[key] == value
                        ), f"Value mismatch for {key}: expected {value}, got {resp_json[key]}"
                    except AssertionError as e:
                        if self.agent_mode == "ENABLED":
                            log.safe_print(
                                f"Standard validation failed for key '{key}': {str(e)}"
                            )
                            log.safe_print(
                                "Triggering AI Agent for RESPONSE_BODY_VALIDATION..."
                            )

                            ai_result = self.ai_agent.run_agent_based_on_context(
                                context="RESPONSE_BODY_VALIDATION",
                                response=resp_json,
                                exp_response=exp_body,
                            )

                            log.safe_print(f"AI Agent validation result: {ai_result}")

                            if str(ai_result).strip().lower() == "true":
                                log.safe_print(
                                    "[OK] Success: AI Agent validated the response body against expectations."
                                )
                                return response
                            else:
                                log.safe_print(
                                    f"[FAIL] AI Agent validation failed: {ai_result}"
                                )
                                raise Exception(
                                    f"Validation failed both normally and via AI. Last error: {str(e)}"
                                )
                        else:
                            raise e
            except json.JSONDecodeError:
                log.safe_print("Failed to decode response as JSON for validation")
                pass

        return response

    def post_request_wrapper(
        self,
        endpoint,
        base_url=None,
        headers=None,
        request_body=None,
        exp_status_code=None,
        exp_body=None,
    ):
        url, body = self.prepare_api_request(
            base_url, endpoint, headers, test_data=request_body
        )

        log.safe_print(f"Making POST request to: {url}")
        log.safe_print(f"Headers: {headers}")
        log.safe_print(f"Request Body: {body}")

        try:
            response = self.session.post(
                url, headers=headers, json=body, timeout=self.timeout, verify=False
            )
        except requests.RequestException as e:
            log.safe_print(f"Request failed: {e}")
            return None

        return self.process_api_response(response, exp_status_code, exp_body)

    # ==================== INTENT-BASED API EXECUTION WITH LEARNING ====================

    def execute_by_intent(
        self,
        intent: str,
        resource: str = None,
        base_url: str = None,
        rag_instance=None,
        max_retries: int = 2,
    ) -> dict:
        """
        Execute an API call based on natural language intent using ChromaDB Learning + RAG + GitLab Duo.

        LEARNING FLOW (same pattern as UI):
        1. RETRIEVE: Search "api_endpoint_learning" collection for stored action by intent
           - If [correct] found → send stored_metadata to DUO for validation
           - If not found or [incorrect] → proceed to swagger
        2. SWAGGER: Retrieve endpoint context from "api_swagger" collection
        3. DUO: Generate action metadata (action_key, method, endpoint, curl, etc.)
        4. EXECUTE: Execute the generated curl command
        5. STORE: Store result with [correct] (status != 404) or [incorrect] status

        Args:
            intent (str): Natural language intent (e.g., "delete book with id 5")
            resource (str): API resource name (e.g., "books", "users"). If not provided, extracted from intent.
            base_url (str): Base URL for the API. Uses instance base_url if not provided.
            rag_instance: RAG instance with embedded swagger. Uses instance rag_instance if not provided.
            max_retries (int): Maximum number of retry attempts for failed curl execution

        Returns:
            dict: Structured result with success status, curl command, response, and analysis
        """
        # Use instance defaults if not provided
        if base_url is None:
            base_url = self.base_url
        if rag_instance is None:
            rag_instance = self.rag_instance

        # Extract resource from intent if not provided
        if resource is None:
            resource = self._extract_resource_from_intent(intent)

        # Initialize logger with API test type
        logger = IntentLogger(test_type="API")
        logger.start_session(intent=intent)

        logger.log(f"\n{'='*100}")
        logger.log(
            f"[INTENT EXECUTION WITH LEARNING] Starting intent-based API execution"
        )
        logger.log(f"[INTENT] {intent}")
        logger.log(f"[RESOURCE] {resource}")
        logger.log(f"[BASE URL] {base_url}")
        logger.log(f"{'='*100}")

        result = {
            "success": False,
            "intent": intent,
            "resource": resource,
            "base_url": base_url,
            "curl_command": None,
            "status_code": None,
            "response_body": None,
            "request_body": None,
            "analysis": None,
            "error": None,
            "retries": 0,
            "learning_source": None,  # "stored" or "swagger"
            "action_metadata": None,
            "prompts": {},
            "responses": {},
        }

        # Step 1: Get RAG instance
        if rag_instance is None:
            rag_instance = getattr(builtins, "RAG_INSTANCE", None)
            if rag_instance is None:
                result["error"] = (
                    "RAG instance not available. Please ensure swagger is embedded first."
                )
                logger.log(f"[ERROR] {result['error']}")
                logger.end_session()
                return result

        # ============================================================================
        # STEP 1: RETRIEVE FROM LEARNING COLLECTION
        # ============================================================================
        logger.log_section(
            "[STEP 1] CHROMADB - RETRIEVING FROM API LEARNING COLLECTION"
        )

        stored_action = rag_instance.retrieve_api_action_for_intent(resource, intent)
        stored_metadata = None
        swagger_context = None

        if stored_action["found"] and stored_action["status"] == "[correct]":
            stored_metadata = stored_action["stored_metadata"]
            result["learning_source"] = "stored"
            logger.log(
                f"\n[OK] Found [correct] stored action (match_score: {stored_action['match_score']:.3f})"
            )
            logger.log_titled_block(
                "STORED METADATA", json.dumps(stored_metadata, indent=2), max_chars=3000
            )
        else:
            if stored_action["found"]:
                logger.log(
                    f"\n[INFO] Found stored action but status is {stored_action['status']}, fetching swagger context..."
                )
            else:
                logger.log(
                    f"\n[INFO] No stored action found for this intent, fetching swagger context..."
                )

            # Retrieve swagger context
            swagger_contexts = rag_instance.retrieve_endpoints_by_intent(
                intent, top_k=1
            )
            if swagger_contexts:
                swagger_context = swagger_contexts[0]
                result["learning_source"] = "swagger"
                logger.log(
                    f"\n[OK] Found swagger context ({len(swagger_context)} chars)"
                )
                logger.log_titled_block(
                    "SWAGGER CONTEXT", swagger_context, max_chars=3000
                )
            else:
                result["error"] = (
                    f"No matching API endpoints found for intent: '{intent}'"
                )
                logger.log(f"[ERROR] {result['error']}")
                logger.end_session()
                return result

        logger.log_step_separator()

        # ============================================================================
        # STEP 2: GITLAB DUO - GENERATE API ACTION METADATA
        # ============================================================================
        logger.log_section("[STEP 2] GITLAB DUO - GENERATING API ACTION METADATA")
        logger.log(
            f"[Source] Using {'stored metadata' if stored_metadata else 'swagger context'}"
        )
        logger.log(f"[Sending request to GitLab Duo...]")

        # Build the prompt
        duo_prompt = get_api_endpoint_action_prompt(
            resource=resource,
            intent=intent,
            swagger_context=swagger_context or "",
            stored_metadata=stored_metadata,
            base_url=base_url,
        )

        result["prompts"]["action_generation"] = duo_prompt
        logger.log_prompt(duo_prompt)

        # Call GitLab Duo
        duo_response = self.ai_agent.run_agent_based_on_context(
            context="API_ENDPOINT_ACTION", prompt=duo_prompt, return_prompt=False
        )

        result["responses"]["action_generation"] = duo_response
        logger.log_ai_response(duo_response)

        if not duo_response:
            result["error"] = "Failed to get action metadata from GitLab Duo"
            logger.log(f"[ERROR] {result['error']}")
            logger.end_session()
            return result

        # Parse the action metadata from DUO response
        action_metadata = self._parse_action_metadata(duo_response)

        if not action_metadata:
            result["error"] = "Failed to parse action metadata from GitLab Duo response"
            logger.log(f"[ERROR] {result['error']}")
            logger.end_session()
            return result

        result["action_metadata"] = action_metadata
        logger.log(f"\n[OK] Parsed action metadata:")
        logger.log_titled_block(
            "ACTION METADATA", json.dumps(action_metadata, indent=2), max_chars=3000
        )

        # Extract curl command from action metadata
        curl_command = action_metadata.get("curl", "")
        if not curl_command:
            result["error"] = "No curl command in action metadata"
            logger.log(f"[ERROR] {result['error']}")
            logger.end_session()
            return result

        curl_command = self._clean_curl_command(curl_command)
        result["curl_command"] = curl_command
        result["request_body"] = action_metadata.get("request_body", {})

        logger.log_step_separator()

        # ============================================================================
        # STEP 3: EXECUTE CURL COMMAND
        # ============================================================================
        logger.log_section("[STEP 3] EXECUTING CURL COMMAND")

        attempt = 0
        execution_result = None
        while attempt <= max_retries:
            logger.log(f"\n[Attempt {attempt + 1}/{max_retries + 1}]")
            logger.log(f"[Executing command]: {curl_command[:100]}...")

            execution_result = self._execute_curl(curl_command)
            result["status_code"] = execution_result["status_code"]
            result["response_body"] = execution_result["stdout"]
            result["retries"] = attempt

            if execution_result["success"]:
                logger.log(f"\n[OK] Curl executed successfully!")
                logger.log(f"\n{'-'*40} CURL RESPONSE {'-'*40}")
                logger.log(f"HTTP Status Code: {execution_result['status_code']}")
                logger.log(f"\nResponse Body:")
                try:
                    resp_json = json.loads(execution_result["stdout"])
                    formatted_resp = json.dumps(resp_json, indent=2)
                    if len(formatted_resp) > 3000:
                        logger.log(formatted_resp[:3000])
                        logger.log(f"\n... (truncated)")
                    else:
                        logger.log(formatted_resp)
                except:
                    if len(execution_result["stdout"]) > 3000:
                        logger.log(execution_result["stdout"][:3000])
                        logger.log(f"\n... (truncated)")
                    else:
                        logger.log(execution_result["stdout"])
                logger.log(f"{'-'*90}")
                break
            else:
                error_msg = execution_result["stderr"] or execution_result["error"]
                logger.log(f"\n[WARNING] Curl execution failed!")
                logger.log(f"Error: {error_msg}")

                if attempt < max_retries:
                    logger.log(
                        f"\n[RETRY] Asking GitLab Duo to fix the curl command..."
                    )

                    retry_result = self.ai_agent.retry_curl_generation(
                        intent=intent,
                        original_curl=curl_command,
                        error_output=error_msg,
                        swagger_context=swagger_context or "",
                        base_url=base_url,
                        return_prompt=True,
                    )

                    if isinstance(retry_result, tuple):
                        fixed_curl, retry_prompt = retry_result
                    else:
                        fixed_curl = retry_result
                        retry_prompt = "(Prompt not available)"

                    result["prompts"][f"retry_{attempt+1}"] = retry_prompt
                    result["responses"][f"retry_{attempt+1}"] = fixed_curl

                    logger.log_prompt(retry_prompt)

                    if fixed_curl:
                        logger.log_ai_response(fixed_curl)
                        curl_command = self._clean_curl_command(fixed_curl)
                        result["curl_command"] = curl_command
                        logger.log(f"\n[OK] GitLab Duo provided fixed curl command:")
                        logger.log_titled_block(
                            "FIXED CURL COMMAND", curl_command, max_chars=5000
                        )
                    else:
                        logger.log(
                            f"[FAIL] Failed to get fixed curl command from GitLab Duo"
                        )
                        break

                attempt += 1

        logger.log_step_separator()

        # ============================================================================
        # STEP 4: STORE RESULT IN LEARNING COLLECTION
        # ============================================================================
        logger.log_section("[STEP 4] STORING RESULT IN API LEARNING COLLECTION")

        # Determine status: [correct] if status != 404, else [incorrect]
        actual_status = result["status_code"]
        learning_status = (
            "[correct]" if actual_status and actual_status != 404 else "[incorrect]"
        )

        logger.log(f"[Actual Status Code] {actual_status}")
        logger.log(f"[Learning Status] {learning_status}")

        # Store the action in ChromaDB
        rag_instance.store_api_action_from_duo(
            resource=resource,
            duo_response=action_metadata,
            status=learning_status,
            curl=result["curl_command"],
            actual_status=actual_status,
            request_body=result["request_body"],
            response_body=result["response_body"],
        )

        logger.log(f"[OK] Stored action with status {learning_status}")

        logger.log_step_separator()

        # ============================================================================
        # STEP 5: GITLAB DUO - ANALYZE RESPONSE
        # ============================================================================
        logger.log_section("[STEP 5] GITLAB DUO - ANALYZING RESPONSE")
        logger.log(f"[Sending response to GitLab Duo for analysis...]")

        analysis_result = self.ai_agent.analyze_api_response(
            intent=intent,
            curl_command=result["curl_command"],
            response_body=result["response_body"] or "",
            status_code=result["status_code"] or -1,
            stderr=execution_result.get("stderr", "") if execution_result else "",
            return_prompt=True,
        )

        if isinstance(analysis_result, tuple):
            analysis, analysis_prompt = analysis_result
        else:
            analysis = analysis_result
            analysis_prompt = "(Prompt not available)"

        result["prompts"]["analysis"] = analysis_prompt
        result["responses"]["analysis"] = analysis

        logger.log_prompt(analysis_prompt)

        result["analysis"] = analysis

        if analysis:
            logger.log_ai_response(analysis)
        else:
            logger.log("(No analysis returned)")

        logger.log_step_separator()

        # ============================================================================
        # STEP 6: PARSE ANALYSIS AND DETERMINE SUCCESS
        # ============================================================================
        logger.log_section("[STEP 6] PARSING AI ANALYSIS RESULT")

        analysis_json = self._parse_analysis_json(analysis)
        result["analysis_result"] = analysis_json

        if analysis_json:
            result["success"] = analysis_json.get("success", False)
            result["reason"] = analysis_json.get("reason", "No reason provided")
            logger.log(f"[AI Analysis] Success: {result['success']}")
            logger.log(f"[AI Analysis] Reason: {result['reason']}")
        else:
            # Fallback: Determine success based on status code if AI analysis parsing fails
            logger.log(
                "[WARNING] Could not parse AI analysis JSON, falling back to status code check"
            )
            if result["status_code"] and 200 <= result["status_code"] < 300:
                result["success"] = True
                result["reason"] = (
                    f"HTTP {result['status_code']} - Request completed successfully"
                )
            else:
                result["success"] = False
                result["reason"] = f"HTTP {result['status_code']} - Request failed"

        logger.log_step_separator()

        # ============================================================================
        # STEP 7: FINAL SUMMARY
        # ============================================================================

        # Log comprehensive summary
        summary_data = {
            "Intent": intent,
            "Resource": resource,
            "Base URL": base_url,
            "Learning Source": result["learning_source"],
            "Curl Command Generated": "Yes" if result["curl_command"] else "No",
            "HTTP Status Code": result["status_code"],
            "Retries Used": result["retries"],
            "Learning Status Stored": learning_status,
            "API Response": (
                result["response_body"][:200] + "..."
                if result["response_body"] and len(result["response_body"]) > 200
                else result["response_body"]
            ),
            "AI Analysis Result": "PASS" if result["success"] else "FAIL",
            "AI Analysis Reason": result.get("reason", "N/A"),
            "Error": result["error"] if result["error"] else "None",
        }
        logger.log_summary(summary_data)

        # Print final summary box
        self._print_execution_summary(result, logger)

        # End logging session
        logger.end_session()

        return result

    def _extract_resource_from_intent(self, intent: str) -> str:
        """
        Extract API resource name from intent.

        Examples:
            "get all users" -> "users"
            "create a new book" -> "books"
            "delete user with id 5" -> "users"
            "fetch products" -> "products"
        """
        # Common resource patterns
        common_resources = [
            "users",
            "user",
            "books",
            "book",
            "products",
            "product",
            "orders",
            "order",
            "items",
            "item",
            "posts",
            "post",
            "comments",
            "comment",
            "categories",
            "category",
            "login",
            "auth",
            "authentication",
            "register",
            "signup",
            "accounts",
            "account",
            "customers",
            "customer",
            "employees",
            "employee",
        ]

        intent_lower = intent.lower()

        # Find the first matching resource in the intent
        for resource in common_resources:
            if resource in intent_lower:
                # Normalize to plural form for consistency
                if not resource.endswith("s") and resource not in [
                    "login",
                    "auth",
                    "authentication",
                    "register",
                    "signup",
                ]:
                    return resource + "s"
                return resource

        # If no known resource found, try to extract from common patterns
        import re

        patterns = [
            r"(?:get|fetch|retrieve|list|create|add|update|delete|remove)\s+(?:a\s+)?(?:new\s+)?(\w+)",
            r"(\w+)\s+(?:with|by|for)\s+",
        ]

        for pattern in patterns:
            match = re.search(pattern, intent_lower)
            if match:
                resource = match.group(1)
                if len(resource) > 2:  # Avoid short words like "id", "by"
                    return resource

        # Default fallback
        return "resource"

    def _parse_action_metadata(self, duo_response: str) -> dict:
        """
        Parse action metadata JSON from GitLab Duo response.

        Args:
            duo_response: Raw response string from GitLab Duo

        Returns:
            dict: Parsed action metadata or None if parsing fails
        """
        if not duo_response:
            return None

        try:
            # Try direct JSON parse
            return json.loads(duo_response.strip())
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        json_patterns = [
            r"```json\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```",
            r'\{[^{}]*"action_key"[^{}]*\}',
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, duo_response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    json_str = match.strip() if isinstance(match, str) else match
                    parsed = json.loads(json_str)
                    if "action_key" in parsed or "curl" in parsed:
                        return parsed
                except (json.JSONDecodeError, TypeError):
                    continue

        # Try to find JSON object with required keys
        try:
            start = duo_response.find("{")
            end = duo_response.rfind("}")
            if start != -1 and end != -1 and end > start:
                potential_json = duo_response[start : end + 1]
                parsed = json.loads(potential_json)
                if isinstance(parsed, dict):
                    return parsed
        except json.JSONDecodeError:
            pass

        return None

    def _parse_analysis_json(self, analysis: str) -> dict:
        """
        Parse the JSON analysis from GitLab Duo response.

        Args:
            analysis: The raw analysis string from GitLab Duo

        Returns:
            dict: Parsed JSON with 'success' and 'reason' keys, or None if parsing fails
        """
        if not analysis:
            return None

        try:
            # Try to parse the analysis directly as JSON
            return json.loads(analysis.strip())
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        import re

        json_patterns = [
            r"```json\s*(.*?)\s*```",  # ```json ... ```
            r"```\s*(.*?)\s*```",  # ``` ... ```
            r'\{[^{}]*"success"[^{}]*\}',  # Find JSON object with "success" key
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, analysis, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    # If match is from regex group, use it directly
                    json_str = match.strip() if isinstance(match, str) else match
                    parsed = json.loads(json_str)
                    if "success" in parsed:
                        return parsed
                except (json.JSONDecodeError, TypeError):
                    continue

        # Last resort: try to find and extract a JSON-like structure
        try:
            # Find the first { and last } to extract potential JSON
            start = analysis.find("{")
            end = analysis.rfind("}")
            if start != -1 and end != -1 and end > start:
                potential_json = analysis[start : end + 1]
                return json.loads(potential_json)
        except json.JSONDecodeError:
            pass

        return None

    def _clean_curl_command(self, curl_command: str) -> str:
        """
        Clean up curl command by removing markdown code blocks, extra whitespace, etc.
        """
        if not curl_command:
            return ""

        # Remove markdown code blocks
        curl_command = re.sub(r"```(?:bash|sh|shell)?\s*", "", curl_command)
        curl_command = re.sub(r"```\s*", "", curl_command)

        # Remove leading/trailing whitespace
        curl_command = curl_command.strip()

        # Remove any "Here is the curl command:" type prefixes
        prefixes_to_remove = [
            "here is the curl command:",
            "the curl command is:",
            "curl command:",
            "here's the curl:",
        ]
        lower_cmd = curl_command.lower()
        for prefix in prefixes_to_remove:
            if lower_cmd.startswith(prefix):
                curl_command = curl_command[len(prefix) :].strip()
                break

        # Ensure the command starts with 'curl'
        if not curl_command.lower().startswith("curl"):
            # Try to find 'curl' in the command
            curl_index = curl_command.lower().find("curl")
            if curl_index != -1:
                curl_command = curl_command[curl_index:]

        return curl_command.strip()

    def _execute_curl(self, curl_command: str) -> dict:
        """
        Execute curl command via subprocess.

        Args:
            curl_command (str): The curl command to execute

        Returns:
            dict: Execution result with success, stdout, stderr, status_code, error
        """
        result = {
            "success": False,
            "stdout": "",
            "stderr": "",
            "status_code": None,
            "error": None,
        }

        if not curl_command:
            result["error"] = "Empty curl command"
            return result

        # Modify curl to include -w for status code and -s for silent mode
        # Also add -k for SSL bypass if not already present
        modified_curl = curl_command

        if "-k" not in modified_curl:
            # Add -k after 'curl'
            modified_curl = modified_curl.replace("curl ", "curl -k ", 1)

        # Add -w to get status code and -s for silent progress
        if "-w" not in modified_curl:
            modified_curl += ' -w "\\n%{http_code}"'
        if "-s" not in modified_curl:
            modified_curl = modified_curl.replace("curl ", "curl -s ", 1)

        log.safe_print(f"[DEBUG] Executing: {modified_curl[:200]}...")

        try:
            # Determine shell based on platform
            is_windows = platform.system().lower() == "windows"

            if is_windows:
                # On Windows, use cmd.exe
                process = subprocess.run(
                    modified_curl,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    encoding="utf-8",
                    errors="replace",
                )
            else:
                # On Linux/Mac, use bash
                process = subprocess.run(
                    ["bash", "-c", modified_curl],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    encoding="utf-8",
                    errors="replace",
                )

            result["stdout"] = process.stdout.strip()
            result["stderr"] = process.stderr.strip()

            # Extract status code from the last line (added by -w)
            if result["stdout"]:
                lines = result["stdout"].split("\n")
                if lines:
                    last_line = lines[-1].strip()
                    if last_line.isdigit():
                        result["status_code"] = int(last_line)
                        # Remove status code from response body
                        result["stdout"] = "\n".join(lines[:-1]).strip()

            # Check for curl errors
            if process.returncode != 0 and not result["stdout"]:
                result["error"] = (
                    f"Curl returned exit code {process.returncode}: {result['stderr']}"
                )
            else:
                result["success"] = True

        except subprocess.TimeoutExpired:
            result["error"] = f"Curl command timed out after {self.timeout} seconds"
        except Exception as e:
            result["error"] = f"Error executing curl: {str(e)}"

        return result

    def _print_execution_summary(self, result: dict, logger: IntentLogger = None):
        """Print a comprehensive summary of the execution result with full logs."""

        # Use logger if provided, otherwise just print
        def log(msg):
            if logger:
                logger.log(msg)
            else:
                log.safe_print(msg)

        log(f"\n{'='*80}")
        log(f"{'='*80}")
        log(f"                    >> FULL EXECUTION SUMMARY <<")
        log(f"{'='*80}")
        log(f"{'='*80}")

        # Intent & Config
        log(f"\n+{'-'*78}+")
        log(
            f"| >> INTENT & CONFIGURATION                                                    |"
        )
        log(f"+{'-'*78}+")
        log(f"| Intent: {result['intent'][:68]:<68} |")
        log(f"| Base URL: {result['base_url'][:66]:<66} |")
        log(f"| Retries Used: {result['retries']:<62} |")
        log(f"+{'-'*78}+")

        # Curl Command
        log(f"\n+{'-'*78}+")
        log(
            f"| >> GENERATED CURL COMMAND                                                    |"
        )
        log(f"+{'-'*78}+")
        if result["curl_command"]:
            # Split long curl commands for display
            curl_lines = [
                result["curl_command"][i : i + 76]
                for i in range(0, len(result["curl_command"]), 76)
            ]
            for line in curl_lines[:10]:  # Limit to 10 lines
                log(f"| {line:<76} |")
            if len(curl_lines) > 10:
                log(f"| {'... (truncated)':<76} |")
        else:
            log(f"| {'No curl command generated':<76} |")
        log(f"+{'-'*78}+")

        # API Response
        log(f"\n+{'-'*78}+")
        log(
            f"| >> API RESPONSE                                                              |"
        )
        log(f"+{'-'*78}+")
        log(f"| Status Code: {str(result['status_code']):<63} |")
        log(f"| Success: {'[OK] Yes' if result['success'] else '[FAIL] No':<68} |")
        log(f"+{'-'*78}+")
        log(
            f"| Response Body:                                                               |"
        )
        if result["response_body"]:
            # Pretty print JSON if possible
            try:
                resp_json = json.loads(result["response_body"])
                resp_formatted = json.dumps(resp_json, indent=2)
                resp_lines = resp_formatted.split("\n")
                for line in resp_lines[:30]:  # Limit to 30 lines
                    log(f"|   {line[:74]:<74} |")
                if len(resp_lines) > 30:
                    log(
                        f"|   {'... (truncated - ' + str(len(resp_lines) - 30) + ' more lines)':<74} |"
                    )
            except:
                # Not JSON, show as text
                resp_lines = [
                    result["response_body"][i : i + 74]
                    for i in range(0, min(len(result["response_body"]), 2000), 74)
                ]
                for line in resp_lines[:20]:
                    log(f"|   {line:<74} |")
                if len(result["response_body"]) > 2000:
                    log(f"|   {'... (truncated)':<74} |")
        else:
            log(f"|   {'(empty response)':<74} |")
        log(f"+{'-'*78}+")

        # Error (if any)
        if result["error"]:
            log(f"\n+{'-'*78}+")
            log(
                f"| [ERROR]                                                                      |"
            )
            log(f"+{'-'*78}+")
            error_lines = [
                result["error"][i : i + 76] for i in range(0, len(result["error"]), 76)
            ]
            for line in error_lines[:5]:
                log(f"| {line:<76} |")
            log(f"+{'-'*78}+")

        # AI Analysis
        log(f"\n+{'-'*78}+")
        log(
            f"| [AI] GITLAB DUO ANALYSIS                                                     |"
        )
        log(f"+{'-'*78}+")
        if result["analysis"]:
            analysis_lines = result["analysis"].split("\n")
            for line in analysis_lines[:40]:  # Limit to 40 lines
                log(f"| {line[:76]:<76} |")
            if len(analysis_lines) > 40:
                log(
                    f"| {'... (truncated - ' + str(len(analysis_lines) - 40) + ' more lines)':<76} |"
                )
        else:
            log(f"| {'No analysis available':<76} |")
        log(f"+{'-'*78}+")

        # Final Result
        log(f"\n{'='*80}")
        if result["success"]:
            log(f"                         [OK] TEST PASSED [OK]")
        else:
            log(f"                         [FAIL] TEST FAILED [FAIL]")
        log(f"{'='*80}")
