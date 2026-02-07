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
    Generate prompt for analyzing API response.

    Args:
        intent (str): Original user intent
        curl_command (str): The curl command that was executed
        response_body (str): The response body from the API
        status_code (int): HTTP status code (or -1 if curl failed)
        stderr (str): Any error output from curl execution

    Returns:
        str: Formatted prompt for response analysis
    """
    return f"""Analyze this API response and determine if the intent was fulfilled.

**User Intent:** {intent}

**Curl Command:** {curl_command}

**HTTP Status Code:** {status_code}

**Response Body:** {response_body}

**Error (if any):** {stderr if stderr else "None"}

**Your Task:**
1. Check if the API request was successful (2xx status)
2. Check if the response data fulfills the user's intent
3. For verification intents ("verify", "check", "confirm"), validate the actual data matches expectations

**Rules:**
- Status 2xx with data matching the intent = success: true
- Status 4xx/5xx or error = success: false
- Status 2xx but data doesn't match intent = success: false

**Response Format (JSON only):**
{{"success": true/false, "reason": "Your analysis of the response"}}"""


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


def get_api_endpoint_retry_prompt(
    resource: str,
    intent: str,
    failed_curl: str,
    error_output: str,
    ai_analysis: str,
    stored_metadata: dict,
    swagger_context: str,
    base_url: str,
) -> str:
    """
    Generate ENHANCED retry prompt with AI analysis and all original context.

    This prompt includes:
    - AI analysis from first attempt (why it failed)
    - Original stored_metadata from learning database
    - Original swagger_context
    - Error details

    Args:
        resource: The API resource name
        intent: Original user intent
        failed_curl: The curl command that failed
        error_output: Error message from execution
        ai_analysis: AI's analysis of why the first attempt failed
        stored_metadata: Original stored action from learning database
        swagger_context: API documentation for reference
        base_url: Base URL for the API
    """

    # Build stored metadata section
    stored_section = """
        ═══════════════════════════════════════════════════════════════════════════════════════
        📚 **ORIGINAL STORED ACTION FROM LEARNING DATABASE**:
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    if stored_metadata:
        stored_section += f"""
        This action was used in the FIRST attempt and FAILED:
        
        - Action Key: {stored_metadata.get('action_key', 'unknown')}
        - Intent: {stored_metadata.get('intent', 'unknown')}
        - Method: {stored_metadata.get('method', 'unknown')}
        - Endpoint: {stored_metadata.get('endpoint', 'unknown')}
        - cURL: {stored_metadata.get('curl', 'unknown')}
        - Status: {stored_metadata.get('status', 'unknown')}
        """
    else:
        stored_section += """
        No stored action was used (first attempt was generated from swagger).
        """

    stored_section += """
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    # Build swagger context section
    swagger_section = """
        ═══════════════════════════════════════════════════════════════════════════════════════
        📖 **SWAGGER API DOCUMENTATION**:
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    if swagger_context:
        swagger_section += f"""
        {swagger_context}
        """
    else:
        swagger_section += """
        No swagger documentation available.
        """

    swagger_section += """
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    # Build AI analysis section
    analysis_section = f"""
        ═══════════════════════════════════════════════════════════════════════════════════════
        🤖 **AI ANALYSIS OF FAILED ATTEMPT** (IMPORTANT - Learn from this!):
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        The AI analyzed why the first attempt failed:
        
        {ai_analysis if ai_analysis else 'No AI analysis available'}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    return f"""
        ═══════════════════════════════════════════════════════════════════════════════════════
        🔄 **API ENDPOINT RETRY** - Fix Failed Request Using AI Analysis
        ═══════════════════════════════════════════════════════════════════════════════════════

        **RESOURCE**: `{resource}`
        **INTENT**: "{intent}"
        **BASE URL**: {base_url}
        
        {stored_section}
        
        {swagger_section}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        ❌ **FAILED ATTEMPT DETAILS**:
        ═══════════════════════════════════════════════════════════════════════════════════════

        The following curl command was attempted and FAILED:
        
        💥 FAILED CURL:
        {failed_curl}

        🔴 ERROR OUTPUT:
        {error_output}
        
        {analysis_section}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        📋 **YOUR TASK**:
        ═══════════════════════════════════════════════════════════════════════════════════════

        1. **STUDY** the AI analysis to understand WHY the first attempt failed
        2. **AVOID** repeating the same mistake
        3. **REFER** to the swagger documentation for correct endpoint/method
        4. **GENERATE** a corrected curl command

        ⚡ **COMMON FIXES**:
        - 404 Not Found → Check endpoint path spelling
        - 400 Bad Request → Check request body JSON format
        - 401/403 → Add/fix authorization headers
        - Connection refused → Check URL format
        - SSL errors → Add -k flag

        ═══════════════════════════════════════════════════════════════════════════════════════
        📤 **REQUIRED OUTPUT**: Return ONLY the corrected curl command (single line)
        ═══════════════════════════════════════════════════════════════════════════════════════

        🚫 NO explanations, NO markdown, NO alternatives

        ═══════════════════════════════════════════════════════════════════════════════════════
        🏁 **GENERATE CORRECTED CURL COMMAND NOW** 🏁
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
    Generate prompt for analyzing a SQL query execution result.

    Args:
        intent: Original user intent
        query: The SQL query that was executed
        result: Query result as JSON string or error message

    Returns:
        str: Formatted prompt for query analysis
    """
    return f"""Analyze this database query result and determine if the intent was fulfilled.

**User Intent:** {intent}

**SQL Query Executed:** {query}

**Query Result:** {result}

**Your Task:**
1. Look at the actual data returned in the Query Result
2. Determine if this result fulfills what the user asked for in the Intent
3. Return your analysis as JSON

**Rules:**
- If the result contains data matching the intent = success: true
- If the result is empty [] but user wanted to verify/find something = success: false
- If there's an error in the result = success: false
- For "list all" or "get all" intents, empty [] is acceptable

**Response Format (JSON only):**
{{"success": true/false, "reason": "Your analysis of what was found or not found"}}"""


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


def get_db_query_action_prompt(
    table: str,
    intent: str,
    schema_context: str = "",
    stored_metadata: dict = None,
) -> str:
    """
    Generate prompt for DUO to produce DB query action metadata.

    This prompt follows the same unified pattern as UI and API:
    - ALWAYS includes BOTH stored_metadata AND schema_context sections
    - If data missing, shows "No data found" message in that section

    Args:
        table: The database table name (e.g., "agents", "users", "orders")
        intent: User's intent describing what database action to perform
        schema_context: Schema specification context for this table (optional)
        stored_metadata: Previously stored action metadata from learning collection (optional)

    Returns:
        Formatted prompt string for DUO
    """

    # Build stored metadata section - ALWAYS present
    stored_section = """
        ═══════════════════════════════════════════════════════════════════════════════════════
        📚 **STORED ACTION FROM LEARNING DATABASE**:
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    if stored_metadata:
        stored_section += f"""
        ✅ A similar query was previously executed. Use as reference:
        
        • Action Key: {stored_metadata.get('action_key', 'unknown')}
        • Intent: {stored_metadata.get('intent', 'unknown')}
        • Query: {stored_metadata.get('query', 'unknown')}
        • Table: {stored_metadata.get('table', 'unknown')}
        • Status: {stored_metadata.get('status', 'unknown')}
        • Expected Columns: {stored_metadata.get('expected_columns', 'N/A')}
        • Expected Row Count: {stored_metadata.get('expected_row_count', 'N/A')}
        """
    else:
        stored_section += """
        ⚠️ No stored action found for this intent.
        This is the FIRST TIME this query is being generated.
        Use schema context to generate the query from scratch.
        """

    stored_section += """
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    # Build schema context section - ALWAYS present
    schema_section = """
        ═══════════════════════════════════════════════════════════════════════════════════════
        📖 **DATABASE SCHEMA CONTEXT**:
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    if schema_context and schema_context.strip():
        schema_section += f"""
        {schema_context}
        """
    else:
        schema_section += """
        ⚠️ No schema context available.
        Generate query based on standard MySQL conventions and table name.
        """

    schema_section += """
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    return f"""
        ═══════════════════════════════════════════════════════════════════════════════════════
        🎯 **DATABASE QUERY ACTION GENERATOR** - Generate SQL Query Metadata
        ═══════════════════════════════════════════════════════════════════════════════════════

        **TABLE**: `{table}`
        **INTENT**: "{intent}"
        
        {stored_section}
        
        {schema_section}

        ═══════════════════════════════════════════════════════════════════════════════════════
        📋 **YOUR TASK**:
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        Generate a COMPLETE DB query action metadata JSON object that includes the SQL query.
        
        **RULES**:
        1. Generate a unique `action_key` based on table + operation + purpose
        2. Use the intent EXACTLY as provided
        3. Determine the correct SQL operation (SELECT, INSERT, UPDATE, DELETE)
        4. Build the complete executable SQL query
        5. Use ONLY tables/columns from the provided schema
        6. Include expected outcomes (columns, row count estimate)

        ═══════════════════════════════════════════════════════════════════════════════════════
        📤 **REQUIRED OUTPUT FORMAT** (JSON ONLY - NO MARKDOWN, NO EXPLANATION):
        ═══════════════════════════════════════════════════════════════════════════════════════

        {{
            "action_key": "unique_action_identifier",
            "intent": "exact intent as provided",
            "table": "{table}",
            "operation": "SELECT|INSERT|UPDATE|DELETE",
            "query": "SELECT * FROM table WHERE condition;",
            "expected_columns": ["column1", "column2"],
            "expected_row_count": "single|multiple|none",
            "description": "Brief description of what this query does"
        }}

        ═══════════════════════════════════════════════════════════════════════════════════════
        📌 **EXAMPLES**:
        ═══════════════════════════════════════════════════════════════════════════════════════

        1️⃣ SELECT all records:
        {{
            "action_key": "get_all_agents",
            "intent": "get all agents from the system",
            "table": "agents",
            "operation": "SELECT",
            "query": "SELECT * FROM agents;",
            "expected_columns": ["id", "agent_name", "status", "created_at"],
            "expected_row_count": "multiple",
            "description": "Retrieves all agent records from the agents table"
        }}

        2️⃣ SELECT with condition:
        {{
            "action_key": "get_active_agents",
            "intent": "get all active agents",
            "table": "agents",
            "operation": "SELECT",
            "query": "SELECT * FROM agents WHERE status = 'active';",
            "expected_columns": ["id", "agent_name", "status", "created_at"],
            "expected_row_count": "multiple",
            "description": "Retrieves only active agents from the agents table"
        }}

        3️⃣ SELECT single record by ID:
        {{
            "action_key": "get_agent_by_id",
            "intent": "get agent with id 5",
            "table": "agents",
            "operation": "SELECT",
            "query": "SELECT * FROM agents WHERE id = 5;",
            "expected_columns": ["id", "agent_name", "status", "created_at"],
            "expected_row_count": "single",
            "description": "Retrieves specific agent by ID"
        }}

        4️⃣ COUNT records:
        {{
            "action_key": "count_all_agents",
            "intent": "count how many agents exist",
            "table": "agents",
            "operation": "SELECT",
            "query": "SELECT COUNT(*) as total FROM agents;",
            "expected_columns": ["total"],
            "expected_row_count": "single",
            "description": "Counts total number of agents"
        }}

        5️⃣ Verify column exists:
        {{
            "action_key": "verify_agent_name_column",
            "intent": "verify that the agents table contains an agent name column",
            "table": "agents",
            "operation": "SELECT",
            "query": "SELECT agent_name FROM agents LIMIT 1;",
            "expected_columns": ["agent_name"],
            "expected_row_count": "single",
            "description": "Verifies that agent_name column exists and is accessible"
        }}

        🚫 **FORBIDDEN**:
        ❌ NO explanations or comments outside JSON
        ❌ NO markdown code blocks
        ❌ NO corrections to user's text - use EXACTLY what they wrote
        ❌ NO missing fields - ALL fields are REQUIRED
        ❌ NO tables/columns not in the schema

        ═══════════════════════════════════════════════════════════════════════════════════════
        🏁 **GENERATE COMPLETE DB QUERY ACTION METADATA JSON NOW** 🏁
        ═══════════════════════════════════════════════════════════════════════════════════════
        """


def get_db_query_retry_prompt_enhanced(
    table: str,
    intent: str,
    failed_query: str,
    error_message: str,
    ai_analysis: str,
    stored_metadata: dict,
    schema_context: str,
) -> str:
    """
    Generate ENHANCED retry prompt with AI analysis and all original context.

    This prompt includes:
    - AI analysis from first attempt (why it failed)
    - Original stored_metadata from learning database
    - Original schema_context
    - Error details

    Args:
        table: The database table name
        intent: Original user intent
        failed_query: The SQL query that failed
        error_message: Error message from execution
        ai_analysis: AI's analysis of why the first attempt failed
        stored_metadata: Original stored action from learning database
        schema_context: Database schema for reference
    """

    # Build stored metadata section
    stored_section = """
        ═══════════════════════════════════════════════════════════════════════════════════════
        📚 **ORIGINAL STORED ACTION FROM LEARNING DATABASE**:
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    if stored_metadata:
        stored_section += f"""
        This action was used in the FIRST attempt and FAILED:
        
        - Action Key: {stored_metadata.get('action_key', 'unknown')}
        - Intent: {stored_metadata.get('intent', 'unknown')}
        - Query: {stored_metadata.get('query', 'unknown')}
        - Table: {stored_metadata.get('table', 'unknown')}
        - Status: {stored_metadata.get('status', 'unknown')}
        """
    else:
        stored_section += """
        No stored action was used (first attempt was generated from schema).
        """

    stored_section += """
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    # Build schema context section
    schema_section = """
        ═══════════════════════════════════════════════════════════════════════════════════════
        📖 **DATABASE SCHEMA CONTEXT**:
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    if schema_context:
        schema_section += f"""
        {schema_context}
        """
    else:
        schema_section += """
        No schema documentation available.
        """

    schema_section += """
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    # Build AI analysis section
    analysis_section = f"""
        ═══════════════════════════════════════════════════════════════════════════════════════
        🤖 **AI ANALYSIS OF FAILED ATTEMPT** (IMPORTANT - Learn from this!):
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        The AI analyzed why the first attempt failed:
        
        {ai_analysis if ai_analysis else 'No AI analysis available'}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    return f"""
        ═══════════════════════════════════════════════════════════════════════════════════════
        🔄 **DB QUERY RETRY** - Fix Failed Query Using AI Analysis
        ═══════════════════════════════════════════════════════════════════════════════════════

        **TABLE**: `{table}`
        **INTENT**: "{intent}"
        
        {stored_section}
        
        {schema_section}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        ❌ **FAILED ATTEMPT DETAILS**:
        ═══════════════════════════════════════════════════════════════════════════════════════

        The following SQL query was attempted and FAILED:
        
        💥 FAILED QUERY:
        {failed_query}

        🔴 ERROR MESSAGE:
        {error_message}
        
        {analysis_section}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        📋 **YOUR TASK**:
        ═══════════════════════════════════════════════════════════════════════════════════════

        1. **STUDY** the AI analysis to understand WHY the first attempt failed
        2. **AVOID** repeating the same mistake
        3. **REFER** to the schema context for correct table/column names
        4. **GENERATE** a corrected SQL query

        ⚡ **COMMON FIXES**:
        - Table doesn't exist → Check schema for correct table name
        - Unknown column → Check schema for correct column name
        - Syntax error → Fix SQL syntax
        - Ambiguous column → Add table alias prefix
        - Data type mismatch → Cast or convert data types

        ═══════════════════════════════════════════════════════════════════════════════════════
        📤 **REQUIRED OUTPUT FORMAT** (JSON ONLY):
        ═══════════════════════════════════════════════════════════════════════════════════════

        {{
            "action_key": "retry_query_identifier",
            "intent": "{intent}",
            "table": "{table}",
            "operation": "SELECT|INSERT|UPDATE|DELETE",
            "query": "CORRECTED SQL QUERY HERE;",
            "expected_columns": ["col1", "col2"],
            "expected_row_count": "single|multiple|none",
            "description": "Brief description"
        }}

        🚫 NO explanations outside JSON, NO markdown code blocks

        ═══════════════════════════════════════════════════════════════════════════════════════
        🏁 **GENERATE CORRECTED QUERY ACTION NOW** 🏁
        ═══════════════════════════════════════════════════════════════════════════════════════
        """


# =============================================================================
# UI INTENT-BASED EXECUTION PROMPTS
# =============================================================================


def get_ui_step_action_prompt(
    step_intent: str,
    step_type: str,
    relevant_elements: list,
    page_url: str,
    previous_steps: list = None,
) -> str:
    """
    Generate prompt for GitLab Duo to determine action for a single UI step.

    Args:
        step_intent: The step text (e.g., "fill username with standard_user")
        step_type: Given/When/Then/And
        relevant_elements: Elements retrieved by IntentLocatorLibrary
        page_url: Current page URL
        previous_steps: List of previously executed steps for context
    """

    elements_str = "\n".join(
        [f"  {i+1}. {elem[:300]}" for i, elem in enumerate(relevant_elements[:10])]
    )

    previous_context = ""
    if previous_steps:
        prev_str = "\n".join(
            [
                f"  - {s.get('step_type', '')} {s.get('intent', '')}: {s.get('status', 'pending')}"
                for s in previous_steps[-3:]
            ]
        )
        previous_context = f"\n## Previous Steps Executed\n{prev_str}\n"

    return f"""
        Your expertise: Playwright browser automation, CSS/XPath selectors, and UI testing.

        📋 **MISSION**: Analyze the step and determine the exact Playwright action to perform.

        📥 **INPUT DATA**
        ═══════════════════════════════════════════════════════════════════════════════════════

        🌐 CURRENT PAGE URL:
        {page_url}

        📝 STEP TO EXECUTE:
        Type: {step_type}
        Intent: {step_intent}
        {previous_context}
        🎯 RELEVANT ELEMENTS FOUND ON PAGE:
        {elements_str}

        ═══════════════════════════════════════════════════════════════════════════════════════

        ⚡ **ACTION DETERMINATION RULES** ⚡
        ═══════════════════════════════════════════════════════════════════════════════════════

        1️⃣ **NAVIGATE ACTION** (keywords: navigate, go to, open, visit)
           - Extract page reference from intent
           - Return: {{"action": "navigate", "page_ref": "login_page"}}

        2️⃣ **CLICK ACTION** (keywords: click, press, tap, submit)
           - Find best matching button/link from elements
           - Return: {{"action": "click", "locator": "#element-selector"}}

        3️⃣ **FILL ACTION** (keywords: fill, enter, type, input, write)
           - Find best matching input field from elements
           - Extract value from intent (after "with", "as", "=")
           - Return: {{"action": "fill", "locator": "#input-selector", "value": "text to enter"}}

        4️⃣ **SELECT ACTION** (keywords: select, choose, pick, dropdown)
           - Find best matching select/dropdown from elements
           - Extract option value from intent
           - Return: {{"action": "select", "locator": "#select-selector", "value": "option"}}

        5️⃣ **VERIFY ACTION** (keywords: verify, assert, check, see, should, displayed, visible, equals, is, be)
           - Determine what to verify from intent
           - ⚠️ CRITICAL: Use the EXACT text from the intent - DO NOT correct typos or spelling!
           - If intent says "Header should be Swag lamb", use "Swag lamb" NOT "Swag Labs"
           
           **VERIFICATION TYPES:**
           - For "should be X" / "equals X" / "is X" → Use "text_equals" to compare element text with expected value
           - For "should contain X" → Use "text_contains" to check if text contains expected value
           - For "should see X" / "X visible" → Use "text_visible" to check if text is visible on page
           - For element visibility → Use "element_visible" to check if element is visible
           - For URL checks → Use "url_contains" to check URL
           
           **EXAMPLES:**
           - "Header should be Swag Labs" → {{"action": "verify", "checks": [{{"type": "text_equals", "locator": ".header", "expected_text": "Swag Labs"}}]}}
           - "Title should contain Login" → {{"action": "verify", "checks": [{{"type": "text_contains", "locator": "h1", "expected_text": "Login"}}]}}
           - "I should see Welcome" → {{"action": "verify", "checks": [{{"type": "text_visible", "text": "Welcome"}}]}}
           - "Login button visible" → {{"action": "verify", "checks": [{{"type": "element_visible", "locator": "#login-btn"}}]}}
           
           Return: {{"action": "verify", "checks": [
               {{"type": "element_visible", "locator": "#element"}},
               {{"type": "url_contains", "value": "expected-url-part"}},
               {{"type": "text_visible", "text": "EXACT text from intent - no corrections"}},
               {{"type": "text_equals", "locator": "#element", "expected_text": "EXACT expected text"}},
               {{"type": "text_contains", "locator": "#element", "expected_text": "text to find"}}
           ]}}

        6️⃣ **WAIT ACTION** (keywords: wait, pause)
           - Return: {{"action": "wait", "locator": "#element-to-wait-for"}}

        7️⃣ **HOVER ACTION** (keywords: hover, mouse over)
           - Return: {{"action": "hover", "locator": "#element-selector"}}

        8️⃣ **START_CAPTURE ACTION** (keywords: start capturing, intercept, listen to, monitor network, start network)
           - Start capturing network/API calls
           - Return: {{"action": "start_capture", "url_pattern": "**/*"}}
           - For specific APIs: {{"action": "start_capture", "url_pattern": "**/api/*"}}

        9️⃣ **VALIDATE_API ACTION** (keywords: validate api, api called, api returned, check api, verify api, network call)
           - Validate that an API was called with expected result
           - Extract URL pattern, method, status, and body requirements from intent
           - Return: {{"action": "validate_api", "url_pattern": "**/api/login*", "method": "POST", "expected_status": 200, "expected_body_contains": "token"}}
           - Minimal: {{"action": "validate_api", "url_pattern": "**/api/endpoint*"}}

        🔟 **STOP_CAPTURE ACTION** (keywords: stop capturing, stop network, stop listening)
           - Stop capturing network calls
           - Return: {{"action": "stop_capture"}}

        🚨 **OUTPUT REQUIREMENTS** 🚨
        ═══════════════════════════════════════════════════════════════════════════════════════

        🔥 **CRITICAL**: Return ONLY a valid JSON object!

        ✅ Single JSON action object
        ✅ Use exact locators from provided elements when possible
        ✅ Extract values EXACTLY as written in the intent - NO corrections, NO fixes, NO spelling corrections!
        ✅ If the user wrote "Swag lamb", use "Swag lamb" - even if you think it's a typo

        🚫 **FORBIDDEN**:
        ❌ NO explanations or comments
        ❌ NO markdown code blocks
        ❌ NO multiple actions
        ❌ NO placeholders
        ❌ NO correcting user's text/values - use EXACTLY what they wrote!

        ═══════════════════════════════════════════════════════════════════════════════════════
        🏁 **GENERATE ACTION JSON NOW** 🏁
        ═══════════════════════════════════════════════════════════════════════════════════════
        """


def get_ui_step_verification_prompt(
    step_intent: str, relevant_elements: list, page_url: str, page_title: str = ""
) -> str:
    """
    Generate prompt for GitLab Duo to verify a 'Then verify' step.

    Args:
        step_intent: The verification intent
        relevant_elements: Elements retrieved by IntentLocatorLibrary
        page_url: Current page URL
        page_title: Current page title
    """

    elements_str = "\n".join(
        [f"  {i+1}. {elem[:300]}" for i, elem in enumerate(relevant_elements[:15])]
    )

    return f"""
        Your expertise: QA validation, UI testing, and page state verification.

        📋 **MISSION**: Verify if the current page state matches the expected condition.

        📥 **INPUT DATA**
        ═══════════════════════════════════════════════════════════════════════════════════════

        🌐 CURRENT PAGE STATE:
        URL: {page_url}
        Title: {page_title}

        ✅ VERIFICATION REQUIRED:
        {step_intent}

        🎯 ELEMENTS FOUND ON PAGE:
        {elements_str}

        ═══════════════════════════════════════════════════════════════════════════════════════

        ⚡ **VERIFICATION LOGIC** ⚡
        ═══════════════════════════════════════════════════════════════════════════════════════

        Analyze what needs to be verified:
        1. Check if current URL matches expected page
        2. Check if expected elements are present
        3. Check if expected text is visible
        4. Consider the intent's expectation

        🚨 **OUTPUT REQUIREMENTS** 🚨
        ═══════════════════════════════════════════════════════════════════════════════════════

        Return ONLY a valid JSON object:
        {{
          "success": true/false,
          "reason": "Brief explanation",
          "evidence": ["Evidence 1", "Evidence 2"]
        }}

        Examples:
        - Pass: {{"success": true, "reason": "Inventory page displayed with products", "evidence": ["URL contains inventory", "6 products visible"]}}
        - Fail: {{"success": false, "reason": "Still on login page with error", "evidence": ["URL is /", "Error message visible"]}}

        ═══════════════════════════════════════════════════════════════════════════════════════
        """


def get_ui_step_retry_prompt(
    step_intent: str,
    failed_action: dict,
    error: str,
    relevant_elements: list,
    page_url: str,
) -> str:
    """
    Generate prompt for GitLab Duo to fix a failed UI step.

    Args:
        step_intent: Original step intent
        failed_action: The action that failed
        error: Error message
        relevant_elements: Fresh elements from current page
        page_url: Current page URL
    """

    elements_str = "\n".join(
        [f"  {i+1}. {elem[:300]}" for i, elem in enumerate(relevant_elements[:10])]
    )

    return f"""
        Your expertise: Playwright debugging, selector fixing, and UI automation.

        📋 **MISSION**: Fix the failed action by finding a better locator.

        📥 **INPUT DATA**
        ═══════════════════════════════════════════════════════════════════════════════════════

        📝 STEP INTENT:
        {step_intent}

        ❌ FAILED ACTION:
        {failed_action}

        🔴 ERROR:
        {error}

        🌐 CURRENT PAGE:
        URL: {page_url}

        🎯 FRESH ELEMENTS FROM PAGE:
        {elements_str}

        ═══════════════════════════════════════════════════════════════════════════════════════

        ⚡ **FIX STRATEGY** ⚡
        ═══════════════════════════════════════════════════════════════════════════════════════

        1. Analyze why the locator failed (not found, not visible, etc.)
        2. Find a better matching element from the fresh elements list
        3. Use data-test, id, or unique class attributes when possible
        4. Return corrected action with new locator

        ⚠️ **CRITICAL CONSTRAINTS** ⚠️
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        🚫 You may ONLY fix the LOCATOR/SELECTOR - NOT the values or text!
        🚫 If the failed action checks for text "Swag lamb", you MUST keep "Swag lamb"
        🚫 Do NOT change: "value", "text", "expected" fields - these come from user's intent
        � If the text/value in user's intent doesn't exist on page, the action SHOULD FAIL
        
        ✅ You CAN change: "locator", "selector" - to find the correct element
        ✅ If there's no way to fix the locator, return the original action unchanged

        �🚨 **OUTPUT REQUIREMENTS** 🚨
        ═══════════════════════════════════════════════════════════════════════════════════════

        Return ONLY the corrected JSON action object (same format as failed action).
        DO NOT change any text/value fields from the original action!

        ═══════════════════════════════════════════════════════════════════════════════════════
        """


def get_ui_module_retry_prompt(
    step_intent: str,
    step_type: str,
    module: str,
    page_url: str,
    failed_action: dict,
    error: str,
    ai_analysis: str,
    stored_metadata: dict,
    relevant_elements: list,
    previous_steps: list = None,
) -> str:
    """
    Generate ENHANCED retry prompt with AI analysis and all original context.

    This prompt includes:
    - AI analysis from first attempt (why it failed)
    - Original stored_metadata from learning database
    - Fresh elements from current page
    - All context from original prompt

    Args:
        step_intent: Original step intent
        step_type: Given/When/Then/And
        module: The UI module name
        page_url: Current page URL
        failed_action: The action that failed
        error: Error message from execution
        ai_analysis: AI's analysis of why the first attempt failed
        stored_metadata: Original stored action from learning database
        relevant_elements: Fresh elements from current page
        previous_steps: List of previously executed steps
    """

    elements_str = "\n".join(
        [f"  {i+1}. {elem[:400]}" for i, elem in enumerate(relevant_elements[:15])]
    )

    previous_steps_str = ""
    if previous_steps:
        previous_steps_str = "\n".join([f"  - {s}" for s in previous_steps[-5:]])

    # Build stored metadata section
    stored_section = """
        ═══════════════════════════════════════════════════════════════════════════════════════
        📚 **ORIGINAL STORED ACTION FROM LEARNING DATABASE**:
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    if stored_metadata:
        action_json = stored_metadata.get("action_json", {})
        if isinstance(action_json, str):
            try:
                import json

                action_json = json.loads(action_json)
            except:
                action_json = {}

        stored_section += f"""
        This action was used in the FIRST attempt and FAILED:
        
        - Action Key: {stored_metadata.get('action_key', 'unknown')}
        - Intent: {stored_metadata.get('intent', 'unknown')}
        - Action Type: {action_json.get('type', 'unknown')}
        - Locator: {action_json.get('locator', 'unknown')}
        - Value: {action_json.get('value', 'N/A')}
        - Status: {stored_metadata.get('status', 'unknown')}
        """
    else:
        stored_section += """
        No stored action was used (first attempt was with live HTML).
        """

    stored_section += """
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    # Build AI analysis section
    analysis_section = f"""
        ═══════════════════════════════════════════════════════════════════════════════════════
        🤖 **AI ANALYSIS OF FAILED ATTEMPT** (IMPORTANT - Learn from this!):
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        The AI analyzed why the first attempt failed:
        
        {ai_analysis if ai_analysis else 'No AI analysis available'}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    return f"""
        ═══════════════════════════════════════════════════════════════════════════════════════
        🔄 **UI ACTION RETRY** - Fix Failed Action Using AI Analysis
        ═══════════════════════════════════════════════════════════════════════════════════════

        **STEP TYPE**: [{step_type}]
        **STEP INTENT**: "{step_intent}"
        **MODULE**: {module}
        **PAGE URL**: {page_url}

        ═══════════════════════════════════════════════════════════════════════════════════════
        📜 **PREVIOUS STEPS** (for context):
        ═══════════════════════════════════════════════════════════════════════════════════════
        {previous_steps_str if previous_steps_str else "  (None - this is the first step)"}
        
        {stored_section}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        ❌ **FAILED ATTEMPT DETAILS**:
        ═══════════════════════════════════════════════════════════════════════════════════════

        The following action was attempted and FAILED:
        
        💥 FAILED ACTION:
        {failed_action}

        🔴 ERROR MESSAGE:
        {error}
        
        {analysis_section}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        🎯 **FRESH LIVE HTML ELEMENTS** (use these for new action):
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        These are the CURRENT elements on the page. Use these to find a better locator:
        
        {elements_str}

        ═══════════════════════════════════════════════════════════════════════════════════════
        📋 **YOUR TASK**:
        ═══════════════════════════════════════════════════════════════════════════════════════

        1. **STUDY** the AI analysis to understand WHY the first attempt failed
        2. **AVOID** repeating the same mistake
        3. **FIND** a better element from the fresh HTML elements above
        4. **GENERATE** a new action with a corrected locator

        ⚠️ **CRITICAL CONSTRAINTS** ⚠️
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        🚫 You may ONLY fix the LOCATOR/SELECTOR - NOT the values or text!
        🚫 The "value", "text", "expected" fields MUST remain EXACTLY as in the failed action
        🚫 If the element truly doesn't exist on the page, the action SHOULD FAIL
        
        ✅ You CAN change: "locator", "selector" fields
        ✅ Use data-test, id, or unique class attributes when possible
        ✅ Try a completely different selector strategy if the old one failed

        ═══════════════════════════════════════════════════════════════════════════════════════
        📤 **REQUIRED OUTPUT FORMAT** (JSON ONLY):
        ═══════════════════════════════════════════════════════════════════════════════════════

        Return the CORRECTED action JSON in the SAME format as the failed action.
        
        Example:
        {{
            "action_key": "retry_login_click",
            "intent": "{step_intent}",
            "action_json": {{
                "type": "click",
                "locator": "[data-test='login-button']"
            }}
        }}

        🚫 **FORBIDDEN**:
        ❌ NO explanations outside JSON
        ❌ NO markdown code blocks
        ❌ NO changing value/text fields

        ═══════════════════════════════════════════════════════════════════════════════════════
        🏁 **GENERATE CORRECTED ACTION NOW** 🏁
        ═══════════════════════════════════════════════════════════════════════════════════════
        """


def get_ui_step_failure_analysis_prompt(
    step_intent: str,
    step_type: str,
    failed_action: dict,
    error: str,
    relevant_elements: list,
    page_url: str,
    page_title: str = "",
    previous_steps: list = None,
) -> str:
    """
    Generate prompt for analyzing why a UI step failed.

    Args:
        step_intent: The step text that failed
        step_type: Given/When/Then/And
        failed_action: The action that was attempted
        error: Error message from execution
        relevant_elements: Elements found on page
        page_url: Current page URL
        page_title: Current page title
        previous_steps: List of previously executed steps
    """

    elements_str = (
        "\n".join([f"  - {elem[:300]}" for elem in relevant_elements[:10]])
        if relevant_elements
        else "No elements found"
    )

    prev_context = ""
    if previous_steps:
        prev_context = "\n".join(
            [
                f"  - [{s.get('step_type', '')}] {s.get('intent', '')}: {s.get('status', 'pending')}"
                for s in previous_steps[-5:]
            ]  # Last 5 steps only
        )

    return f"""Analyze why this UI test step failed and provide insights.

**Failed Step:**
- Type: {step_type}
- Intent: {step_intent}

**Action Attempted:** {failed_action}

**Error:** {error}

**Page State:**
- URL: {page_url}
- Title: {page_title}

**Available Elements on Page:**
{elements_str}

**Previous Steps:**
{prev_context if prev_context else "None"}

**Your Task:**
Analyze the failure and determine:
1. Why did it fail? (element not found, wrong state, timing issue, etc.)
2. What was expected vs what was found?
3. Is this a test issue or application issue?

**Response Format (JSON only):**
{{
    "root_cause": "Brief description of why it failed",
    "failure_type": "element_not_found|wrong_state|data_mismatch|timing|test_bug|app_bug",
    "expected": "What the test expected",
    "actual": "What was found on the page",
    "recommendation": "How to fix this",
    "is_test_issue": true/false
}}"""


# =============================================================================
# UI MODULE-BASED LEARNING PROMPTS (DUO returns full metadata dict)
# =============================================================================


def get_ui_module_action_prompt(
    step_intent: str,
    step_type: str,
    module: str,
    page_url: str,
    stored_metadata: dict = None,
    relevant_elements: list = None,
    previous_steps: list = None,
) -> str:
    """
    Generate prompt for GitLab Duo to decide on action and return FULL METADATA dict.

    IMPORTANT: Both sections (STORED METADATA and LIVE HTML ELEMENTS) are ALWAYS included
    in the prompt. The data inside depends on availability:
    - stored_metadata: Shows data if [correct] action found, otherwise "No stored action found"
    - relevant_elements: Shows data if retrieved, otherwise "No elements retrieved"

    DUO must return the SAME metadata format that will be stored:
    {
        "action_key": "click_login",
        "intent": "click login button",
        "action_type": "click",
        "locator": "#login-btn",
        "action_json": {...},
        "playwright_code": "page.click('#login-btn')"
    }

    Args:
        step_intent: The step text (e.g., "fill username with standard_user")
        step_type: Given/When/Then/And
        module: Current module name (e.g., "inventory", "login")
        page_url: Current page URL
        stored_metadata: Previous stored action from ChromaDB (optional)
        relevant_elements: Fresh HTML elements from IntentLocatorLibrary (optional)
        previous_steps: List of previously executed steps for context
    """

    # ====== SECTION 1: STORED METADATA (ALWAYS PRESENT) ======
    if stored_metadata:
        stored_context = f"""
        📦 STORED ACTION FROM LEARNING DATABASE:
        ═══════════════════════════════════════════════════════════════════════════════════════
        ✅ Found a [correct] stored action that previously worked!
        
        • Action Key: {stored_metadata.get('action_key', 'N/A')}
        • Intent: {stored_metadata.get('intent', 'N/A')}
        • Action Type: {stored_metadata.get('action_type', 'N/A')}
        • Locator: {stored_metadata.get('locator', 'N/A')}
        • Playwright Code: {stored_metadata.get('playwright_code', 'N/A')}
        • Status: {stored_metadata.get('status', 'N/A')}
        
        ⚡ RECOMMENDATION: REUSE this action if the intent matches exactly.
           MODIFY only if the current intent is slightly different.
        ═══════════════════════════════════════════════════════════════════════════════════════
        """
    else:
        stored_context = """
        📦 STORED ACTION FROM LEARNING DATABASE:
        ═══════════════════════════════════════════════════════════════════════════════════════
        ❌ No stored action found for this intent in the learning database.
        
        This is a NEW action that needs to be generated from the live HTML elements below.
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    # ====== SECTION 2: LIVE HTML ELEMENTS (ALWAYS PRESENT) ======
    if relevant_elements and len(relevant_elements) > 0:
        elements_str = "\n".join(
            [
                f"        {i+1}. {elem[:300]}"
                for i, elem in enumerate(relevant_elements[:10])
            ]
        )
        elements_context = f"""
        🎯 LIVE HTML ELEMENTS FROM CURRENT PAGE:
        ═══════════════════════════════════════════════════════════════════════════════════════
        {elements_str}
        
        ⚠️ Use these elements to GENERATE or VALIDATE the action.
           If stored action exists, verify the locator still matches these elements.
        ═══════════════════════════════════════════════════════════════════════════════════════
        """
    else:
        elements_context = """
        🎯 LIVE HTML ELEMENTS FROM CURRENT PAGE:
        ═══════════════════════════════════════════════════════════════════════════════════════
        ❌ No relevant elements retrieved from the current page.
        
        If stored action exists, use it directly.
        If no stored action, this may be a navigation or special action type.
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    # Format previous steps context
    previous_context = ""
    if previous_steps:
        prev_str = "\n".join(
            [
                f"        - {s.get('step_type', '')} {s.get('intent', '')}: {s.get('status', 'pending')}"
                for s in previous_steps[-3:]
            ]
        )
        previous_context = f"""
        ## Previous Steps Executed
        {prev_str}
        """

    return f"""
        Your expertise: Playwright browser automation, CSS/XPath selectors, and UI testing.

        📋 **MISSION**: Analyze the step and return a COMPLETE ACTION METADATA object.

        📥 **INPUT DATA**
        ═══════════════════════════════════════════════════════════════════════════════════════

        🏷️ MODULE: {module}
        🌐 CURRENT PAGE URL: {page_url}

        📝 STEP TO EXECUTE:
        Type: {step_type}
        Intent: {step_intent}
        {previous_context}
        
        {stored_context}
        
        {elements_context}

        ═══════════════════════════════════════════════════════════════════════════════════════

        ⚡ **DECISION LOGIC** ⚡
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        IF stored action exists AND matches current intent:
            → REUSE the stored locator and action
            → Verify against live HTML elements if available
        
        ELSE IF live HTML elements available:
            → GENERATE new action from the live HTML elements
            → Pick the best matching element for the intent
        
        ELSE:
            → Handle as navigation or special action type

        ═══════════════════════════════════════════════════════════════════════════════════════

        ⚡ **ACTION TYPE DETERMINATION** ⚡
        ═══════════════════════════════════════════════════════════════════════════════════════

        Based on keywords in the intent, determine action_type:
        - "navigate/go to/open/visit" → action_type: "navigate"
        - "click/press/tap/submit" → action_type: "click"
        - "fill/enter/type/input" → action_type: "fill"
        - "select/choose/pick/dropdown" → action_type: "select"
        - "verify/assert/check/see/should" → action_type: "verify"
        - "wait" → action_type: "wait"
        - "hover" → action_type: "hover"
        - "start capturing/intercept/monitor" → action_type: "start_capture"
        - "validate api/api called/check api" → action_type: "validate_api"
        - "stop capturing" → action_type: "stop_capture"

        ═══════════════════════════════════════════════════════════════════════════════════════

        🚨 **OUTPUT REQUIREMENTS** 🚨 (CRITICAL - Return this EXACT format!)
        ═══════════════════════════════════════════════════════════════════════════════════════

        Return a JSON object with ALL these fields:

        {{
            "action_key": "<action_type>_<target>",  // e.g., "click_login", "fill_username"
            "intent": "{step_intent}",
            "action_type": "<type>",  // click, fill, navigate, verify, etc.
            "locator": "<css_or_xpath_selector>",  // The element selector
            "action_json": {{
                "action": "<action_type>",
                "locator": "<selector>",
                "value": "<value_if_applicable>",
                // Additional fields based on action type
            }},
            "playwright_code": "<complete_playwright_python_code>"  // e.g., "page.click('#login-btn')"
        }}

        ═══════════════════════════════════════════════════════════════════════════════════════

        📋 **EXAMPLES BY ACTION TYPE**:

        1️⃣ CLICK:
        {{
            "action_key": "click_login_button",
            "intent": "click the login button",
            "action_type": "click",
            "locator": "#login-button",
            "action_json": {{"action": "click", "locator": "#login-button"}},
            "playwright_code": "page.click('#login-button')"
        }}

        2️⃣ FILL:
        {{
            "action_key": "fill_username_standard",
            "intent": "fill username with standard_user",
            "action_type": "fill",
            "locator": "#user-name",
            "action_json": {{"action": "fill", "locator": "#user-name", "value": "standard_user"}},
            "playwright_code": "page.fill('#user-name', 'standard_user')"
        }}

        3️⃣ NAVIGATE:
        {{
            "action_key": "navigate_inventory",
            "intent": "go to inventory page",
            "action_type": "navigate",
            "locator": "",
            "action_json": {{"action": "navigate", "page_ref": "inventory_page"}},
            "playwright_code": "page.goto('https://example.com/inventory.html')"
        }}

        4️⃣ VERIFY:
        {{
            "action_key": "verify_header_products",
            "intent": "I should see header Products",
            "action_type": "verify",
            "locator": ".title",
            "action_json": {{
                "action": "verify",
                "checks": [{{"type": "text_visible", "text": "Products"}}]
            }},
            "playwright_code": "expect(page.get_by_text('Products')).to_be_visible()"
        }}

        5️⃣ VALIDATE_API:
        {{
            "action_key": "validate_api_login",
            "intent": "validate that login API returned 200",
            "action_type": "validate_api",
            "locator": "",
            "action_json": {{
                "action": "validate_api",
                "url_pattern": "**/api/login*",
                "method": "POST",
                "expected_status": 200
            }},
            "playwright_code": "# Network validation for **/api/login*"
        }}

        🚫 **FORBIDDEN**:
        ❌ NO explanations or comments outside JSON
        ❌ NO markdown code blocks
        ❌ NO corrections to user's text - use EXACTLY what they wrote
        ❌ NO missing fields - ALL fields are REQUIRED

        ═══════════════════════════════════════════════════════════════════════════════════════
        🏁 **GENERATE COMPLETE ACTION METADATA JSON NOW** 🏁
        ═══════════════════════════════════════════════════════════════════════════════════════
        """


# ==================== API ENDPOINT ACTION PROMPT ====================
def get_api_endpoint_action_prompt(
    resource: str,
    intent: str,
    swagger_context: str = "",
    stored_metadata: dict = None,
    base_url: str = "",
) -> str:
    """
    Generate prompt for DUO to produce API endpoint action metadata.

    This prompt follows the same pattern as UI module action prompt:
    - If stored_metadata provided: DUO validates/updates the stored action
    - If swagger_context provided: DUO generates new action from swagger

    Args:
        resource: The API resource name (e.g., "users", "login", "products")
        intent: User's intent describing what API action to perform
        swagger_context: Swagger specification context for this endpoint (optional)
        stored_metadata: Previously stored action metadata from learning collection (optional)
        base_url: Base URL for the API

    Returns:
        Formatted prompt string for DUO
    """

    # Build context section
    context_section = ""

    if stored_metadata:
        context_section = f"""
        ═══════════════════════════════════════════════════════════════════════════════════════
        📚 **STORED LEARNED ACTION** (from previous successful execution):
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        This action was previously executed successfully. Use it as reference:
        
        • Action Key: {stored_metadata.get('action_key', 'unknown')}
        • Intent: {stored_metadata.get('intent', 'unknown')}
        • Method: {stored_metadata.get('method', 'unknown')}
        • Endpoint: {stored_metadata.get('endpoint', 'unknown')}
        • cURL: {stored_metadata.get('curl', 'unknown')}
        • Expected Status: {stored_metadata.get('expected_status', 'unknown')}
        • Request Body: {stored_metadata.get('request_body', '{{}}')}
        • Status: {stored_metadata.get('status', 'unknown')}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    if swagger_context:
        context_section += f"""
        ═══════════════════════════════════════════════════════════════════════════════════════
        📖 **SWAGGER SPECIFICATION CONTEXT**:
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        {swagger_context}
        
        ═══════════════════════════════════════════════════════════════════════════════════════
        """

    return f"""
        ═══════════════════════════════════════════════════════════════════════════════════════
        🎯 **API ENDPOINT ACTION GENERATOR** - Generate API Request Metadata
        ═══════════════════════════════════════════════════════════════════════════════════════

        **RESOURCE**: `{resource}`
        **INTENT**: "{intent}"
        **BASE URL**: {base_url}
        
        {context_section}

        ═══════════════════════════════════════════════════════════════════════════════════════
        📋 **YOUR TASK**:
        ═══════════════════════════════════════════════════════════════════════════════════════
        
        Generate a COMPLETE API action metadata JSON object that can be used to execute this API request.
        
        **RULES**:
        1. Generate a unique `action_key` based on resource + method + purpose
        2. Use the intent EXACTLY as provided
        3. Determine the correct HTTP method (GET, POST, PUT, DELETE, PATCH)
        4. Build the complete endpoint path with any path parameters
        5. Generate a working cURL command
        6. Include request body if needed (for POST, PUT, PATCH)
        7. Set appropriate expected status code

        ═══════════════════════════════════════════════════════════════════════════════════════
        📤 **REQUIRED OUTPUT FORMAT** (JSON ONLY - NO MARKDOWN, NO EXPLANATION):
        ═══════════════════════════════════════════════════════════════════════════════════════

        {{
            "action_key": "unique_action_identifier",
            "intent": "exact intent as provided",
            "resource": "{resource}",
            "method": "GET|POST|PUT|DELETE|PATCH",
            "endpoint": "/api/path/to/resource",
            "curl": "curl -X METHOD 'base_url/endpoint' -H 'Content-Type: application/json' -d '{{request_body}}'",
            "expected_status": 200,
            "request_body": {{}},
            "headers": {{
                "Content-Type": "application/json"
            }}
        }}

        ═══════════════════════════════════════════════════════════════════════════════════════
        📌 **EXAMPLES**:
        ═══════════════════════════════════════════════════════════════════════════════════════

        1️⃣ GET all users:
        {{
            "action_key": "get_all_users",
            "intent": "get all users from the system",
            "resource": "users",
            "method": "GET",
            "endpoint": "/api/users",
            "curl": "curl -X GET '{base_url}/api/users' -H 'Content-Type: application/json'",
            "expected_status": 200,
            "request_body": {{}},
            "headers": {{"Content-Type": "application/json"}}
        }}

        2️⃣ POST create user:
        {{
            "action_key": "create_new_user",
            "intent": "create a new user with name John",
            "resource": "users",
            "method": "POST",
            "endpoint": "/api/users",
            "curl": "curl -X POST '{base_url}/api/users' -H 'Content-Type: application/json' -d '{{\"name\": \"John\", \"email\": \"john@example.com\"}}'",
            "expected_status": 201,
            "request_body": {{"name": "John", "email": "john@example.com"}},
            "headers": {{"Content-Type": "application/json"}}
        }}

        3️⃣ GET user by ID:
        {{
            "action_key": "get_user_by_id",
            "intent": "get user with id 5",
            "resource": "users",
            "method": "GET",
            "endpoint": "/api/users/5",
            "curl": "curl -X GET '{base_url}/api/users/5' -H 'Content-Type: application/json'",
            "expected_status": 200,
            "request_body": {{}},
            "headers": {{"Content-Type": "application/json"}}
        }}

        4️⃣ DELETE user:
        {{
            "action_key": "delete_user_5",
            "intent": "delete user with id 5",
            "resource": "users",
            "method": "DELETE",
            "endpoint": "/api/users/5",
            "curl": "curl -X DELETE '{base_url}/api/users/5' -H 'Content-Type: application/json'",
            "expected_status": 200,
            "request_body": {{}},
            "headers": {{"Content-Type": "application/json"}}
        }}

        🚫 **FORBIDDEN**:
        ❌ NO explanations or comments outside JSON
        ❌ NO markdown code blocks
        ❌ NO corrections to user's text - use EXACTLY what they wrote
        ❌ NO missing fields - ALL fields are REQUIRED
        ❌ NO placeholder values - use actual values from context

        ═══════════════════════════════════════════════════════════════════════════════════════
        🏁 **GENERATE COMPLETE API ACTION METADATA JSON NOW** 🏁
        ═══════════════════════════════════════════════════════════════════════════════════════
        """
