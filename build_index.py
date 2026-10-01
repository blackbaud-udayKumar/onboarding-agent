"""
Run this whenever you want to (re)build the knowledge base:

    python build_index.py            # index everything enabled in config.py
    python build_index.py --reset    # wipe the index first, then rebuild

It reads config.SOURCES, runs every source with "enabled": True, chunks the
documents it gets back, and stores them in the local Chroma vector store.
Re-run this any time the repo or docs change -- there's no live sync, this
is a batch rebuild.
"""

import argparse
import sys
import time

import config
from chunking import chunk_document
from ingest import SOURCE_CLASSES
from vectorstore import VectorStore


def run(reset: bool = False):
    store = VectorStore()
    if reset:
        print("Resetting existing index...")
        store.reset()

    total_docs = 0
    total_chunks = 0

    for source_name, settings in config.SOURCES.items():
        if not settings.get("enabled"):
            continue

        source_cls = SOURCE_CLASSES.get(source_name)
        if source_cls is None:
            print(f"[skip] Unknown source '{source_name}'")
            continue

        source = source_cls(settings)
        if not source.is_configured():
            print(f"[skip] '{source_name}' is enabled but not fully configured (check .env / config.py)")
            continue

        print(f"[fetch] {source_name} ...")
        start = time.time()
        try:
            docs = source.fetch()
        except Exception as e:
            print(f"[error] '{source_name}' failed: {e}", file=sys.stderr)
            continue
        print(f"[fetch] {source_name}: {len(docs)} document(s) in {time.time() - start:.1f}s")

        chunks = []
        for doc in docs:
            chunks.extend(
                chunk_document(
                    doc,
                    code_chunk_lines=config.CODE_CHUNK_LINES,
                    code_overlap_lines=config.CODE_CHUNK_OVERLAP_LINES,
                    text_chunk_chars=config.TEXT_CHUNK_CHARS,
                    text_overlap_chars=config.TEXT_CHUNK_OVERLAP_CHARS,
                )
            )

        if chunks:
            print(f"[index] {source_name}: embedding + storing {len(chunks)} chunk(s) ...")
            store.add_chunks(chunks)

        total_docs += len(docs)
        total_chunks += len(chunks)

    print(f"\nDone. Indexed {total_docs} document(s) -> {total_chunks} chunk(s).")
    print(f"Vector store now has {store.count()} chunk(s) total at {config.CHROMA_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build/refresh the onboarding agent's knowledge index.")
    parser.add_argument("--reset", action="store_true", help="Wipe the existing index before rebuilding.")
    args = parser.parse_args()
    run(reset=args.reset)
