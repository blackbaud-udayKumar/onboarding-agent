from .base import Document
from .local_repo import LocalRepoSource
from .local_docs import LocalDocsSource
from .ado_repo import AzureDevOpsRepoSource
from .ado_wiki import AzureDevOpsWikiSource
from .confluence import ConfluenceSource
from .notion import NotionSource
from .slack import SlackSource

# Maps the "SOURCES" keys in config.py to the class that handles them.
SOURCE_CLASSES = {
    "local_repo": LocalRepoSource,
    "local_docs": LocalDocsSource,
    "azure_devops_repo": AzureDevOpsRepoSource,
    "azure_devops_wiki": AzureDevOpsWikiSource,
    "confluence": ConfluenceSource,
    "notion": NotionSource,
    "slack": SlackSource,
}

__all__ = ["Document", "SOURCE_CLASSES"]
