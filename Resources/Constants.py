"""
Constants for API endpoints and headers
"""

from types import SimpleNamespace

services = SimpleNamespace(POSTS="/posts")
# Endpoints as object with attributes
endpoints = SimpleNamespace(
    CHAT_COMPLETION="/chat/completions",
    COMPLETIONS="/completions",
    CODE_SUGGESTIONS="/code_suggestions/completions",
    ADD_POSTS=services.POSTS + "/add",
    GET_POSTS=services.POSTS + "/getPosts",
)

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Headers as object with attributes
headers = SimpleNamespace(
    WITHOUT_TOKEN_HEADERS={"Content-Type": "application/json"},
    WITH_TOKEN_HEADERS={
        "Content-Type": "application/json",
        "Authorization": "Bearer token",
    },
    GITLAB_DUO_HEADERS={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('GITLAB_TOKEN')}",
    },
)


# Legacy constants dictionary
constants = {}
