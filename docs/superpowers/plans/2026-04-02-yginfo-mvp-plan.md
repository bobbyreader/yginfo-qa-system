# YG智能知识库问答系统 - MVP实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付一个具备基础客服能力的MVP：网页Widget + 企业微信接入 + 知识库管理 + 多轮对话

**Architecture:** 采用分层架构 + 领域驱动设计。后端FastAPI提供REST API，AI服务封装RAG pipeline（Pinecone向量检索 + GPT-4o生成），前端独立Widget可嵌入任意网站。

**Tech Stack:** Python 3.11+ / FastAPI / PostgreSQL / Pinecone / LangChain / GPT-4o / React

---

## 系统架构

```
backend/
├── app/
│   ├── api/           # API路由（channels, knowledge, chat）
│   ├── core/          # 核心配置（config, security, db）
│   ├── models/        # 数据模型（SQLAlchemy + Pydantic）
│   └── services/      # 业务逻辑（retrieval, generation, conversation）
├── tests/
└── requirements.txt

frontend/
└── widget/            # 网页Widget（React组件）

docs/superpowers/plans/
```

---

## Task 1: 项目基础架构

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`
- Create: `backend/app/main.py`
- Create: `backend/app/services/__init__.py`

- [ ] **Step 1: 创建依赖文件**

```txt
# backend/requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
asyncpg==0.29.0
pydantic==2.6.0
pydantic-settings==2.1.0
python-multipart==0.0.9
httpx==0.26.0
langchain==0.1.4
langchain-community==0.0.17
langchain-openai==0.0.5
pinecone-client==3.0.0
openai==1.12.0
python-docx==1.1.0
pypdf==4.0.1
rank-bm25==0.2.2
tenacity==8.2.3
```

- [ ] **Step 1.5: 创建services空包**

```bash
# backend/app/services/__init__.py
# 服务层模块，后续Task会填充具体服务
```

- [ ] **Step 2: 创建配置模块**

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/yginfo"

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_environment: str = "us-east-1"
    pinecone_namespace: str = "default"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Application
    app_name: str = "YG智能知识库问答系统"
    debug: bool = False

    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()
```

- [ ] **Step 3: 创建数据库模块**

```python
# backend/app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(
    get_settings().database_url,
    echo=get_settings().debug,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

- [ ] **Step 4: 创建主应用**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings

app = FastAPI(title=get_settings().app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "YG智能知识库问答系统 API"}
```

- [ ] **Step 5: 验证服务启动**

Run: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`
Expected: Server starts on port 8000

Run: `curl http://localhost:8000/health`
Expected: `{"status":"ok"}`

- [ ] **Step 6: Commit**

```bash
cd ~/Projects/YG智能知识库问答系统
git init
git add backend/requirements.txt backend/app/
git commit -m "feat: 项目基础架构 - FastAPI骨架、配置、数据库连接"
```

---

## Task 2: 数据模型

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/document.py`
- Create: `backend/app/models/conversation.py`
- Create: `backend/app/models/channel.py`

- [ ] **Step 1: 创建Document模型**

```python
# backend/app/models/document.py
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)

    status = Column(String(50), default="pending")  # pending, processing, indexed, failed
    chunk_count = Column(Integer, default=0)
    metadata = Column(JSON, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 2: 创建Conversation模型**

```python
# backend/app/models/conversation.py
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    channel = Column(String(50), nullable=False)  # webchat, wechat
    user_id = Column(String(255), nullable=False, index=True)

    session_id = Column(String(255), nullable=False, index=True)
    messages = Column(JSON, default=[])  # [{"role": "user|assistant", "content": "...", "timestamp": "..."}]

    turn_count = Column(Integer, default=0)
    last_message_at = Column(DateTime(timezone=True), server_default=func.now())

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 3: 创建Channel模型**

```python
# backend/app/models/channel.py
from sqlalchemy import Column, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class ChannelConfig(Base):
    __tablename__ = "channel_configs"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    channel = Column(String(50), nullable=False)  # webchat, wechat

    config = Column(JSON, default={})  # channel-specific config
    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

- [ ] **Step 4: 创建模型索引**

```python
# backend/app/models/__init__.py
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.channel import ChannelConfig

__all__ = ["Document", "Conversation", "ChannelConfig"]
```

- [ ] **Step 5: 创建数据库表**

Run: `cd backend && python -c "from app.core.database import engine, Base; from app.models import *; import asyncio; asyncio.run(Base.metadata.create_all(engine))"`
Expected: Tables created without errors

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/
git commit -m "feat: 数据模型 - Document、Conversation、ChannelConfig"
```

---

## Task 3: 知识库管理 - 文档上传与解析

**Files:**
- Create: `backend/app/services/document_processor.py`
- Create: `backend/app/api/knowledge.py`
- Create: `tests/test_document_processor.py`

- [ ] **Step 1: 编写文档处理器服务**

```python
# backend/app/services/document_processor.py
import re
from pathlib import Path
from typing import List, Tuple
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader

class DocumentProcessor:
    """文档解析与分块处理器"""

    CHUNK_SIZE = 500  # 每段500字
    CHUNK_OVERLAP = 50  # 重叠50字

    async def process(self, file_path: str, file_type: str) -> List[Tuple[str, dict]]:
        """处理文档，返回分段列表[(文本, 元数据), ...]"""
        if file_type == "pdf":
            text = await self._extract_pdf(file_path)
        elif file_type in ["doc", "docx"]:
            text = await self._extract_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        return self._chunk_text(text, {"source": file_path})

    async def _extract_pdf(self, file_path: str) -> str:
        loader = PyPDFLoader(file_path)
        pages = await loader.aload()
        return "\n".join([p.page_content for p in pages])

    async def _extract_docx(self, file_path: str) -> str:
        loader = UnstructuredWordDocumentLoader(file_path)
        docs = await loader.aload()
        return "\n".join([d.page_content for d in docs])

    def _chunk_text(self, text: str, metadata: dict) -> List[Tuple[str, dict]]:
        """重叠滑动窗口分块"""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.CHUNK_SIZE
            chunk = text[start:end]

            # 清理空白字符
            chunk = re.sub(r'\s+', ' ', chunk).strip()
            if chunk:
                chunks.append((chunk, {**metadata, "start_char": start}))

            start += self.CHUNK_SIZE - self.CHUNK_OVERLAP

        return chunks
```

- [ ] **Step 2: 编写API路由**

```python
# backend/app/api/knowledge.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.document import Document
import uuid
import os

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

    # 创建记录
    doc = Document(
        id=file_id,
        tenant_id=tenant_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        file_type=file_ext,
        status="pending",
    )
    db.add(doc)
    await db.flush()

    return {"id": doc.id, "filename": doc.filename, "status": doc.status}
```

- [ ] **Step 3: 编写测试**

```python
# backend/tests/test_document_processor.py
import pytest
from app.services.document_processor import DocumentProcessor

@pytest.fixture
def processor():
    return DocumentProcessor()

def test_chunk_text_overlap(processor):
    text = "A" * 600 + "B" * 600 + "C" * 600  # 1800 chars
    chunks = processor._chunk_text(text, {})

    # 3 chunks: 0-500, 450-950, 900-1400
    assert len(chunks) == 3
    assert chunks[0][0] == "A" * 500
    assert chunks[1][0] == "A" * 50 + "B" * 450  # 50 char overlap
    assert chunks[2][0] == "B" * 50 + "C" * 450

def test_chunk_text_removes_whitespace(processor):
    text = "Hello    World\n\n\nTest"
    chunks = processor._chunk_text(text, {})
    assert "\n" not in chunks[0][0]
    assert "  " not in chunks[0][0]
```

- [ ] **Step 4: 运行测试验证**

Run: `cd backend && pytest tests/test_document_processor.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/document_processor.py backend/app/api/knowledge.py
git commit -m "feat: 知识库API - 文档上传与解析服务"
```

---

## Task 4: 知识库管理 - 向量化与索引

**Files:**
- Create: `backend/app/services/embedding.py`
- Create: `backend/app/services/vector_store.py`
- Modify: `backend/app/api/knowledge.py` (新增索引重建接口)

- [ ] **Step 1: 创建Embedding服务**

```python
# backend/app/services/embedding.py
from langchain_openai import OpenAIEmbeddings
from app.core.config import get_settings

class EmbeddingService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            api_key=get_settings().openai_api_key,
            model="text-embedding-ada-002",
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量生成embedding向量"""
        return await self.embeddings.aembed_documents(texts)

    async def embed_query(self, query: str) -> list[float]:
        """为查询生成embedding"""
        return await self.embeddings.aembed_query(query)
```

- [ ] **Step 2: 创建向量存储服务**

```python
# backend/app/services/vector_store.py
from pinecone import Pinecone
from app.core.config import get_settings
from app.services.embedding import EmbeddingService

class VectorStore:
    def __init__(self):
        settings = get_settings()
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = f"yginfo-{settings.pinecone_environment}"
        self.namespace = settings.pinecone_namespace
        self.embedding_service = EmbeddingService()

    async def upsert(self, chunks: list[dict], tenant_id: str):
        """批量写入向量数据"""
        index = self.pc.Index(self.index_name)

        vectors = []
        for chunk in chunks:
            embedding = await self.embedding_service.embed_texts([chunk["text"]])
            vectors.append({
                "id": chunk["id"],
                "values": embedding[0],
                "metadata": {
                    "text": chunk["text"][:300],  # 最多300字
                    "tenant_id": tenant_id,
                    "document_id": chunk["document_id"],
                }
            })

        index.upsert(vectors=vectors, namespace=tenant_id)

    async def search(self, query: str, tenant_id: str, top_k: int = 5) -> list[dict]:
        """向量相似度搜索"""
        query_embedding = await self.embedding_service.embed_query(query)
        index = self.pc.Index(self.index_name)

        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=tenant_id,
            include_metadata=True,
        )

        return [
            {"id": r["id"], "score": r["score"], "text": r["metadata"]["text"]}
            for r in results["matches"]
        ]

    async def delete_by_document(self, document_id: str, tenant_id: str):
        """删除文档的所有向量"""
        index = self.pc.Index(self.index_name)
        # 先查询获取所有相关向量ID
        # 然后批量删除
        index.delete(filter={"document_id": {"$eq": document_id}}, namespace=tenant_id)
```

- [ ] **Step 3: 新增索引API**

```python
# backend/app/api/knowledge.py 新增端点
@router.post("/documents/{document_id}/index")
async def index_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    from app.services.document_processor import DocumentProcessor
    from app.services.vector_store import VectorStore

    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 处理文档
    processor = DocumentProcessor()
    chunks_data = await processor.process(doc.file_path, doc.file_type)

    # 生成chunk记录和向量
    chunks = [
        {"id": f"{doc.id}-{i}", "text": text, "document_id": doc.id}
        for i, (text, _) in enumerate(chunks_data)
    ]

    # 写入向量库
    vector_store = VectorStore()
    await vector_store.upsert(chunks, doc.tenant_id)

    # 更新状态
    doc.status = "indexed"
    doc.chunk_count = len(chunks)
    await db.flush()

    return {"id": doc.id, "chunk_count": len(chunks), "status": "indexed"}
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/embedding.py backend/app/services/vector_store.py
git commit -m "feat: 知识库 - 向量化和索引服务"
```

---

## Task 5: AI服务 - RAG Pipeline（检索+生成）

**Files:**
- Create: `backend/app/services/retrieval.py` (BM25 + 向量融合检索)
- Create: `backend/app/services/generation.py` (LLM生成)
- Create: `backend/app/services/intent.py` (意图识别)
- Create: `backend/app/api/chat.py` (对话API)

- [ ] **Step 1: 创建检索服务**

```python
# backend/app/services/retrieval.py
from sqlalchemy import select
from rank_bm25 import BM25Okapi
from app.services.vector_store import VectorStore
from app.services.embedding import EmbeddingService
import re

class RetrievalService:
    """混合检索：RRF融合向量检索 + BM25"""

    RRF_K = 60  # RRF公式参数

    def __init__(self):
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()

    async def hybrid_search(
        self,
        query: str,
        tenant_id: str,
        top_k_vector: int = 5,
        top_k_bm25: int = 10,
    ) -> list[dict]:
        """混合检索，返回RRF融合后的top-3结果"""
        # 1. 向量检索
        vector_results = await self.vector_store.search(
            query, tenant_id, top_k=top_k_vector
        )

        # 2. BM25检索（需要预先构建索引，这里简化处理）
        bm25_results = await self._bm25_search(query, tenant_id, top_k=top_k_bm25)

        # 3. RRF融合
        fused = self._reciprocal_rank_fusion(vector_results, bm25_results)

        return fused[:3]

    def _reciprocal_rank_fusion(
        self,
        vector_results: list[dict],
        bm25_results: list[dict],
    ) -> list[dict]:
        """RRF融合算法"""
        scores = {}

        # 向量检索得分
        for rank, item in enumerate(vector_results):
            doc_id = item["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (self.RRF_K + rank + 1)
            item["source"] = "vector"

        # BM25检索得分
        for rank, item in enumerate(bm25_results):
            doc_id = item["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (self.RRF_K + rank + 1)
            item["source"] = "bm25"

        # 合并并按RRF分数排序
        all_results = {item["id"]: item for item in vector_results + bm25_results}
        ranked = sorted(all_results.items(), key=lambda x: scores[x[0]], reverse=True)

        return [
            {**item, "rrf_score": scores[doc_id]}
            for doc_id, item in ranked
        ]

    async def _bm25_search(
        self, query: str, tenant_id: str, top_k: int
    ) -> list[dict]:
        """BM25关键词召回 - 从Pinecone元数据中获取文本进行计算"""
        import math
        from app.core.database import AsyncSessionLocal
        from app.models.document import Document

        # 从数据库获取该租户所有已索引的chunk
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Document).where(
                    Document.tenant_id == tenant_id,
                    Document.status == "indexed",
                )
            )
            docs = result.scalars().all()

        # 收集所有chunk文本和ID
        chunk_texts = []
        chunk_ids = []
        # 注意：实际应从向量库或专用chunk表获取，这里简化处理
        # TODO: 后续需建设chunk表存储原始文本以支持BM25

        if not chunk_texts:
            return []  # 无数据时返回空

        # 构建BM25索引
        tokenized_corpus = [self._tokenize(text) for text in chunk_texts]
        bm25 = BM25Okapi(tokenized_corpus)

        # 查询
        tokenized_query = self._tokenize(query)
        scores = bm25.get_scores(tokenized_query)

        # 取top_k
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        return [
            {"id": chunk_ids[i], "text": chunk_texts[i], "bm25_score": scores[i]}
            for i in top_indices
            if scores[i] > 0
        ]

    def _tokenize(self, text: str) -> list[str]:
        """中英文分词（简化版）"""
        import re
        # 简单分词：英文按空格+标点，中文按字符n-gram
        text = text.lower()
        tokens = re.findall(r'\w+', text)
        # 简单的中文字符bigram
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        chinese_bigrams = [chinese_chars[i]+chinese_chars[i+1]
                          for i in range(len(chinese_chars)-1)]
        return tokens + chinese_bigrams
```

- [ ] **Step 2: 创建生成服务**

```python
# backend/app/services/generation.py
from langchain_openai import ChatOpenAI
from app.core.config import get_settings

class GenerationService:
    """LLM生成服务"""

    SYSTEM_PROMPT = """你是一个专业的客服助手。请根据知识库中的内容回答用户问题。

回答要求：
1. 仅根据提供的知识库内容回答，不要编造信息
2. 回答要准确、简洁、有帮助
3. 如果知识库中没有相关信息，请明确告知用户
4. 保持友好的对话语气

知识库内容：
{context}

对话历史：
{history}

用户问题：{question}

回答："""

    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            max_tokens=1000,
        )

    async def generate(
        self,
        question: str,
        context_chunks: list[dict],
        conversation_history: list[dict],
    ) -> str:
        """生成回答"""
        # 构建上下文
        context = "\n\n".join([
            f"[{i+1}] {chunk['text']}"
            for i, chunk in enumerate(context_chunks)
        ]) if context_chunks else "（知识库中未找到相关信息）"

        # 构建历史
        history = "\n".join([
            f"{'用户' if msg['role'] == 'user' else '助手'}: {msg['content']}"
            for msg in conversation_history[-10:]  # 最近10条
        ]) if conversation_history else "（首次对话）"

        prompt = self.SYSTEM_PROMPT.format(
            context=context,
            history=history,
            question=question,
        )

        response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
        return response.content
```

- [ ] **Step 3: 创建意图识别服务**

```python
# backend/app/services/intent.py
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
            model="gpt-4o-mini",  # 用小模型更经济
        )

    async def classify(self, question: str) -> str:
        """识别意图"""
        prompt = self.INTENT_PROMPT.format(question=question)
        response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
        intent = response.content.strip().lower()

        if "knowledge_qa" in intent:
            return "knowledge_qa"
        elif "chitchat" in intent:
            return "chitchat"
        return "invalid"
```

- [ ] **Step 4: 创建对话API**

```python
# backend/app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from app.core.database import get_db
from app.models.conversation import Conversation
from app.services.retrieval import RetrievalService
from app.services.generation import GenerationService
from app.services.intent import IntentService
import uuid

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
    await db.flush()

    # 6. 生成推荐问题（简化版）
    recommendations = await _generate_recommendations(request.message, chunks)

    return {
        "reply": reply,
        "recommendations": recommendations,
        "session_id": request.session_id,
    }

async def _generate_recommendations(question: str, chunks: list[dict]) -> list[str]:
    """基于当前问题和检索结果生成2-3个推荐问题"""
    from app.services.generation import GenerationService

    if not chunks:
        return ["常见问题有哪些？", "如何联系人工客服？"]

    # 提取chunk中的关键词作为推荐依据
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
    response = await generation_service.llm.ainvoke([
        {"role": "user", "content": recommendation_prompt}
    ])

    # 解析返回的问题列表
    lines = [l.strip() for l in response.content.strip().split('\n') if l.strip()]
    # 过滤掉可能的编号前缀如"1." "2." 等
    clean_lines = []
    for line in lines[:3]:
        # 去掉开头的数字编号
        cleaned = line.lstrip('0123456789.、) ').strip()
        if cleaned:
            clean_lines.append(cleaned)

    return clean_lines if clean_lines else ["常见问题有哪些？", "如何联系人工客服？"]
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/retrieval.py backend/app/services/generation.py backend/app/services/intent.py backend/app/api/chat.py
git commit -m "feat: AI服务 - RAG Pipeline（检索+生成+意图识别）"
```

---

## Task 6: 渠道接入 - 企业微信

**Files:**
- Create: `backend/app/services/channels/wechat.py`
- Create: `backend/app/api/channels.py`
- Create: `frontend/widget/index.html`
- Create: `frontend/widget/widget.js`

- [ ] **Step 1: 创建企业微信服务**

```python
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
```

- [ ] **Step 2: 创建渠道API**

```python
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

    # 验证签名（简化）
    msg_signature = body.get("msg_signature", "")
    timestamp = body.get("timestamp", "")
    nonce = body.get("nonce", "")
    encrypted_msg = body.get("encrypt", "")

    # 解密消息（实际使用WXBizMsgCrypt库）
    # 企微消息解密需要使用 WXBizMsgCrypt库，这里简化处理
    # TODO: 接入时需实现完整的加解密逻辑（参考企微官方SDK）
    from fastapi import HTTPException
    try:
        from xml.etree import ElementTree as ET
        # 实际解密后赋值给 msg_xml
        # msg_xml = wxcrypt.decrypt(encrypted_msg, token, encoding_aes_key, corp_id)
        msg_xml = "<xml><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[测试消息]]></Content><FromUserName><![CDATA[user1]]></FromUserName></xml>"  # PLACEHOLDER
    except Exception:
        raise HTTPException(status_code=400, detail="消息解密失败")

    # 解析消息
    root = ET.fromstring(msg_xml)
    msg_type = root.find("MsgType").text
    content = root.find("Content").text
    from_user = root.find("FromUserName").text

    # 生成session_id
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
```

- [ ] **Step 3: 创建网页Widget前端**

```html
<!-- frontend/widget/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YG智能客服</title>
    <style>
        #yg-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 380px;
            height: 520px;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            display: flex;
            flex-direction: column;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            z-index: 9999;
        }
        #yg-widget.minimized {
            height: 60px;
        }
        #yg-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px;
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
        }
        #yg-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }
        .message {
            margin-bottom: 12px;
            max-width: 80%;
        }
        .message.user {
            margin-left: auto;
            background: #667eea;
            color: white;
            border-radius: 16px 16px 4px 16px;
            padding: 10px 14px;
        }
        .message.assistant {
            background: #f1f3f4;
            border-radius: 16px 16px 16px 4px;
            padding: 10px 14px;
        }
        #yg-input-area {
            padding: 12px 16px;
            border-top: 1px solid #eee;
            display: flex;
            gap: 8px;
        }
        #yg-input {
            flex: 1;
            border: 1px solid #ddd;
            border-radius: 20px;
            padding: 10px 16px;
            outline: none;
        }
        #yg-input:focus {
            border-color: #667eea;
        }
        #yg-send {
            background: #667eea;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 10px 20px;
            cursor: pointer;
        }
        #yg-send:disabled {
            background: #ccc;
        }
    </style>
</head>
<body>
    <div id="yg-widget" class="minimized">
        <div id="yg-header" onclick="toggleWidget()">
            <span>🤖 YG智能客服</span>
            <span id="yg-toggle">−</span>
        </div>
        <div id="yg-messages" style="display:none;">
            <div class="message assistant">您好！有什么可以帮助您的吗？</div>
        </div>
        <div id="yg-input-area" style="display:none;">
            <input type="text" id="yg-input" placeholder="输入您的问题..." />
            <button id="yg-send" onclick="sendMessage()">发送</button>
        </div>
    </div>

    <script src="widget.js"></script>
    <script>
        // 初始化Widget
        window.YGWidget.init({
            apiBase: 'http://localhost:8000',
            tenantId: 'default',
            channel: 'webchat',
        });
    </script>
</body>
</html>
```

- [ ] **Step 4: 创建Widget JS**

```javascript
// frontend/widget/widget.js
(function() {
    const CONFIG = {
        apiBase: 'http://localhost:8000',
        tenantId: 'default',
        channel: 'webchat',
        userId: 'user_' + Math.random().toString(36).substr(2, 9),
        sessionId: null,
    };

    let messagesEl, inputEl, sendBtn;

    function init(config) {
        Object.assign(CONFIG, config);
        CONFIG.sessionId = 'session_' + Date.now();

        messagesEl = document.getElementById('yg-messages');
        inputEl = document.getElementById('yg-input');
        sendBtn = document.getElementById('yg-send');

        inputEl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    window.YGWidget = { init };

    function toggleWidget() {
        const widget = document.getElementById('yg-widget');
        const isMin = widget.classList.toggle('minimized');
        const toggle = document.getElementById('yg-toggle');
        toggle.textContent = isMin ? '−' : '−';
        messagesEl.style.display = isMin ? 'none' : 'block';
        document.getElementById('yg-input-area').style.display = isMin ? 'none' : 'flex';
    }
    window.toggleWidget = toggleWidget;

    async function sendMessage() {
        const text = inputEl.value.trim();
        if (!text) return;

        // 添加用户消息
        addMessage('user', text);
        inputEl.value = '';
        sendBtn.disabled = true;

        try {
            const resp = await fetch(`${CONFIG.apiBase}/api/chat/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tenant_id: CONFIG.tenantId,
                    channel: CONFIG.channel,
                    user_id: CONFIG.userId,
                    session_id: CONFIG.sessionId,
                    message: text,
                }),
            });

            const data = await resp.json();

            // 添加助手回复
            addMessage('assistant', data.reply);

            // 添加推荐问题
            if (data.recommendations && data.recommendations.length > 0) {
                const recEl = document.createElement('div');
                recEl.className = 'message assistant';
                recEl.innerHTML = '<small>推荐问题：</small><br>' +
                    data.recommendations.map(r => `<a href="javascript:void(0)" onclick="YGWidget.send('${r}')">${r}</a>`).join('<br>');
                messagesEl.appendChild(recEl);
            }
        } catch (err) {
            addMessage('assistant', '抱歉，服务出了点问题，请稍后再试。');
        } finally {
            sendBtn.disabled = false;
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }
    }
    window.YGWidget.send = sendMessage;

    function addMessage(role, text) {
        const el = document.createElement('div');
        el.className = `message ${role}`;
        el.textContent = text;
        messagesEl.appendChild(el);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }
})();
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/channels/ frontend/widget/
git commit -m "feat: 渠道接入 - 企业微信Webhook + 网页Widget"
```

---

## Task 7: 管理员后台 - 知识库管理

**Files:**
- Create: `backend/app/api/admin.py`
- Create: `frontend/admin/index.html` (简单管理界面)

- [ ] **Step 1: 创建管理员API**

```python
# backend/app/api/admin.py
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
    await db.flush()

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
    await db.flush()

    return {"id": doc.id, "chunk_count": len(chunks)}
```

- [ ] **Step 2: 创建管理界面HTML**

```html
<!-- frontend/admin/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>YG知识库管理后台</title>
    <style>
        body { font-family: -apple-system, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        .toolbar { margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f5f5f5; }
        .status { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .status.pending { background: #fff3cd; }
        .status.indexed { background: #d4edda; }
        .status.failed { background: #f8d7da; }
        .btn { padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-primary { background: #007bff; color: white; }
    </style>
</head>
<body>
    <h1>📚 YG知识库管理后台</h1>

    <div class="toolbar">
        <button class="btn btn-primary" onclick="location.reload()">🔄 刷新</button>
    </div>

    <table id="doc-table">
        <thead>
            <tr>
                <th>文件名</th>
                <th>类型</th>
                <th>状态</th>
                <th>分段数</th>
                <th>上传时间</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody></tbody>
    </table>

    <script>
        const API = 'http://localhost:8000/api/admin';

        async function loadDocuments() {
            const resp = await fetch(`${API}/documents`);
            const docs = await resp.json();

            const tbody = document.querySelector('#doc-table tbody');
            tbody.innerHTML = docs.map(d => `
                <tr>
                    <td>${d.filename}</td>
                    <td>${d.file_type}</td>
                    <td><span class="status ${d.status}">${d.status}</span></td>
                    <td>${d.chunk_count || 0}</td>
                    <td>${new Date(d.created_at).toLocaleString()}</td>
                    <td>
                        ${d.status === 'indexed' ? `<button class="btn btn-primary" onclick="reindex('${d.id}')">重建索引</button>` : ''}
                        <button class="btn btn-danger" onclick="deleteDoc('${d.id}')">删除</button>
                    </td>
                </tr>
            `).join('');
        }

        async function deleteDoc(id) {
            if (!confirm('确定删除？')) return;
            await fetch(`${API}/documents/${id}`, { method: 'DELETE' });
            loadDocuments();
        }

        async function reindex(id) {
            await fetch(`${API}/documents/${id}/reindex`, { method: 'POST' });
            loadDocuments();
        }

        loadDocuments();
    </script>
</body>
</html>
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/admin.py frontend/admin/
git commit -m "feat: 管理员后台 - 知识库管理界面"
```

---

## Task 8: 集成测试与上线

**Files:**
- Create: `backend/tests/test_integration.py`

- [ ] **Step 1: 编写集成测试**

```python
# backend/tests/test_integration.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_chat_flow(client):
    """测试完整对话流程"""
    payload = {
        "tenant_id": "test",
        "channel": "webchat",
        "user_id": "test_user",
        "session_id": "test_session",
        "message": "你们的产品有什么功能？",
    }
    resp = await client.post("/api/chat/message", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert "session_id" in data
```

- [ ] **Step 2: 本地验证服务**

Run: `cd backend && uvicorn app.main:app --reload --port 8000 &`
Expected: 服务在后台启动

Run: `curl http://localhost:8000/health`
Expected: `{"status":"ok"}`

Run: `curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"test","channel":"webchat","user_id":"u1","session_id":"s1","message":"你好"}'`
Expected: 返回对话结果

- [ ] **Step 3: 最终Commit**

```bash
git add backend/tests/
git commit -m "test: 集成测试覆盖"
git tag -a v0.1.0 -m "MVP版本 - 具备基础客服能力"
```

---

## 执行顺序

1. **Task 1** - 项目基础架构（FastAPI骨架）
2. **Task 2** - 数据模型（Document/Conversation/ChannelConfig）
3. **Task 3** - 知识库管理 - 文档上传与解析
4. **Task 4** - 知识库管理 - 向量化与索引
5. **Task 5** - AI服务 - RAG Pipeline
6. **Task 6** - 渠道接入 - 企业微信 + 网页Widget
7. **Task 7** - 管理员后台
8. **Task 8** - 集成测试与上线

---

## 环境变量配置

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/yginfo
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=us-east-1
OPENAI_API_KEY=your_openai_key
```
