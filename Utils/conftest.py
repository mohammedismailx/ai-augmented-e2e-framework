import pytest
import os
import yaml
import sys
from playwright.sync_api import sync_playwright
from Utils import globals

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(scope="session", autouse=True)
def load_global_config():
    """
    Load configuration and URLs into global variables at the start of the session.
    """
    print("\n" + "=" * 80)
    print("CONFTEST: Loading Global Configuration")
    print("=" * 80)

    # Load Config
    config_path = os.path.join(os.path.dirname(__file__), "..", "Config", "config.yaml")
    with open(config_path, "r") as f:
        globals.CONFIG = yaml.safe_load(f)
    print("✓ Config loaded into globals.CONFIG")

    # Load URLs
    urls_path = os.path.join(os.path.dirname(__file__), "..", "Config", "urls.yaml")
    with open(urls_path, "r") as f:
        globals.URLS = yaml.safe_load(f)
    print("✓ URLs loaded into globals.URLS")


@pytest.fixture(scope="session")
def config(load_global_config):
    """Return the global configuration"""
    return globals.CONFIG


@pytest.fixture(scope="session")
def urls(load_global_config):
    """Return the global URLs"""
    return globals.URLS


@pytest.fixture(scope="session")
def playwright_instance():
    """Initialize Playwright"""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser_instance(playwright_instance, config):
    """Initialize Browser"""
    headless = config.get("headless", False)
    slow_mo = config.get("slow_mo", 0)

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
def auth_state(browser_instance, urls):
    """
    Perform login once and save storage state.
    Returns path to state.json.
    """
    storage_state_path = os.path.join(
        os.path.dirname(__file__), "..", "LoginState", "state.json"
    )
    os.makedirs(os.path.dirname(storage_state_path), exist_ok=True)

    if not os.path.exists(storage_state_path):
        print("Creating authentication state...")
        # Import LoginPage locally to avoid circular dependency
        from Logic.UI.Login.LoginPage import LoginPage

        context = browser_instance.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # LoginPage uses globals.CONFIG internally
        login_page = LoginPage(page)
        login_page.navigate(urls["saucedemo"]["base_url"])
        login_page.login("standard_user", "secret_sauce")

        context.storage_state(path=storage_state_path)
        print(f"✓ Storage state saved to: {storage_state_path}")

        page.close()
        context.close()
    else:
        print(f"✓ Storage state already exists: {storage_state_path}")

    return storage_state_path


@pytest.fixture(scope="function")
def page(browser_instance, auth_state):
    """
    Provide a fresh page with authentication state for each test.
    """
    context = browser_instance.new_context(
        storage_state=auth_state, viewport={"width": 1920, "height": 1080}
    )
    page = context.new_page()

    yield page

    page.close()
    context.close()
