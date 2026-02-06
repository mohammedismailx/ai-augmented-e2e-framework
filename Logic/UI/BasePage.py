from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from Logic.API.api_wrapper import APIWrapper
import builtins


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
