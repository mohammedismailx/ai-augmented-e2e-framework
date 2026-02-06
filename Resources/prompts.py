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
