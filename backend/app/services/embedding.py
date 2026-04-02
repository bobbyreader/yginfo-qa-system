from langchain_openai import OpenAIEmbeddings
from app.core.config import get_settings

settings = get_settings()


class EmbeddingService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model="text-embedding-ada-002",
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量生成embedding向量"""
        return await self.embeddings.aembed_documents(texts)

    async def embed_query(self, query: str) -> list[float]:
        """为查询生成embedding"""
        return await self.embeddings.aembed_query(query)
