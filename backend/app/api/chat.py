from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from app.core.database import get_db
from app.models.conversation import Conversation
from app.services.retrieval import RetrievalService
from app.services.generation import GenerationService
from app.services.intent import IntentService

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
    # 1. 意图识别
    intent_service = IntentService()
    intent = await intent_service.classify(request.message)

    if intent == "invalid":
        return {"reply": "抱歉，我没有理解您的问题，请重新描述。", "recommendations": []}

    if intent == "chitchat":
        return {
            "reply": "您好！我是智能客服，请问有什么可以帮您？",
            "recommendations": ["查询常见问题", "联系人工客服"]
        }

    # 2. 知识库检索
    retrieval_service = RetrievalService()
    chunks = await retrieval_service.hybrid_search(
        request.message, request.tenant_id
    )

    # 3. 获取对话历史
    conv = await db.get(Conversation, request.session_id)
    history = conv.messages if conv else []

    # 4. LLM生成
    generation_service = GenerationService()
    reply = await generation_service.generate(
        request.message, chunks, history
    )

    # 5. 保存对话
    if conv:
        conv.messages.append({
            "role": "user",
            "content": request.message,
            "timestamp": "ISO8601",
        })
        conv.messages.append({
            "role": "assistant",
            "content": reply,
            "timestamp": "ISO8601",
        })
        conv.turn_count += 1
        conv.last_message_at = func.now()
    else:
        conv = Conversation(
            id=request.session_id,
            tenant_id=request.tenant_id,
            channel=request.channel,
            user_id=request.user_id,
            session_id=request.session_id,
            messages=[
                {"role": "user", "content": request.message, "timestamp": "ISO8601"},
                {"role": "assistant", "content": reply, "timestamp": "ISO8601"},
            ],
            turn_count=1,
        )
        db.add(conv)
    await db.commit()

    # 6. 生成推荐问题
    recommendations = await _generate_recommendations(request.message, chunks)

    return {
        "reply": reply,
        "recommendations": recommendations,
        "session_id": request.session_id,
    }

async def _generate_recommendations(question: str, chunks: list[dict]) -> list[str]:
    """基于当前问题和检索结果生成推荐问题"""
    from app.services.generation import GenerationService

    if not chunks:
        return ["常见问题有哪些？", "如何联系人工客服？"]

    context = "\n".join([f"- {c['text'][:100]}" for c in chunks[:3]])

    recommendation_prompt = f"""基于以下知识库内容，生成2-3个用户可能会问的相关问题。

当前用户问题：{question}

相关知识库内容：
{context}

要求：
- 生成的问题要与知识库内容相关
- 不要重复当前问题
- 简洁明了，每条不超过20字

直接输出问题列表，每行一条，不要编号。"""

    generation_service = GenerationService()
    try:
        response = await generation_service.llm.ainvoke([
            {"role": "user", "content": recommendation_prompt}
        ])
        content = response.content if hasattr(response, 'content') else str(response)
    except Exception:
        return ["常见问题有哪些？", "如何联系人工客服？"]

    lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
    clean_lines = []
    for line in lines[:3]:
        cleaned = line.lstrip('0123456789.、) ').strip()
        if cleaned:
            clean_lines.append(cleaned)

    return clean_lines if clean_lines else ["常见问题有哪些？", "如何联系人工客服？"]