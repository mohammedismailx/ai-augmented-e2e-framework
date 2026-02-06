from types import SimpleNamespace

# Constant queries
QUERIES = SimpleNamespace(
    GET_POSTS_BY_USER_ID="SELECT * FROM agents WHERE x = {user_id};",
    GET_ALL_AGENTS="SELECT * FROM agents;",
    FETCH_SCHEMA="SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, EXTRA, COLUMN_DEFAULT FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'testdb' ORDER BY TABLE_NAME, ORDINAL_POSITION;",
)


def retrieve_query(query_name, **params):
    """Legacy support for pure retrieval."""
    query_template = getattr(QUERIES, query_name, None)
    if not query_template:
        raise ValueError(f"Query '{query_name}' not found.")
    return query_template.format(**params) if params else query_template
