from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.document import Document
import uuid
from pathlib import Path

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    if file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["pdf", "doc", "docx"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 保存文件
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.{file_ext}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 创建记录 - 使用 Path().name 清理文件名，防止路径遍历攻击
    filename = Path(file.filename).name
    if len(filename) > 255:
        filename = filename[:255]
    doc = Document(
        id=file_id,
        tenant_id=tenant_id,
        filename=filename,
        file_path=str(file_path),
        file_size=len(content),
        file_type=file_ext,
        status="pending",
    )
    db.add(doc)
    await db.flush()

    return {"id": doc.id, "filename": doc.filename, "status": doc.status}
