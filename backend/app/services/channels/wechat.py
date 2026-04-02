# backend/app/services/channels/wechat.py
from fastapi import HTTPException
import httpx
from app.core.config import get_settings

class WeChatService:
    """企业微信客服消息服务"""

    def __init__(self):
        settings = get_settings()
        self.config = settings.wechat_config  # 企微应用配置
        self.api_base = "https://qyapi.weixin.qq.com/cgi-bin"

    async def send_message(self, openid: str, content: str):
        """发送客服消息"""
        url = f"{self.api_base}/message/send"
        params = {"access_token": await self._get_access_token()}

        payload = {
            "touser": openid,
            "msgtype": "text",
            "agentid": self.config["agent_id"],
            "text": {"content": content},
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, params=params, json=payload)
            result = resp.json()
            if result.get("errcode") != 0:
                raise HTTPException(status_code=400, detail=result.get("errmsg"))

    async def _get_access_token(self) -> str:
        """获取access_token（应缓存）"""
        url = f"{self.api_base}/gettoken"
        params = {
            "corpid": self.config["corp_id"],
            "corpsecret": self.config["corp_secret"],
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            result = resp.json()
            if result.get("errcode") != 0:
                raise HTTPException(status_code=400, detail="Failed to get access_token")
            return result["access_token"]