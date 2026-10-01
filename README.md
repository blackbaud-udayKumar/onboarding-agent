# Onboarding Agent (v1)

Answers new-dev questions from your codebase + internal docs, with citations
back to the file/doc it pulled from. Runs entirely on your machine as a
small local chat page.

## Architecture

```
repo folder ┐
docs folder ┼─▶ ingest/*.py ─▶ chunking.py ─▶ vectorstore.py (local Chroma) ─▶ qa_engine.py ─▶ server.py ─▶ static/index.html
(ADO/Confluence/                                                                    │
 Notion/Slack -                                                                     ▼
 stubbed, phase 2)                                                           Claude API (answers
                                                                              using retrieved
                                                                              chunks only)
```

- **ingest/** — one module per knowledge source. `local_repo.py` and
  `local_docs.py` are live today. `ado_repo.py`, `ado_wiki.py`,
  `confluence.py`, `notion.py`, `slack.py` are real implementations that are
  just switched off until you add credentials (see "Phase 2" below).
- **chunking.py** — splits files into citeable pieces (code: by line range,
  docs: by character blocks).
- **vectorstore.py** — local, persistent Chroma DB. Uses Chroma's built-in
  embedding model, so no external embeddings API/account is needed.
- **qa_engine.py** — retrieves the most relevant chunks for a question and
  asks Claude to answer using only those chunks, citing sources.
- **server.py** + **static/index.html** — a minimal local web chat.

## Setup

1. Install Python 3.10+ if you don't have it.
2. From this folder:
   ```
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env`:
   ```
   cp .env.example .env
   ```
4. Point the indexer at a real repo/docs folder. Easiest way: set
   `REPO_PATH` and `DOCS_PATH` in `.env`, e.g.:
   ```
   REPO_PATH=/path/to/your/repo
   DOCS_PATH=/path/to/your/docs
   ```
   (If you skip this, it defaults to indexing this onboarding-agent
   project itself and the `sample_docs/` folder — fine for a first test run.)

## Get an Anthropic API key

You'll need this before the agent can actually *answer* anything (indexing
works without it).

1. Go to https://console.anthropic.com/ and sign up / log in.
2. Create an API key.
3. Paste it into `.env` as `ANTHROPIC_API_KEY=sk-ant-...`.

## Run it

```
# 1. Build the index (run this any time the repo/docs change)
python build_index.py

# 2. Start the server
uvicorn server:app --reload

# 3. Open http://localhost:8000 and start asking questions
```

If you index a real repo, try questions like:
- "How does authentication work in this codebase?"
- "Where is the payment logic?"
- "What does the deploy process look like?"

Each answer shows the file/doc it was pulled from as clickable chips (when
a source has a URL) or plain labels underneath.

## Phase 2: wiring up Azure DevOps (and other connectors)

You mentioned wanting to hold off on the ADO / Azure setup until the rest
of the agent works end-to-end. When you're ready:

1. Create an Azure DevOps Personal Access Token (Azure DevOps → User
   settings → Personal access tokens) with at least "Code (Read)" scope,
   and wiki read scope if you'll also pull the wiki.
2. Add to `.env`:
   ```
   ADO_ORG_URL=https://dev.azure.com/your-org
   ADO_PROJECT=your-project
   ADO_REPO=your-repo-name
   ADO_WIKI_ID=your-wiki-identifier
   ADO_PAT=your-personal-access-token
   ```
3. In `config.py`, flip these to `"enabled": True`:
   - `SOURCES["azure_devops_repo"]`
   - `SOURCES["azure_devops_wiki"]`
4. Re-run `python build_index.py`.

`ingest/ado_repo.py` and `ingest/ado_wiki.py` already implement the real
Azure DevOps REST API calls (repo file listing + content, wiki page tree +
content) — there's nothing left to code, just credentials to add.

Confluence, Notion, and Slack connectors are stubbed the same way in
`ingest/confluence.py`, `ingest/notion.py`, `ingest/slack.py`, in case any
of those end up being where docs actually live instead of/alongside ADO.

## Moving beyond a local chat page

This local web chat is a v1 delivery choice. The retrieval/answer logic
(`qa_engine.py`, `vectorstore.py`, `chunking.py`) doesn't know or care how
questions arrive, so later you can add:
- A Slack bot: a small handler that calls `QAEngine().ask(question)` on
  each mention/DM and posts the answer back.
- A VS Code extension: a webview or command palette entry that calls the
  same `/api/ask` endpoint this server already exposes.
- A CLI: `python -c "from qa_engine import QAEngine; print(QAEngine().ask('...'))"`

None of the core logic needs to change to support any of these.

## Known limitations (v1)

- No incremental indexing — `build_index.py` re-embeds everything each run.
  Fine for a first version; add change-detection (e.g. hash file contents,
  skip unchanged ones) if re-indexing gets slow on a big repo.
- Local embedding model is good enough to prototype with, but retrieval
  quality on a large/complex codebase will improve if you later switch to
  Voyage AI or OpenAI embeddings in `vectorstore.py`.
- Confluence page bodies come back as raw storage-format HTML; strip tags
  in `chunking.py` if you enable that connector and want cleaner chunks.
- Single-user, local-only. No auth on the web page — don't expose port 8000
  beyond your own machine as-is.
