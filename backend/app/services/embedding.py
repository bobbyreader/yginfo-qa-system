from app.core.config import get_settings
import httpx

settings = get_settings()


class EmbeddingService:
    """Embedding服务 - 直接使用httpx调用中转API，兼容各种中转格式"""

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url.rstrip("/")
        self.model = "text-embedding-ada-002"

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量生成embedding向量"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

            # 兼容中转API返回格式：可能是 {data: [...]} 或直接返回数组
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                # 标准OpenAI格式: {"data": [{"embedding": [...]}, ...]}
                if "data" in result:
                    return [item["embedding"] for item in result["data"]]
                # 某些中转返回: {"embedding": [...]} (单个)
                elif "embedding" in result:
                    return [result["embedding"]]
            raise ValueError(f"Unexpected embedding response format: {result}")

    async def embed_query(self, query: str) -> list[float]:
        """为查询生成embedding"""
        results = await self.embed_texts([query])
        return results[0]
