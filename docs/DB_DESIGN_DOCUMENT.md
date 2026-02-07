# AI-Augmented Database Testing Framework - Design Document

## 📋 Document Information

| Field              | Value                                                |
| ------------------ | ---------------------------------------------------- |
| **Document Title** | AI-Augmented E2E Framework - Database Testing Module |
| **Version**        | 2.0.0                                                |
| **Last Updated**   | February 7, 2026                                     |
| **Author**         | Framework Team                                       |
| **Status**         | Production Ready                                     |

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
11. [Learning System](#11-learning-system)
12. [Dependencies](#12-dependencies)
13. [Future Enhancements](#13-future-enhancements)

---

## 1. Executive Summary

### 1.1 Purpose

The AI-Augmented Database Testing Framework provides an innovative approach to database testing by leveraging:
- **Natural Language Processing (NLP)** for query intent interpretation
- **Retrieval-Augmented Generation (RAG)** for schema context retrieval
- **GitLab Duo AI** for intelligent SQL query generation and result analysis
- **Semantic Search** via ChromaDB for matching intents to table schemas
- **Learning System** for storing correct/incorrect queries for future improvement

### 1.2 Key Innovation

Traditional database testing requires explicit SQL queries, parameter binding, and assertion logic. This framework transforms the testing paradigm:

```
Traditional:        Intent: "test SELECT * FROM agents WHERE id = 5"
                    Code: cursor.execute("SELECT * FROM agents WHERE id = 5")
                    Assert: len(results) > 0

AI-Augmented:       Intent: "get agent with id 5"
                    Framework: Automatically generates SQL, executes, and validates
                    Assert: AI determines success based on semantic analysis
```

### 1.3 Key Features

| Feature                           | Description                                                 |
| --------------------------------- | ----------------------------------------------------------- |
| **Intent-Based Execution**        | Execute database queries using natural language             |
| **RAG-Powered Schema Context**    | Automatic schema retrieval with FK relationship grouping    |
| **TF-IDF Table Extraction**       | Extract table name from intent using TF-IDF + keyword match |
| **AI SQL Generation**             | GitLab Duo generates executable SQL queries                 |
| **AI Result Analysis**            | Intelligent success/failure determination                   |
| **Verification Intent Handling**  | Empty result = FAILURE for verify/check/confirm intents     |
| **Learning System**               | Stores correct/incorrect queries for continuous improvement |
| **Built-in Assertions**           | `assert_success` parameter auto-raises `AssertionError`     |
| **Auto-Retry with Error Context** | Failed queries are retried with error analysis              |
| **Comprehensive Logging**         | Beautiful step-by-step logging with full traceability       |

### 1.4 Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DB INTENT EXECUTION WORKFLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│   │  Fetch  │───▶│  Embed  │───▶│Retrieve │───▶│Generate │───▶│ Execute │  │
│   │ Schema  │    │   in    │    │ Context │    │  Query  │    │  Query  │  │
│   │         │    │   RAG   │    │         │    │         │    │         │  │
│   └─────────┘    └─────────┘    └─────────┘    └─────────┘    └────┬────┘  │
│                                                                      │       │
│                                                                      ▼       │
│   ┌─────────┐    ┌─────────┐                                 ┌─────────┐   │
│   │  Store  │◀───│ Analyze │◀────────────────────────────────│  Return │   │
│   │Learning │    │ Result  │                                 │ Result  │   │
│   │         │    │         │                                 │         │   │
│   └─────────┘    └─────────┘                                 └─────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. System Architecture

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         AI-AUGMENTED DATABASE TESTING FRAMEWORK                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────┐                                                               │
│  │   TEST LAYER     │   Tests/DB/test_db_agent.py                                   │
│  │   (Pytest)       │   - TestDBIntentExecution                                     │
│  │                  │   - Fixture: db_context                                       │
│  └────────┬─────────┘                                                               │
│           │                                                                          │
│           ▼                                                                          │
│  ┌──────────────────┐                                                               │
│  │  DB CONNECTOR    │   Utils/db_connector.py                                       │
│  │  (Orchestrator)  │   - execute_by_intent()                                       │
│  │                  │   - Coordinates all components                                │
│  └────────┬─────────┘                                                               │
│           │                                                                          │
│           ├────────────────────┬────────────────────┬───────────────────┐           │
│           ▼                    ▼                    ▼                   ▼           │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────┐   │
│  │   RAG ENGINE     │ │   AI AGENT       │ │   SQL EXECUTOR   │ │  LOGGER      │   │
│  │   (Libs/RAG.py)  │ │ (Utils/ai_agent) │ │   (MySQL)        │ │  (Utils/)    │   │
│  │                  │ │                  │ │                  │ │              │   │
│  │  - ChromaDB      │ │  - GitLab Duo    │ │  - mysql.conn    │ │  - Console   │   │
│  │  - Schema Embed  │ │  - Query Gen     │ │  - Dict cursor   │ │  - File      │   │
│  │  - Learning      │ │  - Analysis      │ │  - Retry Logic   │ │  - Unicode   │   │
│  │    Storage       │ │  - Retry Gen     │ │                  │ │    Safe      │   │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────┘   │
│           │                    │                    │                               │
│           ▼                    ▼                    ▼                               │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐                    │
│  │   CHROMA DB      │ │   GITLAB DUO     │ │    MySQL DB      │                    │
│  │  (Vector Store)  │ │   (LLM API)      │ │  (Target DB)     │                    │
│  │                  │ │                  │ │                  │                    │
│  │  ./chroma_db/    │ │  gitlab.com/api  │ │  testdb          │                    │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘                    │
│                                                                                      │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  EXTERNAL DEPENDENCIES                                                               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐         │
│  │    Ollama     │  │  GitLab Duo   │  │   ChromaDB    │  │    MySQL      │         │
│  │  (Embeddings) │  │    (LLM)      │  │ (Persistence) │  │  (Database)   │         │
│  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘         │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Interaction Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Pytest    │───▶│DBConnector  │───▶│  RAG Engine │───▶│  ChromaDB   │
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
                   │    SQL      │───▶│   MySQL     │
                   │  Executor   │    │  Database   │
                   └──────┬──────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐    ┌─────────────┐
                   │   Result    │───▶│  Learning   │
                   │  Analysis   │    │   Storage   │
                   └─────────────┘    └─────────────┘
```

---

## 3. Core Components

### 3.1 Component Overview

| Component           | File Path               | Primary Responsibility                            |
| ------------------- | ----------------------- | ------------------------------------------------- |
| **DBConnector**     | `Utils/db_connector.py` | Orchestrates intent-based database execution      |
| **RAG**             | `Libs/RAG.py`           | Vector embeddings, schema storage, and learning   |
| **AIAgent**         | `Utils/ai_agent.py`     | LLM communication for SQL generation and analysis |
| **IntentLogger**    | `Utils/logger.py`       | Dual console/file logging with Unicode safety     |
| **FrameworkLogger** | `Utils/logger.py`       | Static logging methods for framework-wide use     |
| **Prompts**         | `Resources/prompts.py`  | Prompt templates for GitLab Duo                   |
| **Fixtures**        | `conftest.py`           | Pytest fixtures for RAG and DB context            |

### 3.2 Directory Structure

```
ai-augmented-e2e-framework/
├── Libs/
│   └── RAG.py                    # RAG engine with ChromaDB + DB methods
├── Utils/
│   ├── db_connector.py           # Main DB connector with intent execution
│   ├── ai_agent.py               # AI agent for GitLab Duo communication
│   └── logger.py                 # Centralized logging
├── Resources/
│   ├── prompts.py                # Prompt templates (DB + API)
│   └── Constants.py              # API endpoints, headers, constants
├── Tests/
│   └── DB/
│       └── test_db_agent.py      # Intent-based DB tests
├── Config/
│   └── config.yaml               # Framework configuration
├── Test_Data/
│   ├── test_data.yaml            # Test data
│   └── urls.yaml                 # URL configurations
├── chroma_db/                    # ChromaDB persistence directory
├── conftest.py                   # Pytest fixtures (db_context)
├── .env                          # Environment variables
└── db_with_intent_logs.txt       # Intent execution logs
```

---

## 4. Data Flow & Sequence Diagrams

### 4.1 Intent-Based Database Execution Flow

```
┌─────────┐     ┌───────────────┐     ┌───────────┐     ┌──────────────┐
│  Test   │     │ DBConnector   │     │   RAG     │     │   ChromaDB   │
│ (User)  │     │               │     │           │     │              │
└────┬────┘     └───────┬───────┘     └─────┬─────┘     └──────┬───────┘
     │                  │                   │                  │
     │ execute_by_intent│                   │                  │
     │ ("get agents")   │                   │                  │
     │─────────────────▶│                   │                  │
     │                  │                   │                  │
     │                  │ retrieve_db_      │                  │
     │                  │ context_by_intent │                  │
     │                  │──────────────────▶│                  │
     │                  │                   │                  │
     │                  │                   │  query(intent)   │
     │                  │                   │─────────────────▶│
     │                  │                   │                  │
     │                  │                   │  schema_docs +   │
     │                  │                   │  learning_docs   │
     │                  │                   │◀─────────────────│
     │                  │                   │                  │
     │                  │  {schema_context, │                  │
     │                  │   correct_examples,│                 │
     │                  │   incorrect_examples}                │
     │                  │◀──────────────────│                  │
     │                  │                   │                  │
```

### 4.2 SQL Generation and Execution Flow

```
┌───────────────┐     ┌───────────┐     ┌──────────────┐     ┌─────────┐
│ DBConnector   │     │  AIAgent  │     │  GitLab Duo  │     │  MySQL  │
│               │     │           │     │              │     │         │
└───────┬───────┘     └─────┬─────┘     └──────┬───────┘     └────┬────┘
        │                   │                  │                  │
        │ generate_db_query │                  │                  │
        │──────────────────▶│                  │                  │
        │                   │                  │                  │
        │                   │  POST /code_     │                  │
        │                   │  suggestions     │                  │
        │                   │─────────────────▶│                  │
        │                   │                  │                  │
        │                   │  SQL Query       │                  │
        │                   │◀─────────────────│                  │
        │                   │                  │                  │
        │  "SELECT * FROM   │                  │                  │
        │   agents;"        │                  │                  │
        │◀──────────────────│                  │                  │
        │                   │                  │                  │
        │  execute_query()  │                  │                  │
        │─────────────────────────────────────────────────────────▶│
        │                   │                  │                  │
        │  [{id:1, name:...}│                  │                  │
        │   {id:2, name:...}]                  │                  │
        │◀─────────────────────────────────────────────────────────│
        │                   │                  │                  │
```

### 4.3 Result Analysis and Learning Flow

```
┌───────────────┐     ┌───────────┐     ┌──────────────┐     ┌───────────┐
│ DBConnector   │     │  AIAgent  │     │  GitLab Duo  │     │    RAG    │
│               │     │           │     │              │     │           │
└───────┬───────┘     └─────┬─────┘     └──────┬───────┘     └─────┬─────┘
        │                   │                  │                   │
        │ analyze_db_result │                  │                   │
        │──────────────────▶│                  │                   │
        │                   │                  │                   │
        │                   │  POST analysis   │                   │
        │                   │  prompt          │                   │
        │                   │─────────────────▶│                   │
        │                   │                  │                   │
        │                   │  {"success":true,│                   │
        │                   │   "reason":"..."}│                   │
        │                   │◀─────────────────│                   │
        │                   │                  │                   │
        │  {success: true,  │                  │                   │
        │   reason: "..."}  │                  │                   │
        │◀──────────────────│                  │                   │
        │                   │                  │                   │
        │  store_query_     │                  │                   │
        │  learning()       │                  │                   │
        │──────────────────────────────────────────────────────────▶│
        │                   │                  │                   │
        │                   │                  │  Stored as        │
        │                   │                  │  [correct] or     │
        │                   │                  │  [incorrect]      │
        │◀──────────────────────────────────────────────────────────│
        │                   │                  │                   │
```

---

## 5. Component Specifications

### 5.1 DBConnector Class

**Location:** `Utils/db_connector.py`

**Purpose:** Main orchestrator for intent-based database query execution.

```python
class DBConnector:
    """
    Database connector with intent-based query execution.
    
    Properties:
        ai_agent: Lazy-loaded AIAgent with APIWrapper
        rag_instance: RAG instance from builtins (set by fixture)
    
    Methods:
        connect(): Establish database connection
        execute_query(query): Execute raw SQL query
        execute_by_intent(intent, max_retries, log_intent, assert_success): Execute query based on natural language
        close(): Close database connection
    """
```

**Key Methods:**

| Method                                                               | Description                                    |
| -------------------------------------------------------------------- | ---------------------------------------------- |
| `execute_by_intent(intent, max_retries, log_intent, assert_success)` | Main orchestrator - generates and executes SQL |
| `_clean_sql_query(query)`                                            | Removes markdown/code blocks from AI response  |
| `_extract_tables_from_query(query)`                                  | Extracts table names for learning storage      |
| `get_table_schema(table_name)`                                       | Gets column definitions via DESCRIBE           |
| `get_all_tables()`                                                   | Gets all table names via SHOW TABLES           |
| `get_foreign_keys(table_name)`                                       | Gets FK relationships from INFORMATION_SCHEMA  |

### 5.2 RAG Class - DB Methods

**Location:** `Libs/RAG.py`

**Purpose:** Schema embedding, context retrieval, and learning storage.

**DB-Specific Methods:**

| Method                                             | Description                                    |
| -------------------------------------------------- | ---------------------------------------------- |
| `embed_db_schema(schema_data, ...)`                | Embeds table schemas with FK relationships     |
| `retrieve_db_context_by_intent(intent)`            | Retrieves schema + learning examples by intent |
| `_rag_extract_table_from_schema_by_intent(intent)` | TF-IDF + keyword hybrid table extraction       |
| `_rag_extract_table_from_intent_keywords(intent)`  | Keyword-based table name matching              |
| `store_query_learning(intent, query, ...)`         | Stores query as correct/incorrect for learning |
| `_group_tables_by_fk(schema_data, rels)`           | Groups related tables by foreign keys          |
| `_format_table_group_for_embedding(...)`           | Formats table group as embeddable document     |

### 5.3 AIAgent Class - DB Methods

**Location:** `Utils/ai_agent.py`

**Purpose:** GitLab Duo communication for SQL generation and analysis.

**DB-Specific Methods:**

| Method                                      | Description                                      |
| ------------------------------------------- | ------------------------------------------------ |
| `generate_db_query(intent, schema, ...)`    | Generates SQL query from intent using GitLab Duo |
| `analyze_db_result(intent, query, result)`  | Analyzes query result for success/failure        |
| `retry_db_query(intent, query, error, ...)` | Regenerates SQL after execution failure          |

---

## 6. API Reference

### 6.1 execute_by_intent() - Multi-Layer Document Flow

**Signature:**
```python
def execute_by_intent(
    self,
    intent: str,
    max_retries: int = 2,
    log_intent: bool = True,
    assert_success: bool = True  # NEW: Built-in assertions
) -> dict
```

**Multi-Layer Document Flow:**
```
1. TF-IDF: Search schema doc by intent → extract table name
2. RAG: Retrieve stored action from db_learning collection (by table)
3. DUO: Send BOTH schema_context AND stored_metadata to generate query
4. EXECUTE: Run the generated SQL query
5. ANALYZE: AI analyzes the result
6. STORE: Store action with [correct]/[incorrect] status
7. ASSERT: Optionally raise AssertionError if AI analysis fails
```

**Parameters:**

| Parameter        | Type | Default | Description                                           |
| ---------------- | ---- | ------- | ----------------------------------------------------- |
| `intent`         | str  | -       | Natural language description of the query             |
| `max_retries`    | int  | 2       | Maximum retry attempts on failure                     |
| `log_intent`     | bool | True    | Whether to log detailed execution steps               |
| `assert_success` | bool | True    | If True, raises AssertionError when AI analysis fails |

**Returns:**
```python
{
    "success": bool,          # Whether the query met the intent
    "reason": str,            # AI analysis explanation
    "data": list or None,     # Query results as list of dicts
    "query": str,             # Generated SQL query
    "error": str or None      # Error message if failed
}
```

**Raises:**
- `AssertionError`: If `assert_success=True` and AI analysis indicates failure

### 6.2 TF-IDF Table Extraction

The system uses a **hybrid approach** to extract the table name from the intent:

```python
# Step 1: Keyword extraction (prioritized)
# Looks for patterns like "verify that agents table", "from the agents table"
table = rag._extract_table_from_intent_keywords(intent)

# Step 2: ChromaDB semantic search (fallback)
if not table:
    results = rag.db_context_collection.query(query_texts=[intent], n_results=1)
    table = results["metadatas"][0][0].get("table_name")
```

**Keyword Patterns Matched:**
- `"from the {table} table"` / `"in the {table} table"`
- `"verify that {table} table"` / `"check the {table} table"`
- `"the {table} contains"` / `"{table} has"`
- Direct table name match against schema collection

### 6.3 Verification Intent Handling

The AI analysis prompt now correctly handles **verification intents**:

```python
# Intent: "verify that Reumaysa email domain is yahoo"
# Query: SELECT email FROM agents WHERE name = 'Reumaysa' AND email LIKE '%@yahoo%'
# Result: [] (empty)

# AI Analysis Rules:
# - Intent contains "verify" → empty result = FAILURE
# - "Reumaysa's email does NOT have yahoo domain"

# CRITICAL RULES in prompt:
# - If intent contains "verify", "check", "confirm", "ensure", "validate":
#   - Empty result [] = FAILURE (verification failed)
#   - Non-empty result with matching data = SUCCESS
```

### 6.4 Built-in Assertions (`assert_success` Parameter)

```python
# Normal test - auto-raises AssertionError on failure
def test_verify_agent_exists(self, db_context):
    db_context.execute_by_intent(
        intent="verify that John is one of the agents"
    )  # Automatically fails if no agent named John

# Negative test - no assertion, returns result for inspection
def test_verify_nonexistent_agent(self, db_context):
    result = db_context.execute_by_intent(
        intent="verify that NonExistent is one of the agents",
        assert_success=False
    )
    assert result["success"] == False  # Manual assertion for negative test
    assert "not found" in result["reason"].lower()
```

**Example:**
```python
result = db_context.execute_by_intent(
    intent="Get all agents from the database"
)

assert result["success"], f"AI Analysis Failed: {result.get('reason')}"
print(f"Found {len(result['data'])} agents")
```

### 6.2 retrieve_db_context_by_intent()

**Signature:**
```python
def retrieve_db_context_by_intent(
    self,
    intent: str,
    collection_name: str = "db_context",
    n_results: int = 5
) -> dict
```

**Returns:**
```python
{
    "schema_context": str,       # Relevant table schemas
    "correct_examples": str,     # Previously successful queries
    "incorrect_examples": str    # Previously failed queries to avoid
}
```

### 6.3 store_query_learning()

**Signature:**
```python
def store_query_learning(
    self,
    intent: str,
    query: str,
    tables_used: list,
    is_correct: bool,
    error_message: str = None,
    collection_name: str = "db_context"
) -> str  # Returns document ID
```

---

## 7. Configuration

### 7.1 Environment Variables (.env)

```bash
# Database Configuration (defaults in db_connector.py)
# DB_HOST=127.0.0.1
# DB_PORT=3306
# DB_USER=root
# DB_PASSWORD=22132213
# DB_NAME=testdb

# Schema Refresh Flags
REFRESH_API_SCHEMA=false    # Set true to re-embed swagger on each run
REFRESH_DB_SCHEMA=false     # Set true to re-embed schema on each run

# GitLab Duo Configuration
GITLAB_TOKEN=glpat-xxxxx    # GitLab personal access token

# Ollama Configuration
LLAMA3=llama3.1:latest
LLAMA3_URL=http://127.0.0.1:2213
```

### 7.2 ChromaDB Collection Structure

**Collection Name:** `db_context`

**Document Types:**

| Type       | Metadata Filter    | Content                                   |
| ---------- | ------------------ | ----------------------------------------- |
| `schema`   | `type: "schema"`   | Table definitions with columns and FKs    |
| `learning` | `type: "learning"` | Query examples with [correct]/[incorrect] |

**Schema Document Metadata:**
```python
{
    "type": "schema",
    "tables": '["agents", "actions"]',  # JSON array
    "has_relationships": True,
    "table_count": 2
}
```

**Learning Document Metadata:**
```python
{
    "type": "learning",
    "status": "correct",  # or "incorrect"
    "intent": "get all agents...",
    "query": "SELECT * FROM agents;",
    "tables_used": '["agents"]'
}
```

---

## 8. Logging & Observability

### 8.1 Log Output Format

The framework provides beautiful, step-by-step logging:

```
======================================================================
  DB INTENT-BASED QUERY EXECUTION
======================================================================
  Intent: Get all agents from the database
======================================================================

----------------------------------------------------------------------
  STEP 1: Retrieving Context from RAG
----------------------------------------------------------------------
  Schema Context:      450 characters
  Correct Examples:    2 characters
  Incorrect Examples:  0 characters

----------------------------------------------------------------------
  STEP 2: Generating SQL Query with GitLab Duo
----------------------------------------------------------------------
  Generated Query:
  >>> SELECT * FROM agents;

----------------------------------------------------------------------
  STEP 3: Executing Query
----------------------------------------------------------------------
  [OK] Query executed successfully
  Rows Returned: 13
  Sample Row: {'id': 1, 'name': 'John Doe', ...}

----------------------------------------------------------------------
  STEP 4: Analyzing Result with GitLab Duo
----------------------------------------------------------------------
  AI Analysis Result: PASS
  AI Reason: Query executed successfully and returned all agent records

----------------------------------------------------------------------
  STEP 5: Storing Query in Learning Collection
----------------------------------------------------------------------
  Status: [CORRECT]
  Tables Used: ['agents']
  Stored for future learning

======================================================================
  FINAL RESULT: SUCCESS
======================================================================
  Success: True
  Reason:  Query executed successfully and returned all agent records
  Query:   SELECT * FROM agents;
  Rows:    13
======================================================================
```

### 8.2 Log File Location

Logs are written to: `db_with_intent_logs.txt`

---

## 9. Test Implementation Guide

### 9.1 Basic Test Structure

```python
import pytest

class TestDBIntentExecution:
    """
    Test class for intent-based database query execution.
    Uses the db_context fixture which:
    - Embeds database schema into ChromaDB
    - Provides DBConnector with execute_by_intent() method
    - Stores query results for learning
    """

    @pytest.mark.db_intent
    def test_get_all_agents(self, db_context):
        """Test: Get all agents from the database."""
        result = db_context.execute_by_intent(
            intent="Get all agents from the database"
        )
        
        # Assert based on AI analysis result
        assert result["success"], \
            f"AI Analysis Failed: {result.get('reason', 'No reason provided')}"
        
        print(f"\n[TEST] Get all agents - PASSED")
        print(f"[AI Analysis] {result.get('reason', 'N/A')}")
```

### 9.2 Test Examples by Query Type

**Simple SELECT:**
```python
def test_get_all_records(self, db_context):
    result = db_context.execute_by_intent(
        intent="Get all agents from the database"
    )
    assert result["success"]
```

**Filtered SELECT:**
```python
def test_get_agent_by_id(self, db_context):
    result = db_context.execute_by_intent(
        intent="Get the agent with id 5"
    )
    assert result["success"]
```

**JOIN Query:**
```python
def test_get_agents_with_actions(self, db_context):
    result = db_context.execute_by_intent(
        intent="Get all agents along with their actions"
    )
    assert result["success"]
```

**Aggregation:**
```python
def test_count_agents(self, db_context):
    result = db_context.execute_by_intent(
        intent="Count the total number of agents"
    )
    assert result["success"]
```

**Validation Query:**
```python
def test_verify_agent_exists(self, db_context):
    result = db_context.execute_by_intent(
        intent="Verify that agent 'John Doe' exists in the database"
    )
    assert result["success"]
```

### 9.3 Fixture Usage

The `db_context` fixture is defined in `conftest.py`:

```python
@pytest.fixture(scope="session")
def db_context():
    """
    Session-scoped fixture for DB intent execution.
    
    - Initializes RAG for DB context
    - Embeds database schema (respects REFRESH_DB_SCHEMA flag)
    - Returns DBConnector with execute_by_intent() method
    """
    from Libs.RAG import Rag
    
    rag = Rag()
    db = DBConnector()
    db.connect()
    
    # Embed schema based on refresh flag
    refresh = os.getenv("REFRESH_DB_SCHEMA", "false").lower() == "true"
    
    # ... schema embedding logic ...
    
    builtins.RAG_DB_INSTANCE = rag
    db._rag_instance = rag
    
    yield db
    
    db.close()
```

---

## 10. Error Handling & Retry Logic

### 10.1 Retry Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RETRY LOGIC FLOW                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────┐                                                   │
│   │  Generate   │                                                   │
│   │   Query     │                                                   │
│   └──────┬──────┘                                                   │
│          │                                                           │
│          ▼                                                           │
│   ┌─────────────┐     ┌─────────────┐                               │
│   │  Execute    │────▶│  Success?   │────▶ YES ────▶ Continue       │
│   │   Query     │     └──────┬──────┘                               │
│   └─────────────┘            │                                       │
│                              NO                                      │
│                              │                                       │
│                              ▼                                       │
│                       ┌─────────────┐                               │
│                       │  Attempt <  │────▶ NO ────▶ Return Error    │
│                       │  max_retry? │                               │
│                       └──────┬──────┘                               │
│                              │                                       │
│                             YES                                      │
│                              │                                       │
│                              ▼                                       │
│                       ┌─────────────┐                               │
│                       │  Retry with │                               │
│                       │  Error Ctx  │──────────────────▶ Loop       │
│                       └─────────────┘                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 10.2 Error Types Handled

| Error Type        | Handling Strategy                  |
| ----------------- | ---------------------------------- |
| SQL Syntax Error  | Retry with error context in prompt |
| Table Not Found   | Retry with schema context          |
| Column Not Found  | Retry with full table definitions  |
| Connection Error  | Reconnect and retry                |
| AI Response Parse | Fallback to default analysis       |

---

## 11. Learning System

### 11.1 How Learning Works

The framework implements a **continuous learning system**:

1. **Execution**: Query is generated and executed
2. **Analysis**: AI determines if result matches intent
3. **Storage**: Query is stored as `[correct]` or `[incorrect]`
4. **Retrieval**: Future similar intents retrieve these examples
5. **Improvement**: AI learns from past successes and failures

### 11.2 Learning Document Format

**Correct Example:**
```
[correct]
Intent: Get all agents from the database
Query: SELECT * FROM agents;
Tables: agents
```

**Incorrect Example:**
```
[incorrect]
Intent: Get all agents from the database And Make sure Rowen is there
Query: SELECT * FROM agents WHERE name = 'Rowen' OR 1=1;
Tables: agents
Error: Query used SQL injection and returned all agents instead of checking for Rowen
```

### 11.3 Learning Benefits

| Benefit                 | Description                                         |
| ----------------------- | --------------------------------------------------- |
| **Pattern Recognition** | AI learns successful query patterns                 |
| **Error Avoidance**     | AI avoids patterns that previously failed           |
| **Context Improvement** | More examples = better query generation             |
| **Self-Healing**        | Framework improves over time without manual updates |

---

## 12. Dependencies

### 12.1 Python Packages

| Package                  | Version | Purpose                         |
| ------------------------ | ------- | ------------------------------- |
| `mysql-connector-python` | 8.x     | MySQL database connectivity     |
| `chromadb`               | 0.4.x   | Vector database for embeddings  |
| `ollama`                 | 0.1.x   | Embedding model interface       |
| `requests`               | 2.x     | HTTP client for GitLab Duo API  |
| `pytest`                 | 7.x     | Test framework                  |
| `python-dotenv`          | 1.x     | Environment variable management |
| `pyyaml`                 | 6.x     | YAML configuration parsing      |

### 12.2 External Services

| Service        | Purpose                                   | Configuration          |
| -------------- | ----------------------------------------- | ---------------------- |
| **Ollama**     | Local embedding model (mxbai-embed-large) | `LLAMA3_URL` in .env   |
| **GitLab Duo** | LLM for SQL generation and analysis       | `GITLAB_TOKEN` in .env |
| **MySQL**      | Target database for query execution       | db_connector defaults  |
| **ChromaDB**   | Vector storage for schema and learning    | `./chroma_db/` folder  |

---

## 13. Future Enhancements

### 13.1 Planned Features

| Feature                     | Priority | Description                                      |
| --------------------------- | -------- | ------------------------------------------------ |
| **Multi-DB Support**        | High     | Support for PostgreSQL, SQLite, Oracle           |
| **Query Optimization**      | Medium   | AI-suggested query performance improvements      |
| **Schema Change Detection** | Medium   | Auto-detect and re-embed schema changes          |
| **Transaction Support**     | Medium   | Support for INSERT, UPDATE, DELETE with rollback |
| **Parallel Execution**      | Low      | Run multiple intents in parallel                 |
| **Query Caching**           | Low      | Cache frequently used queries                    |

### 13.2 Architecture Evolution

```
Future State:
┌─────────────────────────────────────────────────────────────────────┐
│                    MULTI-DATABASE SUPPORT                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────────────┐                                              │
│   │   DB CONNECTOR   │                                              │
│   │   FACTORY        │                                              │
│   └────────┬─────────┘                                              │
│            │                                                         │
│   ┌────────┼────────┬────────────┬────────────┐                     │
│   ▼        ▼        ▼            ▼            ▼                     │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐ ┌──────────┐               │
│ │MySQL │ │Postgres│ │SQLite│ │  Oracle  │ │  MSSQL   │               │
│ │Conn  │ │  Conn │ │ Conn │ │   Conn   │ │   Conn   │               │
│ └──────┘ └──────┘ └──────┘ └──────────┘ └──────────┘               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Appendix A: Sample Execution Log

```
======================================================================
  DB INTENT-BASED QUERY EXECUTION
======================================================================
  Intent: Get all agents from the database
======================================================================

----------------------------------------------------------------------
  STEP 1: Retrieving Context from RAG
----------------------------------------------------------------------
  [RAG] Retrieving DB context for intent: 'Get all agents from the database'
  [Info] Collection has 4 documents
  [[OK]] Found 2 schema document(s)
  [[OK]] Found 2 correct example(s)
  [[OK]] Found 0 incorrect example(s)
  Schema Context:      450 characters
  Correct Examples:    2 characters
  Incorrect Examples:  0 characters

----------------------------------------------------------------------
  STEP 2: Generating SQL Query with GitLab Duo
----------------------------------------------------------------------
  Making AI Agent request with scenario: success
  Making POST request to: https://gitlab.com/api/v4/code_suggestions/completions
  Response Status: 200
  Generated Query:
  >>> SELECT * FROM agents;

----------------------------------------------------------------------
  STEP 3: Executing Query
----------------------------------------------------------------------
  [OK] Query executed successfully
  Rows Returned: 13
  Sample Row: {'id': 1, 'name': 'John Doe', 'phoneno': '1234567890', 
               'email': 'john.doe@example.com', 'address': '123 Main St'}

----------------------------------------------------------------------
  STEP 4: Analyzing Result with GitLab Duo
----------------------------------------------------------------------
  Making AI Agent request with scenario: success
  Response Status: 200
  AI Analysis Result: PASS
  AI Reason: Query executed successfully and returned all agent records 
             from the database, matching the intent to get all agents

----------------------------------------------------------------------
  STEP 5: Storing Query in Learning Collection
----------------------------------------------------------------------
  [Learning] Storing query result...
  Intent: Get all agents from the database...
  Status: [correct]
  [[OK]] Stored learning document: learning_de2f8bf3ce19
  Status: [CORRECT]
  Tables Used: ['agents']
  Stored for future learning

======================================================================
  FINAL RESULT: SUCCESS
======================================================================
  Success: True
  Reason:  Query executed successfully and returned all agent records
  Query:   SELECT * FROM agents;
  Rows:    13
======================================================================

[TEST] Get all agents - PASSED
[AI Analysis] Query executed successfully and returned all agent records
```

---

## Appendix B: Comparison with API Framework

| Aspect               | API Framework        | DB Framework               |
| -------------------- | -------------------- | -------------------------- |
| **Input**            | Swagger/OpenAPI spec | Database schema (DESCRIBE) |
| **Generation**       | curl commands        | SQL queries                |
| **Execution**        | subprocess curl      | mysql-connector execute    |
| **Context Source**   | swagger.json         | INFORMATION_SCHEMA         |
| **Learning Storage** | Not implemented      | Correct/Incorrect queries  |
| **Result Format**    | HTTP status + body   | List of dictionaries       |
| **Retry Trigger**    | HTTP error/status    | SQL execution error        |
| **Collection Name**  | api_endpoints        | db_context                 |
| **Refresh Flag**     | REFRESH_API_SCHEMA   | REFRESH_DB_SCHEMA          |

---

*Document End*
