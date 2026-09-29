from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from service.model_service import get_model

from db.session import get_db
from service import model_service
from agent.chat import build_agent

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatParam(BaseModel):
    """创建模型配置的入参。"""

    llm_id: str
    temperature: float | None = None
    question: str


@router.post("")
async def reply_question(chat_param: ChatParam, db: AsyncSession = Depends(get_db)):
    """创建模型配置：校验入参后交给 service 层落库。"""
    # 获取大模型信息
    model_id = chat_param.llm_id
    model = await get_model(db, model_id)
    current_temperature = model.temperature
    if chat_param.temperature is not None:
        current_temperature = chat_param.temperature
    chat_agent = build_agent(model_name=model.name, base_url=model.api_base, temperature=current_temperature)
    result = await chat_agent.ainvoke({"messages": [{"role": "user", "content": chat_param.question}]})
    question = result["messages"][0].content
    reply = result["messages"][-1].content
    token_detail = result["messages"][-1].usage_metadata
    input_token = token_detail.get("input_tokens")
    output_token = token_detail.get("output_tokens")
    token_cost = input_token + output_token
    price_cost = input_token / 1000 * model.input_price_per_k + output_token / 1000 * model.output_price_per_k

    return JSONResponse(content={"question": question, "reply": reply,
                                 "token_usage": {"input_token": input_token,
                                                 "output_token": output_token,
                                                 "token_cost": token_cost,
                                                 "price_cost": price_cost}})
