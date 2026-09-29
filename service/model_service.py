"""model_config 的业务逻辑层（service）。

职责：处理业务规则（生成主键、组装落库数据、管理事务提交/回滚），
向上给 api 层提供纯粹的业务方法，向下调用 models 层完成数据读写。
api 层不直接碰数据库，models 层不关心事务边界，事务在这里收口。
"""

from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from models import model_config as model_config_db
from models.model_config import ModelConfig


async def create_model(db: AsyncSession, data: dict[str, Any]) -> ModelConfig:
    """创建一条模型配置并真实写入数据库。

    :param db: 异步会话（由 api 层通过依赖注入传入）
    :param data: 已经过 api 层校验的字段字典（不含 id）
    :return: 落库后的 ModelConfig 实例（含数据库生成的 id/时间字段）
    """
    payload = {**data, "id": uuid4().hex}

    try:
        instance = await model_config_db.insert(db, payload)
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return instance
