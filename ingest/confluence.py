"""
Confluence connector (optional). Disabled by default -- only wire this up
if your internal docs actually live in Confluence rather than an ADO wiki.

Fill in CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN in .env,
list the space keys to pull from in config.py, and set "enabled": True.

Auth: Confluence Cloud uses HTTP Basic auth with your email + an API token
(create one at https://id.atlassian.com/manage-profile/security/api-tokens).

Docs: https://developer.atlassian.com/cloud/confluence/rest/v2/
"""

import requests
from requests.auth import HTTPBasicAuth

from .base import BaseSource, Document


class ConfluenceSource(BaseSource):
    name = "confluence"

    def is_configured(self) -> bool:
        s = self.settings
        return all([s.get("base_url"), s.get("email"), s.get("api_token")])

    def fetch(self) -> list[Document]:
        if not self.is_configured():
            raise RuntimeError(
                "confluence is enabled but missing base_url/email/api_token. "
                "Set CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN in .env."
            )

        base_url = self.settings["base_url"].rstrip("/")
        auth = HTTPBasicAuth(self.settings["email"], self.settings["api_token"])
        space_keys = self.settings.get("space_keys") or [None]  # None = all spaces

        docs: list[Document] = []
        for space_key in space_keys:
            params = {"limit": 100, "expand": "body.storage"}
            if space_key:
                params["spaceKey"] = space_key

            url = f"{base_url}/wiki/rest/api/content"
            while url:
                resp = requests.get(url, params=params, auth=auth, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                for page in data.get("results", []):
                    html = page.get("body", {}).get("storage", {}).get("value", "")
                    if not html.strip():
                        continue
                    docs.append(
                        Document(
                            text=html,  # raw storage HTML; strip tags in chunking if needed
                            source=f"Confluence: {page.get('title', 'Untitled')}",
                            source_id=f"confluence::{page.get('id')}",
                            metadata={"type": "confluence"},
                            url=f"{base_url}/wiki{page.get('_links', {}).get('webui', '')}",
                        )
                    )

                next_link = data.get("_links", {}).get("next")
                url = f"{base_url}{next_link}" if next_link else None
                params = {}  # next_link already has query params baked in

        return docs
