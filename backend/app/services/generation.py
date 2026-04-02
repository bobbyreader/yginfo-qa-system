from langchain_openai import ChatOpenAI
from app.core.config import get_settings

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
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            max_tokens=1000,
        )

    async def generate(
        self,
        question: str,
        context_chunks: list[dict],
        conversation_history: list[dict],
    ) -> str:
        """生成回答"""
        context = "\n\n".join([
            f"[{i+1}] {chunk['text']}"
            for i, chunk in enumerate(context_chunks)
        ]) if context_chunks else "（知识库中未找到相关信息）"

        history = "\n".join([
            f"{'用户' if msg['role'] == 'user' else '助手'}: {msg['content']}"
            for msg in conversation_history[-10:]
        ]) if conversation_history else "（首次对话）"

        prompt = self.SYSTEM_PROMPT.format(
            context=context,
            history=history,
            question=question,
        )

        response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
        return response.content