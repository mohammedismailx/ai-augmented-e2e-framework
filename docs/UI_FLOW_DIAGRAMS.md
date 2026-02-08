# UI Module Flow Diagrams

This document contains flow diagrams describing all execution flows for the UI (User Interface) testing module.

---

## 1. Main UI Intent Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UI INTENT EXECUTION FLOW                            │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  User Intent │
                              │   (Gherkin)  │
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │   Parse Intent into   │
                         │   Individual Steps    │
                         │  (Given/When/Then)    │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  For Each Step:       │
                         │  Execute Step Logic   │
                         └───────────┬───────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌───────────┐    ┌───────────┐    ┌───────────┐
            │   Given   │    │   When    │    │   Then    │
            │   Steps   │    │   Steps   │    │   Steps   │
            └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
                  │                │                │
                  └────────────────┼────────────────┘
                                   │
                                   ▼
                         ┌───────────────────────┐
                         │   Return Test Result  │
                         │   {success, steps,    │
                         │    error}             │
                         └───────────────────────┘
```

---

## 2. Single Step Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SINGLE STEP EXECUTION FLOW                           │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  Step Intent │
                              │  (e.g. fill  │
                              │   username)  │
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Determine Module     │
                         │  (from current URL)   │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Query ChromaDB for   │
                         │  Stored [correct]     │
                         │  Action               │
                         └───────────┬───────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
        ┌───────────────────┐             ┌───────────────────┐
        │  [correct] Action │             │  No Stored Action │
        │     FOUND         │             │     or [incorrect]│
        └─────────┬─────────┘             └─────────┬─────────┘
                  │                                 │
                  ▼                                 ▼
        ┌───────────────────┐             ┌───────────────────┐
        │  Use Stored       │             │  Retrieve Live    │
        │  Locator/Action   │             │  HTML Elements    │
        └─────────┬─────────┘             └─────────┬─────────┘
                  │                                 │
                  │                                 ▼
                  │                       ┌───────────────────┐
                  │                       │  Send to AI Agent │
                  │                       │  (GitLab Duo)     │
                  │                       └─────────┬─────────┘
                  │                                 │
                  │                                 ▼
                  │                       ┌───────────────────┐
                  │                       │  AI Generates     │
                  │                       │  Action Metadata  │
                  │                       └─────────┬─────────┘
                  │                                 │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                         ┌───────────────────────┐
                         │   Execute Action on   │
                         │   Playwright Page     │
                         └───────────┬───────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
        ┌───────────────────┐             ┌───────────────────┐
        │  Action SUCCESS   │             │  Action FAILED    │
        └─────────┬─────────┘             └─────────┬─────────┘
                  │                                 │
                  ▼                                 ▼
        ┌───────────────────┐             ┌───────────────────┐
        │  Store as         │             │  Store as         │
        │  [correct] in     │             │  [incorrect] in   │
        │  ChromaDB         │             │  ChromaDB         │
        └─────────┬─────────┘             └─────────┬─────────┘
                  │                                 │
                  ▼                                 ▼
        ┌───────────────────┐             ┌───────────────────┐
        │  Continue to      │             │  Request Failure  │
        │  Next Step        │             │  Analysis from AI │
        └───────────────────┘             └───────────────────┘
```

---

## 3. Action Type Decision Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ACTION TYPE DECISION FLOW                           │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  AI Returns  │
                              │  action_type │
                              └──────┬───────┘
                                     │
         ┌───────────┬───────────┬───┴───┬───────────┬───────────┐
         │           │           │       │           │           │
         ▼           ▼           ▼       ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │navigate │ │  click  │ │  fill   │ │ select  │ │ verify  │ │  wait   │
    └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
         │           │           │           │           │           │
         ▼           ▼           ▼           ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │page.goto│ │page.    │ │page.fill│ │page.    │ │ Verify  │ │page.    │
    │  (url)  │ │click()  │ │(locator,│ │select_  │ │ Element │ │wait_for │
    │         │ │(locator)│ │ value)  │ │option() │ │ Content │ │selector │
    └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

---

## 4. Verification Step Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VERIFICATION STEP FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  Then Step   │
                              │  (Verify)    │
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Determine Verify     │
                         │  Type from Intent     │
                         └───────────┬───────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │  verify_text     │  │  verify_visible  │  │  verify_url      │
    │  (text content)  │  │  (element shown) │  │  (current URL)   │
    └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
             │                     │                     │
             ▼                     ▼                     ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │ Get element text │  │ Check element    │  │ Get page URL     │
    │ Compare expected │  │ visibility state │  │ Match pattern    │
    └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
             │                     │                     │
             └─────────────────────┼─────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
          ┌──────────────────┐          ┌──────────────────┐
          │  PASS            │          │  FAIL            │
          │  (Match Found)   │          │  (No Match)      │
          └──────────────────┘          └──────────────────┘
```

---

## 5. ChromaDB Learning Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CHROMADB LEARNING FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  Action      │
                              │  Completed   │
                              └──────┬───────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
        ┌───────────────────┐             ┌───────────────────┐
        │  Action SUCCESS   │             │  Action FAILED    │
        └─────────┬─────────┘             └─────────┬─────────┘
                  │                                 │
                  ▼                                 ▼
        ┌───────────────────┐             ┌───────────────────┐
        │  Create Document: │             │  Create Document: │
        │  ─────────────────│             │  ─────────────────│
        │  • module         │             │  • module         │
        │  • action_key     │             │  • action_key     │
        │  • intent         │             │  • intent         │
        │  • locator        │             │  • locator        │
        │  • action_type    │             │  • action_type    │
        │  • status:[correct]             │  • status:[incorrect]
        └─────────┬─────────┘             └─────────┬─────────┘
                  │                                 │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                         ┌───────────────────────┐
                         │  Upsert to ChromaDB   │
                         │  ui_learning          │
                         │  Collection           │
                         └───────────────────────┘
                                   │
                                   ▼
                         ┌───────────────────────┐
                         │  Next Execution:      │
                         │  Query returns this   │
                         │  learned action       │
                         └───────────────────────┘
```

---

## 6. Live HTML Element Retrieval Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LIVE HTML ELEMENT RETRIEVAL FLOW                         │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  No Stored   │
                              │  Action Found│
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Get Current Page     │
                         │  DOM Elements         │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Filter Interactive   │
                         │  Elements:            │
                         │  • input, button      │
                         │  • a, select          │
                         │  • textarea           │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Extract Attributes:  │
                         │  • id, name, class    │
                         │  • placeholder        │
                         │  • aria-label         │
                         │  • text content       │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Format as HTML       │
                         │  Context for AI       │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Send to AI Agent     │
                         │  with Step Intent     │
                         └───────────────────────┘
```

---

## 7. Failure Analysis Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FAILURE ANALYSIS FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  Step Failed │
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Collect Context:     │
                         │  • Failed step intent │
                         │  • Error message      │
                         │  • Current URL        │
                         │  • Action attempted   │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Send to AI Agent     │
                         │  for Analysis         │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  AI Returns:          │
                         │  ─────────────────────│
                         │  {                    │
                         │   "success": false,   │
                         │   "reason": "Root     │
                         │    cause analysis..." │
                         │  }                    │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  Store Analysis in    │
                         │  Step Result          │
                         └───────────────────────┘
```

---

## 8. Dashboard UI Test Runner Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DASHBOARD UI TEST RUNNER FLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │  Dashboard  │
    │  (Browser)  │
    └──────┬──────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    User Actions                                  │
    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
    │  │Add Test │  │Run Test │  │Run All  │  │Generate │            │
    │  │ Intent  │  │ (Single)│  │ Tests   │  │  File   │            │
    │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
    └───────┼────────────┼────────────┼────────────┼──────────────────┘
            │            │            │            │
            ▼            ▼            ▼            ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ Store in    │ │ POST /api/  │ │ POST /api/  │ │ POST /api/  │
    │ Local List  │ │ run         │ │ run-all     │ │ approve     │
    └─────────────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
                           │               │               │
                           ▼               ▼               ▼
                    ┌─────────────────────────────────────────────┐
                    │              Flask Backend                   │
                    │  ┌─────────────────────────────────────┐    │
                    │  │         execute_intent()            │    │
                    │  │  • reset_ui_page()                  │    │
                    │  │  • get_ui_page()                    │    │
                    │  │  • execute_by_intent()              │    │
                    │  │  • reset_ui_page()                  │    │
                    │  └─────────────────────────────────────┘    │
                    └──────────────────┬──────────────────────────┘
                                       │
                                       ▼
                    ┌─────────────────────────────────────────────┐
                    │              Return Result                   │
                    │  {                                          │
                    │    "success": true/false,                   │
                    │    "steps": [...],                          │
                    │    "error": null/"message"                  │
                    │  }                                          │
                    └─────────────────────────────────────────────┘
```

---

## Summary of UI Flows

| Flow             | Description                                         |
| ---------------- | --------------------------------------------------- |
| Main Execution   | Parses Gherkin intent into steps, executes each     |
| Single Step      | Queries ChromaDB, generates/reuses action, executes |
| Action Types     | Routes to appropriate Playwright method             |
| Verification     | Validates element text, visibility, URL             |
| Learning         | Stores successful/failed actions in ChromaDB        |
| HTML Retrieval   | Extracts DOM elements for AI context                |
| Failure Analysis | AI analyzes and explains failures                   |
| Dashboard Runner | Web interface for interactive testing               |
