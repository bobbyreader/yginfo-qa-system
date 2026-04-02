import asyncio
from pinecone import Pinecone
from app.core.config import get_settings
from app.services.embedding import EmbeddingService


class VectorStore:
    def __init__(self):
        settings = get_settings()
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = f"yginfo-{settings.pinecone_environment}"
        self.namespace = settings.pinecone_namespace
        self.embedding_service = EmbeddingService()

    async def upsert(self, chunks: list[dict], tenant_id: str):
        """批量写入向量数据"""
        index = self.pc.Index(self.index_name)

        vectors = []
        for chunk in chunks:
            embedding = await self.embedding_service.embed_texts([chunk["text"]])
            vectors.append({
                "id": chunk["id"],
                "values": embedding[0],
                "metadata": {
                    "text": chunk["text"][:300],  # 最多300字
                    "tenant_id": tenant_id,
                    "document_id": chunk["document_id"],
                }
            })

        await asyncio.to_thread(index.upsert, vectors=vectors, namespace=tenant_id)

    async def search(self, query: str, tenant_id: str, top_k: int = 5) -> list[dict]:
        """向量相似度搜索"""
        query_embedding = await self.embedding_service.embed_query(query)
        index = self.pc.Index(self.index_name)

        results = await asyncio.to_thread(
            index.query,
            vector=query_embedding,
            top_k=top_k,
            namespace=tenant_id,
            include_metadata=True,
        )

        return [
            {"id": r["id"], "score": r["score"], "text": r["metadata"]["text"]}
            for r in results["matches"]
        ]

    async def delete_by_document(self, document_id: str, tenant_id: str):
        """删除文档的所有向量"""
        index = self.pc.Index(self.index_name)
        await asyncio.to_thread(
            index.delete, filter={"document_id": {"$eq": document_id}}, namespace=tenant_id
        )
