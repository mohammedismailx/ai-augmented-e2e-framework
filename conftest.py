import pytest
import os
import yaml
import sys
import builtins
from dotenv import load_dotenv

# Add project root to path FIRST before importing from Utils
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.append(PROJECT_ROOT)

# Import centralized logger
from Utils.logger import FrameworkLogger as log

# Optional playwright import (not needed for API tests)
try:
    from playwright.sync_api import sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    log.warning("Playwright not installed. UI tests will not be available.")


# 1. Load configuration and environment FIRST
def _load_configuration_files():
    """
    Internal function to load configuration files into global variables.
    This ensures configuration is loaded only once and reused.
    """
    global PROJECT_ROOT

    log.section("CONFTEST: Loading Global Configuration")

    # Load environment variables
    env_path = os.path.join(PROJECT_ROOT, ".env")
    load_dotenv(env_path)
    log.ok("Environment variables loaded from .env")

    # Load Config
    config_path = os.path.join(PROJECT_ROOT, "Config", "config.yaml")
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    log.ok("Config loaded into global variable")

    # Load URLs (now in Test_Data)
    urls_path = os.path.join(PROJECT_ROOT, "Test_Data", "urls.yaml")
    if not os.path.exists(urls_path):
        urls_path = os.path.join(PROJECT_ROOT, "Config", "urls.yaml")

    with open(urls_path, "r") as f:
        urls_data = yaml.safe_load(f)
    log.ok(f"URLs loaded from {urls_path}")

    # DATA
    data_path = os.path.join(PROJECT_ROOT, "Test_Data", "test_data.yaml")
    with open(data_path, "r") as f:
        test_data = yaml.safe_load(f)
    log.ok("Test Data loaded into global variable")

    # Store in builtins for global access
    builtins.CONFIG = config_data
    builtins.URLS = urls_data
    builtins.PROJECT_ROOT = PROJECT_ROOT
    builtins.TEST_DATA = test_data
    log.ok("Configuration populated to builtins (CONFIG, URLS, PROJECT_ROOT)")


# Execute loading before importing custom modules
_load_configuration_files()

# 2. Now safe to import custom modules that might use globals/env
from Utils.db_connector import DBConnector

# Optional UI imports (not needed for API tests)
try:
    from Logic.UI.Login.LoginPage import LoginPage

    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False
    LoginPage = None
    log.warning("UI modules not available. UI tests will not be available.")


@pytest.fixture(scope="session")
def db_session():
    """
    Session-scoped fixture to handle DB connection lifecycle.
    """
    log.section("FIXTURE: Initializing DB Connection")

    db = DBConnector()
    db.connect()

    yield db

    log.section("FIXTURE: Closing DB Connection")
    db.close()


# ==================== UI FIXTURES (Playwright) ====================
# These fixtures are only available when Playwright is installed

if PLAYWRIGHT_AVAILABLE:

    @pytest.fixture(scope="session")
    def playwright_instance():
        """Initialize Playwright"""
        with sync_playwright() as p:
            yield p

    @pytest.fixture(scope="session")
    def browser_instance(playwright_instance):
        """
        Initialize Browser
        """
        headless = builtins.CONFIG.get("headless", False)
        slow_mo = builtins.CONFIG.get("slow_mo", 0)

        log.section("FIXTURE: Initializing Browser")

        browser = playwright_instance.chromium.launch(
            headless=headless, slow_mo=slow_mo
        )
        yield browser

        log.section("FIXTURE: Closing Browser")
        browser.close()

    @pytest.fixture(scope="session")
    def auth_state(browser_instance):
        """
        Perform login once and save storage state.
        """
        storage_state_path = os.path.join(PROJECT_ROOT, "saved_states", "state.json")
        os.makedirs(os.path.dirname(storage_state_path), exist_ok=True)

        if not os.path.exists(storage_state_path):
            log.info("Creating authentication state...")

            context = browser_instance.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            login_page = LoginPage(page)
            login_page.navigate(builtins.URLS["saucedemo"]["base_url"])

            # Load credentials from environment
            username = os.getenv("SAUCE_USERNAME")
            password = os.getenv("SAUCE_PASSWORD")

            login_page.login(username, password)

            context.storage_state(path=storage_state_path)
            log.ok(f"Storage state saved to: {storage_state_path}")

            page.close()
            context.close()
        else:
            log.ok(f"Storage state already exists: {storage_state_path}")

        return storage_state_path

    @pytest.fixture(scope="module")
    def page(browser_instance, auth_state):
        """
        Provide a fresh page with authentication state for each module (test file).
        """
        context = browser_instance.new_context(
            storage_state=auth_state, viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        yield page

        page.close()
        context.close()


# ==================== API CONTEXT FIXTURES ====================


@pytest.fixture(scope="session")
def api_context():
    """
    Session-scoped fixture to initialize RAG with embedded swagger.

    This fixture:
    1. Creates a RAG instance
    2. Embeds swagger.json endpoints grouped by resource
    3. Stores RAG instance in builtins for global access
    4. Returns the RAG instance for use in tests

    Usage in tests:
        def test_api_intent(api_context):
            rag = api_context
            # Use rag.retrieve_endpoints_by_intent(...)
    """
    from Libs.RAG import Rag

    log.section("FIXTURE: Initializing API Context (RAG + Swagger Embedding)")

    # Initialize RAG
    rag = Rag()

    # Embed swagger
    swagger_path = os.path.join(PROJECT_ROOT, "swagger.json")

    if os.path.exists(swagger_path):
        log.ok(f"Found swagger file: {swagger_path}")
        rag.embed_swagger_by_resource(swagger_path, collection_name="api_endpoints")
        log.ok("Swagger endpoints embedded successfully")
    else:
        log.warning(f"Swagger file not found: {swagger_path}")
        log.warning("API intent execution will not work without swagger embedding")

    # Store in builtins for global access
    builtins.RAG_INSTANCE = rag
    log.ok("RAG instance stored in builtins.RAG_INSTANCE")

    yield rag

    log.section("FIXTURE: API Context cleanup complete")


@pytest.fixture(scope="session")
def api_wrapper(api_context):
    """
    Session-scoped fixture for APIWrapper with RAG context.

    This fixture depends on api_context to ensure swagger is embedded first.

    Usage in tests:
        def test_api_intent(api_wrapper):
            result = api_wrapper.execute_by_intent(
                intent="get all books",
                base_url="https://fakerestapi.azurewebsites.net"
            )
    """
    from Logic.API.api_wrapper import APIWrapper

    log.section("FIXTURE: Initializing API Wrapper")

    wrapper = APIWrapper()
    log.ok("API Wrapper initialized")

    yield wrapper

    log.section("FIXTURE: API Wrapper cleanup complete")
