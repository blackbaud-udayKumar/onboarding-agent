"""
Azure DevOps wiki connector -- pulls in your team's ADO dashboard/wiki pages
as the "internal docs" half of the knowledge source.

Disabled by default. Fill in ADO_ORG_URL, ADO_PROJECT, ADO_WIKI_ID, ADO_PAT
in .env and set "enabled": True in config.py when ready.

Docs: https://learn.microsoft.com/en-us/rest/api/azure/devops/wiki/pages
"""

import base64

import requests

from .base import BaseSource, Document

API_VERSION = "7.1"


class AzureDevOpsWikiSource(BaseSource):
    name = "azure_devops_wiki"

    def is_configured(self) -> bool:
        s = self.settings
        return all([s.get("org_url"), s.get("project"), s.get("wiki_identifier"), s.get("pat")])

    def _auth_header(self) -> dict:
        token = base64.b64encode(f":{self.settings['pat']}".encode()).decode()
        return {"Authorization": f"Basic {token}"}

    def _list_page_paths(self, base_url: str, headers: dict) -> list[str]:
        # The pages tree comes back nested; flatten it.
        resp = requests.get(
            f"{base_url}/pages?path=%2F&recursionLevel=Full&api-version={API_VERSION}",
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        root = resp.json()

        paths: list[str] = []

        def walk(node: dict):
            path = node.get("path")
            if path:
                paths.append(path)
            for child in node.get("subPages", []) or []:
                walk(child)

        walk(root)
        return paths

    def fetch(self) -> list[Document]:
        if not self.is_configured():
            raise RuntimeError(
                "azure_devops_wiki is enabled but missing org_url/project/wiki_identifier/pat. "
                "Set ADO_ORG_URL, ADO_PROJECT, ADO_WIKI_ID, ADO_PAT in .env."
            )

        org_url = self.settings["org_url"].rstrip("/")
        project = self.settings["project"]
        wiki_id = self.settings["wiki_identifier"]
        headers = self._auth_header()
        base_url = f"{org_url}/{project}/_apis/wiki/wikis/{wiki_id}"

        docs: list[Document] = []
        for path in self._list_page_paths(base_url, headers):
            page_resp = requests.get(
                f"{base_url}/pages?path={path}&includeContent=true&api-version={API_VERSION}",
                headers=headers,
                timeout=30,
            )
            if page_resp.status_code != 200:
                continue
            page = page_resp.json()
            text = page.get("content", "")
            if not text.strip():
                continue

            docs.append(
                Document(
                    text=text,
                    source=f"wiki:{path}",
                    source_id=f"ado_wiki::{wiki_id}::{path}",
                    metadata={"type": "wiki"},
                    url=f"{org_url}/{project}/_wiki/wikis/{wiki_id}?pagePath={path}",
                )
            )

        return docs
