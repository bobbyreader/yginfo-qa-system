from langchain_openai import OpenAIEmbeddings
from app.core.config import get_settings


class EmbeddingService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            api_key=get_settings().openai_api_key,
            model="text-embedding-ada-002",
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量生成embedding向量"""
        return await self.embeddings.aembed_documents(texts)

    async def embed_query(self, query: str) -> list[float]:
        """为查询生成embedding"""
        return await self.embeddings.aembed_query(query)
