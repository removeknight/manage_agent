import datetime
from typing import Optional, Any

from sqlalchemy import String, Float, DateTime, Integer, Boolean, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ModelConfig(Base):
    __tablename__ = "model_config"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(36))
    provider: Mapped[str] = mapped_column(String(50))
    api_base: Mapped[str] = mapped_column(String(255))
    temperature: Mapped[float] = mapped_column(Float)
    # max_tokens 允许为空：不同模型不一定限制输出长度
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_price_per_k: Mapped[float] = mapped_column(Float)
    output_price_per_k: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    extra_params: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(),
                                                          nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(),
                                                          onupdate=func.now(),
                                                          nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


async def insert(db: AsyncSession, data: dict[str, Any]) -> ModelConfig:
    """model 层：把一条 model_config 数据写入数据库。

    只负责数据落库：构造 ORM 对象、flush 触发 INSERT，再 refresh 拿到
    数据库生成的字段（created_at / updated_at 等）。事务的提交/回滚交给上层
    （service 层）统一管理，保证一个业务操作是一个完整事务。

    :param db: 异步会话
    :param data: 与列名对应的字段字典（需已包含主键 id）
    :return: 写入后的 ModelConfig 实例
    """
    instance = ModelConfig(**data)
    db.add(instance)
    await db.flush()       # 执行 INSERT，但不提交事务
    await db.refresh(instance)  # 读回 server_default 生成的字段
    return instance
