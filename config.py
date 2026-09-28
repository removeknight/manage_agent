import os
from functools import lru_cache

from sqlalchemy import URL
from sqlalchemy.engine import make_url

# 若安装了 python-dotenv，则自动加载同目录下的 .env（把敏感信息放这里，不进源码）。
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # 没装也不报错，直接用真实环境变量
    pass


@lru_cache
def get_database_url(async_driver: bool = True) -> URL:
    """构造数据库连接 URL。

    绝不在源码中硬编码任何密码；所有敏感信息均来自环境变量 / .env。
    - async_driver=True  -> postgresql+asyncpg（应用/建表脚本运行时用）
    - async_driver=False -> postgresql+psycopg2（部分同步工具用）

    优先读取完整 DATABASE_URL；否则由分项拼装。使用 URL.create 让密码里的
    特殊字符（如 '#'）被正确编码，避免手动拼字符串出错。
    """
    target_driver = "postgresql+asyncpg" if async_driver else "postgresql+psycopg2"

    raw = os.getenv("DATABASE_URL")
    if raw:
        url = make_url(raw)
    else:
        url = URL.create(
            drivername=target_driver,
            username=_require("POSTGRES_USER"),
            password=_require("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=_require("POSTGRES_DB"),
        )

    if url.drivername != target_driver:
        url = url.set(drivername=target_driver)
    return url


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(
            f"缺少必需的环境变量 {key}，请在 .env 或部署环境中配置（不要写进源码）。"
        )
    return value
