"""
Notion connector (optional, disabled by default). Only needed if some
internal docs live in Notion.

Fill in NOTION_API_KEY in .env, list page_ids (or wire up a search call) in
config.py, and set "enabled": True.

Docs: https://developers.notion.com/reference/retrieve-a-page
"""

import requests

from .base import BaseSource, Document

NOTION_VERSION = "2022-06-28"


def _extract_plain_text(rich_text_list: list) -> str:
    return "".join(rt.get("plain_text", "") for rt in rich_text_list or [])


def _block_to_text(block: dict) -> str:
    block_type = block.get("type")
    content = block.get(block_type, {})
    rich_text = content.get("rich_text")
    if rich_text:
        return _extract_plain_text(rich_text)
    return ""


class NotionSource(BaseSource):
    name = "notion"

    def is_configured(self) -> bool:
        return bool(self.settings.get("api_key"))

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.settings['api_key']}",
            "Notion-Version": NOTION_VERSION,
        }

    def fetch(self) -> list[Document]:
        if not self.is_configured():
            raise RuntimeError("notion is enabled but missing api_key. Set NOTION_API_KEY in .env.")

        headers = self._headers()
        page_ids = self.settings.get("page_ids", [])
        docs: list[Document] = []

        for page_id in page_ids:
            page_resp = requests.get(f"https://api.notion.com/v1/pages/{page_id}", headers=headers, timeout=30)
            if page_resp.status_code != 200:
                continue
            page = page_resp.json()
            title_prop = next(
                (p for p in page.get("properties", {}).values() if p.get("type") == "title"),
                None,
            )
            title = _extract_plain_text(title_prop.get("title", [])) if title_prop else page_id

            blocks_resp = requests.get(
                f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100",
                headers=headers,
                timeout=30,
            )
            if blocks_resp.status_code != 200:
                continue
            blocks = blocks_resp.json().get("results", [])
            text = "\n".join(filter(None, (_block_to_text(b) for b in blocks)))

            if not text.strip():
                continue

            docs.append(
                Document(
                    text=text,
                    source=f"Notion: {title}",
                    source_id=f"notion::{page_id}",
                    metadata={"type": "notion"},
                    url=f"https://notion.so/{page_id.replace('-', '')}",
                )
            )

        return docs
