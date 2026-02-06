import pytest
import os
import yaml
import sys
import builtins
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Add project root to path FIRST before importing from Utils
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.append(PROJECT_ROOT)

# Import centralized logger
from Utils.logger import FrameworkLogger as log

# Optional playwright import (not needed for API tests)


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
from Logic.UI.Login.LoginPage import LoginPage


# ==================== TEST INFO EXTRACTION FIXTURE ====================


@pytest.fixture(autouse=True)
def extract_test_markers(request):
    """
    Auto-use fixture that extracts @pytest.mark.id and @pytest.mark.title
    from the current test and stores them in builtins.CURRENT_TEST_INFO.

    This allows the IntentLogger to automatically read test ID and title
    without needing to pass them as parameters.

    Usage in tests:
        @pytest.mark.id("API-001")
        @pytest.mark.title("Get Book by ID")
        def test_example(self, api_wrapper):
            # Logger will automatically use "API-001" and "Get Book by ID"
            pass
    """
    # Extract markers from the test
    test_id = "UNKNOWN"
    test_title = ""

    # Get the 'id' marker
    id_marker = request.node.get_closest_marker("id")
    if id_marker and id_marker.args:
        test_id = id_marker.args[0]

    # Get the 'title' marker
    title_marker = request.node.get_closest_marker("title")
    if title_marker and title_marker.args:
        test_title = title_marker.args[0]

    # Store in builtins for global access by IntentLogger
    builtins.CURRENT_TEST_INFO = {
        "id": test_id,
        "title": test_title,
        "node_id": request.node.nodeid,
        "name": request.node.name,
    }

    yield

    # Cleanup after test
    builtins.CURRENT_TEST_INFO = {}


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

    browser = playwright_instance.chromium.launch(headless=headless, slow_mo=slow_mo)
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

        context = browser_instance.new_context(viewport={"width": 1920, "height": 1080})
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
    2. Embeds swagger.json endpoints grouped by resource (if REFRESH_API_SCHEMA=true)
    3. Stores RAG instance in builtins for global access
    4. Returns the RAG instance for use in tests

    Environment Variables:
        REFRESH_API_SCHEMA: If "true", re-embeds swagger even if collection exists

    Usage in tests:
        def test_api_intent(api_context):
            rag = api_context
            # Use rag.retrieve_endpoints_by_intent(...)
    """
    from Libs.RAG import Rag

    log.section("FIXTURE: Initializing API Context (RAG + Swagger Embedding)")

    # Initialize RAG
    rag = Rag()

    # Check if we need to refresh schema
    refresh_schema = os.getenv("REFRESH_API_SCHEMA", "false").lower() == "true"

    # Embed swagger
    swagger_path = os.path.join(PROJECT_ROOT, "swagger.json")

    if os.path.exists(swagger_path):
        log.ok(f"Found swagger file: {swagger_path}")

        if refresh_schema:
            log.info("REFRESH_API_SCHEMA=true: Forcing swagger re-embedding")
            rag.embed_swagger_by_resource(
                swagger_path, collection_name="api_endpoints", force_refresh=True
            )
            log.ok("Swagger endpoints embedded successfully")
        else:
            # Check if collection already exists with data
            try:
                collection = rag.client.get_collection("api_endpoints")
                if collection.count() > 0:
                    log.ok(
                        f"Using cached API embeddings ({collection.count()} documents)"
                    )
                else:
                    log.info("Collection empty, embedding swagger...")
                    rag.embed_swagger_by_resource(
                        swagger_path, collection_name="api_endpoints"
                    )
                    log.ok("Swagger endpoints embedded successfully")
            except Exception:
                log.info("Collection not found, embedding swagger...")
                rag.embed_swagger_by_resource(
                    swagger_path, collection_name="api_endpoints"
                )
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
    Session-scoped fixture for APIWrapper with RAG context and base URL pre-configured.

    This fixture depends on api_context to ensure swagger is embedded first.
    The wrapper is configured with base_url and rag_instance so tests only need to provide intent.

    Usage in tests:
        def test_api_intent(api_wrapper):
            result = api_wrapper.execute_by_intent(intent="get all books")
    """
    from Logic.API.api_wrapper import APIWrapper

    log.section("FIXTURE: Initializing API Wrapper")

    # Create wrapper with base_url and rag_instance pre-configured
    wrapper = APIWrapper(
        base_url="https://fakerestapi.azurewebsites.net", rag_instance=api_context
    )
    log.ok(f"API Wrapper initialized with base_url: {wrapper.base_url}")

    yield wrapper

    log.section("FIXTURE: API Wrapper cleanup complete")


# ==================== DB CONTEXT FIXTURES ====================


@pytest.fixture(scope="session")
def db_context():
    """
    Session-scoped fixture to initialize RAG with embedded database schema.

    This fixture:
    1. Creates a RAG instance for DB context
    2. Connects to the database
    3. Embeds table schemas grouped by foreign key relationships
    4. Stores RAG instance in builtins for global access
    5. Returns DBConnector instance for use in tests

    Environment Variables:
        REFRESH_DB_SCHEMA: If "true", re-embeds schema even if collection exists

    Usage in tests:
        def test_db_intent(db_context):
            result = db_context.execute_by_intent(
                intent="get all posts by user with id 5"
            )
            assert result["success"] is True
    """
    from Libs.RAG import Rag

    log.section("FIXTURE: Initializing DB Context (RAG + Schema Embedding)")

    # Initialize RAG for DB context
    rag = Rag()

    # Initialize DB connection
    db = DBConnector()
    db.connect()

    # Check if we need to refresh schema
    refresh_schema = os.getenv("REFRESH_DB_SCHEMA", "false").lower() == "true"

    if refresh_schema:
        log.info("REFRESH_DB_SCHEMA=true: Forcing schema re-embedding")

    # Embed database schema
    try:
        log.info("Fetching database schema...")

        # Get all tables
        tables = db.get_all_tables()
        log.ok(f"Found {len(tables)} tables: {tables}")

        if tables:
            # Build schema data for RAG embedding
            schema_data = {}

            for table_name in tables:
                log.info(f"Fetching schema for table: {table_name}")

                # Get table columns
                columns = db.get_table_schema(table_name)

                # Get foreign keys
                foreign_keys = db.get_foreign_keys(table_name)

                schema_data[table_name] = {
                    "columns": columns or [],
                    "foreign_keys": foreign_keys or [],
                }

            # Embed schema into RAG
            rag.embed_db_schema(
                schema_data=schema_data,
                collection_name="db_context",
                force_refresh=refresh_schema,
            )
            log.ok("Database schema embedded successfully")
        else:
            log.warning("No tables found in database")
            log.warning("DB intent execution may not work without schema embedding")

    except Exception as e:
        log.warning(f"Failed to embed database schema: {e}")
        log.warning("DB intent execution may not work properly")

    # Store in builtins for global access
    builtins.RAG_DB_INSTANCE = rag
    log.ok("RAG DB instance stored in builtins.RAG_DB_INSTANCE")

    # Set the RAG instance on the db connector
    db._rag_instance = rag

    yield db

    log.section("FIXTURE: Closing DB Connection")
    db.close()
    log.section("FIXTURE: DB Context cleanup complete")
