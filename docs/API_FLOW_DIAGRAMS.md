# API Module Flow Diagrams

This document contains flow diagrams describing all execution flows for the API testing module.

---

## 1. Main API Intent Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        API INTENT EXECUTION FLOW                            │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  User Intent │
                              │  (Natural    │
                              │   Language)  │
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  STEP 1: Extract      │
                         │  Resource from Intent │
                         │  (e.g., "books",      │
                         │   "users", "orders")  │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  STEP 2: Query        │
                         │  ChromaDB for Stored  │
                         │  API Action           │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  STEP 3: Get Swagger  │
                         │  Context from RAG     │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  STEP 4: AI Generates │
                         │  API Action Metadata  │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  STEP 5: Execute      │
                         │  cURL Command         │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  STEP 6: Store Result │
                         │  in Learning DB       │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  STEP 7: AI Analyzes  │
                         │  Response             │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  STEP 8: Parse        │
                         │  Analysis & Return    │
                         └───────────────────────┘
```

---

## 2. Resource Extraction Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       RESOURCE EXTRACTION FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  User Intent │
                              │  "get all    │
                              │   books"     │
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Query Swagger        │
                         │  Endpoints Collection │
                         │  in ChromaDB          │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Semantic Search      │
                         │  Returns Matching     │
                         │  Endpoints            │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Extract:             │
                         │  • Resource: "Books"  │
                         │  • Method: GET        │
                         │  • Endpoint Pattern:  │
                         │    /api/v1/Books      │
                         └───────────────────────┘
```

---

## 3. ChromaDB API Learning Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CHROMADB API LEARNING FLOW                            │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  Intent +    │
                              │  Resource    │
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Query api_learning   │
                         │  Collection           │
                         │  WHERE:               │
                         │  • endpoint_pattern   │
                         │  • status = [correct] │
                         └───────────┬───────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
        ┌───────────────────┐             ┌───────────────────┐
        │  [correct] Action │             │  No Match Found   │
        │     FOUND         │             │  or [incorrect]   │
        └─────────┬─────────┘             └─────────┬─────────┘
                  │                                 │
                  ▼                                 ▼
        ┌───────────────────┐             ┌───────────────────┐
        │  Use as Reference │             │  Generate New     │
        │  for AI:          │             │  Action from      │
        │  • cURL template  │             │  Swagger Context  │
        │  • Expected status│             │                   │
        │  • Request body   │             │                   │
        └───────────────────┘             └───────────────────┘
```

---

## 4. Swagger Context Retrieval Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SWAGGER CONTEXT RETRIEVAL FLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   Resource   │
                              │   "Books"    │
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Query api_endpoints  │
                         │  Collection           │
                         │  (Embedded Swagger)   │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Returns Swagger      │
                         │  Context:             │
                         │  ─────────────────────│
                         │  Resource: Books      │
                         │  Endpoint: GET /api/  │
                         │    v1/Books           │
                         │  Actions: get all,    │
                         │    list, fetch...     │
                         │  ResponseCodes: 200   │
                         └───────────────────────┘
```

---

## 5. AI Action Metadata Generation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   AI ACTION METADATA GENERATION FLOW                        │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │            INPUT TO AI              │
                    │  ─────────────────────────────────  │
                    │  • Intent                           │
                    │  • Resource                         │
                    │  • Base URL                         │
                    │  • Stored Action (if any)           │
                    │  • Swagger Context                  │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                         ┌───────────────────────┐
                         │  Send Prompt to       │
                         │  GitLab Duo / AI      │
                         └───────────┬───────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────────┐
                    │          AI GENERATES               │
                    │  ─────────────────────────────────  │
                    │  {                                  │
                    │    "action_key": "get_all_books",   │
                    │    "intent": "get all books",       │
                    │    "resource": "Books",             │
                    │    "method": "GET",                 │
                    │    "endpoint": "/api/v1/Books",     │
                    │    "curl": "curl -X GET '...'",     │
                    │    "expected_status": 200,          │
                    │    "request_body": {},              │
                    │    "headers": {...}                 │
                    │  }                                  │
                    └─────────────────────────────────────┘
```

---

## 6. cURL Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          cURL EXECUTION FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  cURL        │
                              │  Command     │
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Clean cURL Command   │
                         │  (Remove markdown,    │
                         │   fix escaping)       │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Execute via          │
                         │  subprocess           │
                         │  (with timeout)       │
                         └───────────┬───────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
        ┌───────────────────┐             ┌───────────────────┐
        │  Attempt 1        │             │  FAILED           │
        │  SUCCESS          │             │                   │
        └─────────┬─────────┘             └─────────┬─────────┘
                  │                                 │
                  │                    ┌────────────┴────────────┐
                  │                    │                         │
                  │                    ▼                         ▼
                  │          ┌───────────────────┐     ┌───────────────────┐
                  │          │  Retry Attempt 2  │     │  Retry Attempt 3  │
                  │          └─────────┬─────────┘     └─────────┬─────────┘
                  │                    │                         │
                  └────────────────────┼─────────────────────────┘
                                       │
                                       ▼
                         ┌───────────────────────┐
                         │  Parse Response:      │
                         │  • HTTP Status Code   │
                         │  • Response Body      │
                         │  • stderr (errors)    │
                         └───────────────────────┘
```

---

## 7. Learning Storage Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LEARNING STORAGE FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  API Call    │
                              │  Completed   │
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Compare Status:      │
                         │  actual vs expected   │
                         └───────────┬───────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
        ┌───────────────────┐             ┌───────────────────┐
        │  Status Matches   │             │  Status Mismatch  │
        │  (e.g., 200=200)  │             │  (e.g., 404≠200)  │
        └─────────┬─────────┘             └─────────┬─────────┘
                  │                                 │
                  ▼                                 ▼
        ┌───────────────────┐             ┌───────────────────┐
        │  Status: [correct]│             │  Status:[incorrect]
        └─────────┬─────────┘             └─────────┬─────────┘
                  │                                 │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │         STORE IN CHROMADB           │
                    │  ─────────────────────────────────  │
                    │  Document:                          │
                    │  • endpoint_pattern                 │
                    │  • sample_intent                    │
                    │  • resource                         │
                    │  • method                           │
                    │  • endpoint                         │
                    │  • curl                             │
                    │  • expected_status                  │
                    │  • actual_status                    │
                    │  • request_body                     │
                    │  • response_body (truncated)        │
                    │  • base_url                         │
                    │  • status: [correct]/[incorrect]    │
                    └─────────────────────────────────────┘
```

---

## 8. Response Analysis Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RESPONSE ANALYSIS FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │          INPUT TO AI                │
                    │  ─────────────────────────────────  │
                    │  • User Intent                      │
                    │  • cURL Command                     │
                    │  • HTTP Status Code                 │
                    │  • Response Body                    │
                    │  • Error (if any)                   │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                         ┌───────────────────────┐
                         │  Send Analysis        │
                         │  Prompt to AI         │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  AI Evaluates:        │
                         │  1. Status 2xx?       │
                         │  2. Data matches      │
                         │     intent?           │
                         │  3. Verification      │
                         │     requirements met? │
                         └───────────┬───────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────────┐
                    │          AI RETURNS                 │
                    │  ─────────────────────────────────  │
                    │  {                                  │
                    │    "success": true/false,           │
                    │    "reason": "Analysis of the       │
                    │               response..."          │
                    │  }                                  │
                    └─────────────────────────────────────┘
```

---

## 9. HTTP Method Decision Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HTTP METHOD DECISION FLOW                            │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  User Intent │
                              └──────┬───────┘
                                     │
         ┌───────────┬───────────┬───┴───┬───────────┬───────────┐
         │           │           │       │           │           │
         ▼           ▼           ▼       ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │  "get"  │ │"create" │ │"update" │ │"delete" │ │"modify" │ │"replace"│
    │  "list" │ │ "add"   │ │"change" │ │"remove" │ │"patch"  │ │  "set"  │
    │ "fetch" │ │ "new"   │ │         │ │         │ │         │ │         │
    └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
         │           │           │           │           │           │
         ▼           ▼           ▼           ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │   GET   │ │  POST   │ │   PUT   │ │ DELETE  │ │  PATCH  │ │   PUT   │
    └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

---

## 10. Full API Execution Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FULL API EXECUTION PIPELINE                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: EXTRACT ENDPOINT                                                     │
│ ┌────────────┐    ┌────────────┐    ┌────────────┐                          │
│ │   Intent   │───▶│  Swagger   │───▶│  Resource  │                          │
│ │            │    │   RAG      │    │  Endpoint  │                          │
│ └────────────┘    └────────────┘    └────────────┘                          │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: CHECK LEARNING DATABASE                                              │
│ ┌────────────┐    ┌────────────┐    ┌────────────┐                          │
│ │ Endpoint   │───▶│  ChromaDB  │───▶│  Stored    │                          │
│ │ Pattern    │    │   Query    │    │  Action?   │                          │
│ └────────────┘    └────────────┘    └────────────┘                          │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: GET SWAGGER CONTEXT                                                  │
│ ┌────────────┐    ┌────────────┐    ┌────────────┐                          │
│ │  Resource  │───▶│  Swagger   │───▶│  Endpoint  │                          │
│ │   Name     │    │  Embedded  │    │  Details   │                          │
│ └────────────┘    └────────────┘    └────────────┘                          │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: AI GENERATES ACTION METADATA                                         │
│ ┌────────────┐    ┌────────────┐    ┌────────────┐                          │
│ │ Context +  │───▶│  GitLab    │───▶│  Action    │                          │
│ │ Intent     │    │   Duo      │    │  Metadata  │                          │
│ └────────────┘    └────────────┘    └────────────┘                          │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: EXECUTE cURL COMMAND                                                 │
│ ┌────────────┐    ┌────────────┐    ┌────────────┐                          │
│ │   cURL     │───▶│ subprocess │───▶│  Response  │                          │
│ │  Command   │    │   exec     │    │   Body     │                          │
│ └────────────┘    └────────────┘    └────────────┘                          │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: STORE IN LEARNING DATABASE                                           │
│ ┌────────────┐    ┌────────────┐    ┌────────────┐                          │
│ │  Result    │───▶│  ChromaDB  │───▶│ [correct]  │                          │
│ │            │    │  Upsert    │    │[incorrect] │                          │
│ └────────────┘    └────────────┘    └────────────┘                          │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 7: AI ANALYZES RESPONSE                                                 │
│ ┌────────────┐    ┌────────────┐    ┌────────────┐                          │
│ │ Intent +   │───▶│  GitLab    │───▶│  Analysis  │                          │
│ │ Response   │    │   Duo      │    │   Result   │                          │
│ └────────────┘    └────────────┘    └────────────┘                          │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 8: PARSE ANALYSIS & RETURN                                              │
│ ┌────────────┐    ┌────────────┐    ┌────────────┐                          │
│ │  AI JSON   │───▶│  Extract   │───▶│  Final     │                          │
│ │  Response  │    │  success/  │    │  Result    │                          │
│ │            │    │  reason    │    │            │                          │
│ └────────────┘    └────────────┘    └────────────┘                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Swagger Embedding Flow (Initialization)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SWAGGER EMBEDDING FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │ swagger.json │
                              │    File      │
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Parse Swagger JSON   │
                         │  Extract Paths        │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Group by Resource    │
                         │  (e.g., /Books,       │
                         │   /Users, /Orders)    │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  For Each Resource:   │
                         │  Create Document with │
                         │  • Resource name      │
                         │  • Endpoints          │
                         │  • Methods            │
                         │  • Parameters         │
                         │  • Response codes     │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Embed Documents in   │
                         │  ChromaDB Collection  │
                         │  "api_endpoints"      │
                         └───────────────────────┘
```

---

## Summary of API Flows

| Flow                | Description                                  |
| ------------------- | -------------------------------------------- |
| Main Execution      | 8-step pipeline from intent to result        |
| Resource Extraction | Semantic search in Swagger to find endpoint  |
| ChromaDB Learning   | Query and store API actions with status      |
| Swagger Context     | Retrieve endpoint details from embedded docs |
| AI Generation       | Generate action metadata with cURL command   |
| cURL Execution      | Execute HTTP request with retry logic        |
| Learning Storage    | Store success/failure for future reference   |
| Response Analysis   | AI evaluates if intent was fulfilled         |
| HTTP Methods        | Map intent verbs to HTTP methods             |
| Swagger Embedding   | Initialize by embedding Swagger spec         |
