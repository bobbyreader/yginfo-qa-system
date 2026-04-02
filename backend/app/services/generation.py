from langchain_openai import ChatOpenAI
from app.core.config import get_settings
import httpx

class GenerationService:
    """LLM生成服务"""

    SYSTEM_PROMPT = """你是一个专业的客服助手。请根据知识库中的内容回答用户问题。

回答要求：
1. 仅根据提供的知识库内容回答，不要编造信息
2. 回答要准确、简洁、有帮助
3. 如果知识库中没有相关信息，请明确告知用户
4. 保持友好的对话语气

知识库内容：
{context}

对话历史：
{history}

用户问题：{question}

回答："""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url.rstrip("/")
        self.model = settings.openai_model

    async def generate(
        self,
        question: str,
        context_chunks: list[dict],
        conversation_history: list[dict],
    ) -> str:
        """生成回答"""
        context = "\n\n".join([
            f"[{i+1}] {chunk.get('text', '')}"
            for i, chunk in enumerate(context_chunks)
        ]) if context_chunks else "（知识库中未找到相关信息）"

        history = "\n".join([
            f"{'用户' if msg.get('role') == 'user' else '助手'}: {msg.get('content', '')}"
            for msg in (conversation_history[-10:] if conversation_history else [])
        ]) if conversation_history else "（首次对话）"

        prompt = self.SYSTEM_PROMPT.format(
            context=context,
            history=history,
            question=question,
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1000,
                    },
                )
                data = resp.json()
                if "error" in data:
                    return f"抱歉，服务暂时不可用。错误: {data['error'].get('message', 'unknown')}"
                choices = data.get("choices", [{}])
                raw_content = choices[0].get("message", {}).get("content", "")
                # 兼容 MiniMax reasoning 模型：content 为空时从 reasoning_content 取
                if not raw_content.strip():
                    raw_content = choices[0].get("message", {}).get("reasoning_content", "")
                return raw_content.strip() or "抱歉，未能获取回答"
        except Exception as e:
            import traceback
            error_msg = f"LLM调用失败: {type(e).__name__}: {e}\n{traceback.format_exc()}"
            return f"抱歉，服务暂时不可用。错误信息: {error_msg[:300]}"