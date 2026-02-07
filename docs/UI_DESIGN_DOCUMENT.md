# AI-Augmented UI Testing Framework - Design Document

## 📋 Document Information

| Field              | Value                                                 |
| ------------------ | ----------------------------------------------------- |
| **Document Title** | AI-Augmented E2E Framework - UI Testing Module Design |
| **Version**        | 2.0.0                                                 |
| **Last Updated**   | February 7, 2026                                      |
| **Author**         | Framework Team                                        |
| **Status**         | Production Ready                                      |

---

## 📑 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Core Components](#3-core-components)
4. [Data Flow & Sequence Diagrams](#4-data-flow--sequence-diagrams)
5. [Component Specifications](#5-component-specifications)
6. [Intent-Based Execution](#6-intent-based-execution)
7. [Network Interception](#7-network-interception)
8. [Configuration](#8-configuration)
9. [Logging & Observability](#9-logging--observability)
10. [Test Implementation Guide](#10-test-implementation-guide)
11. [Error Handling & Self-Healing](#11-error-handling--self-healing)
12. [Dependencies](#12-dependencies)
13. [Future Enhancements](#13-future-enhancements)

---

## 1. Executive Summary

### 1.1 Purpose

The AI-Augmented UI Testing Framework provides an innovative approach to browser automation testing by leveraging:
- **Natural Language Processing (NLP)** for Gherkin-style test intent interpretation
- **Semantic Element Matching** via IntentLocatorLibrary with TF-IDF scoring
- **GitLab Duo AI** for intelligent action generation and self-healing
- **Network Interception** for API validation during UI flows
- **Playwright** for robust cross-browser automation

### 1.2 Key Innovation

Traditional UI testing requires explicit selectors and step definitions. This framework transforms the testing paradigm:

```
Traditional:        Step: "Login as standard user"
                    Code: page.fill("#username", "standard_user")
                          page.fill("#password", "secret_sauce")
                          page.click("#login-button")

AI-Augmented:       Intent: "Given I am on the login page
                            When I fill username with standard_user
                            And I fill password with secret_sauce
                            And I click login button
                            Then I should see the inventory page"
                    Framework: Automatically finds elements, generates actions, and validates
```

### 1.3 Key Features

| Feature                            | Description                                                             |
| ---------------------------------- | ----------------------------------------------------------------------- |
| **Intent-Based Execution**         | Execute UI flows using Gherkin-style natural language descriptions      |
| **Semantic Element Matching**      | TF-IDF vectorization + intent weighting for intelligent element finding |
| **AI Action Generation**           | GitLab Duo generates Playwright actions from step intents               |
| **Self-Healing Selectors**         | Automatic locator repair when elements change                           |
| **Network Interception**           | Capture and validate API calls during UI flows                          |
| **Comprehensive Failure Analysis** | AI-powered root cause analysis for failed steps                         |
| **RAG-Based Learning**             | Store successful executions for future intent matching                  |
| **Built-in Assertions**            | `assert_success` parameter auto-raises `AssertionError` on failure      |
| **Module-Based Storage**           | Actions stored by URL module (e.g., `/inventory` → "inventory")         |

---

## 2. System Architecture

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            AI-AUGMENTED UI TESTING FRAMEWORK                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────┐                                                               │
│  │   TEST LAYER     │   test_ui_agent.py                                            │
│  │   (Pytest)       │   - TestLoginSelfHealing                                      │
│  │                  │   - Fixtures: ui_page, ui_context                             │
│  └────────┬─────────┘                                                               │
│           │                                                                          │
│           ▼                                                                          │
│  ┌──────────────────┐                                                               │
│  │   BASE PAGE      │   Logic/UI/BasePage.py                                        │
│  │   (Orchestrator) │   - execute_by_intent()                                       │
│  │                  │   - Network interception methods                              │
│  │                  │   - Self-healing logic                                        │
│  └────────┬─────────┘                                                               │
│           │                                                                          │
│           ├────────────────────┬────────────────────┬───────────────────┐           │
│           ▼                    ▼                    ▼                   ▼           │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────┐   │
│  │  INTENT LOCATOR  │ │   AI AGENT       │ │   PLAYWRIGHT     │ │  LOGGER      │   │
│  │ (IntentLocator   │ │ (Utils/ai_agent) │ │   (Browser)      │ │  (Utils/)    │   │
│  │  Library.py)     │ │                  │ │                  │ │              │   │
│  │                  │ │  - GitLab Duo    │ │  - Chrome/FF/WK  │ │  - Console   │   │
│  │  - TF-IDF        │ │  - Action Gen    │ │  - Page Actions  │ │  - File      │   │
│  │  - Semantic      │ │  - Retry Gen     │ │  - Network       │ │  - Unicode   │   │
│  │    Scoring       │ │  - Analysis      │ │    Capture       │ │    Safe      │   │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────┘   │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                              EXTERNAL SERVICES                                │   │
│  ├──────────────────┬──────────────────┬────────────────────────────────────────┤   │
│  │  GitLab Duo AI   │   URLs Config    │   RAG Context (ChromaDB)               │   │
│  │  (Action Gen)    │   (urls.yaml)    │   (UI Learning)                        │   │
│  └──────────────────┴──────────────────┴────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Interaction Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Test      │────▶│  BasePage   │────▶│ IntentLoc   │────▶│ AI Agent    │
│   Layer     │     │  execute_   │     │  Library    │     │ (GitLab     │
│             │     │  by_intent  │     │             │     │  Duo)       │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
                    │ Playwright  │     │ TF-IDF      │     │ Action JSON │
                    │ Execution   │◀────│ Element     │◀────│ Generation  │
                    │             │     │ Matching    │     │             │
                    └─────────────┘     └─────────────┘     └─────────────┘
```

---

## 3. Core Components

### 3.1 Component Overview

| Component                | File Location                  | Purpose                                      |
| ------------------------ | ------------------------------ | -------------------------------------------- |
| **BasePage**             | `Logic/UI/BasePage.py`         | Core orchestrator for intent-based execution |
| **IntentLocatorLibrary** | `Libs/IntentLocatorLibrary.py` | Semantic element matching via TF-IDF         |
| **AI Agent**             | `Utils/ai_agent.py`            | GitLab Duo integration for action generation |
| **LoginPage**            | `Logic/UI/Login/LoginPage.py`  | Page-specific actions (extends BasePage)     |
| **IntentLogger**         | `Utils/logger.py`              | Structured logging with test context         |
| **Prompts**              | `Resources/prompts.py`         | AI prompt templates for UI actions           |

### 3.2 BasePage - Core Orchestrator

```python
class BasePage:
    """
    Base class for all Page Objects.
    Handles direct Playwright interactions and AI self-healing logic.
    """
    
    def __init__(self, page: Page, api_wrapper: APIWrapper = None):
        self.page = page
        self.config = builtins.CONFIG
        self.ai_agent = self.api_wrapper.ai_agent
        
        # Network interception storage
        self._captured_requests = []
        self._captured_responses = []
        self._network_listener_active = False
    
    # Key Methods
    def execute_by_intent(
        intent: str, 
        rag_context=None, 
        assert_success: bool = True  # NEW: Built-in assertions
    ) -> dict
    def start_network_capture(url_pattern: str = "**/*")
    def validate_api_called(url_pattern, method, expected_status, ...)
    def _resolve_url(page_ref: str) -> str
    def _execute_action(action: dict, logger) -> bool
```

#### 3.2.1 Built-in Assertions (`assert_success` Parameter)

The `execute_by_intent` function now includes a built-in assertion mechanism:

```python
def execute_by_intent(self, intent: str, rag_context=None, assert_success: bool = True) -> dict:
    """
    Args:
        intent: Multi-line Gherkin steps
        rag_context: RAG instance for learning storage
        assert_success (bool): If True, raises AssertionError when any step fails.
                               Set to False for negative testing scenarios.
    
    Raises:
        AssertionError: If assert_success=True and any step fails
    """
```

**Usage Examples:**

```python
# Normal test - auto-raises AssertionError on failure (no manual assert needed)
def test_login_success(self, ui_page, ui_context):
    ui_page.execute_by_intent(
        intent="""
        Given I am on the login page
        When I fill username with standard_user
        And I click login button
        Then I should see the inventory page
        """,
        rag_context=ui_context,
    )  # Automatically fails test if any step fails

# Negative test - no assertion, returns result for inspection
def test_login_failure_expected(self, ui_page, ui_context):
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
    assert result["success"] == False  # Manual assertion for negative test
```

### 3.3 IntentLocatorLibrary - Semantic Element Matching

```python
class IntentLocatorLibrary:
    """Semantic element matching with TF-IDF vectorization and intent weighting."""
    
    def find_elements_outerhtml_by_intent(
        html_or_path: str,
        intent_str: str,
        top_k: int = 5,
        min_score: float = 0.0,
        locator_value: str = ""
    ) -> List[str]
    
    def find_elements_outerhtml_with_score_backoff(
        html_or_path: str,
        intent_str: str,
        top_k: int = 5,
        start: float = 0.5,
        min_floor: float = 0.05,
        step: float = 0.05
    ) -> List[str]
```

---

## 4. Data Flow & Sequence Diagrams

### 4.1 Intent-Based UI Execution Flow

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│   Test   │  │ BasePage │  │  Gherkin │  │ Intent   │  │ AI Agent │  │Playwright│
│   File   │  │          │  │  Parser  │  │ Locator  │  │(GitLab)  │  │ Browser  │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │             │             │             │
     │  execute_by_intent(intent)│             │             │             │
     │─────────────▶             │             │             │             │
     │             │             │             │             │             │
     │             │ _parse_gherkin_steps()    │             │             │
     │             │─────────────▶             │             │             │
     │             │             │             │             │             │
     │             │   [Given, When, And, Then] steps       │             │
     │             │◀─────────────────────────────────────────────────────│
     │             │             │             │             │             │
     │             │ FOR EACH STEP:            │             │             │
     │             │             │             │             │             │
     │             │ _get_page_html()          │             │             │
     │             │─────────────────────────────────────────────────────▶│
     │             │                           │             │   HTML     │
     │             │◀─────────────────────────────────────────────────────│
     │             │             │             │             │             │
     │             │ find_elements_with_backoff()            │             │
     │             │────────────────────────────▶             │             │
     │             │             │             │             │             │
     │             │             │   [Relevant Elements]     │             │
     │             │◀────────────────────────────             │             │
     │             │             │             │             │             │
     │             │ run_agent(UI_STEP_ACTION, elements)     │             │
     │             │──────────────────────────────────────────▶             │
     │             │             │             │             │             │
     │             │             │             │   {action: "click", locator: "#btn"}
     │             │◀──────────────────────────────────────────             │
     │             │             │             │             │             │
     │             │ _execute_action(action)   │             │             │
     │             │─────────────────────────────────────────────────────▶│
     │             │             │             │             │   Success   │
     │             │◀─────────────────────────────────────────────────────│
     │             │             │             │             │             │
     │ {success: true, steps: [...]}           │             │             │
     │◀────────────────────────────────────────────────────────────────────│
```

### 4.2 Self-Healing Flow

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ BasePage │  │ AI Agent │  │ Intent   │  │Playwright│
│          │  │          │  │ Locator  │  │          │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │             │
     │ _execute_action(action)   │             │
     │─────────────────────────────────────────▶
     │             │             │             │
     │             │             │   ❌ TIMEOUT ERROR
     │◀─────────────────────────────────────────
     │             │             │             │
     │ [RETRY] Refresh HTML      │             │
     │─────────────────────────────────────────▶
     │             │             │             │
     │◀─────────────────────────────────────────
     │             │             │             │
     │ find_elements_with_backoff() (top_k * 2)│
     │────────────────────────────▶             │
     │             │             │             │
     │◀────────────────────────────             │
     │             │             │             │
     │ run_agent(UI_STEP_RETRY, fresh_elements)│
     │─────────────▶             │             │
     │             │             │             │
     │ {fixed_action}            │             │
     │◀─────────────             │             │
     │             │             │             │
     │ _execute_action(fixed_action)           │
     │─────────────────────────────────────────▶
     │             │             │             │
     │             │             │   ✅ SUCCESS │
     │◀─────────────────────────────────────────
```

### 4.3 Network Interception Flow

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Test     │  │ BasePage │  │Playwright│  │ Target   │
│          │  │          │  │ Network  │  │ Server   │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │             │
     │ "start capturing network" │             │
     │─────────────▶             │             │
     │             │             │             │
     │             │ page.on("request", handler)│
     │             │─────────────▶             │
     │             │             │             │
     │             │ page.on("response", handler)
     │             │─────────────▶             │
     │             │             │             │
     │ [Continue UI actions...]  │             │
     │─────────────▶             │             │
     │             │             │             │
     │             │ page.goto() │             │
     │             │─────────────▶             │
     │             │             │ HTTP Request│
     │             │             │─────────────▶
     │             │             │             │
     │             │             │ HTTP Response
     │             │◀─────────────             │
     │             │             │             │
     │             │ [Store in _captured_*]    │
     │             │◀─────────────             │
     │             │             │             │
     │ "validate api **/swagger* 200"          │
     │─────────────▶             │             │
     │             │             │             │
     │             │ validate_api_called()     │
     │             │─────────────▶             │
     │             │             │             │
     │             │ {success, matching_calls} │
     │◀─────────────             │             │
```

---

## 5. Component Specifications

### 5.1 BasePage Methods

#### 5.1.1 execute_by_intent()

```python
def execute_by_intent(self, intent: str, rag_context=None) -> dict:
    """
    Execute UI test by Gherkin-style intent.

    Args:
        intent: Multi-line Gherkin steps:
            Given I am on the login page
            When I fill username with standard_user
            And I fill password with secret_sauce
            And I click login button
            Then I should see the inventory page

        rag_context: Optional RAG context for learning (ui_context fixture)

    Returns:
        dict with execution results:
        {
            "success": True/False,
            "intent": "original intent",
            "steps": [
                {"step_type": "Given", "intent": "...", "status": "passed", "action": {...}},
                ...
            ],
            "error": "error message if failed"
        }
    """
```

#### 5.1.2 _resolve_url()

```python
def _resolve_url(self, page_ref: str) -> str:
    """
    Resolve a page reference to an actual URL from urls.yaml.
    Uses exact key match - pass the exact key name from urls.yaml.

    Resolution Order:
    1. EXACT top-level key match (e.g., "swagger_page")
    2. Nested key with dot notation (e.g., "saucedemo.base_url")
    3. Exact key inside nested dicts (e.g., "base_url" in saucedemo)
    4. If already a URL, return as-is

    Args:
        page_ref: Exact key from urls.yaml

    Returns:
        Resolved URL or None
    """
```

#### 5.1.3 _execute_action()

```python
def _execute_action(self, action: dict, logger: IntentLogger) -> bool:
    """
    Execute a single action on the page.

    Supported Action Types:
    - navigate: Go to a URL by page reference
    - click: Click an element by locator
    - fill: Enter text into an input field
    - select: Select option from dropdown
    - verify: Validate page state (URL, element visibility, text)
    - wait: Wait for element to be visible
    - hover: Hover over element
    - start_capture: Start network interception
    - stop_capture: Stop network interception
    - validate_api: Validate captured API calls
    - clear_capture: Clear captured network data

    Returns:
        True if successful, False otherwise
    """
```

### 5.2 IntentLocatorLibrary Methods

#### 5.2.1 Scoring Algorithm

```python
def _build_weighted_vectors(docs: List[str], intent_str: str, locator_tokens: str):
    """
    Build TF-IDF vectors with proper intent weighting.
    
    Process:
    1. Normalize intent text (snake_case → spaces, camelCase → spaces)
    2. Weight intent heavily (repeat 3x in query vector)
    3. Build word + character n-gram vectors
    4. Combine word (1,2-grams) and char (3,4-grams) TF-IDF matrices
    """

def _calculate_intent_boost(el: Tag, intent_str: str, locator_tokens: str) -> float:
    """
    Calculate additional boost based on intent matching.
    
    Boosts:
    - +0.05 per intent word match in element text
    - +0.02 per locator token match
    - +0.1 for exact attribute matches (username, password, login)
    """
```

#### 5.2.2 Element Finding with Score Backoff

```python
def find_elements_outerhtml_with_score_backoff(
    html_or_path: str,
    intent_str: str,
    top_k: int = 5,
    start: float = 0.5,
    min_floor: float = 0.05,
    step: float = 0.05
) -> List[str]:
    """
    Find elements with decreasing score threshold until results found.
    
    Algorithm:
    1. Start at threshold 0.5
    2. If no matches, decrease by 0.05
    3. Repeat until min_floor (0.05) or matches found
    4. Return outerHTML of matching elements
    """
```

### 5.3 AI Agent Action Types

| Action Type       | JSON Structure                                                                     |
| ----------------- | ---------------------------------------------------------------------------------- |
| **navigate**      | `{"action": "navigate", "page_ref": "swagger_page"}`                               |
| **click**         | `{"action": "click", "locator": "#login-button"}`                                  |
| **fill**          | `{"action": "fill", "locator": "#username", "value": "standard_user"}`             |
| **select**        | `{"action": "select", "locator": "#dropdown", "value": "option1"}`                 |
| **verify**        | `{"action": "verify", "checks": [{"type": "url_contains", "value": "inventory"}]}` |
| **wait**          | `{"action": "wait", "locator": "#loading-spinner"}`                                |
| **hover**         | `{"action": "hover", "locator": "#menu-item"}`                                     |
| **start_capture** | `{"action": "start_capture", "url_pattern": "**/*"}`                               |
| **validate_api**  | `{"action": "validate_api", "url_pattern": "**/api/*", "expected_status": 200}`    |
| **stop_capture**  | `{"action": "stop_capture"}`                                                       |

---

## 6. Intent-Based Execution

### 6.1 Gherkin Step Parsing

```python
def _parse_gherkin_steps(self, intent: str) -> list:
    """
    Parse Gherkin-style steps from intent string.

    Supported Keywords:
    - Given: Setup/precondition steps
    - When: Action steps
    - Then: Verification/assertion steps
    - And: Continue previous step type

    Returns:
        [{"type": "Given", "intent": "I am on the login page"}, ...]
    """
```

### 6.2 Action Type Detection

```python
TOP_K_BY_ACTION = {
    "click": 5,      # 5 elements for click candidates
    "fill": 3,       # 3 elements for input fields
    "select": 3,     # 3 elements for dropdowns
    "verify": 10,    # 10 elements for verification
    "navigate": 0,   # No elements needed
    "wait": 5,
    "hover": 5,
    "network": 0,    # Network actions don't need elements
    "default": 5,
}
```

### 6.3 Example Intent Execution

```python
# Test file usage
result = ui_page.execute_by_intent(
    intent="""
    Given navigate to swagger_page
    And Check network requests for api call to '**/swagger*' with status 200
    """,
    rag_context=ui_context,
)

assert result["success"] is True
```

---

## 7. Network Interception

### 7.1 Network Capture Methods

```python
def start_network_capture(self, url_pattern: str = "**/*"):
    """Start capturing network requests and responses."""
    
def stop_network_capture(self):
    """Stop capturing network requests."""
    
def clear_captured_network(self):
    """Clear all captured network data."""
    
def get_captured_requests(url_pattern: str = None, method: str = None) -> list:
    """Get captured requests, optionally filtered."""
    
def get_captured_responses(url_pattern: str = None, status: int = None) -> list:
    """Get captured responses, optionally filtered."""
```

### 7.2 API Validation

```python
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

    Returns:
        {
            "success": True/False,
            "matching_calls": [...],
            "total_matches": int,
            "error": "error message if failed"
        }
    """
```

### 7.3 Network Action Intent Examples

| Intent                                                             | Generated Action                                                               |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| "start capturing network traffic"                                  | `{"action": "start_capture", "url_pattern": "**/*"}`                           |
| "Check network requests for api call to '**/api*' with status 200" | `{"action": "validate_api", "url_pattern": "**/api*", "expected_status": 200}` |
| "stop capturing network"                                           | `{"action": "stop_capture"}`                                                   |

---

## 8. Configuration

### 8.1 urls.yaml Structure

```yaml
# Top-level URLs (direct key lookup)
swagger_page: "https://fakerestapi.azurewebsites.net/index.html"

# Nested URLs (dot notation: saucedemo.base_url)
saucedemo:
  base_url: "https://www.saucedemo.com/"
  inventory_url: "https://www.saucedemo.com/inventory.html"

api:
  base_url: "https://dummyjson.com"

gitlab:
  base_url: "https://gitlab.com/api/v4"
```

### 8.2 config.yaml Settings

```yaml
# Browser settings
headless: false
slow_mo: 0
timeout: 5000

# AI Agent settings
max_retries: 3
retry_interval: 1
agent_mode: "ENABLED"  # ENABLED or DISABLED
```

### 8.3 URL Resolution Examples

| page_ref             | Resolution Method      | Result URL                                         |
| -------------------- | ---------------------- | -------------------------------------------------- |
| `swagger_page`       | Top-level key          | `https://fakerestapi.azurewebsites.net/index.html` |
| `saucedemo.base_url` | Dot notation           | `https://www.saucedemo.com/`                       |
| `base_url`           | Nested dict lookup     | First match in nested dicts                        |
| `https://...`        | Direct URL passthrough | Returns as-is                                      |

---

## 9. Logging & Observability

### 9.1 IntentLogger Output Format

```
==============================================================================
                         INTENT-BASED UI EXECUTION LOG
==============================================================================
Test ID: UI-NET-002
Test Title: Validate Specific API Response
Test Type: UI
Session Start: 2026-02-07 00:49:06
Intent:
    Given navigate to swagger page
    And Check network requests for api call to '**/swagger*' with status 200
==============================================================================

[PARSE] Found 2 steps to execute

==============================================================================
STEP: [Given] navigate to swagger page
==============================================================================
[ACTION] Generated: {"action": "navigate", "page_ref": "swagger_page"}
[EXECUTE] Navigated to https://fakerestapi.azurewebsites.net/index.html
[RESULT] [Given] PASSED

==============================================================================
STEP: [And] Check network requests for api call to '**/swagger*' with status 200
==============================================================================
[ACTION] Generated: {"action": "validate_api", "url_pattern": "**/swagger*", "expected_status": 200}
[NETWORK] API validation passed: **/swagger* (3 matching calls)
[RESULT] [And] PASSED

==============================================================================
END OF TEST: [UI-NET-002] Validate Specific API Response
Session End: 2026-02-07 00:49:27
Duration: 21.45 seconds
==============================================================================
```

### 9.2 Failure Analysis Output

```
[ERROR] [And] FAILED: Network validation failed for: **/config*
[ANALYSIS] Requesting failure analysis from GitLab Duo...
[ANALYSIS] Root Cause: No API call to '**/config*' found in captured traffic
[ANALYSIS] Suggestions:
  1. Verify the correct URL pattern is used
  2. Ensure network capture was started before the action
  3. Check if the API call uses a different endpoint
[ANALYSIS] Element Analysis: {'current_domain': 'saucelabs.com', 'expected_domain': 'Original application'}
```

---

## 10. Test Implementation Guide

### 10.1 Basic Test Structure

```python
"""
Test Suite for UI with AI Self-Healing and Intent-Based Execution
"""
import pytest

class TestLoginSelfHealing:
    
    @pytest.mark.id("UI-001")
    @pytest.mark.title("Login Flow - Standard User")
    def test_login_flow(self, ui_page, ui_context):
        result = ui_page.execute_by_intent(
            intent="""
            Given I am on the login page
            When I fill username with standard_user
            And I fill password with secret_sauce
            And I click login button
            Then I should see the inventory page
            """,
            rag_context=ui_context,
        )
        
        assert result["success"] is True, f"Login failed: {result.get('error')}"
```

### 10.2 Network Validation Test

```python
@pytest.mark.id("UI-NET-002")
@pytest.mark.title("Validate API Calls During Navigation")
def test_validate_api(self, ui_page, ui_context):
    result = ui_page.execute_by_intent(
        intent="""
        Given I start capturing network traffic
        Given I am on the login page
        When I fill username with standard_user
        And I fill password with secret_sauce
        And I click login button
        Then I should see the inventory page
        And Check network requests for api call to '**/inventory*' with status 200
        """,
        rag_context=ui_context,
    )
    
    assert result["success"] is True, f"Test failed: {result.get('error')}"
```

### 10.3 Custom URL Navigation

```python
def test_swagger_navigation(self, ui_page, ui_context):
    result = ui_page.execute_by_intent(
        intent="""
        Given navigate to swagger_page
        Then I should see the API documentation
        """,
        rag_context=ui_context,
    )
    
    assert result["success"] is True
```

---

## 11. Error Handling & Self-Healing

### 11.1 Self-Healing Flow

1. **Action Execution Fails**: Timeout, element not found, etc.
2. **Skip Retry for Network Actions**: `start_capture`, `validate_api`, etc. don't retry
3. **Refresh Page HTML**: Get fresh DOM state
4. **Get More Elements**: Double `top_k` for broader element search
5. **AI Retry Generation**: Ask GitLab Duo to fix the locator
6. **Execute Fixed Action**: Try the AI-suggested action
7. **Failure Analysis**: If still failing, get detailed analysis

### 11.2 Network Action Handling

```python
# Network actions skip retry loop
is_network_action = action_type in [
    "start_capture",
    "stop_capture", 
    "validate_api",
    "clear_capture"
]

if not success and not is_network_action:
    # Try retry once (only for non-network actions)
    ...
```

### 11.3 Failure Analysis Prompt

The framework uses GitLab Duo to analyze failures:

```python
failure_analysis = self.ai_agent.run_agent_based_on_context(
    context="UI_STEP_FAILURE_ANALYSIS",
    step_intent=step_intent,
    step_type=step_type,
    action_attempted=action,
    error_message=str(e),
    relevant_elements=relevant_elements,
    page_url=self.page.url,
    page_html_snippet=page_html_snippet,
    previous_steps=previous_steps,
)
```

---

## 12. Dependencies

### 12.1 Core Dependencies

| Package             | Version | Purpose                       |
| ------------------- | ------- | ----------------------------- |
| `playwright`        | Latest  | Browser automation            |
| `pytest`            | 7.4.3+  | Test framework                |
| `pytest-playwright` | 0.4.3+  | Playwright pytest integration |
| `beautifulsoup4`    | Latest  | HTML parsing                  |
| `lxml`              | Latest  | Fast HTML/XML parsing         |
| `scikit-learn`      | Latest  | TF-IDF vectorization          |
| `scipy`             | Latest  | Sparse matrix operations      |
| `pyyaml`            | Latest  | YAML configuration loading    |
| `python-dotenv`     | Latest  | Environment variable loading  |

### 12.2 AI Integration

| Service    | Purpose                                   |
| ---------- | ----------------------------------------- |
| GitLab Duo | Action generation, self-healing, analysis |
| ChromaDB   | RAG storage for UI learning               |
| Ollama     | Local embeddings (optional)               |

---

## 13. Future Enhancements

### 13.1 Planned Features

| Feature                   | Description                                      | Priority |
| ------------------------- | ------------------------------------------------ | -------- |
| **Visual AI Validation**  | Screenshot-based visual regression testing       | High     |
| **Multi-Browser Support** | Firefox, WebKit in addition to Chromium          | Medium   |
| **Parallel Execution**    | Run multiple intent flows concurrently           | Medium   |
| **Test Recording**        | Record user actions and generate Gherkin intents | Low      |
| **Accessibility Testing** | Integrate ARIA and accessibility checks          | Low      |

### 13.2 Architecture Improvements

| Improvement                | Description                                      |
| -------------------------- | ------------------------------------------------ |
| **Element Caching**        | Cache TF-IDF vectors for frequently used pages   |
| **Learning Feedback Loop** | Store failed patterns to improve future matching |
| **Custom Action Plugins**  | Allow user-defined action types                  |
| **Mobile Emulation**       | Support for mobile viewport and touch actions    |

---

## 📝 Appendix

### A. Gherkin Keywords Reference

| Keyword | Purpose                   | Example                                 |
| ------- | ------------------------- | --------------------------------------- |
| Given   | Setup/preconditions       | Given I am on the login page            |
| When    | User actions              | When I fill username with standard_user |
| And     | Continue previous keyword | And I click login button                |
| Then    | Assertions/verifications  | Then I should see the inventory page    |

### B. Verification Check Types

| Type              | Purpose                       | Example                                          |
| ----------------- | ----------------------------- | ------------------------------------------------ |
| `element_visible` | Check element is displayed    | `{"type": "element_visible", "locator": "#btn"}` |
| `url_contains`    | Check URL contains substring  | `{"type": "url_contains", "value": "inventory"}` |
| `text_visible`    | Check text is visible on page | `{"type": "text_visible", "text": "Products"}`   |

### C. File Structure

```
ai-augmented-e2e-framework/
├── Logic/
│   └── UI/
│       ├── BasePage.py          # Core orchestrator
│       ├── Common.py            # Shared utilities
│       └── Login/
│           └── LoginPage.py     # Page-specific actions
├── Libs/
│   └── IntentLocatorLibrary.py  # Semantic element matching
├── Utils/
│   ├── ai_agent.py              # GitLab Duo integration
│   └── logger.py                # IntentLogger
├── Resources/
│   └── prompts.py               # AI prompt templates
├── Tests/
│   └── UI/
│       └── test_ui_agent.py     # UI test files
├── Test_Data/
│   ├── urls.yaml                # URL configuration
│   └── test_data.yaml           # Test data
├── Config/
│   └── config.yaml              # Framework configuration
└── conftest.py                  # Pytest fixtures
```
