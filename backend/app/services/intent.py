from app.core.config import get_settings
import httpx

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
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url.rstrip("/")
        self.model = settings.openai_model

    async def classify(self, question: str) -> str:
        """识别意图"""
        prompt = self.INTENT_PROMPT.format(question=question)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 50,
                    },
                )
                data = resp.json()
                if "error" in data:
                    return "knowledge_qa"
                choices = data.get("choices", [{}])
                raw_content = choices[0].get("message", {}).get("content", "")
                # 兼容 MiniMax reasoning 模型：content 为空时从 reasoning_content 取
                if not raw_content.strip():
                    raw_content = choices[0].get("message", {}).get("reasoning_content", "")
                intent = raw_content.strip().lower()
        except Exception:
            return "knowledge_qa"

        if "knowledge_qa" in intent:
            return "knowledge_qa"
        elif "chitchat" in intent:
            return "chitchat"
        return "invalid"