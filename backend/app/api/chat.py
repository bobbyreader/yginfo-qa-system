from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from app.core.database import get_db
from app.models.conversation import Conversation
from app.services.retrieval import RetrievalService
from app.services.generation import GenerationService

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    tenant_id: str = "default"
    channel: str = "webchat"
    user_id: str
    session_id: str
    message: str


@router.post("/message")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        # 1. 知识库检索（跳过意图识别，直接走知识库）
        retrieval_service = RetrievalService()
        chunks = await retrieval_service.hybrid_search(
            request.message, request.tenant_id
        )

        # 2. 获取对话历史
        conv = await db.get(Conversation, request.session_id)
        history = (conv.messages or []) if conv else []

        # 3. LLM生成
        generation_service = GenerationService()
        reply = await generation_service.generate(
            request.message, chunks, history
        )

        # 4. 保存对话
        if conv:
            if conv.messages is None:
                conv.messages = []
            conv.messages.append({
                "role": "user",
                "content": request.message,
                "timestamp": "2026-04-02T00:00:00Z",
            })
            conv.messages.append({
                "role": "assistant",
                "content": reply,
                "timestamp": "2026-04-02T00:00:00Z",
            })
            conv.turn_count = (conv.turn_count or 0) + 1
            conv.last_message_at = func.now()
        else:
            conv = Conversation(
                id=request.session_id,
                tenant_id=request.tenant_id,
                channel=request.channel,
                user_id=request.user_id,
                session_id=request.session_id,
                messages=[
                    {"role": "user", "content": request.message, "timestamp": "2026-04-02T00:00:00Z"},
                    {"role": "assistant", "content": reply, "timestamp": "2026-04-02T00:00:00Z"},
                ],
                turn_count=1,
            )
            db.add(conv)
        await db.commit()

        # 5. 生成推荐问题
        recommendations = await _generate_recommendations(request.message, chunks)

        return {
            "reply": reply,
            "recommendations": recommendations,
            "session_id": request.session_id,
        }
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_recommendations(question: str, chunks: list[dict]) -> list[str]:
    """基于当前问题和检索结果生成推荐问题"""
    if not chunks:
        return ["常见问题有哪些？", "如何联系人工客服？"]

    context = "\n".join([f"- {c.get('text', '')[:100]}" for c in chunks[:3]])

    recommendation_prompt = f"""基于以下知识库内容，生成2-3个用户可能会问的相关问题。

当前用户问题：{question}

相关知识库内容：
{context}

要求：
- 生成的问题要与知识库内容相关
- 不要重复当前问题
- 简洁明了，每条不超过20字

直接输出问题列表，每行一条，不要编号。"""

    try:
        from app.core.config import get_settings
        import httpx
        settings = get_settings()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.openai_base_url.rstrip('/')}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.openai_model,
                    "messages": [{"role": "user", "content": recommendation_prompt}],
                    "max_tokens": 200,
                },
            )
            data = resp.json()
            if "error" in data:
                return ["常见问题有哪些？", "如何联系人工客服？"]
            choices = data.get("choices", [{}])
            raw_content = choices[0].get("message", {}).get("content", "")
            if not raw_content.strip():
                raw_content = choices[0].get("message", {}).get("reasoning_content", "")
            content = raw_content.strip()
    except Exception:
        return ["常见问题有哪些？", "如何联系人工客服？"]

    lines = [l.strip() for l in content.split('\n') if l.strip()]
    clean_lines = []
    for line in lines[:3]:
        cleaned = line.lstrip('0123456789.、) ').strip()
        if cleaned:
            clean_lines.append(cleaned)

    return clean_lines if clean_lines else ["常见问题有哪些？", "如何联系人工客服？"]
