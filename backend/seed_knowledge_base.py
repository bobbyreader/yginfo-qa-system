#!/usr/bin/env python3
"""
知识库数据灌入脚本
用法: python seed_knowledge_base.py
"""
import asyncio
import os
import re
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from pinecone import Pinecone
from app.core.config import get_settings
from app.services.embedding import EmbeddingService

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TENANT_ID = "default"


def chunk_text(text: str) -> list[tuple[str, dict]]:
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        chunk = re.sub(r'\s+', ' ', chunk).strip()
        if chunk:
            chunks.append((chunk, {"start_char": start}))
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


async def seed():
    settings = get_settings()

    # Init Pinecone
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index_name = f"yginfo-{settings.pinecone_environment}"
    print(f"Using Pinecone index: {index_name}")

    # Check index exists
    try:
        pc.Index(index_name)
        print(f"Index '{index_name}' exists")
    except Exception:
        print(f"ERROR: Index '{index_name}' not found!")
        print("Create it at: https://app.pinecone.io/")
        return

    embedding_service = EmbeddingService()

    # Docs to ingest
    docs_base = Path(__file__).parent.parent.parent / "docs" / "superpowers"
    files = [
        ("mvp-plan", docs_base / "plans" / "2026-04-02-yginfo-mvp-plan.md"),
        ("system-design", docs_base / "specs" / "2026-04-02-yginfo-qa-system-design.md"),
    ]

    all_chunks = []

    for name, filepath in files:
        if not filepath.exists():
            print(f"SKIP: {filepath} not found")
            continue

        print(f"Reading: {filepath}")
        text = filepath.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        print(f"  -> {len(chunks)} chunks")

        for i, (chunk_text_content, meta) in enumerate(chunks):
            chunk_id = f"{name}-{i}"
            all_chunks.append({
                "id": chunk_id,
                "text": chunk_text_content,
                "document_id": name,
                "meta": meta,
            })

    if not all_chunks:
        print("No chunks to ingest!")
        return

    print(f"\nTotal chunks: {len(all_chunks)}")
    print("Generating embeddings...")

    # Batch embed
    texts = [c["text"] for c in all_chunks]
    embeddings = await embedding_service.embed_texts(texts)

    # Prepare vectors for upsert
    vectors = []
    for chunk, embedding in zip(all_chunks, embeddings):
        vectors.append({
            "id": chunk["id"],
            "values": embedding,
            "metadata": {
                "text": chunk["text"][:300],
                "tenant_id": TENANT_ID,
                "document_id": chunk["document_id"],
            }
        })

    # Upsert to Pinecone
    print("Upserting to Pinecone...")
    index = pc.Index(index_name)
    index.upsert(vectors=vectors, namespace=TENANT_ID)
    print(f"Done! Upserted {len(vectors)} vectors to namespace '{TENANT_ID}'")

    # Verify
    stats = index.describe_namespace_stats(namespace=TENANT_ID)
    print(f"Namespace stats: {stats}")


if __name__ == "__main__":
    asyncio.run(seed())
