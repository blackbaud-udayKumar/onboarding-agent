"""
Central configuration for the onboarding agent.

Edit SOURCES below to control what gets indexed. Local sources (repo folder,
docs folder) work today with no extra setup. The remote connectors (Azure
DevOps, Confluence, Notion, Slack) are stubbed out in ingest/ and are meant
to be wired up in the final phase, once credentials are ready -- flip
"enabled": True and fill in the matching .env values when you get there.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Where the local vector index is persisted.
CHROMA_DIR = str(BASE_DIR / "data" / "chroma")
COLLECTION_NAME = "onboarding_knowledge"

# LLM settings
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

# How many chunks to retrieve per question.
TOP_K = 6

# Chunking settings
CODE_CHUNK_LINES = 60
CODE_CHUNK_OVERLAP_LINES = 10
TEXT_CHUNK_CHARS = 1500
TEXT_CHUNK_OVERLAP_CHARS = 200

# ---------------------------------------------------------------------------
# SOURCES: what to ingest when you run build_index.py
# ---------------------------------------------------------------------------
# "enabled": True/False turns a source on/off without deleting the config.
# Local sources take a real path. Remote connectors take connection details
# that are read from environment variables (see .env.example) -- leave them
# disabled until you actually configure credentials.

SOURCES = {
    "local_repo": {
        "enabled": True,
        "path": os.getenv("REPO_PATH", str(BASE_DIR)),  # point this at your real repo
        "extensions": [
            ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb",
            ".cs", ".cpp", ".c", ".h", ".rs", ".php", ".sql",
            ".md", ".mdx", ".rst", ".txt", ".yaml", ".yml", ".json",
        ],
        "ignore_dirs": [
            ".git", "node_modules", "venv", ".venv", "__pycache__",
            "dist", "build", ".idea", ".vscode", "data",
        ],
        "max_file_size_kb": 500,
    },
    "local_docs": {
        "enabled": True,
        "path": os.getenv("DOCS_PATH", str(BASE_DIR / "sample_docs")),
        "extensions": [".md", ".txt", ".docx", ".pdf"],
    },

    # --- Remote connectors: stubs today, enable in the final phase ---
    "azure_devops_repo": {
        "enabled": False,
        "org_url": os.getenv("ADO_ORG_URL", ""),
        "project": os.getenv("ADO_PROJECT", ""),
        "repo": os.getenv("ADO_REPO", ""),
        "pat": os.getenv("ADO_PAT", ""),
    },
    "azure_devops_wiki": {
        "enabled": False,
        "org_url": os.getenv("ADO_ORG_URL", ""),
        "project": os.getenv("ADO_PROJECT", ""),
        "wiki_identifier": os.getenv("ADO_WIKI_ID", ""),
        "pat": os.getenv("ADO_PAT", ""),
    },
    "confluence": {
        "enabled": False,
        "base_url": os.getenv("CONFLUENCE_BASE_URL", ""),
        "email": os.getenv("CONFLUENCE_EMAIL", ""),
        "api_token": os.getenv("CONFLUENCE_API_TOKEN", ""),
        "space_keys": [],
    },
    "notion": {
        "enabled": False,
        "api_key": os.getenv("NOTION_API_KEY", ""),
        "page_ids": [],
    },
    "slack": {
        "enabled": False,
        "bot_token": os.getenv("SLACK_BOT_TOKEN", ""),
        "channel_ids": [],
    },
}
