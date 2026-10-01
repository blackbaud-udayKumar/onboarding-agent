"""
The actual "answer questions using retrieved context, with citations" step.

Flow: embed the question (handled inside VectorStore.query) -> retrieve the
top-K most relevant chunks -> hand them to Claude with instructions to
answer ONLY from that context and cite sources -> return the answer plus
the raw list of sources so the UI can show them even if Claude's inline
citations are imperfect.
"""

import anthropic

import config
from vectorstore import VectorStore

SYSTEM_PROMPT = """You are an onboarding assistant for new engineers on this team.
Answer the user's question using ONLY the context snippets provided below.
Each snippet is labeled with its source (a file path, wiki page, or doc name).

Rules:
- If the context does not contain enough information to answer, say so plainly \
and suggest who or where the person might check instead -- do not guess or make things up.
- Every claim in your answer must be traceable to a snippet. Cite sources inline \
using the exact label shown, like: "Auth is handled via JWT (src/auth/login.py)."
- Prefer concise, direct answers over long ones. Use short paragraphs; only use a \
list if the answer is a genuine sequence of steps.
- If snippets conflict (e.g. an older doc vs newer code), point out the conflict \
rather than picking one silently.
"""


class QAEngine:
    def __init__(self):
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key "
                "(see https://console.anthropic.com/) before asking questions."
            )
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.store = VectorStore()

    def _build_context_block(self, hits: list[dict]) -> str:
        parts = []
        for i, hit in enumerate(hits, start=1):
            source = hit["metadata"].get("source", "unknown source")
            parts.append(f"[Snippet {i} | source: {source}]\n{hit['text']}")
        return "\n\n---\n\n".join(parts)

    def ask(self, question: str) -> dict:
        hits = self.store.query(question, top_k=config.TOP_K)

        if not hits:
            return {
                "answer": (
                    "I don't have anything indexed yet, so I can't answer that. "
                    "Run `python build_index.py` first to index your repo/docs."
                ),
                "sources": [],
            }

        context_block = self._build_context_block(hits)

        message = self.client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Context snippets:\n\n{context_block}\n\n"
                        f"---\n\nQuestion: {question}"
                    ),
                }
            ],
        )

        answer_text = "".join(block.text for block in message.content if block.type == "text")

        # De-duplicate sources for the UI's citation list, preserving order.
        seen = set()
        sources = []
        for hit in hits:
            source = hit["metadata"].get("source", "unknown source")
            url = hit["metadata"].get("url") or None
            key = (source, url)
            if key in seen:
                continue
            seen.add(key)
            sources.append({"source": source, "url": url})

        return {"answer": answer_text, "sources": sources}
