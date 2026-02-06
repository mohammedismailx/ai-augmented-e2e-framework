import pytest
import os
import yaml
import sys
import builtins
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.append(PROJECT_ROOT)


# 1. Load configuration and environment FIRST
def _load_configuration_files():
    """
    Internal function to load configuration files into global variables.
    This ensures configuration is loaded only once and reused.
    """
    global PROJECT_ROOT

    print("\n" + "=" * 80)
    print("CONFTEST: Loading Global Configuration")
    print("=" * 80)

    # Load environment variables
    env_path = os.path.join(PROJECT_ROOT, ".env")
    load_dotenv(env_path)
    print("✓ Environment variables loaded from .env")

    # Load Config
    config_path = os.path.join(PROJECT_ROOT, "Config", "config.yaml")
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    print("✓ Config loaded into global variable")

    # Load URLs (now in Test_Data)
    urls_path = os.path.join(PROJECT_ROOT, "Test_Data", "urls.yaml")
    if not os.path.exists(urls_path):
        urls_path = os.path.join(PROJECT_ROOT, "Config", "urls.yaml")

    with open(urls_path, "r") as f:
        urls_data = yaml.safe_load(f)
    print(f"✓ URLs loaded from {urls_path}")

    # DATA
    data_path = os.path.join(PROJECT_ROOT, "Test_Data", "test_data.yaml")
    with open(data_path, "r") as f:
        test_data = yaml.safe_load(f)
    print("✓ Test Data loaded into global variable")

    # Store in builtins for global access
    builtins.CONFIG = config_data
    builtins.URLS = urls_data
    builtins.PROJECT_ROOT = PROJECT_ROOT
    builtins.TEST_DATA = test_data
    print("✓ Configuration populated to builtins (CONFIG, URLS, PROJECT_ROOT)")


# Execute loading before importing custom modules
_load_configuration_files()

# 2. Now safe to import custom modules that might use globals/env
from Utils.db_connector import DBConnector
from Logic.UI.Login.LoginPage import LoginPage


@pytest.fixture(scope="session")
def db_session():
    """
    Session-scoped fixture to handle DB connection lifecycle.
    """
    print("\n" + "=" * 80)
    print("FIXTURE: Initializing DB Connection")
    print("=" * 80)

    db = DBConnector()
    db.connect()

    yield db

    print("\n" + "=" * 80)
    print("FIXTURE: Closing DB Connection")
    print("=" * 80)
    db.close()


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

    print("\n" + "=" * 80)
    print("FIXTURE: Initializing Browser")
    print("=" * 80)

    browser = playwright_instance.chromium.launch(headless=headless, slow_mo=slow_mo)
    yield browser

    print("\n" + "=" * 80)
    print("FIXTURE: Closing Browser")
    print("=" * 80)
    browser.close()


@pytest.fixture(scope="session")
def auth_state(browser_instance):
    """
    Perform login once and save storage state.
    """
    storage_state_path = os.path.join(PROJECT_ROOT, "saved_states", "state.json")
    os.makedirs(os.path.dirname(storage_state_path), exist_ok=True)

    if not os.path.exists(storage_state_path):
        print("Creating authentication state...")

        context = browser_instance.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        login_page = LoginPage(page)
        login_page.navigate(builtins.URLS["saucedemo"]["base_url"])

        # Load credentials from environment
        username = os.getenv("SAUCE_USERNAME")
        password = os.getenv("SAUCE_PASSWORD")

        login_page.login(username, password)

        context.storage_state(path=storage_state_path)
        print(f"✓ Storage state saved to: {storage_state_path}")

        page.close()
        context.close()
    else:
        print(f"✓ Storage state already exists: {storage_state_path}")

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
