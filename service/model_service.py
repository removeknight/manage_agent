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


async def get_model(db: AsyncSession, model_id: str) -> ModelConfig | None:
    """按 id 获取一条模型配置（自动过滤已软删除的记录）。

    供其他 service / 接口复用：例如对话流程里要拿模型的 api_base、价格等。
    取不到返回 None，由调用方决定报 404 还是走默认逻辑。

    :param db: 异步会话
    :param model_id: 模型配置主键
    :return: ModelConfig 或 None
    """
    return await model_config_db.get_one(
        db,
        {"id": model_id, "is_deleted": False},
    )


async def list_models(
    db: AsyncSession,
    *,
    filters: dict[str, Any] | None = None,
    order_by: list[dict[str, str]] | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[ModelConfig]:
    """按条件查询模型配置列表（默认只返回未软删除的）。

    filters / order_by 的写法直接透传给 db.query.build_sql_stmt，调用方自由组合，例如：
        list_models(
            db,
            filters={"provider": "siliconflow", "is_active": True},
            order_by=[{"key": "created_at", "sort_order": "desc"}],
            limit=20, offset=0,
        )

    :return: ModelConfig 列表
    """
    merged_filters: dict[str, Any] = {"is_deleted": False}
    if filters:
        merged_filters.update(filters)

    return await model_config_db.get_many(
        db,
        merged_filters,
        order_by=order_by,
        limit=limit,
        offset=offset,
    )


