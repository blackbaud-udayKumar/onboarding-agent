"""
Azure DevOps repo connector.

Disabled by default (see config.py -> SOURCES["azure_devops_repo"]). Fill in
ADO_ORG_URL, ADO_PROJECT, ADO_REPO, ADO_PAT in .env and set "enabled": True
when you're ready -- that's the "final phase" step you mentioned wanting to
do last.

Auth: Azure DevOps REST API accepts a Personal Access Token (PAT) as the
password half of HTTP Basic auth (username can be blank). Create one under
Azure DevOps -> User settings -> Personal access tokens, with "Code (Read)"
scope at minimum.

Docs: https://learn.microsoft.com/en-us/rest/api/azure/devops/git/items
"""

import base64

import requests

from .base import BaseSource, Document

API_VERSION = "7.1"
TEXT_EXTENSIONS = (
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb", ".cs",
    ".cpp", ".c", ".h", ".rs", ".php", ".sql", ".md", ".mdx", ".rst",
    ".txt", ".yaml", ".yml", ".json",
)


class AzureDevOpsRepoSource(BaseSource):
    name = "azure_devops_repo"

    def is_configured(self) -> bool:
        s = self.settings
        return all([s.get("org_url"), s.get("project"), s.get("repo"), s.get("pat")])

    def _auth_header(self) -> dict:
        token = base64.b64encode(f":{self.settings['pat']}".encode()).decode()
        return {"Authorization": f"Basic {token}"}

    def fetch(self) -> list[Document]:
        if not self.is_configured():
            raise RuntimeError(
                "azure_devops_repo is enabled but missing org_url/project/repo/pat. "
                "Set ADO_ORG_URL, ADO_PROJECT, ADO_REPO, ADO_PAT in .env."
            )

        org_url = self.settings["org_url"].rstrip("/")
        project = self.settings["project"]
        repo = self.settings["repo"]
        headers = self._auth_header()

        # 1. List all items (files) in the repo.
        items_url = (
            f"{org_url}/{project}/_apis/git/repositories/{repo}/items"
            f"?recursionLevel=Full&api-version={API_VERSION}"
        )
        resp = requests.get(items_url, headers=headers, timeout=30)
        resp.raise_for_status()
        items = resp.json().get("value", [])

        docs: list[Document] = []
        for item in items:
            path = item.get("path", "")
            if item.get("isFolder") or not path.lower().endswith(TEXT_EXTENSIONS):
                continue

            content_url = (
                f"{org_url}/{project}/_apis/git/repositories/{repo}/items"
                f"?path={path}&api-version={API_VERSION}&$format=text"
            )
            file_resp = requests.get(content_url, headers=headers, timeout=30)
            if file_resp.status_code != 200:
                continue

            text = file_resp.text
            if not text.strip():
                continue

            docs.append(
                Document(
                    text=text,
                    source=path.lstrip("/"),
                    source_id=f"ado_repo::{repo}::{path}",
                    metadata={"type": "code", "repo": repo},
                    url=f"{org_url}/{project}/_git/{repo}?path={path}",
                )
            )

        return docs
