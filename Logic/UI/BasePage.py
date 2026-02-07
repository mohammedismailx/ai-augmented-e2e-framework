from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from Logic.API.api_wrapper import APIWrapper
from Libs.IntentLocatorLibrary import IntentLocatorLibrary
from Utils.logger import IntentLogger
import builtins
import re
import json
import time
import fnmatch


class BasePage:
    """
    Base class for all Page Objects.
    Handles direct Playwright interactions and AI self-healing logic.
    """

    def __init__(self, page: Page, api_wrapper: APIWrapper = None):
        """
        Initialize BasePage.
        Page must be provided (e.g., from pytest fixtures).
        Config is loaded from globals.
        """
        if not page:
            raise ValueError("Page object must be provided to BasePage")

        self.page = page
        self.config = builtins.CONFIG

        # Initialize APIWrapper internally if not provided
        # This wrapper will handle the AIAgent initialization
        base_ai_url = builtins.URLS.get("gitlab", {}).get(
            "base_url"
        ) or self.config.get("base_url")
        self.api_wrapper = api_wrapper if api_wrapper else APIWrapper(base_ai_url)
        self.ai_agent = self.api_wrapper.ai_agent

        # Load settings from config
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_interval = self.config.get("retry_interval", 1)
        self.agent_mode = self.config.get("agent_mode", "ENABLED")
        self.timeout = self.config.get("timeout", 5000)

        # Network interception storage
        self._captured_requests = []
        self._captured_responses = []
        self._network_listener_active = False

    def prepare_element(self, locator, timeout=None):
        """
        Waits for element to be attached, visible, and stable.
        Uses configured timeout if not specified.
        """
        timeout = timeout if timeout is not None else self.timeout
        print(f"Preparing element: {locator}")
        try:
            # Wait for attached
            self.page.wait_for_selector(locator, state="attached", timeout=timeout)
            # Wait for visible
            self.page.wait_for_selector(locator, state="visible", timeout=timeout)
            # Wait for stable
            self.page.locator(locator).wait_for(state="visible", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            print(f"Element {locator} failed to be ready within {timeout}ms")
            raise

    def click_custom(self, locator, var_name="unknown_var"):
        """
        Click element with retry and AI self-healing.
        """
        print(f"Clicking custom: {locator}")
        last_err = ""

        for attempt in range(1, self.max_retries + 2):
            print(f"Attempt {attempt}/{self.max_retries} on locator: {locator}")

            try:
                self.prepare_element(locator)
                self.page.click(locator)
                print(f"Clicked {locator}")
                return "PASS"
            except Exception as e:
                last_err = str(e)
                print(f"Error: {last_err}")

                # Check if last attempt and agent enabled
                if attempt > self.max_retries and self.agent_mode == "ENABLED":
                    print("Last attempt: Trying AI Agent suggested locator")

                    # Call AI Agent
                    new_locator = self.ai_agent.run_agent_based_on_context(
                        context="SELF_HEALING",
                        locator_name=var_name,
                        locator_value=locator,
                        html_content=self.page.content(),
                    )

                    print(f"AI Agent suggested: {new_locator}")

                    try:
                        self.prepare_element(new_locator)
                        self.page.click(new_locator)
                        print(f"Clicked {new_locator}")
                        print(
                            f'Success: AI Agent self-healing worked with locator: "{new_locator}", You can update the variable "{var_name}" with the new value "{new_locator}" as the old value "{locator}" was failing'
                        )
                        return "PASS"
                    except Exception as ai_e:
                        last_err = f"AI Agent suggestion failed: {ai_e}"

        raise Exception(
            f"Click failed after {self.max_retries} attempts. Last error: {last_err}"
        )

    # Common page methods
    def navigate(self, url):
        """Navigate to a URL"""
        print(f"Navigating to {url}")
        self.page.goto(url)

    def get_title(self):
        """Get page title"""
        return self.page.title()

    def get_url(self):
        """Get current URL"""
        return self.page.url

    def wait_for_url(self, url_pattern, timeout=None):
        """Wait for URL to match pattern"""
        timeout = timeout if timeout is not None else self.timeout
        self.page.wait_for_url(url_pattern, timeout=timeout)

    def take_screenshot(self, path):
        """Take a screenshot"""
        self.page.screenshot(path=path)
        print(f"Screenshot saved to {path}")

    def fill_input(self, locator, value):
        """Fill an input field"""
        print(f"Filling {locator} with value: {value}")
        self.page.fill(locator, value)

    def get_text(self, locator):
        """Get text content of an element"""
        return self.page.locator(locator).text_content()

    def is_visible(self, locator):
        """Check if element is visible"""
        return self.page.locator(locator).is_visible()

    def wait_for_element(self, locator, timeout=None):
        """Wait for element to be visible"""
        timeout = timeout if timeout is not None else self.timeout
        self.page.wait_for_selector(locator, state="visible", timeout=timeout)

    # =========================================================================
    # INTENT-BASED EXECUTION WITH RAG LEARNING
    # =========================================================================

    # Top K elements to retrieve per action type
    TOP_K_BY_ACTION = {
        "click": 5,
        "fill": 3,
        "select": 3,
        "verify": 10,
        "navigate": 0,
        "wait": 5,
        "hover": 5,
        "network": 0,  # Network actions don't need elements
        "default": 5,
    }

    # Actions that mark HTML as dirty (need refresh)
    DIRTY_ACTIONS = {"navigate", "click"}

    # Maximum retry attempts (Trial 1: RAG, Trial 2: Live HTML)
    MAX_TRIALS = 2

    def execute_by_intent(
        self, intent: str, rag_context=None, assert_success: bool = True
    ) -> dict:
        """
        Execute UI test by Gherkin-style intent with RAG-based learning.

        NEW ALGORITHM (Simplified DUO-Centric Flow):
        =============================================
        For each step:
        1. Extract module from current URL (e.g., /inventory -> "inventory")
        2. Retrieve from ChromaDB by module + intent
           - If found [correct] → send stored_metadata to DUO
           - If not found or [incorrect] → get live HTML elements, send to DUO
        3. DUO returns FULL metadata dict (same format as stored):
           {
               "action_key": "click_login",
               "intent": "...",
               "action_type": "click",
               "locator": "#login-btn",
               "action_json": {...},
               "playwright_code": "page.click('#login-btn')"
           }
        4. Extract playwright_code from DUO response, execute
        5. Mark status [correct] or [incorrect], store in ChromaDB

        Args:
            intent: Multi-line Gherkin steps
            rag_context: RAG instance for learning storage
            assert_success (bool): If True, raises AssertionError when any step fails.
                                   Set to False for negative testing scenarios.

        Returns:
            dict with execution results
        """
        logger = IntentLogger(test_type="UI")
        logger.start_session(intent)

        result = {
            "success": False,
            "intent": intent,
            "steps": [],
            "error": None,
        }

        try:
            # Parse Gherkin steps
            steps = self._parse_gherkin_steps(intent)
            if not steps:
                result["error"] = "No valid Gherkin steps found"
                logger.log("[PARSE] No valid Gherkin steps found in intent")
                logger.end_session()
                return result

            logger.log(f"[PARSE] Found {len(steps)} steps to execute")

            # Initialize IntentLocatorLibrary
            intent_locator = IntentLocatorLibrary()

            # Execute each step
            previous_steps = []
            for step_idx, step in enumerate(steps):
                step_type = step["type"]
                step_intent = step["intent"]

                logger.log_section(f"STEP {step_idx + 1}: [{step_type}] {step_intent}")

                step_result = {
                    "step_type": step_type,
                    "intent": step_intent,
                    "status": "pending",
                    "duo_response": None,
                    "source": None,  # "stored_metadata" or "live_html"
                }

                try:
                    # === STEP 1: Extract module from current URL ===
                    current_url = self.page.url
                    current_module = self._extract_module_from_url(current_url)
                    logger.log(f"[MODULE] {current_module} (from {current_url})")

                    # Get action type hint for element retrieval
                    action_hint = self._guess_action_type(step_intent)
                    top_k = self.TOP_K_BY_ACTION.get(
                        action_hint, self.TOP_K_BY_ACTION["default"]
                    )

                    # Check if this is a network action (skip RAG for network actions)
                    is_network_action = action_hint == "network"

                    stored_metadata = None
                    relevant_elements = None
                    source = "live_html"

                    # === STEP 2: Retrieve from ChromaDB ===
                    if not is_network_action and rag_context:
                        rag_result = rag_context.retrieve_ui_action_for_intent(
                            current_module, step_intent
                        )

                        if (
                            rag_result.get("found")
                            and rag_result.get("status") == "[correct]"
                        ):
                            # Found [correct] action - send stored metadata to DUO
                            stored_metadata = rag_result.get("stored_metadata")
                            source = "stored_metadata"

                            # Log retrieval success
                            logger.log_rag_retrieval(
                                module=current_module,
                                found=True,
                                status="[correct]",
                                action_key=stored_metadata.get("action_key"),
                                match_score=rag_result.get("match_score", 0),
                            )

                            # Log full stored metadata
                            logger.log_stored_metadata(stored_metadata)
                        else:
                            # Not found or [incorrect] - will rely on live HTML
                            logger.log_rag_retrieval(
                                module=current_module,
                                found=False,
                                status=rag_result.get("status"),
                            )

                    # === STEP 3: ALWAYS get live HTML elements (for validation) ===
                    # Even if stored_metadata exists, we get live HTML so DUO can validate
                    if top_k > 0:
                        logger.log(f"\n[HTML] Getting live page elements...")
                        html_content = self._get_page_html()

                        if html_content:
                            relevant_elements = intent_locator.find_elements_outerhtml_with_score_backoff(
                                html_or_path=html_content,
                                intent_str=step_intent,
                                top_k=top_k,
                                start=0.5,
                                min_floor=0.05,
                            )
                            logger.log(
                                f"[HTML] Found {len(relevant_elements)} relevant elements"
                            )

                            # Log live HTML elements
                            logger.log_live_html_elements(relevant_elements)
                        else:
                            logger.log(f"[HTML] Failed to get page HTML")

                    # === STEP 4: Send to DUO (GitLab Duo AI) ===
                    logger.log_duo_request(
                        source=source,
                        module=current_module,
                        step_intent=step_intent,
                        step_type=step_type,
                    )

                    # Get the prompt that will be sent to DUO
                    duo_prompt = self.ai_agent.run_agent_based_on_context(
                        context="UI_MODULE_ACTION",
                        step_intent=step_intent,
                        step_type=step_type,
                        module=current_module,
                        page_url=current_url,
                        stored_metadata=stored_metadata,
                        relevant_elements=relevant_elements,
                        previous_steps=previous_steps,
                        return_prompt=True,  # Get prompt first
                    )

                    # Log the prompt being sent
                    logger.log_duo_prompt(duo_prompt)

                    # Now actually call DUO
                    logger.log(f"\n[DUO] Sending to GitLab Duo...")

                    duo_response = self.ai_agent.run_agent_based_on_context(
                        context="UI_MODULE_ACTION",
                        step_intent=step_intent,
                        step_type=step_type,
                        module=current_module,
                        page_url=current_url,
                        stored_metadata=stored_metadata,
                        relevant_elements=relevant_elements,
                        previous_steps=previous_steps,
                    )

                    if not duo_response:
                        raise Exception("DUO failed to generate action metadata")

                    # Log full DUO response
                    logger.log_duo_response(duo_response)

                    step_result["duo_response"] = duo_response
                    step_result["source"] = source

                    # === STEP 5: Execute action using action_json ===
                    action_json = duo_response.get("action_json", {})
                    if isinstance(action_json, str):
                        try:
                            action_json = json.loads(action_json)
                        except:
                            action_json = {}

                    logger.log(f"\n[EXECUTE] Executing action...")
                    success = self._execute_action(action_json, logger)

                    action_type = duo_response.get("action_type", "")
                    locator = duo_response.get("locator", "")

                    if success:
                        step_result["status"] = "passed"
                        logger.log(f"[RESULT] [{step_type}] PASSED")

                        # === STORE [correct] IN CHROMADB ===
                        if rag_context and not is_network_action:
                            logger.log_store_action(
                                module=current_module,
                                action_key=duo_response.get("action_key"),
                                status="[correct]",
                                locator=duo_response.get("locator"),
                                playwright_code=duo_response.get("playwright_code"),
                            )

                            rag_context.store_ui_action_from_duo(
                                module=current_module,
                                duo_response=duo_response,
                                status="[correct]",
                                url=current_url,
                            )

                        # Mark HTML dirty if needed
                        if action_type in self.DIRTY_ACTIONS:
                            time.sleep(0.5)  # Small wait for page to update

                    else:
                        # === ACTION FAILED ===
                        logger.log(f"[EXECUTE] Action failed")

                        # Capture the failed action for retry analysis
                        failed_action = duo_response
                        error_msg = "Action execution failed"

                        # If we used stored_metadata, try again with enhanced retry
                        if source == "stored_metadata" and not is_network_action:
                            logger.log(
                                f"\n[RETRY] Stored action failed, trying with AI analysis..."
                            )

                            # STEP 1: Get AI analysis of why the action failed
                            logger.log(f"[RETRY] Getting AI analysis of failure...")
                            ai_analysis = self.ai_agent.run_agent_based_on_context(
                                context="UI_STEP_FAILURE_ANALYSIS",
                                step_intent=step_intent,
                                step_type=step_type,
                                failed_action=failed_action,
                                error=error_msg,
                                relevant_elements=(
                                    relevant_elements[:5] if relevant_elements else []
                                ),
                                page_url=current_url,
                                page_title=(
                                    self.page.title()
                                    if hasattr(self.page, "title")
                                    else ""
                                ),
                                previous_steps=previous_steps,
                            )
                            logger.log(
                                f"[RETRY] AI Analysis: {str(ai_analysis)[:200]}..."
                            )

                            # Mark old action as [incorrect] in store
                            if rag_context:
                                logger.log_store_action(
                                    module=current_module,
                                    action_key=duo_response.get("action_key"),
                                    status="[incorrect]",
                                    context="MARKING ACTION AS INCORRECT",
                                )

                                rag_context.store_ui_action_from_duo(
                                    module=current_module,
                                    duo_response=duo_response,
                                    status="[incorrect]",
                                    url=current_url,
                                )

                            # STEP 2: Get fresh live HTML elements
                            html_content = self._get_page_html()
                            if html_content:
                                relevant_elements = intent_locator.find_elements_outerhtml_with_score_backoff(
                                    html_or_path=html_content,
                                    intent_str=step_intent,
                                    top_k=top_k * 2,
                                    start=0.5,
                                    min_floor=0.05,
                                )

                                # Log retry elements
                                logger.log_live_html_elements(
                                    relevant_elements, is_retry=True
                                )

                            # STEP 3: Use ENHANCED retry with AI analysis and all original context
                            logger.log(
                                f"[RETRY] Sending to DUO with AI analysis and fresh HTML..."
                            )
                            duo_response = self.ai_agent.run_agent_based_on_context(
                                context="UI_MODULE_RETRY",
                                step_intent=step_intent,
                                step_type=step_type,
                                module=current_module,
                                page_url=current_url,
                                failed_action=failed_action,
                                error=error_msg,
                                ai_analysis=str(ai_analysis) if ai_analysis else "",
                                stored_metadata=stored_metadata,  # Original stored metadata
                                relevant_elements=relevant_elements,
                                previous_steps=previous_steps,
                            )

                            if duo_response:
                                # Log retry DUO response
                                logger.log_duo_response(duo_response, is_retry=True)

                                step_result["duo_response"] = duo_response
                                step_result["source"] = "ai_analysis_retry"

                                action_json = duo_response.get("action_json", {})
                                if isinstance(action_json, str):
                                    try:
                                        action_json = json.loads(action_json)
                                    except:
                                        action_json = {}

                                success = self._execute_action(action_json, logger)

                                if success:
                                    step_result["status"] = "passed"
                                    logger.log(
                                        f"[RESULT] [{step_type}] PASSED (AI Retry)"
                                    )

                                    # Store as [correct]
                                    if rag_context:
                                        logger.log_store_action(
                                            module=current_module,
                                            action_key=duo_response.get("action_key"),
                                            status="[correct]",
                                            context="STORING RETRY ACTION AS CORRECT",
                                        )

                                        rag_context.store_ui_action_from_duo(
                                            module=current_module,
                                            duo_response=duo_response,
                                            status="[correct]",
                                            url=current_url,
                                        )
                                else:
                                    # Store as [incorrect]
                                    if rag_context:
                                        logger.log_store_action(
                                            module=current_module,
                                            action_key=duo_response.get("action_key"),
                                            status="[incorrect]",
                                            context="STORING RETRY ACTION AS INCORRECT",
                                        )

                                        rag_context.store_ui_action_from_duo(
                                            module=current_module,
                                            duo_response=duo_response,
                                            status="[incorrect]",
                                            url=current_url,
                                        )
                                    raise Exception(
                                        "Action execution failed after AI-assisted retry"
                                    )
                            else:
                                raise Exception(
                                    "DUO failed to generate action on retry"
                                )
                        else:
                            # First attempt with live HTML failed
                            if rag_context and not is_network_action:
                                logger.log_store_action(
                                    module=current_module,
                                    action_key=duo_response.get("action_key"),
                                    status="[incorrect]",
                                    context="STORING FAILED ACTION AS INCORRECT",
                                )

                                rag_context.store_ui_action_from_duo(
                                    module=current_module,
                                    duo_response=duo_response,
                                    status="[incorrect]",
                                    url=current_url,
                                )
                            raise Exception("Action execution failed")

                except Exception as e:
                    step_result["status"] = "failed"
                    step_result["error"] = str(e)
                    logger.log(f"[ERROR] [{step_type}] FAILED: {e}")

                    # Run failure analysis with duo_response
                    duo_resp = step_result.get("duo_response", {})
                    self._run_failure_analysis(
                        step_intent, step_type, duo_resp, str(e), previous_steps, logger
                    )

                    result["error"] = f"Step failed: [{step_type}] {step_intent} - {e}"
                    result["steps"].append(step_result)
                    logger.end_session()

                    # Assert on failure if enabled (don't silently return)
                    if assert_success:
                        raise AssertionError(
                            f"Step Failed: [{step_type}] {step_intent} - {e}"
                        )
                    return result

                result["steps"].append(step_result)
                previous_steps.append(step_result)

            # All steps passed
            result["success"] = True
            logger.log("\n[COMPLETE] All steps executed successfully")

            # Print learning summary if RAG context available
            if rag_context:
                self._print_learning_summary(rag_context, logger)

        except Exception as e:
            result["error"] = str(e)
            logger.log(f"[ERROR] Execution failed: {e}")

        logger.end_session()

        # ============================================================================
        # ASSERT SUCCESS (if enabled)
        # ============================================================================
        if assert_success:
            # Check overall success
            if not result["success"]:
                raise AssertionError(
                    f"UI Execution Failed: {result.get('error', 'Unknown error')}"
                )

            # Check each step passed
            for step in result.get("steps", []):
                if step.get("status") != "passed":
                    raise AssertionError(
                        f"Step Failed: [{step.get('step_type')}] {step.get('intent')} - {step.get('error', 'Unknown error')}"
                    )

        return result

    def _extract_module_from_url(self, url: str) -> str:
        """
        Extract module name from URL path.

        Examples:
            https://www.saucedemo.com/ -> "home"
            https://www.saucedemo.com -> "home"
            https://www.saucedemo.com/inventory.html -> "inventory"
            https://www.saucedemo.com/cart.html -> "cart"
            about:blank -> "home"
        """
        from urllib.parse import urlparse

        if not url:
            return "home"

        # Handle special URLs like about:blank
        if url.startswith("about:") or url == "":
            return "home"

        try:
            parsed = urlparse(url)
            path = parsed.path.strip("/")

            # No path means home page
            if not path:
                return "home"

            # Remove .html extension
            if path.endswith(".html"):
                path = path[:-5]

            # Get last segment
            segments = path.split("/")
            module = segments[-1] if segments else "home"

            # Handle index pages or empty
            if module in ("index", ""):
                return "home"

            return module if module else "home"

        except Exception:
            return "home"

    def _run_failure_analysis(
        self,
        step_intent: str,
        step_type: str,
        duo_response: dict,
        error: str,
        previous_steps: list,
        logger: IntentLogger,
    ):
        """Run failure analysis with GitLab Duo."""
        logger.log("[ANALYSIS] Requesting failure analysis from GitLab Duo...")

        try:
            page_html_snippet = None
            try:
                page_html_snippet = self._get_page_html()[:5000]
            except:
                pass

            # Extract action_json from duo_response for analysis
            action_attempted = (
                duo_response.get("action_json", duo_response) if duo_response else {}
            )

            failure_analysis = self.ai_agent.run_agent_based_on_context(
                context="UI_STEP_FAILURE_ANALYSIS",
                step_intent=step_intent,
                step_type=step_type,
                action_attempted=action_attempted,
                error_message=error,
                relevant_elements=[],
                page_url=self.page.url,
                page_html_snippet=page_html_snippet,
                previous_steps=previous_steps,
            )

            if failure_analysis:
                logger.log(
                    f"[ANALYSIS] Root Cause: {failure_analysis.get('root_cause', 'Unknown')}"
                )

                suggestions = failure_analysis.get("suggestions", [])
                if suggestions:
                    logger.log("[ANALYSIS] Suggestions:")
                    for i, suggestion in enumerate(suggestions[:3], 1):
                        logger.log(f"  {i}. {suggestion}")

        except Exception as analysis_error:
            logger.log(
                f"[ANALYSIS] Could not generate failure analysis: {analysis_error}"
            )

    def _print_learning_summary(self, rag_context, logger: IntentLogger):
        """Print summary of stored learning data."""
        try:
            summary = rag_context.get_ui_module_summary()

            logger.log("\n" + "=" * 60)
            logger.log("              UI LEARNING SUMMARY")
            logger.log("=" * 60)
            logger.log(f"Total stored actions: {summary.get('total', 0)}")
            logger.log(
                f"Correct: {summary.get('correct_count', 0)} | Incorrect: {summary.get('incorrect_count', 0)}"
            )

            modules = summary.get("modules", {})
            if modules:
                logger.log("\nBy Module:")
                for mod, data in modules.items():
                    logger.log(
                        f"  {mod}: {data['correct']} correct, {data['incorrect']} incorrect"
                    )

            logger.log("=" * 60)

        except Exception as e:
            logger.log(f"[SUMMARY] Could not print learning summary: {e}")

    def _parse_gherkin_steps(self, intent: str) -> list:
        """
        Parse Gherkin-style steps from intent string.

        Returns list of dicts:
            [{"type": "Given", "intent": "I am on the login page"}, ...]
        """
        steps = []

        # Pattern: Given/When/Then/And followed by step text (case-insensitive)
        pattern = r"(?i)^\s*(given|when|then|and)\s+(.+)$"

        for line in intent.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            match = re.match(pattern, line)
            if match:
                step_type = match.group(
                    1
                ).capitalize()  # Normalize to Given/When/Then/And
                step_text = match.group(2).strip()
                steps.append({"type": step_type, "intent": step_text})

        return steps

    def _guess_action_type(self, step_intent: str) -> str:
        """
        Guess the action type from step intent for top_k selection.
        """
        intent_lower = step_intent.lower()

        if any(
            kw in intent_lower for kw in ["navigate", "go to", "open", "visit", "am on"]
        ):
            return "navigate"
        elif any(kw in intent_lower for kw in ["click", "press", "tap", "submit"]):
            return "click"
        elif any(
            kw in intent_lower for kw in ["fill", "enter", "type", "input", "write"]
        ):
            return "fill"
        elif any(kw in intent_lower for kw in ["select", "choose", "pick", "dropdown"]):
            return "select"
        elif any(
            kw in intent_lower
            for kw in [
                "verify",
                "assert",
                "check",
                "see",
                "should",
                "visible",
                "displayed",
            ]
        ):
            return "verify"
        elif any(kw in intent_lower for kw in ["wait"]):
            return "wait"
        elif any(kw in intent_lower for kw in ["hover"]):
            return "hover"
        elif any(
            kw in intent_lower
            for kw in [
                "start capturing",
                "intercept",
                "monitor network",
                "start network",
                "listen to",
            ]
        ):
            return "network"
        elif any(
            kw in intent_lower
            for kw in [
                "validate api",
                "api called",
                "api returned",
                "check api",
                "verify api",
                "network call",
            ]
        ):
            return "network"
        elif any(kw in intent_lower for kw in ["stop capturing", "stop network"]):
            return "network"

        return "default"

    def _get_page_html(self) -> str:
        """Get current page HTML content."""
        try:
            return self.page.content()
        except Exception as e:
            print(f"Failed to get page HTML: {e}")
            return ""

    def _execute_action(self, action: dict, logger: IntentLogger) -> bool:
        """
        Execute a single action on the page.

        Returns True if successful, False otherwise.
        """
        if not action:
            return False

        action_type = action.get("action", "")
        locator = action.get("locator", "")
        value = action.get("value", "")

        try:
            if action_type == "navigate":
                page_ref = action.get("page_ref", "")
                url = self._resolve_url(page_ref)
                if url:
                    self.page.goto(url)
                    logger.log(f"[EXECUTE] Navigated to {url}")
                    return True
                else:
                    logger.log(f"[EXECUTE] Could not resolve URL for {page_ref}")
                    return False

            elif action_type == "click":
                if locator:
                    self.page.click(locator, timeout=self.timeout)
                    logger.log(f"[EXECUTE] Clicked {locator}")
                    return True

            elif action_type == "fill":
                if locator and value is not None:
                    self.page.fill(locator, str(value))
                    logger.log(f"[EXECUTE] Filled {locator} with '{value}'")
                    return True

            elif action_type == "select":
                if locator and value:
                    self.page.select_option(locator, value)
                    logger.log(f"[EXECUTE] Selected '{value}' in {locator}")
                    return True

            elif action_type == "verify":
                return self._execute_verification(action, logger)

            elif action_type == "wait":
                if locator:
                    self.page.wait_for_selector(
                        locator, state="visible", timeout=self.timeout
                    )
                    logger.log(f"[EXECUTE] Waited for {locator}")
                    return True

            elif action_type == "hover":
                if locator:
                    self.page.hover(locator)
                    logger.log(f"[EXECUTE] Hovered over {locator}")
                    return True

            # Network interception actions
            elif action_type in [
                "start_capture",
                "stop_capture",
                "validate_api",
                "clear_capture",
            ]:
                return self._execute_network_action(action, logger)

            logger.log(f"[EXECUTE] Unknown action type: {action_type}")
            return False

        except PlaywrightTimeoutError as e:
            logger.log(f"[EXECUTE] Timeout: {e}")
            return False
        except Exception as e:
            logger.log(f"[EXECUTE] Error: {e}")
            return False

    def _execute_verification(self, action: dict, logger: IntentLogger) -> bool:
        """
        Execute verification checks.
        """
        checks = action.get("checks", [])

        for check in checks:
            check_type = check.get("type", "")
            locator = check.get("locator", "")
            value = check.get("value", "")
            text = check.get("text", "")

            try:
                if check_type == "element_visible":
                    # Use .first to handle multiple matches gracefully
                    element = self.page.locator(locator).first
                    if not element.is_visible():
                        logger.log(f"[VERIFY] Element not visible: {locator}")
                        return False
                    logger.log(f"[VERIFY] Element visible: {locator}")

                elif check_type == "url_contains":
                    current_url = self.page.url
                    if value not in current_url:
                        logger.log(
                            f"[VERIFY] URL '{current_url}' does not contain '{value}'"
                        )
                        return False
                    logger.log(f"[VERIFY] URL contains '{value}'")

                elif check_type == "text_visible":
                    # Use .first to handle multiple matches gracefully
                    text_element = self.page.locator(f"text={text}").first
                    if not text_element.is_visible():
                        logger.log(f"[VERIFY] Text not visible: {text}")
                        return False
                    logger.log(f"[VERIFY] Text visible: {text}")

            except Exception as e:
                logger.log(f"[VERIFY] Check failed: {e}")
                return False

        return True

    def _resolve_url(self, page_ref: str) -> str:
        """
        Resolve a page reference to an actual URL from urls.yaml.
        Uses exact key match - pass the exact key name from urls.yaml.

        Args:
            page_ref: Exact key from urls.yaml like "swagger_page", "saucedemo.base_url", etc.

        Returns:
            Resolved URL or None
        """
        urls = getattr(builtins, "URLS", {})

        # 1. Try EXACT top-level key match (e.g., "swagger_page")
        if page_ref in urls:
            value = urls[page_ref]
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value

        # 2. Try nested key with dot notation (e.g., "saucedemo.base_url")
        if "." in page_ref:
            parts = page_ref.split(".", 1)
            if len(parts) == 2 and parts[0] in urls:
                nested = urls[parts[0]]
                if isinstance(nested, dict) and parts[1] in nested:
                    value = nested[parts[1]]
                    if isinstance(value, str) and value.startswith(
                        ("http://", "https://")
                    ):
                        return value

        # 3. Try exact key inside nested dicts (e.g., "base_url" in saucedemo)
        for site_name, site_urls in urls.items():
            if isinstance(site_urls, dict) and page_ref in site_urls:
                value = site_urls[page_ref]
                if isinstance(value, str) and value.startswith(("http://", "https://")):
                    return value

        # 4. If it's already a URL, return as-is
        if page_ref.startswith(("http://", "https://")):
            return page_ref

        return None

    # =========================================================================
    # NETWORK INTERCEPTION METHODS
    # =========================================================================

    def start_network_capture(self, url_pattern: str = "**/*"):
        """
        Start capturing network requests and responses.

        Args:
            url_pattern: Glob pattern to filter which URLs to capture.
                        Examples: "**/api/*", "https://api.example.com/*"
        """
        if self._network_listener_active:
            return  # Already active

        self._captured_requests = []
        self._captured_responses = []
        self._network_listener_active = True

        def handle_request(request):
            """Capture request details."""
            try:
                # Handle post_data - it might be binary
                post_data = None
                try:
                    post_data = request.post_data
                except:
                    post_data = "<binary data>"

                request_data = {
                    "url": request.url,
                    "method": request.method,
                    "headers": dict(request.headers),
                    "post_data": post_data,
                    "resource_type": request.resource_type,
                    "timestamp": time.time(),
                }
                self._captured_requests.append(request_data)
            except Exception as e:
                print(f"Error capturing request: {e}")

        def handle_response(response):
            """Capture response details."""
            try:
                # Try to get response body (may fail for some responses)
                body = None
                try:
                    body = response.text()
                except:
                    try:
                        body = response.body().decode("utf-8", errors="ignore")
                    except:
                        body = "<binary or unavailable>"

                response_data = {
                    "url": response.url,
                    "status": response.status,
                    "status_text": response.status_text,
                    "headers": dict(response.headers),
                    "body": body,
                    "timestamp": time.time(),
                }
                self._captured_responses.append(response_data)
            except Exception as e:
                print(f"Error capturing response: {e}")

        # Attach event listeners
        self.page.on("request", handle_request)
        self.page.on("response", handle_response)

    def stop_network_capture(self):
        """Stop capturing network requests."""
        self._network_listener_active = False
        # Note: Playwright doesn't have a simple way to remove listeners,
        # but we can stop storing by checking the flag

    def clear_captured_network(self):
        """Clear all captured network data."""
        self._captured_requests = []
        self._captured_responses = []

    def get_captured_requests(
        self, url_pattern: str = None, method: str = None
    ) -> list:
        """
        Get captured requests, optionally filtered.

        Args:
            url_pattern: Glob pattern to filter URLs (e.g., "**/api/users*")
            method: HTTP method to filter (e.g., "GET", "POST")

        Returns:
            List of matching request dictionaries
        """
        results = self._captured_requests

        if url_pattern:
            results = [r for r in results if fnmatch.fnmatch(r["url"], url_pattern)]

        if method:
            results = [r for r in results if r["method"].upper() == method.upper()]

        return results

    def get_captured_responses(
        self, url_pattern: str = None, status: int = None
    ) -> list:
        """
        Get captured responses, optionally filtered.

        Args:
            url_pattern: Glob pattern to filter URLs
            status: HTTP status code to filter

        Returns:
            List of matching response dictionaries
        """
        results = self._captured_responses

        if url_pattern:
            results = [r for r in results if fnmatch.fnmatch(r["url"], url_pattern)]

        if status:
            results = [r for r in results if r["status"] == status]

        return results

    def validate_api_called(
        self,
        url_pattern: str,
        method: str = None,
        expected_status: int = None,
        expected_body_contains: str = None,
        min_calls: int = 1,
    ) -> dict:
        """
        Validate that an API was called with expected parameters.

        Args:
            url_pattern: Glob pattern for the API URL (e.g., "**/api/login*")
            method: Expected HTTP method (optional)
            expected_status: Expected response status code (optional)
            expected_body_contains: Text that should be in response body (optional)
            min_calls: Minimum number of matching calls expected (default: 1)

        Returns:
            dict with validation results:
            {
                "success": True/False,
                "matching_calls": [...],
                "total_matches": int,
                "error": "error message if failed"
            }
        """
        result = {
            "success": False,
            "matching_calls": [],
            "total_matches": 0,
            "error": None,
        }

        try:
            # Find matching requests
            matching_requests = self.get_captured_requests(url_pattern, method)

            if len(matching_requests) < min_calls:
                result["error"] = (
                    f"Expected at least {min_calls} calls to '{url_pattern}', "
                    f"but found {len(matching_requests)}"
                )
                return result

            # Find matching responses
            for req in matching_requests:
                # Find corresponding response
                matching_responses = [
                    r
                    for r in self._captured_responses
                    if r["url"] == req["url"] and r["timestamp"] >= req["timestamp"]
                ]

                if not matching_responses:
                    continue

                resp = matching_responses[0]  # Get first matching response

                call_data = {
                    "request": req,
                    "response": resp,
                    "status_match": True,
                    "body_match": True,
                }

                # Check status
                if expected_status and resp["status"] != expected_status:
                    call_data["status_match"] = False
                    call_data["status_error"] = (
                        f"Expected status {expected_status}, got {resp['status']}"
                    )

                # Check body contains
                if expected_body_contains:
                    body = resp.get("body", "")
                    if expected_body_contains not in str(body):
                        call_data["body_match"] = False
                        call_data["body_error"] = (
                            f"Expected body to contain '{expected_body_contains}'"
                        )

                result["matching_calls"].append(call_data)

            result["total_matches"] = len(result["matching_calls"])

            # Check if all validations passed
            if result["total_matches"] >= min_calls:
                all_passed = all(
                    c.get("status_match", True) and c.get("body_match", True)
                    for c in result["matching_calls"]
                )
                if all_passed:
                    result["success"] = True
                else:
                    failed_calls = [
                        c
                        for c in result["matching_calls"]
                        if not c.get("status_match") or not c.get("body_match")
                    ]
                    errors = []
                    for fc in failed_calls:
                        if not fc.get("status_match"):
                            errors.append(fc.get("status_error", "Status mismatch"))
                        if not fc.get("body_match"):
                            errors.append(fc.get("body_error", "Body mismatch"))
                    result["error"] = "; ".join(errors)
            else:
                result["error"] = (
                    f"Expected at least {min_calls} matching calls, "
                    f"found {result['total_matches']}"
                )

        except Exception as e:
            result["error"] = str(e)

        return result

    def _execute_network_action(self, action: dict, logger: IntentLogger) -> bool:
        """
        Execute a network-related action (intercept, validate_api).

        Args:
            action: Action dict with network operation
            logger: Logger for output

        Returns:
            True if action succeeded, False otherwise
        """
        action_type = action.get("action", "")

        if action_type == "start_capture":
            # Start network capture
            url_pattern = action.get("url_pattern", "**/*")
            self.start_network_capture(url_pattern)
            logger.log(f"[NETWORK] Started capturing network traffic: {url_pattern}")
            return True

        elif action_type == "stop_capture":
            # Stop network capture
            self.stop_network_capture()
            logger.log("[NETWORK] Stopped network capture")
            return True

        elif action_type == "validate_api":
            # Validate API call
            url_pattern = action.get("url_pattern", "")
            method = action.get("method")
            expected_status = action.get("expected_status")
            expected_body = action.get("expected_body_contains")
            min_calls = action.get("min_calls", 1)

            result = self.validate_api_called(
                url_pattern=url_pattern,
                method=method,
                expected_status=expected_status,
                expected_body_contains=expected_body,
                min_calls=min_calls,
            )

            if result["success"]:
                logger.log(
                    f"[NETWORK] API validation passed: {url_pattern} "
                    f"({result['total_matches']} matching calls)"
                )
                return True
            else:
                logger.log(f"[NETWORK] API validation failed: {result['error']}")
                return False

        elif action_type == "clear_capture":
            # Clear captured data
            self.clear_captured_network()
            logger.log("[NETWORK] Cleared captured network data")
            return True

        else:
            logger.log(f"[NETWORK] Unknown network action: {action_type}")
            return False
