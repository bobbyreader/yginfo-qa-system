from app.core.config import get_settings
from langchain_openai import ChatOpenAI

class IntentService:
    """意图识别：判断是知识库问答还是闲聊"""

    INTENT_PROMPT = """判断用户的问题是知识库相关问答还是闲聊/无效输入。

问题：{question}

回答选项：
- knowledge_qa: 知识库相关问答
- chitchat: 闲聊
- invalid: 无效输入（乱码、广告等）

只回答选项中的一个，不要解释。"""

    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
        )

    async def classify(self, question: str) -> str:
        """识别意图"""
        prompt = self.INTENT_PROMPT.format(question=question)
        try:
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            # 兼容中转API返回的字符串或标准AIMessage对象
            intent = response.content if hasattr(response, 'content') else str(response)
            intent = intent.strip().lower()
        except Exception as e:
            # 中转API异常时默认走知识库检索
            return "knowledge_qa"

        if "knowledge_qa" in intent:
            return "knowledge_qa"
        elif "chitchat" in intent:
            return "chitchat"
        return "invalid"