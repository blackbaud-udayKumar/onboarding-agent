"""
Walks a local git repo folder and turns code/config/markdown files into
Documents. This is the "codebase" half of the knowledge source.
"""

import os
from pathlib import Path

from .base import BaseSource, Document


class LocalRepoSource(BaseSource):
    name = "local_repo"

    def is_configured(self) -> bool:
        path = self.settings.get("path")
        return bool(path) and Path(path).exists()

    def fetch(self) -> list[Document]:
        root = Path(self.settings["path"]).resolve()
        extensions = set(self.settings.get("extensions", []))
        ignore_dirs = set(self.settings.get("ignore_dirs", []))
        max_bytes = self.settings.get("max_file_size_kb", 500) * 1024

        docs: list[Document] = []

        for dirpath, dirnames, filenames in os.walk(root):
            # Prune ignored directories in place so os.walk doesn't descend into them.
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith(".git")]

            for filename in filenames:
                file_path = Path(dirpath) / filename
                if file_path.suffix.lower() not in extensions:
                    continue
                try:
                    if file_path.stat().st_size > max_bytes:
                        continue
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                except (OSError, UnicodeDecodeError):
                    continue
                if not text.strip():
                    continue

                rel_path = str(file_path.relative_to(root)).replace("\\", "/")
                docs.append(
                    Document(
                        text=text,
                        source=rel_path,
                        source_id=f"repo::{rel_path}",
                        metadata={
                            "type": "code" if file_path.suffix.lower() != ".md" else "markdown",
                            "repo_root": str(root),
                        },
                    )
                )

        return docs
