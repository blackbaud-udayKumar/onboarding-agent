"""
Splits a Document's text into smaller chunks with metadata that lets us
cite exactly where an answer came from (file path + line range, or doc name).

Code files are split by line count (so citations read naturally as
"file.py lines 40-100"); everything else is split by character count with
overlap so we don't cut sentences awkwardly.
"""

from dataclasses import dataclass

from ingest.base import Document

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb", ".cs",
    ".cpp", ".c", ".h", ".rs", ".php", ".sql", ".yaml", ".yml", ".json",
}


@dataclass
class Chunk:
    id: str
    text: str
    source: str
    source_id: str
    url: str | None
    metadata: dict


def _is_code(doc: Document) -> bool:
    if doc.metadata.get("type") == "code":
        return True
    for ext in CODE_EXTENSIONS:
        if doc.source.lower().endswith(ext):
            return True
    return False


def _chunk_by_lines(doc: Document, chunk_lines: int, overlap_lines: int) -> list[Chunk]:
    lines = doc.text.splitlines()
    chunks = []
    step = max(chunk_lines - overlap_lines, 1)

    for i, start in enumerate(range(0, len(lines), step)):
        end = min(start + chunk_lines, len(lines))
        text = "\n".join(lines[start:end])
        if not text.strip():
            continue
        chunks.append(
            Chunk(
                id=f"{doc.source_id}::L{start + 1}-{end}",
                text=text,
                source=f"{doc.source} (lines {start + 1}-{end})",
                source_id=doc.source_id,
                url=doc.url,
                metadata={**doc.metadata, "line_start": start + 1, "line_end": end},
            )
        )
        if end == len(lines):
            break

    return chunks


def _chunk_by_chars(doc: Document, chunk_chars: int, overlap_chars: int) -> list[Chunk]:
    text = doc.text
    chunks = []
    step = max(chunk_chars - overlap_chars, 1)

    for i, start in enumerate(range(0, len(text), step)):
        end = min(start + chunk_chars, len(text))
        piece = text[start:end]
        if not piece.strip():
            continue
        chunks.append(
            Chunk(
                id=f"{doc.source_id}::C{start}-{end}",
                text=piece,
                source=doc.source if len(text) <= chunk_chars else f"{doc.source} (part {i + 1})",
                source_id=doc.source_id,
                url=doc.url,
                metadata={**doc.metadata},
            )
        )
        if end == len(text):
            break

    return chunks


def chunk_document(
    doc: Document,
    code_chunk_lines: int,
    code_overlap_lines: int,
    text_chunk_chars: int,
    text_overlap_chars: int,
) -> list[Chunk]:
    if _is_code(doc):
        return _chunk_by_lines(doc, code_chunk_lines, code_overlap_lines)
    return _chunk_by_chars(doc, text_chunk_chars, text_overlap_chars)
