from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

# CORS中间件 - 允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok"}


@app.get("/")
async def root():
    """根路径"""
    return {"message": "YG智能知识库问答系统 API"}
