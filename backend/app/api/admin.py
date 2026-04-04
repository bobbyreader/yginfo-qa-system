from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.document import Document
from app.services.vector_store import VectorStore
from app.services.document_processor import DocumentProcessor

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/documents")
async def list_documents(
    tenant_id: str = Query("default"),
    status: str = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Document).where(
        Document.tenant_id == tenant_id,
        Document.deleted_at == None,
    )
    if status:
        query = query.where(Document.status == status)

    result = await db.execute(query)
    docs = result.scalars().all()

    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "status": d.status,
            "chunk_count": d.chunk_count,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    """软删除文档"""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 从向量库删除
    vector_store = VectorStore()
    await vector_store.delete_by_document(document_id, doc.tenant_id)

    # 软删除
    from datetime import datetime
    doc.deleted_at = datetime.utcnow()
    await db.commit()

    return {"success": True}

@router.post("/documents/{document_id}/reindex")
async def reindex_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    """重建索引"""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 删除旧向量
    vector_store = VectorStore()
    await vector_store.delete_by_document(doc.id, doc.tenant_id)

    # 重新处理并索引
    processor = DocumentProcessor()
    chunks_data = await processor.process(doc.file_path, doc.file_type)

    chunks = [
        {"id": f"{doc.id}-{i}", "text": text, "document_id": doc.id}
        for i, (text, _) in enumerate(chunks_data)
    ]

    await vector_store.upsert(chunks, doc.tenant_id)

    doc.chunk_count = len(chunks)
    doc.status = "indexed"
    await db.commit()

    return {"id": doc.id, "chunk_count": len(chunks)}


@router.post("/seed")
async def seed_knowledge_base(tenant_id: str = "default"):
    """
    无鉴权种子端点 - 仅用于初始化灌数据。
    通过 curl 触发: curl -X POST https://yginfo-qa-system-1.onrender.com/api/admin/seed
    """
    chunks = [
        {"id": "yginfo-0", "text": "YG智能知识库问答系统是企业级智能客服系统，基于知识库文档提供多轮对话和主动推荐。核心技术：Pinecone向量库、GPT-4o、LangChain、FastAPI。", "document_id": "overview"},
        {"id": "yginfo-1", "text": "系统支持多渠道接入：网页Widget、企业微信、钉钉、飞书。核心功能：7x24小时响应、多轮对话、智能推荐、知识库管理。目标用户：中小企业产品FAQ客服。", "document_id": "overview"},
        {"id": "yginfo-2", "text": "部署架构：后端Render云托管（Python/FastAPI），数据库Supabase PostgreSQL（Pooler连接），向量库Pinecone。环境变量：DATABASE_URL、PINECONE_API_KEY、OPENAI_API_KEY。", "document_id": "overview"},
        {"id": "yginfo-3", "text": "知识库API：POST /api/knowledge/documents/upload 上传文档（PDF/DOCX），POST /api/knowledge/documents/{id}/index 触发索引。管理API：GET /api/admin/documents、DELETE /api/admin/documents/{id}、POST /api/admin/documents/{id}/reindex。", "document_id": "overview"},
        {"id": "yginfo-4", "text": "对话API：POST /api/chat/message，参数：user_id、session_id、message、tenant_id。返回：reply（AI回答）、recommendations（推荐问题列表）、session_id。", "document_id": "overview"},
    ]
    try:
        from app.services.vector_store import VectorStore
        vs = VectorStore()
        await vs.upsert(chunks, tenant_id)
        from pinecone import Pinecone
        from app.core.config import get_settings
        s = get_settings()
        pc = Pinecone(api_key=s.pinecone_api_key)
        idx = pc.Index(f"yginfo-{s.pinecone_environment}")
        stats = idx.describe_namespace_stats(namespace=tenant_id)
        return {"success": True, "chunks_seeded": len(chunks), "total_vectors": stats.total_vector_count}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
