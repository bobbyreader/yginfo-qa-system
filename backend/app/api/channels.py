# backend/app/api/channels.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.channels.wechat import WeChatService
from app.services.retrieval import RetrievalService
from app.services.generation import GenerationService
from app.models.conversation import Conversation
import hashlib
import time

router = APIRouter(prefix="/api/channels", tags=["channels"])

@router.post("/wechat/webhook")
async def wechat_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """企业微信消息回调"""
    body = await request.json()

    msg_signature = body.get("msg_signature", "")
    timestamp = body.get("timestamp", "")
    nonce = body.get("nonce", "")
    encrypted_msg = body.get("encrypt", "")

    # 解密消息（实际使用WXBizMsgCrypt库）
    try:
        from xml.etree import ElementTree as ET
        # PLACEHOLDER - 实际需要WXBizMsgCrypt解密
        msg_xml = "<xml><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[测试消息]]></Content><FromUserName><![CDATA[user1]]></FromUserName></xml>"
    except Exception:
        raise HTTPException(status_code=400, detail="消息解密失败")

    root = ET.fromstring(msg_xml)
    msg_type = root.find("MsgType").text
    content = root.find("Content").text
    from_user = root.find("FromUserName").text

    session_id = hashlib.md5(
        f"{from_user}-{time.strftime('%Y%m%d')}".encode()
    ).hexdigest()

    # 调用AI服务处理
    retrieval_service = RetrievalService()
    chunks = await retrieval_service.hybrid_search(content, "default")
    generation_service = GenerationService()
    reply = await generation_service.generate(content, chunks, [])

    # 发送回复
    wechat_service = WeChatService()
    await wechat_service.send_message(from_user, reply)

    return {"success": True}