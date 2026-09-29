"""model_config 的接口层（api）。

职责：只处理「参数」——请求体校验（Pydantic 入参）、依赖注入拿到 db 会话、
把校验后的数据交给 service 层，再用响应模型把结果序列化返回。
不写任何业务逻辑，也不直接操作数据库。
"""

import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from service import model_service

router = APIRouter(prefix="/model", tags=["model"])


class ModelCreateParam(BaseModel):
    """创建模型配置的入参。"""

    name: str
    provider: Literal["openai", "qwen", "siliconflow"] = "siliconflow"
    api_base: str
    temperature: float = 1.0
    max_tokens: Optional[int] = None
    input_price_per_k: float
    output_price_per_k: float
    is_active: bool = True
    extra_params: Optional[dict] = None
    description: Optional[str] = None


class ModelUpdateParam(BaseModel):
    """更新模型配置的入参。"""

    temperature: float = 1.0
    max_tokens: Optional[int] = None
    input_price_per_k: float
    output_price_per_k: float
    is_active: bool = True
    extra_params: Optional[dict] = None
    description: Optional[str] = None


class ModelResponse(BaseModel):
    """模型配置的出参（从 ORM 对象序列化）。"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    provider: str
    api_base: str
    temperature: float
    max_tokens: Optional[int] = None
    input_price_per_k: float
    output_price_per_k: float
    is_active: bool
    extra_params: Optional[dict] = None
    description: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_deleted: bool


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    param: ModelCreateParam,
    db: AsyncSession = Depends(get_db),
) -> ModelResponse:
    """创建模型配置：校验入参后交给 service 层落库。"""
    instance = await model_service.create_model(db, param.model_dump())
    return instance


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str, db: AsyncSession = Depends(get_db)):
    pass


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    update_param: ModelUpdateParam,
    db: AsyncSession = Depends(get_db),
):
    pass


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(model_id: str, db: AsyncSession = Depends(get_db)):
    pass
