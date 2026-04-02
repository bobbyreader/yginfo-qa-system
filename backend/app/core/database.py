from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings

settings = get_settings()

# 创建异步引擎
engine_kwargs = {
    "echo": settings.debug,
    "pool_pre_ping": True,
}

# SQLite 不支持 pool_size 和 max_overflow
if not settings.database_url.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
    })

async_engine = create_async_engine(settings.database_url, **engine_kwargs)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy声明式基类"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """数据库会话依赖"""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
