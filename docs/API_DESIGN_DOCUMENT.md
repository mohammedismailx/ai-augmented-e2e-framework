# AI-Augmented API Testing Framework - Design Document

## 📋 Document Information

| Field              | Value                                                  |
| ------------------ | ------------------------------------------------------ |
| **Document Title** | AI-Augmented E2E Framework - API Testing Module Design |
| **Version**        | 1.0.0                                                  |
| **Last Updated**   | February 6, 2026                                       |
| **Author**         | Framework Team                                         |
| **Status**         | Production Ready                                       |

---

## 📑 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Core Components](#3-core-components)
4. [Data Flow & Sequence Diagrams](#4-data-flow--sequence-diagrams)
5. [Component Specifications](#5-component-specifications)
6. [API Reference](#6-api-reference)
7. [Configuration](#7-configuration)
8. [Logging & Observability](#8-logging--observability)
9. [Test Implementation Guide](#9-test-implementation-guide)
10. [Error Handling & Retry Logic](#10-error-handling--retry-logic)
11. [Dependencies](#11-dependencies)
12. [Future Enhancements](#12-future-enhancements)

---

## 1. Executive Summary

### 1.1 Purpose

The AI-Augmented API Testing Framework provides an innovative approach to API testing by leveraging:
- **Natural Language Processing (NLP)** for test intent interpretation
- **Retrieval-Augmented Generation (RAG)** for API context retrieval
- **GitLab Duo AI** for intelligent curl command generation and response analysis
- **Semantic Search** via ChromaDB for matching intents to API endpoints

### 1.2 Key Innovation

Traditional API testing requires explicit endpoint definitions, request body construction, and assertion logic. This framework transforms the testing paradigm:

```
Traditional:        Intent: "test GET /api/v1/Books/1"
                    Code: requests.get(url, headers, params...)
                    Assert: response.status_code == 200

AI-Augmented:       Intent: "get book with id 1"
                    Framework: Automatically generates curl, executes, and validates
                    Assert: AI determines success based on semantic analysis
```

### 1.3 Key Features

| Feature                           | Description                                                 |
| --------------------------------- | ----------------------------------------------------------- |
| **Intent-Based Execution**        | Execute API calls using natural language descriptions       |
| **RAG-Powered Context**           | Automatic API documentation retrieval from embedded Swagger |
| **AI Curl Generation**            | GitLab Duo generates executable curl commands               |
| **AI Response Analysis**          | Intelligent success/failure determination                   |
| **Auto-Retry with Error Context** | Failed requests are retried with error analysis             |
| **Comprehensive Logging**         | Dual logging to console and file with full traceability     |

---

## 2. System Architecture

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            AI-AUGMENTED API TESTING FRAMEWORK                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────┐                                                               │
│  │   TEST LAYER     │   test_api_agent.py                                           │
│  │   (Pytest)       │   - TestIntentBasedAPI                                        │
│  │                  │   - Fixtures: api_wrapper, api_context                        │
│  └────────┬─────────┘                                                               │
│           │                                                                          │
│           ▼                                                                          │
│  ┌──────────────────┐                                                               │
│  │   API WRAPPER    │   Logic/API/api_wrapper.py                                    │
│  │   (Orchestrator) │   - execute_by_intent()                                       │
│  │                  │   - Coordinates all components                                │
│  └────────┬─────────┘                                                               │
│           │                                                                          │
│           ├────────────────────┬────────────────────┬───────────────────┐           │
│           ▼                    ▼                    ▼                   ▼           │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────┐   │
│  │   RAG ENGINE     │ │   AI AGENT       │ │   CURL EXECUTOR  │ │  LOGGER      │   │
│  │   (Libs/RAG.py)  │ │ (Utils/ai_agent) │ │   (subprocess)   │ │  (Utils/)    │   │
│  │                  │ │                  │ │                  │ │              │   │
│  │  - ChromaDB      │ │  - GitLab Duo    │ │  - Windows/Linux │ │  - Console   │   │
│  │  - Ollama Embed  │ │  - Curl Gen      │ │  - Status Parse  │ │  - File      │   │
│  │  - Semantic      │ │  - Analysis      │ │  - Retry Logic   │ │  - Unicode   │   │
│  │    Search        │ │  - Retry Gen     │ │                  │ │    Safe      │   │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────┘   │
│           │                    │                                                     │
│           ▼                    ▼                                                     │
│  ┌──────────────────┐ ┌──────────────────┐                                          │
│  │   CHROMA DB      │ │   GITLAB DUO     │                                          │
│  │  (Vector Store)  │ │   (LLM API)      │                                          │
│  │                  │ │                  │                                          │
│  │  ./chroma_db/    │ │  gitlab.com/api  │                                          │
│  └──────────────────┘ └──────────────────┘                                          │
│                                                                                      │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  EXTERNAL DEPENDENCIES                                                               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐         │
│  │    Ollama     │  │  GitLab Duo   │  │   ChromaDB    │  │  Target API   │         │
│  │  (Embeddings) │  │    (LLM)      │  │ (Persistence) │  │ (FakeRestAPI) │         │
│  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘         │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Interaction Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Pytest    │───▶│ API Wrapper │───▶│  RAG Engine │───▶│  ChromaDB   │
│   Test      │    │             │    │             │    │             │
└─────────────┘    └──────┬──────┘    └─────────────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐    ┌─────────────┐
                   │  AI Agent   │───▶│ GitLab Duo  │
                   │             │    │    API      │
                   └──────┬──────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐    ┌─────────────┐
                   │    Curl     │───▶│ Target API  │
                   │  Executor   │    │             │
                   └──────┬──────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  Response   │
                   │  Analysis   │
                   └─────────────┘
```

---

## 3. Core Components

### 3.1 Component Overview

| Component           | File Path                  | Primary Responsibility                             |
| ------------------- | -------------------------- | -------------------------------------------------- |
| **APIWrapper**      | `Logic/API/api_wrapper.py` | Orchestrates intent-based API execution            |
| **RAG**             | `Libs/RAG.py`              | Vector embeddings and semantic search              |
| **AIAgent**         | `Utils/ai_agent.py`        | LLM communication for curl generation and analysis |
| **IntentLogger**    | `Utils/logger.py`          | Dual console/file logging with Unicode safety      |
| **FrameworkLogger** | `Utils/logger.py`          | Static logging methods for framework-wide use      |
| **Prompts**         | `Resources/prompts.py`     | Prompt templates for GitLab Duo                    |
| **Fixtures**        | `conftest.py`              | Pytest fixtures for RAG and API wrapper            |

### 3.2 Directory Structure

```
ai-augmented-e2e-framework/
├── Libs/
│   └── RAG.py                    # RAG engine with ChromaDB
├── Logic/
│   └── API/
│       ├── api_wrapper.py        # Main API wrapper with intent execution
│       └── ai/
│           └── builder.py        # AI agent request builder
├── Utils/
│   ├── ai_agent.py               # AI agent for GitLab Duo communication
│   └── logger.py                 # Centralized logging
├── Resources/
│   ├── prompts.py                # Prompt templates
│   └── Constants.py              # API endpoints, headers, constants
├── Tests/
│   └── API/
│       └── test_api_agent.py     # Intent-based API tests
├── Config/
│   └── config.yaml               # Framework configuration
├── Test_Data/
│   ├── test_data.yaml            # Test data
│   └── urls.yaml                 # URL configurations
├── chroma_db/                    # ChromaDB persistence directory
├── swagger.json                  # API documentation (Swagger/OpenAPI)
├── conftest.py                   # Pytest fixtures
└── api_with_intent_logs.txt      # Intent execution logs
```

---

## 4. Data Flow & Sequence Diagrams

### 4.1 Intent-Based API Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        INTENT-BASED API EXECUTION FLOW                               │
└─────────────────────────────────────────────────────────────────────────────────────┘

STEP 1: RAG - RETRIEVE SWAGGER CONTEXT
═══════════════════════════════════════════════════════════════════════════════════════
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Intent    │────▶│   Ollama     │────▶│   ChromaDB   │────▶│   Swagger    │
│ "get book 1" │     │  Embedding   │     │   Query      │     │   Context    │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘

                                    │
                                    ▼
STEP 2: GITLAB DUO - GENERATE CURL COMMAND
═══════════════════════════════════════════════════════════════════════════════════════
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Intent +   │────▶│   GitLab     │────▶│    Curl      │
│   Swagger    │     │     Duo      │     │   Command    │
│   Context    │     │     API      │     │              │
└──────────────┘     └──────────────┘     └──────────────┘

                                    │
                                    ▼
STEP 3: EXECUTE CURL COMMAND
═══════════════════════════════════════════════════════════════════════════════════════
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Curl      │────▶│  Subprocess  │────▶│  API         │
│   Command    │     │  Execution   │     │  Response    │
└──────────────┘     └──────────────┘     └──────────────┘

                                    │
                     ┌──────────────┴──────────────┐
                     │                             │
                     ▼                             ▼
              ┌──────────────┐              ┌──────────────┐
              │   Success    │              │   Failed     │
              │  (2xx code)  │              │  (4xx/5xx)   │
              └──────┬───────┘              └──────┬───────┘
                     │                             │
                     │                             ▼
                     │                      ┌──────────────┐
                     │                      │  Retry with  │
                     │                      │  Error       │
                     │                      │  Context     │
                     │                      └──────┬───────┘
                     │                             │
                     ▼                             │
                                    ◀──────────────┘
STEP 4: GITLAB DUO - ANALYZE RESPONSE
═══════════════════════════════════════════════════════════════════════════════════════
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Response   │────▶│   GitLab     │────▶│    JSON      │
│   + Intent   │     │     Duo      │     │   Analysis   │
│   + Curl     │     │     API      │     │  {success,   │
│              │     │              │     │   reason}    │
└──────────────┘     └──────────────┘     └──────────────┘

                                    │
                                    ▼
STEP 5: RETURN RESULT
═══════════════════════════════════════════════════════════════════════════════════════
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  {                                                                                   │
│    "success": true/false,                                                            │
│    "reason": "AI analysis explanation",                                              │
│    "status_code": 200,                                                               │
│    "response_body": "{...}",                                                         │
│    "curl_command": "curl -X GET ...",                                                │
│    "analysis": "...",                                                                │
│    "retries": 0                                                                      │
│  }                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Sequence Diagram

```
┌────────┐  ┌──────────┐  ┌────────┐  ┌────────┐  ┌──────────┐  ┌────────┐
│  Test  │  │APIWrapper│  │  RAG   │  │AIAgent │  │GitLabDuo │  │ Target │
│        │  │          │  │        │  │        │  │   API    │  │  API   │
└───┬────┘  └────┬─────┘  └───┬────┘  └───┬────┘  └────┬─────┘  └───┬────┘
    │            │            │           │            │            │
    │ execute_by_intent()     │           │            │            │
    │───────────▶│            │           │            │            │
    │            │            │           │            │            │
    │            │ retrieve_endpoints_by_intent()      │            │
    │            │───────────▶│           │            │            │
    │            │            │           │            │            │
    │            │ [Swagger Context]      │            │            │
    │            │◀───────────│           │            │            │
    │            │            │           │            │            │
    │            │ execute_swagger_intent_context()    │            │
    │            │────────────────────────▶│           │            │
    │            │            │           │            │            │
    │            │            │           │ POST /completions       │
    │            │            │           │───────────▶│            │
    │            │            │           │            │            │
    │            │            │           │ [Curl Command]          │
    │            │            │           │◀───────────│            │
    │            │            │           │            │            │
    │            │ [Curl Command]         │            │            │
    │            │◀────────────────────────│           │            │
    │            │            │           │            │            │
    │            │ _execute_curl()        │            │            │
    │            │─────────────────────────────────────────────────▶│
    │            │            │           │            │            │
    │            │ [API Response]         │            │            │
    │            │◀─────────────────────────────────────────────────│
    │            │            │           │            │            │
    │            │ analyze_api_response() │            │            │
    │            │────────────────────────▶│           │            │
    │            │            │           │            │            │
    │            │            │           │ POST /completions       │
    │            │            │           │───────────▶│            │
    │            │            │           │            │            │
    │            │            │           │ [JSON Analysis]         │
    │            │            │           │◀───────────│            │
    │            │            │           │            │            │
    │            │ [Analysis JSON]        │            │            │
    │            │◀────────────────────────│           │            │
    │            │            │           │            │            │
    │ [Result Dictionary]     │           │            │            │
    │◀───────────│            │           │            │            │
    │            │            │           │            │            │
```

---

## 5. Component Specifications

### 5.1 APIWrapper Class

**File:** `Logic/API/api_wrapper.py`

**Purpose:** Main orchestrator for intent-based API execution.

#### 5.1.1 Class Definition

```python
class APIWrapper:
    """
    API Wrapper for intent-based API execution.
    
    Attributes:
        base_url (str): Default base URL for API requests
        session (requests.Session): HTTP session for traditional requests
        timeout (int): Request timeout in seconds
        config (dict): Framework configuration
        agent_mode (str): AI agent mode (ENABLED/DISABLED)
        ai_agent (AIAgent): AI agent instance for LLM communication
    """
```

#### 5.1.2 Core Methods

| Method                     | Parameters                                    | Returns | Description                         |
| -------------------------- | --------------------------------------------- | ------- | ----------------------------------- |
| `__init__`                 | `base_url=None`                               | `None`  | Initialize wrapper with AI agent    |
| `execute_by_intent`        | `intent, base_url, rag_instance, max_retries` | `dict`  | Execute API call based on intent    |
| `_clean_curl_command`      | `curl_command`                                | `str`   | Clean markdown/formatting from curl |
| `_execute_curl`            | `curl_command`                                | `dict`  | Execute curl via subprocess         |
| `_parse_analysis_json`     | `analysis`                                    | `dict`  | Parse JSON from AI analysis         |
| `_print_execution_summary` | `result, logger`                              | `None`  | Print formatted summary             |

#### 5.1.3 execute_by_intent Method

```python
def execute_by_intent(
    self,
    intent: str,
    base_url: str,
    rag_instance=None,
    max_retries: int = 2
) -> dict:
    """
    Execute an API call based on natural language intent.
    
    Args:
        intent: Natural language intent (e.g., "delete book with id 5")
        base_url: Base URL for the API
        rag_instance: RAG instance with embedded swagger
        max_retries: Maximum retry attempts for failed requests
    
    Returns:
        dict: {
            "success": bool,          # AI-determined success
            "reason": str,            # AI explanation
            "intent": str,            # Original intent
            "base_url": str,          # Base URL used
            "curl_command": str,      # Generated curl command
            "status_code": int,       # HTTP status code
            "response_body": str,     # Raw response body
            "analysis": str,          # Raw AI analysis
            "analysis_result": dict,  # Parsed {success, reason}
            "error": str,             # Error message if any
            "retries": int,           # Number of retries used
            "prompts": dict,          # Prompts sent to AI
            "responses": dict         # AI responses
        }
    """
```

#### 5.1.4 Curl Execution Process

```python
def _execute_curl(self, curl_command: str) -> dict:
    """
    Execute curl command via subprocess.
    
    Modifications applied automatically:
    - Add -k flag for SSL bypass
    - Add -s flag for silent mode
    - Add -w "\\n%{http_code}" for status code extraction
    
    Returns:
        dict: {
            "success": bool,
            "stdout": str,
            "stderr": str,
            "status_code": int,
            "error": str
        }
    """
```

### 5.2 RAG Class

**File:** `Libs/RAG.py`

**Purpose:** Vector embeddings and semantic search for API documentation.

#### 5.2.1 Class Definition

```python
class Rag:
    """
    Retrieval-Augmented Generation engine using ChromaDB and Ollama.
    
    Attributes:
        embedding_fn: Ollama embedding function (mxbai-embed-large)
        chroma_client: ChromaDB persistent client
    """
```

#### 5.2.2 Core Methods

| Method                             | Parameters                       | Returns      | Description                       |
| ---------------------------------- | -------------------------------- | ------------ | --------------------------------- |
| `embed_swagger_by_resource`        | `swagger_path, collection_name`  | `Collection` | Parse and embed swagger endpoints |
| `retrieve_endpoints_by_intent`     | `intent, collection_name, top_k` | `List[str]`  | Semantic search for endpoints     |
| `_format_single_endpoint_document` | `resource, endpoint, schemas`    | `str`        | Format endpoint for embedding     |
| `_get_action_keywords`             | `method, path, resource`         | `str`        | Generate searchable keywords      |
| `retrieve_similar_semantic`        | `collection, intent, label, k`   | `List[str]`  | General semantic search           |

#### 5.2.3 Swagger Embedding Process

```python
def embed_swagger_by_resource(
    self,
    swagger_path: str,
    collection_name: str = "api_endpoints"
):
    """
    Parse swagger.json and embed each endpoint individually.
    
    Each endpoint document contains:
    - Resource name (e.g., Books, Users)
    - HTTP method and path
    - Action keywords for semantic matching
    - Summary and description
    - Parameters (path, query, body)
    - Request body schema
    - Response codes
    
    Example embedded document:
        Resource: Books
        Endpoint: GET /api/v1/Books/{id}
        Actions: get Book, fetch Book, retrieve Book, find Book, get Book by id
        Parameters: id(path)*
        ResponseCodes: 200
    """
```

#### 5.2.4 Semantic Search Process

```python
def retrieve_endpoints_by_intent(
    self,
    intent: str,
    collection_name: str = "api_endpoints",
    top_k: int = 1
) -> List[str]:
    """
    Find relevant API endpoints based on user intent.
    
    Process:
    1. Generate embedding for intent using Ollama
    2. Query ChromaDB for similar documents
    3. Apply distance-based ranking
    4. Return top_k matches
    
    Args:
        intent: "delete book with id 5"
    
    Returns:
        ["Resource: Books\nEndpoint: DELETE /api/v1/Books/{id}\n..."]
    """
```

### 5.3 AIAgent Class

**File:** `Utils/ai_agent.py`

**Purpose:** Communication with GitLab Duo LLM for curl generation and response analysis.

#### 5.3.1 Class Definition

```python
class AIAgent:
    """
    AI Agent for LLM-based API testing operations.
    
    Attributes:
        agent_type: "GITLAB_DUO" or "LOCAL"
        base_url: GitLab API base URL
        chat_history: Conversation history
        api_wrapper: Reference to APIWrapper (dependency injection)
        builder: AIAgentBuilder for request construction
    """
```

#### 5.3.2 Core Methods

| Method                           | Parameters                                                                      | Returns     | Description           |
| -------------------------------- | ------------------------------------------------------------------------------- | ----------- | --------------------- |
| `execute_swagger_intent_context` | `intent, swagger_context, base_url, return_prompt`                              | `str/tuple` | Generate curl command |
| `analyze_api_response`           | `intent, curl_command, response_body, status_code, stderr, return_prompt`       | `str/tuple` | Analyze API response  |
| `retry_curl_generation`          | `intent, original_curl, error_output, swagger_context, base_url, return_prompt` | `str/tuple` | Fix failed curl       |
| `_prompt_agent`                  | `prompt, file_name, constraints, backstory`                                     | `str`       | Send prompt to LLM    |

#### 5.3.3 GitLab Duo Request Structure

```python
# Request body for GitLab Duo Code Suggestions API
{
    "current_file": {
        "file_name": "analysis_result.json",
        "content_above_cursor": "Analyze the API response and return JSON: ",
        "content_below_cursor": ""
    },
    "context": [{
        "name": "analysis_result.json",
        "type": "snippet",
        "content": "<prompt content>"
    }],
    "user_instruction": "Return ONLY the JSON object with success and reason fields",
    "intent": "generation"
}
```

### 5.4 Logger Classes

**File:** `Utils/logger.py`

#### 5.4.1 FrameworkLogger (Static)

```python
class FrameworkLogger:
    """
    Static logger for framework-wide logging with Unicode safety.
    
    Methods:
        safe_print(message)      # Unicode-safe console print
        info(message)            # [INFO] prefix
        ok(message)              # [OK] prefix
        warning(message)         # [WARNING] prefix
        error(message)           # [ERROR] prefix
        section(title)           # ======= title =======
        separator()              # ________________
        json_block(data, title)  # Formatted JSON output
        box(title, content)      # Box-formatted output
        result(success, message) # Test result banner
    """
```

#### 5.4.2 IntentLogger (Instance)

```python
class IntentLogger:
    """
    Logger for intent-based API execution with dual output.
    
    Features:
    - Console output with safe encoding
    - File output (api_with_intent_logs.txt) with UTF-8
    - Session tracking with timestamps
    - Structured sections for prompts and responses
    
    Methods:
        start_session()           # Initialize logging session
        end_session()             # Close session with duration
        log(message)              # Log to both outputs
        log_section(title)        # Section header
        log_prompt(prompt)        # Prompt to GitLab Duo
        log_ai_response(response) # GitLab Duo response
        log_summary(data)         # Execution summary
    """
```

---

## 6. API Reference

### 6.1 GitLab Duo Integration

**Endpoint:** `https://gitlab.com/api/v4/code_suggestions/completions`

**Authentication:** Personal Access Token via `Authorization: Bearer <token>`

**Request:**
```json
{
    "current_file": {
        "file_name": "string",
        "content_above_cursor": "string",
        "content_below_cursor": ""
    },
    "context": [{
        "name": "string",
        "type": "snippet",
        "content": "string"
    }],
    "user_instruction": "string",
    "intent": "generation"
}
```

**Response:**
```json
{
    "choices": [{
        "text": "generated content",
        "index": 0,
        "finish_reason": "length"
    }],
    "metadata": {
        "model": {
            "engine": "agent",
            "name": "Code Generations Agent"
        }
    }
}
```

### 6.2 Ollama Embeddings

**Model:** `mxbai-embed-large`

**API Call:**
```python
ollama.embeddings(model="mxbai-embed-large", prompt=text)["embedding"]
```

**Vector Dimensions:** 1024 (typical for mxbai-embed-large)

### 6.3 ChromaDB Collections

| Collection            | Purpose                     | Document Format                         |
| --------------------- | --------------------------- | --------------------------------------- |
| `api_endpoints`       | Swagger endpoint embeddings | Resource, Endpoint, Actions, Parameters |
| `user_stories`        | User story embeddings       | Story text blocks                       |
| `conversation_memory` | Conversation history        | User/Agent exchanges                    |

---

## 7. Configuration

### 7.1 config.yaml

```yaml
# Agent Configuration
agent_type: "GITLAB_DUO"    # GITLAB_DUO or LOCAL
agent_mode: "ENABLED"       # ENABLED or DISABLED

# API Settings
timeout: 30

# UI Settings (for Playwright tests)
headless: false
slow_mo: 0
```

### 7.2 urls.yaml

```yaml
gitlab:
  base_url: "https://gitlab.com"

fakerestapi:
  base_url: "https://fakerestapi.azurewebsites.net"
```

### 7.3 Environment Variables (.env)

```bash
# GitLab Duo
GITLAB_PAT=glpat-xxxxxxxxxxxxxxxxxxxxxxx

# Ollama
LLAMA3_URL=http://localhost:11434
LLAMA3=llama3

# Database (for DB tests)
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=testdb
```

---

## 8. Logging & Observability

### 8.1 Log File Structure

**File:** `api_with_intent_logs.txt`

```
================================================================================
                        INTENT-BASED API EXECUTION LOG
================================================================================
Session Start: 2026-02-06 19:06:14

================================================================================

======================================...
[INTENT EXECUTION] Starting intent-based API execution
[INTENT] get book with id 1
[BASE URL] https://fakerestapi.azurewebsites.net
======================================...

================================================================================
[STEP 1] RAG - RETRIEVING SWAGGER CONTEXT
================================================================================
[RAG] Searching for endpoints matching intent: 'get book with id 1'
[[OK]] Found 1 matching endpoint(s)
  [1] Resource: Books
  [1] Endpoint: GET /api/v1/Books/{id}

--- SWAGGER CONTEXT RETRIEVED ---
Resource: Books
Endpoint: GET /api/v1/Books/{id}
...
--- END SWAGGER CONTEXT RETRIEVED ---

================================================================================
[STEP 2] GITLAB DUO - GENERATING CURL COMMAND
================================================================================
[Sending request to GitLab Duo...]

--- PROMPT TO GITLAB DUO ---
...prompt content...
--- END PROMPT ---

--- GITLAB DUO RESPONSE ---
curl -X GET "https://fakerestapi.azurewebsites.net/api/v1/Books/1" -H "Accept: application/json"
--- END RESPONSE ---

================================================================================
[STEP 3] EXECUTING CURL COMMAND
================================================================================
[Attempt 1/3]
[Executing command]: curl -X GET ...
[OK] Curl executed successfully!

--- CURL RESPONSE ---
HTTP Status Code: 200
Response Body:
{
  "id": 1,
  "title": "Book 1",
  ...
}
--- END CURL RESPONSE ---

================================================================================
[STEP 4] GITLAB DUO - ANALYZING RESPONSE
================================================================================
[Sending response to GitLab Duo for analysis...]

--- PROMPT TO GITLAB DUO ---
Analyze this API response and return ONLY a JSON object.
...
--- END PROMPT ---

--- GITLAB DUO RESPONSE ---
{"success": true, "reason": "Successfully retrieved book with id 1. Status 200 with valid JSON response."}
--- END RESPONSE ---

================================================================================
[STEP 5] PARSING AI ANALYSIS RESULT
================================================================================
[AI Analysis] Success: True
[AI Analysis] Reason: Successfully retrieved book with id 1...

================================================================================
                            EXECUTION SUMMARY
================================================================================
  Intent: get book with id 1
  Base URL: https://fakerestapi.azurewebsites.net
  Swagger Context Found: Yes (161 chars)
  Curl Command Generated: Yes
  HTTP Status Code: 200
  AI Analysis Result: PASS
  AI Analysis Reason: Successfully retrieved book...
================================================================================

Session End: 2026-02-06 19:06:32
Duration: 18.49 seconds
================================================================================
```

### 8.2 Console Output Levels

| Level   | Format              | Usage               |
| ------- | ------------------- | ------------------- |
| INFO    | `[INFO] message`    | General information |
| OK      | `[OK] message`      | Success indicators  |
| WARNING | `[WARNING] message` | Non-fatal issues    |
| ERROR   | `[ERROR] message`   | Errors and failures |
| DEBUG   | `[DEBUG] message`   | Debug information   |
| STEP    | `[STEP N] message`  | Execution steps     |

---

## 9. Test Implementation Guide

### 9.1 Writing Intent-Based Tests

```python
# Tests/API/test_api_agent.py

class TestIntentBasedAPI:
    """Test suite for Intent-Based API Execution."""
    
    BASE_URL = "https://fakerestapi.azurewebsites.net"
    
    def test_get_book_by_id(self, api_wrapper, api_context):
        """
        Test: Get a specific book by ID.
        Intent: "get book with id 1" -> GET /api/v1/Books/1
        
        The assertion is based on GitLab Duo's AI analysis.
        """
        result = api_wrapper.execute_by_intent(
            intent="get book with id 1",
            base_url=self.BASE_URL,
            rag_instance=api_context,
        )
        
        # Assert based on AI analysis
        assert result["success"], f"AI Analysis Failed: {result.get('reason', 'No reason')}"
        print(f"\n[TEST] PASSED - {result.get('reason', 'N/A')}")
```

### 9.2 Intent Examples

| Intent                            | HTTP Method | Endpoint         | Notes             |
| --------------------------------- | ----------- | ---------------- | ----------------- |
| "get all books"                   | GET         | /api/v1/Books    | Collection        |
| "get book with id 1"              | GET         | /api/v1/Books/1  | Single resource   |
| "delete book number 5"            | DELETE      | /api/v1/Books/5  | ID extraction     |
| "create a new book titled 'Test'" | POST        | /api/v1/Books    | Body construction |
| "update book 3 with new title"    | PUT         | /api/v1/Books/3  | Update with body  |
| "list all users"                  | GET         | /api/v1/Users    | Synonym handling  |
| "fetch user profile for id 10"    | GET         | /api/v1/Users/10 | Synonym handling  |

### 9.3 Fixtures Usage

```python
@pytest.fixture(scope="session")
def api_context():
    """Initialize RAG with embedded swagger."""
    from Libs.RAG import Rag
    
    rag = Rag()
    rag.embed_swagger_by_resource("swagger.json", collection_name="api_endpoints")
    builtins.RAG_INSTANCE = rag
    
    yield rag

@pytest.fixture(scope="session")
def api_wrapper(api_context):
    """Initialize API wrapper with RAG context."""
    from Logic.API.api_wrapper import APIWrapper
    
    wrapper = APIWrapper()
    yield wrapper
```

---

## 10. Error Handling & Retry Logic

### 10.1 Retry Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              RETRY FLOW                                              │
└─────────────────────────────────────────────────────────────────────────────────────┘

Attempt 1: Execute curl command
    │
    ├── Success (2xx) ──────────────────────────────────────▶ Analyze Response
    │
    └── Failure ──────────┐
                          │
                          ▼
            ┌─────────────────────────┐
            │  GitLab Duo: Fix Curl   │
            │  (with error context)   │
            └───────────┬─────────────┘
                        │
                        ▼
Attempt 2: Execute fixed curl command
    │
    ├── Success (2xx) ──────────────────────────────────────▶ Analyze Response
    │
    └── Failure ──────────┐
                          │
                          ▼
            ┌─────────────────────────┐
            │  GitLab Duo: Fix Curl   │
            │  (with error context)   │
            └───────────┬─────────────┘
                        │
                        ▼
Attempt 3 (final): Execute fixed curl command
    │
    ├── Success (2xx) ──────────────────────────────────────▶ Analyze Response
    │
    └── Failure ────────────────────────────────────────────▶ Return Error Result
```

### 10.2 Error Types Handled

| Error Type                 | Handling Strategy             |
| -------------------------- | ----------------------------- |
| Connection Error           | Retry with -k flag for SSL    |
| 404 Not Found              | Retry with corrected endpoint |
| 400 Bad Request            | Retry with fixed JSON body    |
| 415 Unsupported Media Type | Add Content-Type header       |
| JSON Parse Error           | Fix quote escaping            |
| Timeout                    | Extend timeout and retry      |

### 10.3 Curl Retry Prompt

```python
def get_curl_retry_prompt(intent, original_curl, error_output, swagger_context, base_url):
    """
    Generate prompt to fix failed curl command.
    
    Provides:
    - Original intent
    - Failed curl command
    - Error output
    - API documentation
    - Common fix suggestions
    """
```

---

## 11. Dependencies

### 11.1 Python Packages

```
# requirements.txt

# Core
requests>=2.28.0
pyyaml>=6.0
python-dotenv>=1.0.0
pytest>=7.4.0

# AI/ML
chromadb>=0.4.0
ollama>=0.1.0

# Utilities
numpy>=1.24.0
```

### 11.2 External Services

| Service    | Purpose                              | Required           |
| ---------- | ------------------------------------ | ------------------ |
| Ollama     | Local embeddings (mxbai-embed-large) | Yes                |
| GitLab Duo | LLM for curl generation/analysis     | Yes                |
| ChromaDB   | Vector database (local)              | Yes (auto-managed) |

### 11.3 Installation

```bash
# Create virtual environment
python -m venv ai-augmented-venv

# Activate (Windows PowerShell)
.\ai-augmented-venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Verify Ollama is running
ollama list

# Pull embedding model
ollama pull mxbai-embed-large
```

---

## 12. Future Enhancements

### 12.1 Planned Features

| Feature                                | Priority | Status  |
| -------------------------------------- | -------- | ------- |
| Multi-step API workflows               | High     | Planned |
| Request body validation against schema | Medium   | Planned |
| GraphQL support                        | Medium   | Planned |
| Custom assertion plugins               | Low      | Planned |
| Test data generation from schemas      | Low      | Planned |

### 12.2 Architecture Improvements

| Improvement     | Description                            |
| --------------- | -------------------------------------- |
| Async execution | Parallel API calls for performance     |
| Caching layer   | Cache embeddings and frequent queries  |
| Plugin system   | Extensible analyzers and generators    |
| Dashboard       | Real-time test execution visualization |

### 12.3 AI Enhancements

| Enhancement         | Description                              |
| ------------------- | ---------------------------------------- |
| Local LLM fallback  | Use local models when GitLab unavailable |
| Fine-tuned models   | Custom models for API testing domain     |
| Conversation memory | Multi-turn test conversations            |
| Self-healing tests  | Automatic test updates on API changes    |

---

## Appendix A: Prompt Templates

### A.1 Curl Generation Prompt

```
Your expertise: REST API integration, curl command generation.

📋 MISSION: Generate an executable curl command.

📥 INPUT DATA
🎯 USER INTENT: {intent}
🌐 BASE URL: {base_url}
📚 API DOCUMENTATION: {swagger_context}

⚡ RULES:
- Extract action: CREATE, READ, UPDATE, DELETE
- Map to HTTP method: GET, POST, PUT, DELETE
- Extract IDs and values from intent
- Single line, executable command
- NO explanations, NO markdown

🏁 GENERATE CURL COMMAND NOW
```

### A.2 Response Analysis Prompt

```
Analyze this API response and return ONLY a JSON object.

Intent: {intent}
Command: {curl_command}
Status: {status_code}
Response: {response_body}
Error: {stderr}

Rules:
- Status 2xx with valid data = success
- Status 4xx/5xx or error = failure
- Check if intent was fulfilled

Return ONLY this JSON format:
{"success": true, "reason": "explanation"}
or
{"success": false, "reason": "explanation"}

JSON result:
```

---

## Appendix B: Glossary

| Term                | Definition                                                           |
| ------------------- | -------------------------------------------------------------------- |
| **Intent**          | Natural language description of desired API action                   |
| **RAG**             | Retrieval-Augmented Generation - combining retrieval with generation |
| **ChromaDB**        | Open-source vector database for embeddings                           |
| **Ollama**          | Local LLM runtime for embeddings and inference                       |
| **GitLab Duo**      | GitLab's AI assistant with code completion capabilities              |
| **Swagger**         | OpenAPI specification format for REST APIs                           |
| **Embedding**       | Vector representation of text for semantic similarity                |
| **Semantic Search** | Finding similar content based on meaning, not keywords               |

---

## Appendix C: Troubleshooting

### C.1 Common Issues

| Issue                        | Cause                | Solution                                        |
| ---------------------------- | -------------------- | ----------------------------------------------- |
| "RAG instance not available" | Swagger not embedded | Ensure api_context fixture runs first           |
| "No matching endpoints"      | Intent doesn't match | Use keywords from swagger (get, create, delete) |
| Curl SSL error               | Certificate issues   | Framework auto-adds -k flag                     |
| Unicode errors in console    | Windows encoding     | Framework uses safe_print with error handling   |
| GitLab 401 Unauthorized      | Invalid token        | Check GITLAB_PAT in .env                        |
| Ollama connection refused    | Ollama not running   | Start Ollama: `ollama serve`                    |

### C.2 Debug Commands

```bash
# Check Ollama status
ollama list

# Test embedding
python -c "import ollama; print(ollama.embeddings(model='mxbai-embed-large', prompt='test'))"

# Check ChromaDB
python -c "from chromadb import PersistentClient; c = PersistentClient('./chroma_db'); print(c.list_collections())"

# Run single test with verbose output
pytest Tests/API/test_api_agent.py::TestIntentBasedAPI::test_get_book_by_id -v -s
```

---

**Document End**
