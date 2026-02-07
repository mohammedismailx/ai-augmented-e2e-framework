"""
AI-Augmented Intent Test Runner Dashboard
==========================================
A single-file Flask application for managing and executing intent-based tests
across UI, API, and DB modules.

Features:
- Module selection (UI, API, DB)
- Add/Edit/Delete intents
- Run individual or all tests
- Visual pass/fail status (green/red highlighting)
- AI analysis panel with detailed results
- Approve & Generate test files

Run with:
    python intent_test_runner.py

Access at:
    http://localhost:5000

Author: Framework Team
Version: 1.0.0
"""

import os
import sys
import json
import threading
import time
import uuid
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

# Pre-load onnxruntime before any other module that might use it (like chromadb)
# This prevents binary incompatibility issues
try:
    import onnxruntime
except ImportError:
    print("[WARNING] onnxruntime not installed. Some features may not work.")
except Exception as e:
    print(f"[WARNING] onnxruntime load issue: {e}")

from flask import Flask, request, jsonify

# ============================================================================
# PROJECT SETUP - Add project root to path and load configuration
# ============================================================================

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Load configuration files before importing framework modules
import yaml
import builtins
from dotenv import load_dotenv


def load_configuration():
    """Load configuration files into builtins for global access."""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    load_dotenv(env_path)

    # Load Config
    config_path = os.path.join(PROJECT_ROOT, "Config", "config.yaml")
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    # Load URLs
    urls_path = os.path.join(PROJECT_ROOT, "Test_Data", "urls.yaml")
    if not os.path.exists(urls_path):
        urls_path = os.path.join(PROJECT_ROOT, "Config", "urls.yaml")
    with open(urls_path, "r") as f:
        urls_data = yaml.safe_load(f)

    # Load Test Data
    data_path = os.path.join(PROJECT_ROOT, "Test_Data", "test_data.yaml")
    with open(data_path, "r") as f:
        test_data = yaml.safe_load(f)

    # Store in builtins
    builtins.CONFIG = config_data
    builtins.URLS = urls_data
    builtins.PROJECT_ROOT = PROJECT_ROOT
    builtins.TEST_DATA = test_data
    builtins.CURRENT_TEST_INFO = {"id": "RUNNER", "title": "Intent Test Runner"}


# Load configuration
load_configuration()

# ============================================================================
# FLASK APP SETUP
# ============================================================================

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ============================================================================
# DATA MODEL
# ============================================================================


@dataclass
class IntentTest:
    id: str
    module: str  # "ui", "api", "db"
    intent: str
    status: str  # "pending", "running", "passed", "failed"
    result: Optional[Dict] = None
    ai_analysis: str = ""
    execution_time: float = 0.0
    created_at: str = ""

    def to_dict(self):
        return asdict(self)


# In-memory storage for current session
session_data = {"intents": [], "current_module": "api"}

# Module configuration (dynamic, set from UI)
module_config = {
    "ui": {
        "base_url": builtins.URLS.get("saucedemo", {}).get(
            "base_url", "https://www.saucedemo.com"
        )
    },
    "api": {
        "base_url": "https://fakerestapi.azurewebsites.net",
        "swagger_path": os.path.join(PROJECT_ROOT, "swagger.json"),
        "swagger_content": None,  # Will be set when uploaded
    },
    "db": {
        "db_type": "mysql",  # mysql, postgresql, sqlite
        "host": "127.0.0.1",
        "port": "3306",
        "database": "testdb",
        "username": "root",
        "password": "",
    },
}

# Global instances (lazy loaded)
_instances = {
    "api_wrapper": None,
    "db_context": None,
    "ui_context": None,
    "ui_page": None,
    "ui_page_context": None,
    "browser": None,
    "playwright": None,
}

# ============================================================================
# LAZY LOADERS FOR FRAMEWORK COMPONENTS
# ============================================================================


def reset_api_wrapper():
    """Reset API wrapper to pick up new configuration."""
    _instances["api_wrapper"] = None


def reset_db_context():
    """Reset DB context to pick up new configuration."""
    if _instances["db_context"]:
        try:
            _instances["db_context"].close()
        except:
            pass
    _instances["db_context"] = None


def reset_ui_page():
    """Reset UI page for a fresh state between tests.
    Creates a new page/context but keeps the browser open.
    """
    if _instances["browser"] is not None:
        try:
            # Close old context if exists
            if _instances["ui_page_context"]:
                try:
                    _instances["ui_page_context"].close()
                except:
                    pass
                _instances["ui_page_context"] = None

            _instances["ui_page"] = None

            # Create new context and page
            from Logic.UI.BasePage import BasePage

            browser = _instances["browser"]
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()
            base_page = BasePage(page)
            _instances["ui_page"] = base_page
            _instances["ui_page_context"] = context
            print("[RESET] UI Page reset for new test")
        except Exception as e:
            print(f"[WARNING] Failed to reset UI page: {e}")
            # Force full re-initialization
            _instances["ui_page"] = None
            _instances["ui_page_context"] = None
            _instances["browser"] = None
            _instances["playwright"] = None


def _is_ui_page_valid():
    """Check if the current UI page is still valid and usable."""
    if _instances["ui_page"] is None:
        return False
    if _instances["browser"] is None:
        return False

    try:
        # Try to access the page to see if it's still connected
        page = _instances["ui_page"].page
        # Simple check - try to get the URL (will fail if page is closed)
        _ = page.url
        return True
    except Exception:
        return False


def get_api_wrapper(force_refresh=False):
    """Lazy load API wrapper with RAG context."""
    if _instances["api_wrapper"] is None or force_refresh:
        from Libs.RAG import Rag
        from Logic.API.api_wrapper import APIWrapper

        print("[INIT] Initializing API Context...")

        # Initialize RAG and embed swagger
        rag = Rag()

        # Use configured swagger path or content
        swagger_path = module_config["api"].get(
            "swagger_path", os.path.join(PROJECT_ROOT, "swagger.json")
        )

        if os.path.exists(swagger_path):
            # Force refresh if configuration changed
            if force_refresh:
                try:
                    rag.client.delete_collection("api_endpoints")
                except:
                    pass
                rag.embed_swagger_by_resource(
                    swagger_path, collection_name="api_endpoints"
                )
            else:
                try:
                    collection = rag.client.get_collection("api_endpoints")
                    if collection.count() == 0:
                        rag.embed_swagger_by_resource(
                            swagger_path, collection_name="api_endpoints"
                        )
                except Exception:
                    rag.embed_swagger_by_resource(
                        swagger_path, collection_name="api_endpoints"
                    )

        builtins.RAG_INSTANCE = rag

        # Create API wrapper with configured base URL
        wrapper = APIWrapper(
            base_url=module_config["api"].get(
                "base_url", "https://fakerestapi.azurewebsites.net"
            ),
            rag_instance=rag,
        )
        _instances["api_wrapper"] = wrapper
        print(f"[OK] API Wrapper initialized with base_url: {wrapper.base_url}")

    return _instances["api_wrapper"]


def get_db_context(force_refresh=False):
    """Lazy load DB connector with RAG context."""
    if _instances["db_context"] is None or force_refresh:
        from Libs.RAG import Rag
        from Utils.db_connector import DBConnector

        print("[INIT] Initializing DB Context...")

        # Initialize RAG
        rag = Rag()

        # Get DB configuration
        db_config = module_config["db"]

        # Initialize DB connection with configured parameters
        db = DBConnector(
            host=db_config.get("host", "127.0.0.1"),
            port=db_config.get("port", "3306"),
            user=db_config.get("username", "root"),
            password=db_config.get("password", ""),
            database=db_config.get("database", "testdb"),
        )
        db.connect()

        # Embed schema if needed
        try:
            # Force refresh if configuration changed
            if force_refresh:
                try:
                    rag.client.delete_collection("db_context")
                except:
                    pass

            tables = db.get_all_tables()
            if tables:
                schema_data = {}
                for table_name in tables:
                    columns = db.get_table_schema(table_name)
                    foreign_keys = db.get_foreign_keys(table_name)
                    schema_data[table_name] = {
                        "columns": columns or [],
                        "foreign_keys": foreign_keys or [],
                    }

                try:
                    collection = rag.client.get_collection("db_context")
                    if collection.count() == 0:
                        rag.embed_db_schema(schema_data, collection_name="db_context")
                except Exception:
                    rag.embed_db_schema(schema_data, collection_name="db_context")
        except Exception as e:
            print(f"[WARNING] Failed to embed DB schema: {e}")

        builtins.RAG_DB_INSTANCE = rag
        db._rag_instance = rag
        _instances["db_context"] = db
        print("[OK] DB Context initialized")

    return _instances["db_context"]


def get_ui_context():
    """Lazy load UI context (RAG for learning)."""
    if _instances["ui_context"] is None:
        from Libs.RAG import Rag

        print("[INIT] Initializing UI Context...")

        rag = Rag()

        try:
            collection = rag.chroma_client.get_or_create_collection(
                name="ui_learning", embedding_function=rag.embedding_fn
            )
            rag._ui_learning_collection = collection
        except Exception as e:
            print(f"[WARNING] Failed to initialize UI learning: {e}")
            rag._ui_learning_collection = None

        builtins.RAG_UI_INSTANCE = rag
        _instances["ui_context"] = rag
        print("[OK] UI Context initialized")

    return _instances["ui_context"]


def get_ui_page():
    """Lazy load Playwright browser and UI page.
    Also validates that existing page is still usable.
    """
    # Check if we need to reinitialize (page is None or closed)
    if _instances["ui_page"] is None or not _is_ui_page_valid():
        from playwright.sync_api import sync_playwright
        from Logic.UI.BasePage import BasePage

        print("[INIT] Initializing UI Page (Playwright)...")

        # Ensure UI context is loaded
        get_ui_context()

        # Clean up any existing playwright/browser first
        if _instances["playwright"]:
            try:
                if _instances["browser"]:
                    _instances["browser"].close()
                _instances["playwright"].stop()
            except:
                pass
            _instances["playwright"] = None
            _instances["browser"] = None
            _instances["ui_page"] = None
            _instances["ui_page_context"] = None

        # Initialize Playwright
        playwright = sync_playwright().start()
        _instances["playwright"] = playwright

        # Launch browser
        headless = builtins.CONFIG.get("headless", False)
        slow_mo = builtins.CONFIG.get("slow_mo", 0)
        browser = playwright.chromium.launch(headless=headless, slow_mo=slow_mo)
        _instances["browser"] = browser

        # Create page
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Create BasePage
        base_page = BasePage(page)
        _instances["ui_page"] = base_page
        _instances["ui_page_context"] = context
        print("[OK] UI Page initialized")

    return _instances["ui_page"]

    return _instances["ui_page"]


def cleanup_instances():
    """Cleanup all instances on shutdown."""
    if _instances["ui_page_context"]:
        try:
            _instances["ui_page_context"].close()
        except:
            pass

    if _instances["browser"]:
        try:
            _instances["browser"].close()
        except:
            pass

    if _instances["playwright"]:
        try:
            _instances["playwright"].stop()
        except:
            pass

    if _instances["db_context"]:
        try:
            _instances["db_context"].close()
        except:
            pass


# ============================================================================
# INTENT EXECUTION
# ============================================================================


def execute_intent(intent_test: IntentTest) -> IntentTest:
    """Execute a single intent based on its module."""
    start_time = time.time()
    intent_test.status = "running"

    try:
        if intent_test.module == "api":
            wrapper = get_api_wrapper()
            result = wrapper.execute_by_intent(
                intent=intent_test.intent,
                assert_success=False,  # Don't raise, we capture result
            )

        elif intent_test.module == "db":
            db = get_db_context()
            result = db.execute_by_intent(
                intent=intent_test.intent, assert_success=False
            )

        elif intent_test.module == "ui":
            ui_page = get_ui_page()
            ui_context = get_ui_context()
            result = ui_page.execute_by_intent(
                intent=intent_test.intent, rag_context=ui_context, assert_success=False
            )
            # Navigate to blank page to clean state for next test (but keep browser open)
            try:
                ui_page.page.goto("about:blank")
            except:
                pass  # If page is closed, it will be recreated on next get_ui_page()
        else:
            result = {
                "success": False,
                "reason": f"Unknown module: {intent_test.module}",
            }

        # Update intent test with results
        intent_test.result = result
        intent_test.status = "passed" if result.get("success", False) else "failed"

        # Extract AI analysis
        if intent_test.module == "api":
            intent_test.ai_analysis = json.dumps(
                {
                    "curl_command": result.get("curl_command", "N/A"),
                    "status_code": result.get("status_code", "N/A"),
                    "response_body": result.get("response_body", {}),
                    "analysis": result.get("analysis", {}),
                    "error": result.get("error", None),
                },
                indent=2,
            )
        elif intent_test.module == "db":
            intent_test.ai_analysis = json.dumps(
                {
                    "query": result.get("query", "N/A"),
                    "data": result.get("data", []),
                    "reason": result.get("reason", ""),
                    "error": result.get("error", None),
                },
                indent=2,
            )
        elif intent_test.module == "ui":
            intent_test.ai_analysis = json.dumps(
                {"steps": result.get("steps", []), "error": result.get("error", None)},
                indent=2,
            )

    except Exception as e:
        intent_test.status = "failed"
        intent_test.result = {"success": False, "error": str(e)}
        intent_test.ai_analysis = json.dumps({"error": str(e)}, indent=2)

    intent_test.execution_time = round(time.time() - start_time, 2)
    return intent_test


# ============================================================================
# TEST FILE GENERATION
# ============================================================================


def generate_test_file(module: str, intents: List[IntentTest]) -> str:
    """Generate a pytest test file from approved intents."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if module == "ui":
        content = generate_ui_test_file(intents, timestamp)
        filename = f"test_generated_ui_{timestamp}.py"
        filepath = os.path.join(PROJECT_ROOT, "Tests", "UI", filename)
    elif module == "api":
        content = generate_api_test_file(intents, timestamp)
        filename = f"test_generated_api_{timestamp}.py"
        filepath = os.path.join(PROJECT_ROOT, "Tests", "API", filename)
    elif module == "db":
        content = generate_db_test_file(intents, timestamp)
        filename = f"test_generated_db_{timestamp}.py"
        filepath = os.path.join(PROJECT_ROOT, "Tests", "DB", filename)
    else:
        return None

    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Write file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def generate_ui_test_file(intents: List[IntentTest], timestamp: str) -> str:
    """Generate UI test file content."""
    tests = []
    for idx, intent in enumerate(intents, 1):
        test_id = f"GEN-UI-{idx:03d}"
        # Create a title from first line of intent
        title = intent.intent.strip().split("\n")[0][:50].replace('"', '\\"')

        # Escape the intent for triple quotes
        intent_text = intent.intent.strip()

        tests.append(
            f'''
    @pytest.mark.id("{test_id}")
    @pytest.mark.title("{title}")
    def test_intent_{idx}(self, ui_page, ui_context):
        """Auto-generated from Intent Test Runner on {timestamp}"""
        ui_page.execute_by_intent(
            intent="""
{indent_text(intent_text, 12)}
            """,
            rag_context=ui_context,
        )
'''
        )

    return f'''"""
Auto-Generated UI Test Suite
Generated: {timestamp}
Source: Intent Test Runner Dashboard
"""

import pytest
import sys
import builtins

sys.path.append(builtins.PROJECT_ROOT)


class TestGenerated_{timestamp}:
{"".join(tests)}
'''


def generate_api_test_file(intents: List[IntentTest], timestamp: str) -> str:
    """Generate API test file content."""
    tests = []
    for idx, intent in enumerate(intents, 1):
        test_id = f"GEN-API-{idx:03d}"
        title = intent.intent.strip()[:50].replace('"', '\\"')
        intent_text = intent.intent.strip().replace('"""', '\\"\\"\\"')

        tests.append(
            f'''
    @pytest.mark.api_intent
    @pytest.mark.id("{test_id}")
    @pytest.mark.title("{title}")
    def test_intent_{idx}(self, api_wrapper):
        """Auto-generated from Intent Test Runner on {timestamp}"""
        api_wrapper.execute_by_intent(intent="{intent_text}")
'''
        )

    return f'''"""
Auto-Generated API Test Suite
Generated: {timestamp}
Source: Intent Test Runner Dashboard
"""

import pytest


class TestGenerated_{timestamp}:
{"".join(tests)}
'''


def generate_db_test_file(intents: List[IntentTest], timestamp: str) -> str:
    """Generate DB test file content."""
    tests = []
    for idx, intent in enumerate(intents, 1):
        test_id = f"GEN-DB-{idx:03d}"
        title = intent.intent.strip()[:50].replace('"', '\\"')
        intent_text = intent.intent.strip().replace('"""', '\\"\\"\\"')

        tests.append(
            f'''
    @pytest.mark.db_intent
    @pytest.mark.id("{test_id}")
    @pytest.mark.title("{title}")
    def test_intent_{idx}(self, db_context):
        """Auto-generated from Intent Test Runner on {timestamp}"""
        db_context.execute_by_intent(intent="{intent_text}")
'''
        )

    return f'''"""
Auto-Generated Database Test Suite
Generated: {timestamp}
Source: Intent Test Runner Dashboard
"""

import pytest


class TestGenerated_{timestamp}:
{"".join(tests)}
'''


def indent_text(text: str, spaces: int) -> str:
    """Indent each line of text by specified spaces."""
    indent = " " * spaces
    return "\n".join(indent + line for line in text.split("\n"))


# ============================================================================
# HTML TEMPLATE
# ============================================================================


def get_html_template():
    """Load HTML template from file."""
    template_path = os.path.join(
        os.path.dirname(__file__), "Resources", "dashboard_template.html"
    )
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================================
# FLASK ROUTES
# ============================================================================


@app.route("/")
def index():
    """Render main dashboard."""
    return get_html_template()


@app.route("/api/run", methods=["POST"])
def run_intent():
    """Run a single intent test."""
    data = request.json

    # Create IntentTest from data
    intent_test = IntentTest(
        id=data.get("id", str(uuid.uuid4())),
        module=data.get("module", "api"),
        intent=data.get("intent", ""),
        status="pending",
        created_at=data.get("created_at", datetime.now().isoformat()),
    )

    # Execute
    result = execute_intent(intent_test)

    return jsonify(result.to_dict())


@app.route("/api/run-all", methods=["POST"])
def run_all():
    """Run all intents for a module."""
    data = request.json
    module = data.get("module", "api")
    intent_list = data.get("intents", [])

    results = []
    for intent_data in intent_list:
        intent_test = IntentTest(
            id=intent_data.get("id", str(uuid.uuid4())),
            module=module,
            intent=intent_data.get("intent", ""),
            status="pending",
            created_at=intent_data.get("created_at", datetime.now().isoformat()),
        )
        result = execute_intent(intent_test)
        results.append(result.to_dict())

    return jsonify({"results": results})


@app.route("/api/approve", methods=["POST"])
def approve():
    """Generate test file from approved intents."""
    data = request.json
    module = data.get("module", "api")
    intent_list = data.get("intents", [])

    # Convert to IntentTest objects
    intent_tests = [
        IntentTest(
            id=i.get("id", str(uuid.uuid4())),
            module=module,
            intent=i.get("intent", ""),
            status=i.get("status", "pending"),
            created_at=i.get("created_at", datetime.now().isoformat()),
        )
        for i in intent_list
    ]

    # Generate test file
    try:
        filepath = generate_test_file(module, intent_tests)
        return jsonify(
            {
                "success": True,
                "filepath": filepath,
                "message": f"Test file generated successfully",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/save-session", methods=["POST"])
def save_session():
    """Save current session to file."""
    data = request.json
    session_path = os.path.join(
        PROJECT_ROOT, "saved_states", "intent_runner_session.json"
    )

    os.makedirs(os.path.dirname(session_path), exist_ok=True)

    with open(session_path, "w") as f:
        json.dump(data, f, indent=2)

    return jsonify({"success": True, "path": session_path})


@app.route("/api/load-session", methods=["GET"])
def load_session():
    """Load saved session from file."""
    session_path = os.path.join(
        PROJECT_ROOT, "saved_states", "intent_runner_session.json"
    )

    if os.path.exists(session_path):
        with open(session_path, "r") as f:
            data = json.load(f)
        return jsonify({"success": True, "data": data})

    return jsonify({"success": False, "error": "No saved session found"})


# ============================================================================
# CONFIGURATION API ROUTES
# ============================================================================


@app.route("/api/config/ui", methods=["POST"])
def config_ui():
    """Update UI module configuration."""
    data = request.json

    base_url = data.get("base_url", "")

    if not base_url:
        return jsonify({"success": False, "error": "Base URL is required"})

    # Update module configuration
    module_config["ui"]["base_url"] = base_url

    # Update URLs in builtins
    if "custom" not in builtins.URLS:
        builtins.URLS["custom"] = {}
    builtins.URLS["custom"]["base_url"] = base_url

    return jsonify(
        {"success": True, "message": "UI configuration updated", "base_url": base_url}
    )


@app.route("/api/config/api", methods=["POST"])
def config_api():
    """Update API module configuration."""
    data = request.json

    base_url = data.get("base_url", "")
    swagger_content = data.get("swagger_content", None)

    if not base_url:
        return jsonify({"success": False, "error": "Base URL is required"})

    try:
        # Update module configuration
        module_config["api"]["base_url"] = base_url

        # If swagger content provided, save it and embed
        if swagger_content:
            try:
                # Validate JSON
                swagger_data = json.loads(swagger_content)

                # Save to file
                swagger_path = os.path.join(PROJECT_ROOT, "swagger_custom.json")
                with open(swagger_path, "w") as f:
                    json.dump(swagger_data, f, indent=2)

                module_config["api"]["swagger_path"] = swagger_path

                # Reset API wrapper to pick up new config
                reset_api_wrapper()

            except json.JSONDecodeError as e:
                return jsonify({"success": False, "error": f"Invalid JSON: {str(e)}"})

        # Reset API wrapper to use new base URL
        reset_api_wrapper()

        return jsonify(
            {
                "success": True,
                "message": "API configuration updated",
                "base_url": base_url,
                "swagger_embedded": swagger_content is not None,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/config/db", methods=["POST"])
def config_db():
    """Update DB module configuration and connect."""
    data = request.json

    try:
        # Update module configuration
        module_config["db"]["db_type"] = data.get("db_type", "mysql")
        module_config["db"]["host"] = data.get("host", "127.0.0.1")
        module_config["db"]["port"] = data.get("port", "3306")
        module_config["db"]["database"] = data.get("database", "testdb")
        module_config["db"]["username"] = data.get("username", "root")
        module_config["db"]["password"] = data.get("password", "")

        # Reset DB context to use new config
        reset_db_context()

        # Try to connect with new configuration
        db = get_db_context(force_refresh=True)

        # Get table count
        tables = db.get_all_tables() if db else []
        table_count = len(tables) if tables else 0

        return jsonify(
            {
                "success": True,
                "message": "Database connected successfully",
                "tables": table_count,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/config/db/test", methods=["POST"])
def test_db_connection():
    """Test database connection without applying configuration."""
    data = request.json

    try:
        from Utils.db_connector import DBConnector

        # Create temporary connection
        db = DBConnector(
            host=data.get("host", "127.0.0.1"),
            port=data.get("port", "3306"),
            user=data.get("username", "root"),
            password=data.get("password", ""),
            database=data.get("database", "testdb"),
        )

        connection = db.connect()

        if connection and connection.is_connected():
            # Get table count
            tables = db.get_all_tables()
            table_count = len(tables) if tables else 0
            db.close()

            return jsonify(
                {
                    "success": True,
                    "message": "Connection successful",
                    "tables": table_count,
                }
            )
        else:
            return jsonify(
                {"success": False, "error": "Could not establish connection"}
            )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/config/get", methods=["GET"])
def get_config():
    """Get current module configuration."""
    # Don't return passwords
    safe_config = {
        "ui": module_config["ui"].copy(),
        "api": {
            "base_url": module_config["api"]["base_url"],
            "swagger_path": module_config["api"].get("swagger_path", ""),
        },
        "db": {
            "db_type": module_config["db"]["db_type"],
            "host": module_config["db"]["host"],
            "port": module_config["db"]["port"],
            "database": module_config["db"]["database"],
            "username": module_config["db"]["username"],
            # Password not returned for security
        },
    }

    return jsonify({"success": True, "config": safe_config})


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import atexit

    # Register cleanup on exit
    atexit.register(cleanup_instances)

    print("\n" + "=" * 60)
    print("  🤖 AI Intent Test Runner Dashboard")
    print("=" * 60)
    print(f"  📁 Project Root: {PROJECT_ROOT}")
    print(f"  🌐 Starting server at: http://localhost:5000")
    print("=" * 60)
    print("\n  Open your browser and navigate to http://localhost:5000\n")

    # Run Flask app
    # NOTE: threaded=False is required for Playwright sync API compatibility
    # Playwright sync API doesn't work across threads
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=False)
