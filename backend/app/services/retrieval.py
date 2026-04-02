from sqlalchemy import select
from rank_bm25 import BM25Okapi
from app.services.vector_store import VectorStore
from app.services.embedding import EmbeddingService
import re

class RetrievalService:
    """混合检索：RRF融合向量检索 + BM25"""

    RRF_K = 60  # RRF公式参数

    def __init__(self):
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()

    async def hybrid_search(
        self,
        query: str,
        tenant_id: str,
        top_k_vector: int = 5,
        top_k_bm25: int = 10,
    ) -> list[dict]:
        """混合检索，返回RRF融合后的top-3结果"""
        try:
            vector_results = await self.vector_store.search(
                query, tenant_id, top_k=top_k_vector
            )
        except Exception:
            vector_results = []

        try:
            bm25_results = await self._bm25_search(query, tenant_id, top_k=top_k_bm25)
        except Exception:
            bm25_results = []

        fused = self._reciprocal_rank_fusion(vector_results, bm25_results)

        return fused[:3]

    def _reciprocal_rank_fusion(
        self,
        vector_results: list[dict],
        bm25_results: list[dict],
    ) -> list[dict]:
        """RRF融合算法"""
        scores = {}

        for rank, item in enumerate(vector_results):
            doc_id = item["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (self.RRF_K + rank + 1)
            item["source"] = "vector"

        for rank, item in enumerate(bm25_results):
            doc_id = item["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (self.RRF_K + rank + 1)
            item["source"] = "bm25"

        all_results = {item["id"]: item for item in vector_results + bm25_results}
        ranked = sorted(all_results.items(), key=lambda x: scores[x[0]], reverse=True)

        return [
            {**item, "rrf_score": scores[doc_id]}
            for doc_id, item in ranked
        ]

    async def _bm25_search(
        self, query: str, tenant_id: str, top_k: int
    ) -> list[dict]:
        """BM25关键词召回 - 当前返回空列表，BM25需要chunk表支持"""
        # TODO: 后续需建设chunk表存储原始文本以支持BM25
        return []

    def _tokenize(self, text: str) -> list[str]:
        """中英文分词（简化版）"""
        text = text.lower()
        tokens = re.findall(r'\w+', text)
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        chinese_bigrams = [chinese_chars[i]+chinese_chars[i+1]
                          for i in range(len(chinese_chars)-1)]
        return tokens + chinese_bigrams