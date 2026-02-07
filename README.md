# 🤖 AI-Augmented E2E Testing Framework

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Playwright-1.40.0-green?logo=playwright&logoColor=white" alt="Playwright">
  <img src="https://img.shields.io/badge/Pytest-7.4.3-yellow?logo=pytest&logoColor=white" alt="Pytest">
  <img src="https://img.shields.io/badge/GitLab%20Duo-AI%20Powered-orange?logo=gitlab&logoColor=white" alt="GitLab Duo">
  <img src="https://img.shields.io/badge/ChromaDB-Vector%20Store-purple" alt="ChromaDB">
  <img src="https://img.shields.io/badge/MySQL-8.0+-blue?logo=mysql&logoColor=white" alt="MySQL">
</p>

> **A next-generation testing framework that uses Natural Language Processing, Retrieval-Augmented Generation (RAG), and GitLab Duo AI to enable intent-based test automation across UI, API, and Database layers.**

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Configuration](#-configuration)
- [Running Tests](#-running-tests)
- [Test Examples](#-test-examples)
- [New in v2.0: Built-in Assertions & Verification Intents](#-new-in-v20-built-in-assertions--verification-intents)
- [Module Documentation](#-module-documentation)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## 🎯 Overview

The **AI-Augmented E2E Testing Framework** revolutionizes traditional test automation by replacing explicit selectors and queries with **natural language intents**. The framework intelligently interprets what you want to test and generates the appropriate actions automatically.

### Traditional vs AI-Augmented Approach

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         TRADITIONAL APPROACH                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  UI Test:                                                                        │
│    page.fill("#username", "standard_user")                                       │
│    page.fill("#password", "secret_sauce")                                        │
│    page.click("#login-button")                                                   │
│    assert page.url == "https://www.saucedemo.com/inventory.html"                │
│                                                                                  │
│  API Test:                                                                       │
│    response = requests.get("https://api.example.com/books/1")                   │
│    assert response.status_code == 200                                           │
│    assert response.json()["id"] == 1                                            │
│                                                                                  │
│  DB Test:                                                                        │
│    cursor.execute("SELECT * FROM agents WHERE id = 5")                          │
│    results = cursor.fetchall()                                                   │
│    assert len(results) > 0                                                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    ▼ ▼ ▼

┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AI-AUGMENTED APPROACH (v2.0)                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  UI Test (with built-in assertions):                                            │
│    ui_page.execute_by_intent(                                                   │
│        intent="Given I login with standard_user and secret_sauce"               │
│    )  # Auto-raises AssertionError on failure!                                  │
│                                                                                  │
│  API Test (with verification):                                                  │
│    api_wrapper.execute_by_intent(                                               │
│        intent="Get book with id 1 and verify title is 'Hello World'"            │
│    )  # AI validates response data against expected values!                     │
│                                                                                  │
│  DB Test (with verification):                                                   │
│    db_context.execute_by_intent(                                                │
│        intent="verify that John is one of the agents"                           │
│    )  # Empty result = FAILURE for verification intents!                        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

| Feature                         | Description                                                   |
| ------------------------------- | ------------------------------------------------------------- |
| 🗣️ **Intent-Based Execution**    | Write tests in natural language (Gherkin-style for UI)        |
| 🧠 **GitLab Duo AI Integration** | Intelligent action/query generation and response analysis     |
| 🔍 **RAG-Powered Context**       | ChromaDB + Ollama embeddings for smart context retrieval      |
| 🔄 **Self-Healing Selectors**    | Auto-repair broken UI locators with AI                        |
| 📡 **Network Interception**      | Capture and validate API calls during UI flows                |
| 🎯 **TF-IDF Extraction**         | Extract resources/tables from intent using TF-IDF matching    |
| 📚 **Learning System**           | Store successful/failed executions for continuous improvement |
| ✅ **Built-in Assertions**       | `assert_success` parameter auto-raises `AssertionError`       |
| 🔎 **Verification Intents**      | AI validates response data against expected values in intent  |
| 📊 **Comprehensive Logging**     | Beautiful step-by-step logs with full traceability            |
| 🧪 **Multi-Layer Testing**       | UI, API, and Database testing in one unified framework        |

---

## 🏗️ Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        AI-AUGMENTED E2E TESTING FRAMEWORK                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                              TEST LAYER (Pytest)                             │   │
│   │   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                 │   │
│   │   │   UI Tests  │      │  API Tests  │      │  DB Tests   │                 │   │
│   │   │ test_ui_    │      │ test_api_   │      │ test_db_    │                 │   │
│   │   │ agent.py    │      │ agent.py    │      │ agent.py    │                 │   │
│   │   └──────┬──────┘      └──────┬──────┘      └──────┬──────┘                 │   │
│   └──────────┼─────────────────────┼─────────────────────┼──────────────────────┘   │
│              │                     │                     │                          │
│              ▼                     ▼                     ▼                          │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                           ORCHESTRATION LAYER                                │   │
│   │   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                 │   │
│   │   │  BasePage   │      │ APIWrapper  │      │DBConnector  │                 │   │
│   │   │ (UI Logic)  │      │ (API Logic) │      │ (DB Logic)  │                 │   │
│   │   │             │      │             │      │             │                 │   │
│   │   │ execute_by_ │      │ execute_by_ │      │ execute_by_ │                 │   │
│   │   │ intent()    │      │ intent()    │      │ intent()    │                 │   │
│   │   └──────┬──────┘      └──────┬──────┘      └──────┬──────┘                 │   │
│   └──────────┼─────────────────────┼─────────────────────┼──────────────────────┘   │
│              │                     │                     │                          │
│              └─────────────────────┼─────────────────────┘                          │
│                                    │                                                │
│                                    ▼                                                │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                            INTELLIGENCE LAYER                                │   │
│   │                                                                              │   │
│   │   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                 │   │
│   │   │   AI Agent    │   │  RAG Engine   │   │IntentLocator  │                 │   │
│   │   │               │   │               │   │  Library      │                 │   │
│   │   │ • GitLab Duo  │   │ • ChromaDB    │   │               │                 │   │
│   │   │ • Action Gen  │   │ • Ollama      │   │ • TF-IDF      │                 │   │
│   │   │ • Analysis    │   │ • Semantic    │   │ • Score       │                 │   │
│   │   │ • Retry Gen   │   │   Search      │   │   Backoff     │                 │   │
│   │   └───────────────┘   └───────────────┘   └───────────────┘                 │   │
│   │                                                                              │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                           EXECUTION LAYER                                    │   │
│   │   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                 │   │
│   │   │  Playwright   │   │    cURL       │   │    MySQL      │                 │   │
│   │   │   Browser     │   │  Subprocess   │   │   Connector   │                 │   │
│   │   └───────────────┘   └───────────────┘   └───────────────┘                 │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                          EXTERNAL SERVICES                                   │   │
│   │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │   │
│   │   │ GitLab   │  │  Ollama  │  │ ChromaDB │  │  MySQL   │  │  Target  │     │   │
│   │   │  Duo AI  │  │  (LLM)   │  │ (Vector) │  │   DB     │  │   APIs   │     │   │
│   │   └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Intent Execution Flow

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          INTENT EXECUTION FLOW                                    │
└──────────────────────────────────────────────────────────────────────────────────┘

     USER INTENT                    FRAMEWORK PROCESSING                    RESULT
  ┌─────────────┐                                                      ┌─────────────┐
  │   Natural   │                                                      │   Success/  │
  │   Language  │                                                      │   Failure   │
  │   Intent    │                                                      │   + Data    │
  └──────┬──────┘                                                      └──────▲──────┘
         │                                                                    │
         │ ①                                                                  │ ⑤
         ▼                                                                    │
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │   Parse     │────▶│  RAG Query  │────▶│  AI Action  │────▶│  Execute    │
  │   Intent    │ ②   │  Context    │ ③   │  Generate   │ ④   │  Action     │
  │             │     │             │     │             │     │             │
  │ • Gherkin   │     │ • Swagger   │     │ • GitLab    │     │ • Playwright│
  │   Steps     │     │ • Schema    │     │   Duo AI    │     │ • cURL      │
  │ • NL Parse  │     │ • Learning  │     │ • Prompt    │     │ • SQL       │
  └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘

                                         ⬇️ On Failure

                              ┌─────────────────────────┐
                              │   SELF-HEALING LOOP     │
                              │                         │
                              │  ① Capture Error        │
                              │  ② Get Fresh Context    │
                              │  ③ AI Retry Generation  │
                              │  ④ Re-execute Action    │
                              │  ⑤ Analyze Result       │
                              └─────────────────────────┘
```

---

## 🛠️ Technology Stack

### Core Technologies

| Technology     | Version | Purpose                                      |
| -------------- | ------- | -------------------------------------------- |
| **Python**     | 3.11+   | Core programming language                    |
| **Pytest**     | 7.4.3   | Testing framework with fixtures              |
| **Playwright** | 1.40.0  | Browser automation for UI testing            |
| **GitLab Duo** | -       | AI-powered code generation and analysis      |
| **ChromaDB**   | 0.5.23  | Vector database for RAG embeddings           |
| **Ollama**     | -       | Local LLM for embeddings (mxbai-embed-large) |
| **MySQL**      | 8.0+    | Database connectivity for DB testing         |

### AI/ML Libraries

| Library            | Purpose                                    |
| ------------------ | ------------------------------------------ |
| **scikit-learn**   | TF-IDF vectorization for semantic matching |
| **NumPy**          | Numerical computations                     |
| **SciPy**          | Scientific computing                       |
| **BeautifulSoup4** | HTML parsing for element extraction        |

### Supporting Libraries

| Library           | Purpose                         |
| ----------------- | ------------------------------- |
| **PyYAML**        | Configuration file parsing      |
| **python-dotenv** | Environment variable management |
| **requests**      | HTTP client for GitLab Duo API  |
| **lxml**          | Fast HTML/XML parsing           |

---

## 📁 Project Structure

```
ai-augmented-e2e-framework/
│
├── 📄 README.md                    # This documentation file
├── 📄 requirements.txt             # Python dependencies
├── 📄 pytest.ini                   # Pytest configuration
├── 📄 conftest.py                  # Global pytest fixtures
├── 📄 swagger.json                 # API documentation (OpenAPI/Swagger)
├── 📄 .env                         # Environment variables (create from .env.example)
│
├── 📁 Config/
│   └── 📄 config.yaml              # Framework configuration
│
├── 📁 Test_Data/
│   ├── 📄 urls.yaml                # URL configurations for all environments
│   └── 📄 test_data.yaml           # Test data (credentials, etc.)
│
├── 📁 Tests/                       # All test files
│   ├── 📁 UI/
│   │   └── 📄 test_ui_agent.py     # UI intent-based tests
│   ├── 📁 API/
│   │   └── 📄 test_api_agent.py    # API intent-based tests
│   └── 📁 DB/
│       └── 📄 test_db_agent.py     # DB intent-based tests
│
├── 📁 Logic/                       # Business logic layer
│   ├── 📁 UI/
│   │   ├── 📄 BasePage.py          # Core UI orchestrator
│   │   └── 📁 Login/
│   │       └── 📄 LoginPage.py     # Login page actions
│   └── 📁 API/
│       └── 📄 api_wrapper.py       # API orchestrator
│
├── 📁 Libs/                        # Core libraries
│   ├── 📄 RAG.py                   # RAG engine (ChromaDB + Ollama)
│   ├── 📄 IntentLocatorLibrary.py  # TF-IDF element matching
│   └── 📄 IntentQueriesLibrary.py  # Query intent matching
│
├── 📁 Utils/                       # Utility modules
│   ├── 📄 ai_agent.py              # GitLab Duo AI communication
│   ├── 📄 db_connector.py          # Database connection & queries
│   ├── 📄 logger.py                # Centralized logging
│   └── 📄 utils.py                 # General utilities
│
├── 📁 Resources/                   # Static resources
│   ├── 📄 prompts.py               # AI prompt templates
│   ├── 📄 Constants.py             # Constants and configurations
│   └── 📄 schemaAnalysis.md        # Schema analysis documentation
│
├── 📁 docs/                        # Design documentation
│   ├── 📄 UI_DESIGN_DOCUMENT.md    # UI module design
│   ├── 📄 API_DESIGN_DOCUMENT.md   # API module design
│   └── 📄 DB_DESIGN_DOCUMENT.md    # DB module design
│
├── 📁 chroma_db/                   # ChromaDB persistence (auto-generated)
│
├── 📁 saved_states/                # Browser state storage
│   └── 📄 state.json               # Authentication state
│
└── 📁 ai-augmented-venv/           # Python virtual environment
```

---

## 📋 Prerequisites

Before setting up the framework, ensure you have the following installed:

### Required Software

| Software   | Version | Installation                                    |
| ---------- | ------- | ----------------------------------------------- |
| **Python** | 3.11+   | [python.org](https://www.python.org/downloads/) |
| **Git**    | Latest  | [git-scm.com](https://git-scm.com/)             |
| **Ollama** | Latest  | [ollama.ai](https://ollama.ai/)                 |
| **MySQL**  | 8.0+    | [mysql.com](https://dev.mysql.com/downloads/)   |

### GitLab Duo Access

You need a GitLab Personal Access Token with Code Suggestions enabled:

1. Go to GitLab → Settings → Access Tokens
2. Create a token with `api` and `read_user` scopes
3. Ensure your GitLab account has Duo access enabled

### Ollama Model

```bash
# Install the embedding model
ollama pull mxbai-embed-large

# Verify installation
ollama list
```

---

## 🚀 Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/mohammedismailx/ai-augmented-e2e-framework.git
cd ai-augmented-e2e-framework
```

### Step 2: Create Virtual Environment

```powershell
# Windows (PowerShell)
python -m venv ai-augmented-venv
.\ai-augmented-venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv ai-augmented-venv
source ai-augmented-venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install Playwright Browsers

```bash
playwright install chromium
# Or install all browsers
playwright install
```

### Step 5: Create Environment File

Create a `.env` file in the project root:

```env
# ============================================================
# GitLab Duo Configuration (REQUIRED)
# ============================================================
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx

# ============================================================
# Database Configuration (Required for DB tests)
# ============================================================
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=testdb

# ============================================================
# Ollama Configuration
# ============================================================
LLAMA3=llama3.1:latest
LLAMA3_URL=http://127.0.0.1:2213

# ============================================================
# UI Test Credentials (Optional - for SauceDemo tests)
# ============================================================
SAUCE_USERNAME=standard_user
SAUCE_PASSWORD=secret_sauce

# ============================================================
# Schema Refresh Flags
# ============================================================
REFRESH_API_SCHEMA=false
REFRESH_DB_SCHEMA=false
```

### Step 6: Start Required Services

```bash
# Start Ollama (in a separate terminal)
ollama serve

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### Step 7: Verify Installation

```bash
# Run a quick test
pytest Tests/API/test_api_agent.py -v -s

# Or run all tests
pytest -v -s
```

---

## ⚙️ Configuration

### config.yaml

```yaml
# Framework Configuration
agent_type: "GITLAB_DUO"    # AI agent type
headless: false              # Browser headless mode
slow_mo: 1000                # Slow motion delay (ms)
agent_mode: "ENABLED"        # Enable/Disable AI agent
manage_browser_lifecycle: true
timeout: 5000                # Default timeout (ms)
max_retries: 3               # Max retry attempts
retry_interval: 1            # Retry interval (seconds)
```

### urls.yaml

```yaml
# Top-level URLs (direct key access)
swagger_page: "https://fakerestapi.azurewebsites.net/index.html"

# Nested URLs (dot notation: saucedemo.base_url)
saucedemo:
  base_url: "https://www.saucedemo.com/"
  inventory_url: "https://www.saucedemo.com/inventory.html"

swagger:
  base_url: "https://fakerestapi.azurewebsites.net/index.html"

api:
  base_url: "https://dummyjson.com"

ollama:
  base_url: "http://127.0.0.1:2213"
```

---

## 🧪 Running Tests

### Basic Commands

```powershell
# Run all tests
pytest -v -s

# Run with detailed output
pytest -v -s --tb=long

# Run specific test type
pytest Tests/UI/ -v -s      # UI tests only
pytest Tests/API/ -v -s     # API tests only
pytest Tests/DB/ -v -s      # DB tests only
```

### Run Specific Tests

```powershell
# Run a specific test file
pytest Tests/UI/test_ui_agent.py -v -s

# Run a specific test class
pytest Tests/UI/test_ui_agent.py::TestLoginSelfHealing -v -s

# Run a specific test method
pytest Tests/UI/test_ui_agent.py::TestLoginSelfHealing::test_validate_specific_api -v -s
```

### Filter by Markers

```powershell
# Run only API intent tests
pytest -m api_intent -v -s

# Run only DB intent tests
pytest -m db_intent -v -s

# Run tests by ID
pytest -v -s -k "API-001"
```

### Parallel Execution

```powershell
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel
pytest -n auto -v
```

### Generate Reports

```powershell
# Install pytest-html for HTML reports
pip install pytest-html

# Generate HTML report
pytest --html=reports/report.html --self-contained-html -v
```

---

## 📝 Test Examples

### UI Test Example

```python
"""
UI Test with Intent-Based Execution (v2.0 - Built-in Assertions)
"""
import pytest

class TestLoginSelfHealing:
    
    @pytest.mark.id("UI-001")
    @pytest.mark.title("Login Flow - Standard User")
    def test_login_flow(self, ui_page, ui_context):
        # No manual assertion needed - auto-raises AssertionError on failure!
        ui_page.execute_by_intent(
            intent="""
            Given navigate to saucedemo.base_url page
            Given I am on the login page
            When I fill username with standard_user
            And I fill password with secret_sauce
            And I click login button
            Then I should see the inventory page
            Then Header should be Products
            """,
            rag_context=ui_context,
        )

    @pytest.mark.id("UI-002")
    @pytest.mark.title("Negative Test - Expected Failure")
    def test_login_invalid_user(self, ui_page, ui_context):
        # For negative tests, use assert_success=False
        result = ui_page.execute_by_intent(
            intent="""
            Given I am on the login page
            When I fill username with invalid_user
            And I click login button
            Then I should see error message
            """,
            rag_context=ui_context,
            assert_success=False,  # Don't auto-assert
        )
        # Manual assertion for expected failure
        assert "error" in result.get("error", "").lower()
```

### API Test Example

```python
"""
API Test with Intent-Based Execution (v2.0 - Verification Intents)
"""
import pytest

class TestIntentBasedAPI:
    
    @pytest.mark.api_intent
    @pytest.mark.id("API-001")
    @pytest.mark.title("Get Book by ID")
    def test_get_book_by_id(self, api_wrapper):
        # No manual assertion needed!
        api_wrapper.execute_by_intent(intent="get book with id 1")

    @pytest.mark.api_intent
    @pytest.mark.id("API-002")
    @pytest.mark.title("Verify Activity Title")
    def test_verify_activity_title(self, api_wrapper):
        # AI will verify the response data matches expected value
        api_wrapper.execute_by_intent(
            intent="Get Activity with ID 5 and verify that its title is Activity 5"
        )
        # FAILS if title is different (e.g., "Activity 10")

    @pytest.mark.api_intent
    @pytest.mark.id("API-003")
    @pytest.mark.title("Negative Test - 404 Expected")
    def test_get_nonexistent_book(self, api_wrapper):
        result = api_wrapper.execute_by_intent(
            intent="get book with id 99999",
            assert_success=False  # Don't auto-assert
        )
        assert result["status_code"] == 404
```

### Database Test Example

```python
"""
Database Test with Intent-Based Execution (v2.0 - Verification Intents)
"""
import pytest

class TestDBIntentExecution:
    
    @pytest.mark.db_intent
    @pytest.mark.id("DB-001")
    @pytest.mark.title("Get All Agents")
    def test_get_all_agents(self, db_context):
        # No manual assertion needed!
        db_context.execute_by_intent(intent="get all agents from the database")

    @pytest.mark.db_intent
    @pytest.mark.id("DB-002")
    @pytest.mark.title("Verify Agent Exists")
    def test_verify_agent_exists(self, db_context):
        # For verification intents, empty result = FAILURE
        db_context.execute_by_intent(
            intent="verify that Rowen is one of the agents at Emirates"
        )
        # FAILS if no agent named Rowen found

    @pytest.mark.db_intent
    @pytest.mark.id("DB-003")
    @pytest.mark.title("Verify Agent Email Domain")
    def test_verify_agent_email_domain(self, db_context):
        db_context.execute_by_intent(
            intent="verify that Reumaysa email domain is yahoo"
        )
        # FAILS if Reumaysa's email is not @yahoo.com

    @pytest.mark.db_intent
    @pytest.mark.id("DB-004")
    @pytest.mark.title("Negative Test - Agent Should Not Exist")
    def test_nonexistent_agent(self, db_context):
        result = db_context.execute_by_intent(
            intent="verify that NonExistentUser is one of the agents",
            assert_success=False  # Don't auto-assert
        )
        assert result["success"] == False
```

---

## 🆕 New in v2.0: Built-in Assertions & Verification Intents

### Built-in Assertions (`assert_success` Parameter)

All `execute_by_intent()` methods now include a built-in assertion mechanism that automatically raises `AssertionError` on failure:

| Layer   | Method                                                                | Default     |
| ------- | --------------------------------------------------------------------- | ----------- |
| **UI**  | `ui_page.execute_by_intent(intent, rag_context, assert_success=True)` | Auto-assert |
| **API** | `api_wrapper.execute_by_intent(intent, assert_success=True)`          | Auto-assert |
| **DB**  | `db_context.execute_by_intent(intent, assert_success=True)`           | Auto-assert |

**Benefits:**
- ✅ Cleaner test code - no manual `assert` statements needed
- ✅ Consistent assertion messages across all layers
- ✅ Negative testing support with `assert_success=False`

### Verification Intents

The AI now understands **verification intents** that check specific data values:

```python
# API: Verify response data matches expected value
api_wrapper.execute_by_intent(
    intent="Get Activity with ID 5 and verify that its title is Activity 5"
)
# AI checks: response.title == "Activity 5" → SUCCESS or FAILURE

# DB: Verify condition is true
db_context.execute_by_intent(
    intent="verify that Reumaysa email domain is yahoo"
)
# Query: SELECT email FROM agents WHERE name = 'Reumaysa' AND email LIKE '%@yahoo%'
# Result: [] (empty) → FAILURE (verification failed)
# Result: [{"email": "reumaysa@yahoo.com"}] → SUCCESS
```

**Verification Keywords:** `verify`, `check`, `confirm`, `ensure`, `validate`, `make sure`

---

## 📚 Module Documentation

For detailed design documentation, see the following documents:

| Module          | Document                                              | Description                                                |
| --------------- | ----------------------------------------------------- | ---------------------------------------------------------- |
| **UI Testing**  | [UI_DESIGN_DOCUMENT.md](docs/UI_DESIGN_DOCUMENT.md)   | Playwright integration, self-healing, network interception |
| **API Testing** | [API_DESIGN_DOCUMENT.md](docs/API_DESIGN_DOCUMENT.md) | Swagger embedding, curl generation, response analysis      |
| **DB Testing**  | [DB_DESIGN_DOCUMENT.md](docs/DB_DESIGN_DOCUMENT.md)   | Schema embedding, SQL generation, learning system          |

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Ollama Connection Error

```
Error: Connection refused to http://localhost:11434
```

**Solution:**
```bash
# Start Ollama service
ollama serve

# Or check if running on different port
ollama serve --port 2213
```

#### 2. GitLab Duo Authentication Error

```
Error: 401 Unauthorized
```

**Solution:**
- Verify your `GITLAB_TOKEN` in `.env`
- Ensure token has `api` scope
- Check GitLab Duo is enabled for your account

#### 3. ChromaDB Permission Error

```
Error: Cannot access chroma_db directory
```

**Solution:**
```powershell
# Windows - Run as Administrator or fix permissions
icacls chroma_db /grant Everyone:F /T
```

#### 4. Playwright Browser Not Found

```
Error: Browser not found
```

**Solution:**
```bash
# Install browsers
playwright install chromium

# Or install all
playwright install
```

#### 5. MySQL Connection Error

```
Error: Can't connect to MySQL server
```

**Solution:**
- Verify MySQL is running
- Check credentials in `.env`
- Ensure database exists:
```sql
CREATE DATABASE IF NOT EXISTS testdb;
```

### Debug Mode

Enable verbose logging:

```python
# In config.yaml
agent_mode: "ENABLED"
```

Check log files:
- `api_with_intent_logs.txt` - API test logs
- `db_with_intent_logs.txt` - DB test logs
- `ui_with_intent_logs.txt` - UI test logs

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 👥 Authors

- Mohammed Ismail (mohammed.ismail2@emirates.com)
- Linked_in : https://www.linkedin.com/in/mohammed-nasr-ibrahim/
- 
---

## 🙏 Acknowledgments

- GitLab Duo for AI-powered code generation
- Playwright team for the excellent browser automation framework
- ChromaDB for the vector database
- Ollama for local LLM support

---

<p align="center">
  Made with ❤️ for intelligent test automation
</p>
