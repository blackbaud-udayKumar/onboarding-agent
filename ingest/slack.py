"""
Slack connector (optional, disabled by default). Only useful if there's a
channel with genuinely durable knowledge (e.g. #eng-faq) worth indexing --
general chat history is usually too noisy to be good RAG context.

Fill in SLACK_BOT_TOKEN in .env (needs channels:history + channels:read
scopes), list channel_ids in config.py, and set "enabled": True.

Docs: https://api.slack.com/methods/conversations.history
"""

import requests

from .base import BaseSource, Document


class SlackSource(BaseSource):
    name = "slack"

    def is_configured(self) -> bool:
        return bool(self.settings.get("bot_token"))

    def fetch(self) -> list[Document]:
        if not self.is_configured():
            raise RuntimeError("slack is enabled but missing bot_token. Set SLACK_BOT_TOKEN in .env.")

        headers = {"Authorization": f"Bearer {self.settings['bot_token']}"}
        channel_ids = self.settings.get("channel_ids", [])
        docs: list[Document] = []

        for channel_id in channel_ids:
            cursor = None
            while True:
                params = {"channel": channel_id, "limit": 200}
                if cursor:
                    params["cursor"] = cursor
                resp = requests.get(
                    "https://slack.com/api/conversations.history",
                    headers=headers,
                    params=params,
                    timeout=30,
                )
                data = resp.json()
                if not data.get("ok"):
                    break

                for msg in data.get("messages", []):
                    text = msg.get("text", "")
                    if not text.strip() or msg.get("subtype"):  # skip joins/leaves/etc.
                        continue
                    ts = msg.get("ts")
                    docs.append(
                        Document(
                            text=text,
                            source=f"Slack #{channel_id}",
                            source_id=f"slack::{channel_id}::{ts}",
                            metadata={"type": "slack", "ts": ts},
                            url=f"https://slack.com/archives/{channel_id}/p{ts.replace('.', '')}",
                        )
                    )

                cursor = data.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break

        return docs
