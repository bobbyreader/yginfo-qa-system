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
    await vector_store.delete_by_document(document_id, doc.tenant_id)

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
