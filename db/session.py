from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import get_database_url

# 全局异步引擎：整个应用共享一个连接池。
engine: AsyncEngine = create_async_engine(
    get_database_url(async_driver=True),
    echo=False,
    pool_pre_ping=True,   # 取连接前先探活，避免用到被数据库回收的死连接
    pool_size=5,
    max_overflow=10,
)

# 会话工厂：每个请求/任务用它开一个独立 session。
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：路由里用 `db: AsyncSession = Depends(get_db)` 注入。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
