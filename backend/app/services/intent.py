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

直接回答选项，例如：knowledge_qa"""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url.rstrip("/")
        self.model = settings.openai_model

    async def classify(self, question: str) -> str:
        """识别意图"""
        prompt = f"判断：{question}\n选项：0=知识库问答 1=闲聊 2=无效输入\n直接回答数字："
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
                        "max_tokens": 100,
                    },
                )
                data = resp.json()
                if "error" in data:
                    return "knowledge_qa"
                choices = data.get("choices", [{}])
                raw_content = choices[0].get("message", {}).get("content", "")
                if not raw_content.strip():
                    raw_content = choices[0].get("message", {}).get("reasoning_content", "")
                # 从 reasoning_content 中解析答案（格式如 "...是 chitchat" 或 "...是 1"）
                reasoning = raw_content.lower()
                if "chitchat" in reasoning or "1" in reasoning:
                    return "chitchat"
                elif "invalid" in reasoning or "2" in reasoning:
                    return "invalid"
        except Exception:
            return "knowledge_qa"
        return "knowledge_qa"