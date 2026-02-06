def get_self_healing_prompt(locator_name, locator_value, matches):
    return f"""
        Your expertise: DOM analysis, semantic element matching, and robust selector creation for test automation.
        
        MISSION: Select the most appropriate element from candidate elements based on locator intent and value, ensuring stable and reliable test automation.
        
        INPUT DATA
        LOCATOR INTENT: {locator_name}
        LOCATOR HINT: {locator_value}
        CANDIDATE ELEMENTS: {matches}
        
        ELEMENT SELECTION STRATEGY
        
        2. GENERIC XPATH INTENT HANDLING
        If locator intent is a generic XPath (contains //x[@id='xx'], //x[@x='x'], or similar placeholder patterns):
        - IGNORE the generic intent and focus on locator hint for semantic meaning
        - Extract keywords from locator hint to determine element purpose
        - Look for elements that match hint semantics (button, input, login, submit, etc.)
        - Prioritize elements with attributes that semantically relate to hint keywords
        
        Generic XPath patterns to detect:
        - //x[@id='xx'] or //x[@x='x'] or similar placeholder patterns
        - //Afra[@id='user-name'] or //Asad[@id='password'] (non-semantic prefixes)
        - Any XPath with placeholder or non-descriptive element names
        
        3. COMBINED INTENT AND VALUE MATCHING
        If primary matching yields multiple candidates, combine locator intent and value
        Extract keywords from both locator_name and locator_value
        Find elements that match the combined semantic meaning
        
        Examples:
        - Intent: "submit_button", Value: "checkout" → Combined: ["submit", "button", "checkout"]
        - Look for: button elements with submit and checkout related attributes
        - Intent: "//x[@id='xx']", Hint: "//x[@id='xx']" → IGNORE intent, analyze hint for semantic meaning
        - If hint is also generic, look for submit/button elements with login-related attributes
        - Intent: "//Afra[@id='user-name']", Hint: "username input" → Focus on hint: ["username", "input"]
        - Look for: input elements with username-related attributes
        
        4. ATTRIBUTE ANALYSIS PRIORITY
        Examine element attributes in this order:
        - Core attributes: id, name, class, type, value
        - Accessibility: aria-label, aria-labelledby, role, title
        - Custom attributes: data-*, test-id, automation-id
        - Form attributes: placeholder, label, for
        - Visible text content and element tag type
        
        5. SELECTION CRITERIA PRIORITY
        PRIORITY 1: EXACT ATTRIBUTE MATCH - Element attributes exactly match extracted keywords
        PRIORITY 2: SEMANTIC ATTRIBUTE MATCH - Attributes semantically relate to keywords
        PRIORITY 3: TAG TYPE MATCH - Element tag matches expected type from keywords
        PRIORITY 4: CONTENT MATCH - Element text/values match keywords
        PRIORITY 5: STABILITY - Prefer elements with stable identifiers
        
        Stability ranking (best to worst):
        1. id (unique identifier)
        2. name (form element identifier)
        3. data-testid, data-automation-id (test-specific)
        4. class (styling identifier)
        5. placeholder, aria-label (semantic identifiers)
        
        6. ANALYSIS WORKFLOW
        STEP 1: Check if locator intent is generic XPath (//x[@id='xx'] pattern)
        STEP 2: If generic XPath, check if locator hint is also generic
        STEP 3: If both are generic, use context clues from element attributes and types
        STEP 4: If hint is meaningful, extract semantic meaning from locator hint
        STEP 5: If intent is meaningful, parse locator intent into meaningful tokens
        STEP 6: Find candidates matching extracted tokens (from intent, hint, or context)
        STEP 7: If multiple matches, combine intent and value for refinement
        STEP 8: For each candidate element:
        - Extract all attribute values
        - Extract visible text content
        - Compare against extracted tokens
        - Calculate relevance score based on matches
        STEP 9: Select candidate with highest relevance score
        
        SPECIAL CASE: When both intent and hint are generic XPaths
        - Look for submit buttons (type="submit") with login-related attributes
        - Prioritize elements with data-test attributes containing "login"
        - Consider element context (form submission, authentication flow)
        
        7. SELECTOR GENERATION
        CSS PREFERRED: Use CSS selectors when possible
        - ID: #element-id
        - Class: .class-name or tag.class-name
        - Attribute: tag[attribute="value"] or tag[attribute*="partial"]
        - Combined: tag#id.class[attribute="value"]
        
        XPATH FALLBACK: Use XPath only when CSS insufficient
        - Prefix with "xpath="
        - Use stable attributes: xpath=//button[@id='submit-btn']
        - Avoid position-based: xpath=(//button)[1] (unstable)
        
        OUTPUT REQUIREMENTS
        MANDATORY OUTPUT FORMAT:
        - Return ONLY the selector string (no explanations, comments, or formatting)
        - Must match exactly ONE element from the provided candidates
        - Use CSS format when possible: #id, .class, tag[attr="value"]
        - Use XPath format only when necessary: xpath=//tag[@attr='value']
        
        FORBIDDEN OUTPUTS:
        - NO explanations or reasoning
        - NO commentary or analysis
        - NO multiple selectors or alternatives
        - NO formatting or special characters
        - NO "The best selector is..." or similar phrases
        
        SUCCESS CRITERIA: Select the most semantically relevant and stable element that matches locator intent first, then combined intent and value if needed.
        FAILURE AVOIDANCE: Avoid elements with unstable identifiers or weak semantic matches.
        
        SELECT OPTIMAL ELEMENT NOW
        """


def get_db_context_prompt(res, db_requirement):
    # Format the results into a readable string for the prompt
    knowledge_str = ""

    if isinstance(res, dict):
        if res.get("schemas"):
            knowledge_str += "### Table Schemas:\n"
            for schema in res["schemas"]:
                knowledge_str += f"{schema['text']}\n\n"

        if res.get("queries"):
            knowledge_str += "### Reference Queries:\n"
            for query in res["queries"]:
                knowledge_str += f"{query['text']}\n\n"

        if res.get("relationships"):
            knowledge_str += "### Relationships:\n"
            for rel in res["relationships"]:
                knowledge_str += f"{rel['text']}\n\n"
    else:
        knowledge_str = str(res)

    if not knowledge_str.strip():
        knowledge_str = "No specific schema information found. Please use standard SQL practices or ask for clarification if schema is unknown."

    return f"""
        Your expertise: MySQL syntax, performance optimization, and enterprise database schema design.
        
        📋 **MISSION**: Generate a precise MySQL query that fulfills the given requirement using only the provided database knowledge.
        
        📥 **INPUT DATA**
        ═══════════════════════════════════════════════════════════════════════════════════════
        🗄️ DATABASE KNOWLEDGE:
        {knowledge_str}
        
        📝 REQUIREMENT:
        {db_requirement}
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        ⚡ **CRITICAL SQL GENERATION RULES** ⚡
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        1️⃣ **MYSQL SYNTAX REQUIREMENTS**
        
        ✅ Use ONLY MySQL syntax and functions
        
        ✅ Use ANSI JOIN syntax (INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL OUTER JOIN)
        
        ✅ Qualify tables with schema names when they appear in Knowledge
        
        📝 EXAMPLES:
        
        • Good: SELECT a.id FROM schema.table_a a INNER JOIN schema.table_b b ON a.id = b.ref_id
        
        • Bad: SELECT * FROM table_a, table_b WHERE table_a.id = table_b.ref_id
        
        2️⃣ **COLUMN SELECTION STRATEGY**
        
        ✅ Select ONLY columns explicitly needed by the Requirement
        
        ✅ For counts/existence/aggregates, return single scalar with clear alias
        
        📝 EXAMPLES:
        
        • Count: SELECT COUNT(*) AS total_records FROM table_name
        
        • Existence: SELECT CASE WHEN COUNT(*) > 0 THEN 'EXISTS' ELSE 'NOT_EXISTS' END AS status FROM table_name
        
        • Aggregate: SELECT MAX(created_date) AS latest_date, MIN(created_date) AS earliest_date FROM table_name
        
        3️⃣ **RELATIONSHIP & JOIN CONSTRAINTS**
        
        ✅ Use ONLY relationships explicitly defined in Knowledge
        
        ❌ NEVER join tables that are absent from Knowledge
        
        ✅ Use explicit ON predicates for all joins
        
        📝 EXAMPLE:
        
        • Knowledge shows: users.id → orders.user_id relationship
        
        • Query: SELECT u.name, o.order_date FROM users u INNER JOIN orders o ON u.id = o.user_id
        
        4️⃣ **PLACEHOLDER USAGE**
        
        ✅ Use standard placeholders for ALL dynamic inputs
        
        ✅ For "today" requirements, use CURDATE()
        
        📝 EXAMPLES:
        
        • Flight number: WHERE flight_no = 'FL123' (or use {{param}})
        
        • Date range: WHERE created_date >= '2023-01-01' AND created_date <= '2023-12-31'
        
        • Today's data: WHERE DATE(created_date) = CURDATE()
        
        5️⃣ **DATE HANDLING PRECISION**
        
        ✅ For date-only comparisons, wrap column with DATE(...)
        
        📝 EXAMPLES:
        
        • Date comparison: WHERE DATE(order_date) = '2023-05-10'
        
        • Today comparison: WHERE DATE(order_date) = CURDATE()
        
        6️⃣ **CASE-INSENSITIVE SEARCHES**
        
        ✅ Use UPPER() function on BOTH column and parameter for case-insensitive matches
        
        📝 EXAMPLES:
        
        • Name search: WHERE UPPER(user_name) = UPPER(:search_name)
        
        • Pattern search: WHERE UPPER(description) LIKE UPPER(:pattern)
        
        7️⃣ **SCHEMA INTEGRITY RULES**
        
        ❌ NEVER invent table or column names not present in Knowledge
        
        ✅ If multiple variants exist in Knowledge, choose the most consistent one
        
        ✅ Cross-reference all table/column names against provided Knowledge
        
        8️⃣ **QUERY TYPE RESTRICTIONS**
        
        ✅ Generate SELECT queries by default
        
        ✅ Generate DML (INSERT/UPDATE/DELETE) ONLY if Requirement explicitly requests it
        
        📝 EXAMPLES:
        
        • Default: SELECT statements for data retrieval
        
        • Explicit DML: "Insert new record" → INSERT INTO table_name...
        
        9️⃣ **CODE QUALITY STANDARDS**
        
        ✅ Use meaningful table aliases (single letters or descriptive names)
        
        ✅ Include explicit ON predicates for all joins
        
        ✅ Add ORDER BY ONLY if Requirement implies specific ordering
        
        ✅ Format query for readability with proper indentation
        
        📝 EXAMPLE:
        
        SELECT u.user_id,
        
        u.user_name,
        
        o.order_date,
        
        o.total_amount
        
        FROM users u
        
        INNER JOIN orders o ON u.user_id = o.user_id
        
        WHERE u.status = :user_status
        
        ORDER BY o.order_date DESC;
        
        🚨 **CRITICAL VALIDATION CHECKLIST** 🚨
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        ✅ **BEFORE GENERATING QUERY, VERIFY**:
        
        🔍 All table names exist in Knowledge
        
        🔍 All column names exist in Knowledge
        
        🔍 All relationships are defined in Knowledge
        
        🔍 MySQL-specific syntax is used correctly
        
        🔍 Query fulfills the exact Requirement
        
        🎯 **OUTPUT REQUIREMENTS**:
        
        • Return ONLY the SQL query (no explanations or commentary)
        
        • Use proper SQL formatting with indentation
        
        • Ensure query is syntactically correct MySQL
        
        • Include all necessary bind variables
        """


def get_response_body_validation_prompt(response, exp_response):
    return f"""
        Your expertise: Precise JSON path resolution, strict value matching, and automated validation.
        
        📋 **MISSION**: Validate if a JSON RESPONSE matches expected values at specific JSON paths.
        
        📥 **INPUT DATA**
        ═══════════════════════════════════════════════════════════════════════════════════════
        🔍 RESPONSE OBJECT:
        {response}
        
        🎯 EXPECTED VALIDATIONS:
        {exp_response}
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        ⚡ **CRITICAL VALIDATION RULES** ⚡
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        1️⃣ **JSON PARSING REQUIREMENTS**
            ✅ Parse both RESPONSE and EXPECTED as valid JSON
            ✅ Normalize Python dicts (single quotes → double quotes, True/False/None → true/false/null)
            ✅ Handle all JSON data types correctly (string, number, boolean, null, array, object)
        
        2️⃣ **PATH SYNTAX SPECIFICATION**
            ✅ Object navigation: Use dot notation → user.profile.name
            ✅ Array indexing: Use bracket notation → items[0].id or users[2].email
            ✅ Special characters: Use bracket notation → ["key.with.dots"] or ["key-with-dashes"]
            📝 EXAMPLES:
            • Simple: status → validates root-level "status" field
            • Nested: user.profile.email → validates nested email field
            • Array: results[0].title → validates first result's title
            • Complex: metadata["api-version"] → validates key with special characters
        
        3️⃣ **PATH RESOLUTION LOGIC**
            ✅ For EACH path in EXPECTED, locate the corresponding value in RESPONSE
            ❌ FAIL if path is missing, malformed, or resolves to undefined
            ❌ FAIL if path resolves to multiple ambiguous locations
            ✅ Handle nested objects and arrays correctly
        
        4️⃣ **VALUE COMPARISON STANDARDS**
            ✅ STRICT TYPE-PRESERVING EQUALITY:
            • String "123" ≠ Number 123
            • Boolean true ≠ String "true"
            • null ≠ undefined ≠ ""
            ✅ DEEP EQUALITY for complex types:
            • Arrays: Order matters, [1,2,3] ≠ [3,2,1]
            • Objects: All properties must match exactly
            ✅ ALL paths in EXPECTED must have EXACT matches in RESPONSE
        
        5️⃣ **VALIDATION EXAMPLES**
            📝 EXPECTED: {{"status": "success", "data[0].id": 123}}
            ✅ VALID RESPONSE: {{"status": "success", "data": [{{"id": 123, "name": "test"}}]}}
            ❌ INVALID RESPONSE: {{"status": "success", "data": [{{"id": "123", "name": "test"}}]}} (type mismatch)
            ❌ INVALID RESPONSE: {{"status": "success", "data": []}} (missing path)
        
        🚨 **ABSOLUTE OUTPUT REQUIREMENTS** 🚨
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        🔥 **CRITICAL**: Your response must be EXACTLY ONE WORD:
            • ✅ "True" ← ALL validations pass
            • ❌ "False" ← ANY validation fails
        
        🚫 **FORBIDDEN OUTPUTS**:
            ❌ NO explanations, reasoning, or commentary
            ❌ NO code snippets or pseudo-code
            ❌ NO partial results or counts
            ❌ NO formatting, markdown, or special characters
            ❌ NO "The validation result is..." or similar phrases
            ❌ NO JSON or structured output
        
        🎯 **SUCCESS CRITERIA**: Every single path in EXPECTED must have an exact match in RESPONSE
        🎯 **FAILURE TRIGGER**: Any path missing, any value mismatch, any type difference
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        🏁 **EXECUTE VALIDATION NOW** 🏁
        ═══════════════════════════════════════════════════════════════════════════════════════
        """


def get_logs_analyzing_prompt(logs):
    return f"""
        Analyze The Logs {logs}
        /nAnd Give Me On Sugestion Or Solution Using Robot Framework
        """


def get_curl_generation_prompt(intent: str, swagger_context: str, base_url: str) -> str:
    """
    Generate prompt for GitLab Duo to create an executable curl command.

    Args:
        intent (str): User's natural language intent (e.g., "delete book with id 5")
        swagger_context (str): Retrieved swagger API documentation from RAG
        base_url (str): Base URL for the API (e.g., "https://fakerestapi.azurewebsites.net")

    Returns:
        str: Formatted prompt for curl generation
    """
    return f"""
        Your expertise: REST API integration, curl command generation, and API request construction.
        
        📋 **MISSION**: Generate an executable curl command based on the user's intent and the provided API documentation.
        
        📥 **INPUT DATA**
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        🎯 USER INTENT:
        {intent}
        
        🌐 BASE URL:
        {base_url}
        
        📚 API DOCUMENTATION (from Swagger):
        {swagger_context}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        ⚡ **CRITICAL CURL GENERATION RULES** ⚡
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        1️⃣ **INTENT ANALYSIS**
        ✅ Extract the action from intent: CREATE, READ, UPDATE, DELETE
        ✅ Identify the resource being targeted (e.g., Books, Users, Activities)
        ✅ Extract any IDs, values, or data from the intent
        ✅ Map action to HTTP method:
           - "get", "fetch", "retrieve", "list", "show" → GET
           - "create", "add", "new", "post" → POST
           - "update", "modify", "change", "edit" → PUT
           - "delete", "remove", "destroy" → DELETE
        
        2️⃣ **ENDPOINT SELECTION**
        ✅ Match the intent to the correct endpoint from the API documentation
        ✅ For single resource operations (get one, update one, delete one), use the endpoint with {{id}}
        ✅ For collection operations (list all, create new), use the base resource endpoint
        ✅ Replace path parameters with actual values from intent
        
        3️⃣ **PARAMETER EXTRACTION FROM INTENT**
        ✅ Extract numeric IDs: "book 5", "id 123", "number 42" → 5, 123, 42
        ✅ Extract string values: "named 'Test Book'" → "Test Book"
        ✅ For POST/PUT, construct JSON body based on schema properties
        
        4️⃣ **CURL COMMAND FORMAT**
        ✅ Use single-line format for cross-platform compatibility
        ✅ Include all required headers
        ✅ Use proper quoting for JSON body
        ✅ Include -k flag for SSL verification bypass (if needed)
        
        📝 CURL TEMPLATE:
        ```
        curl -X METHOD "URL" -H "Content-Type: application/json" -H "Accept: application/json" -d 'JSON_BODY'
        ```
        
        5️⃣ **EXAMPLES**
        
        Intent: "get all books"
        → curl -X GET "{base_url}/api/v1/Books" -H "Accept: application/json"
        
        Intent: "delete book with id 5"
        → curl -X DELETE "{base_url}/api/v1/Books/5" -H "Accept: application/json"
        
        Intent: "create a new book titled 'Test Book' with 100 pages"
        → curl -X POST "{base_url}/api/v1/Books" -H "Content-Type: application/json" -H "Accept: application/json" -d '{{"id":0,"title":"Test Book","pageCount":100,"description":"","excerpt":"","publishDate":"2026-02-06T00:00:00.000Z"}}'
        
        Intent: "update book 3 with new title 'Updated Title'"
        → curl -X PUT "{base_url}/api/v1/Books/3" -H "Content-Type: application/json" -H "Accept: application/json" -d '{{"id":3,"title":"Updated Title","pageCount":0,"description":"","excerpt":"","publishDate":"2026-02-06T00:00:00.000Z"}}'
        
        🚨 **OUTPUT REQUIREMENTS** 🚨
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        🔥 **CRITICAL**: Return ONLY the curl command, nothing else!
        
        ✅ Single line, executable curl command
        ✅ Properly escaped quotes
        ✅ Complete URL with base URL + endpoint path
        ✅ All necessary headers
        ✅ Request body (for POST/PUT) based on schema
        
        🚫 **FORBIDDEN**:
        ❌ NO explanations or comments
        ❌ NO markdown code blocks
        ❌ NO multiple commands or alternatives
        ❌ NO line breaks within the command
        ❌ NO "Here is the curl command:" or similar phrases
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        🏁 **GENERATE CURL COMMAND NOW** 🏁
        ═══════════════════════════════════════════════════════════════════════════════════════
        """


def get_api_response_analysis_prompt(
    intent: str,
    curl_command: str,
    response_body: str,
    status_code: int,
    stderr: str = "",
) -> str:
    """
    Generate prompt for GitLab Duo to analyze API response.

    Args:
        intent (str): Original user intent
        curl_command (str): The curl command that was executed
        response_body (str): The response body from the API
        status_code (int): HTTP status code (or -1 if curl failed)
        stderr (str): Any error output from curl execution

    Returns:
        str: Formatted prompt for response analysis
    """
    # Truncate response body if too long to avoid token limits
    truncated_body = (
        response_body[:2000] if len(response_body) > 2000 else response_body
    )

    return f"""Analyze this API response and return ONLY a JSON object.

Intent: {intent}
Command: {curl_command}
Status: {status_code}
Response: {truncated_body}
Error: {stderr if stderr else "None"}

Rules:
- Status 2xx with valid data = success
- Status 4xx/5xx or error = failure
- Check if intent was fulfilled

Return ONLY this JSON format (no other text):
{{"success": true, "reason": "explanation"}}
or
{{"success": false, "reason": "explanation"}}

JSON result:"""


def get_curl_retry_prompt(
    intent: str,
    original_curl: str,
    error_output: str,
    swagger_context: str,
    base_url: str,
) -> str:
    """
    Generate prompt for GitLab Duo to fix a failed curl command.

    Args:
        intent (str): Original user intent
        original_curl (str): The curl command that failed
        error_output (str): Error message from the failed execution
        swagger_context (str): API documentation for reference
        base_url (str): Base URL for the API

    Returns:
        str: Formatted prompt for curl retry/fix
    """
    return f"""
        Your expertise: REST API debugging, curl command troubleshooting, and error resolution.
        
        📋 **MISSION**: The previous curl command failed. Analyze the error and generate a corrected curl command.
        
        📥 **INPUT DATA**
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        🎯 ORIGINAL INTENT:
        {intent}
        
        💻 FAILED CURL COMMAND:
        {original_curl}
        
        ❌ ERROR OUTPUT:
        {error_output}
        
        🌐 BASE URL:
        {base_url}
        
        📚 API DOCUMENTATION:
        {swagger_context}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        ⚡ **ERROR ANALYSIS & FIX** ⚡
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        1️⃣ **COMMON ERROR FIXES**
        ✅ Connection refused → Check URL format, add -k for SSL issues
        ✅ 404 Not Found → Verify endpoint path and parameters
        ✅ 400 Bad Request → Check request body JSON format
        ✅ 415 Unsupported Media Type → Add Content-Type header
        ✅ JSON parse error → Fix quote escaping in body
        
        2️⃣ **CROSS-PLATFORM CONSIDERATIONS**
        ✅ Windows: Use double quotes for -d body, escape inner quotes
        ✅ Linux/Mac: Use single quotes for -d body
        ✅ Use -k flag to bypass SSL certificate issues
        
        🚨 **OUTPUT REQUIREMENTS** 🚨
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        🔥 **CRITICAL**: Return ONLY the corrected curl command!
        
        ✅ Single line, executable curl command
        ✅ Fixed based on the error analysis
        ✅ Include -k flag for SSL bypass
        
        🚫 **FORBIDDEN**:
        ❌ NO explanations
        ❌ NO markdown
        ❌ NO alternatives
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        🏁 **GENERATE FIXED CURL COMMAND NOW** 🏁
        ═══════════════════════════════════════════════════════════════════════════════════════
        """


# ==================== DB INTENT-BASED PROMPTS ====================


def get_db_query_generation_prompt(
    intent: str,
    schema_context: str,
    correct_examples: str = "",
    incorrect_examples: str = "",
) -> str:
    """
    Generate prompt for GitLab Duo to create a SQL query based on user intent.

    Args:
        intent: User's natural language intent (e.g., "get all posts by user id 5")
        schema_context: Retrieved database schema from RAG
        correct_examples: Similar successful queries from learning context
        incorrect_examples: Similar failed queries to avoid

    Returns:
        str: Formatted prompt for SQL query generation
    """
    examples_section = ""
    if correct_examples:
        examples_section += f"""
        ✅ **SIMILAR SUCCESSFUL QUERIES (Learn from these)**:
        {correct_examples}
        """

    if incorrect_examples:
        examples_section += f"""
        ❌ **SIMILAR FAILED QUERIES (Avoid these mistakes)**:
        {incorrect_examples}
        """

    return f"""
        Your expertise: MySQL query generation, database schema analysis, and SQL optimization.
        
        📋 **MISSION**: Generate an executable MySQL query based on the user's intent and the provided database schema.
        
        📥 **INPUT DATA**
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        🎯 USER INTENT:
        {intent}
        
        📊 DATABASE SCHEMA:
        {schema_context}
        {examples_section}
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        ⚡ **CRITICAL SQL GENERATION RULES** ⚡
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        1️⃣ **INTENT ANALYSIS**
        ✅ Extract the action from intent: SELECT, INSERT, UPDATE, DELETE, COUNT
        ✅ Identify the target table(s) from the schema
        ✅ Extract filter conditions (WHERE clauses) from the intent
        ✅ Identify any aggregations (COUNT, SUM, AVG, etc.)
        ✅ Map intent keywords to SQL operations:
           - "get", "fetch", "retrieve", "list", "find", "show" → SELECT
           - "count", "how many" → SELECT COUNT(*)
           - "create", "add", "insert" → INSERT
           - "update", "modify", "change" → UPDATE
           - "delete", "remove" → DELETE
        
        2️⃣ **TABLE AND COLUMN SELECTION**
        ✅ Use ONLY tables and columns that exist in the provided schema
        ✅ Use exact column names as shown in the schema (case-sensitive)
        ✅ For JOINs, use the relationships defined in the schema
        ✅ If a column doesn't exist, use the closest matching column from schema
        
        3️⃣ **FILTER EXTRACTION FROM INTENT**
        ✅ Extract numeric IDs: "user id 5", "post 123", "with id 42" → WHERE column = value
        ✅ Extract string values: "named 'John'" → WHERE column = 'John'
        ✅ Extract date ranges: "last 7 days" → WHERE date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ✅ Extract comparisons: "greater than 10" → WHERE column > 10
        
        4️⃣ **JOIN LOGIC**
        ✅ Use relationships from schema for proper JOINs
        ✅ Prefer INNER JOIN for related data
        ✅ Use LEFT JOIN when optional relationships are needed
        ✅ Always use table aliases for clarity in multi-table queries
        
        5️⃣ **SQL FORMAT**
        ✅ Use MySQL syntax
        ✅ Single line format preferred
        ✅ Use backticks for reserved words if needed
        ✅ End query with semicolon
        
        📝 SQL TEMPLATE EXAMPLES:
        
        Intent: "get all users"
        → SELECT * FROM users;
        
        Intent: "get posts by user id 5"
        → SELECT * FROM posts WHERE user_id = 5;
        
        Intent: "count all active users"
        → SELECT COUNT(*) FROM users WHERE status = 'active';
        
        Intent: "get user details with their posts"
        → SELECT u.*, p.* FROM users u INNER JOIN posts p ON u.id = p.user_id;
        
        Intent: "get top 10 recent posts"
        → SELECT * FROM posts ORDER BY created_at DESC LIMIT 10;
        
        🚨 **OUTPUT REQUIREMENTS** 🚨
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        🔥 **CRITICAL**: Return ONLY the SQL query, nothing else!
        
        ✅ Single executable MySQL query
        ✅ Properly formatted with correct syntax
        ✅ Uses ONLY tables/columns from the provided schema
        ✅ Ends with semicolon
        
        🚫 **FORBIDDEN**:
        ❌ NO explanations or comments
        ❌ NO markdown code blocks
        ❌ NO multiple queries
        ❌ NO "Here is the query:" or similar phrases
        ❌ NO tables or columns not in the schema
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        🏁 **GENERATE SQL QUERY NOW** 🏁
        ═══════════════════════════════════════════════════════════════════════════════════════
        """


def get_db_query_analysis_prompt(
    intent: str,
    query: str,
    result: str,
) -> str:
    """
    Generate prompt for GitLab Duo to analyze a SQL query execution result.

    Args:
        intent: Original user intent
        query: The SQL query that was executed
        result: Query result as JSON string or error message

    Returns:
        str: Formatted prompt for query analysis
    """
    # Truncate result if too long
    result_preview = result[:1000] if result else "No results"

    return f"""Analyze this SQL query execution and return ONLY a JSON object.

Intent: {intent}
Query: {query}
Result: {result_preview}

Rules:
- Query executed without error AND returned relevant data = success
- Query returned empty array [] but no error = success (data may not exist)
- Query had syntax error or execution error = failure
- Query returned data but doesn't match intent = failure

Return ONLY this JSON format (no other text):
{{"success": true, "reason": "explanation"}}
or
{{"success": false, "reason": "explanation"}}

JSON result:"""


def get_db_query_retry_prompt(
    intent: str,
    original_query: str,
    error_message: str,
    schema_context: str,
) -> str:
    """
    Generate prompt for GitLab Duo to fix a failed SQL query.

    Args:
        intent: Original user intent
        original_query: The query that failed
        error_message: Error from database
        schema_context: Database schema for reference

    Returns:
        str: Formatted prompt for query fix
    """
    return f"""
        Your expertise: MySQL debugging, SQL error resolution, and query optimization.
        
        📋 **MISSION**: The previous SQL query failed. Analyze the error and generate a corrected query.
        
        📥 **INPUT DATA**
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        🎯 ORIGINAL INTENT:
        {intent}
        
        💻 FAILED QUERY:
        {original_query}
        
        ❌ ERROR MESSAGE:
        {error_message}
        
        📊 DATABASE SCHEMA:
        {schema_context}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        ⚡ **COMMON ERROR FIXES** ⚡
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        1️⃣ **Table doesn't exist** → Check schema for correct table name
        2️⃣ **Unknown column** → Check schema for correct column name
        3️⃣ **Syntax error** → Fix SQL syntax
        4️⃣ **Ambiguous column** → Add table alias prefix
        5️⃣ **Data type mismatch** → Cast or convert data types
        
        🚨 **OUTPUT REQUIREMENTS** 🚨
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        🔥 **CRITICAL**: Return ONLY the corrected SQL query!
        
        ✅ Single executable MySQL query
        ✅ Fixed based on the error analysis
        ✅ Uses ONLY tables/columns from the schema
        
        🚫 **FORBIDDEN**:
        ❌ NO explanations
        ❌ NO markdown
        ❌ NO alternatives
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        🏁 **GENERATE FIXED SQL QUERY NOW** 🏁
        ═══════════════════════════════════════════════════════════════════════════════════════
        """
