from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .core.config import get_settings
from .core.database import Base, async_engine
from .api import chat, knowledge, channels, admin

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

# 获取 frontend 目录的绝对路径
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"


@app.on_event("startup")
async def on_startup():
    """启动时自动创建所有表"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# CORS中间件 - 允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
if FRONTEND_DIR.exists():
    app.mount("/admin", StaticFiles(directory=str(FRONTEND_DIR / "admin"), html=True), name="admin")
    app.mount("/widget", StaticFiles(directory=str(FRONTEND_DIR / "widget"), html=True), name="widget")

# 注册路由
app.include_router(chat.router)
app.include_router(knowledge.router)
app.include_router(channels.router)
app.include_router(admin.router)


@app.get("/debug/env")
async def debug_env():
    """调试端点：显示环境变量配置（不暴露敏感值）"""
    settings = get_settings()
    return {
        "database_url": "***" if settings.database_url else "NOT SET",
        "openai_api_key": "***" if settings.openai_api_key else "NOT SET",
        "openai_base_url": settings.openai_base_url or "NOT SET",
        "openai_model": settings.openai_model or "NOT SET",
        "pinecone_api_key": "***" if settings.pinecone_api_key else "NOT SET",
        "debug": settings.debug,
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok"}


@app.get("/")
async def root():
    """根路径"""
    return {"message": "YG智能知识库问答系统 API"}
