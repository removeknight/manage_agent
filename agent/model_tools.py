"""给 agent 用的 SiliconFlow 模型查询工具。只返回信息，不写数据库。"""

import json
import sys
from pathlib import Path

from langchain.tools import tool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from siliconflow import find_model, search_models, to_model_config


def _dump(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


@tool
def search_siliconflow_models(keyword: str) -> str:
    """按关键词查找 SiliconFlow 可用模型。

    用户问「qwen 有哪些模型」这类问题时调用。keyword 只传系列名，例如 qwen、deepseek，
    不要传整句问话。返回匹配的模型 id，交给用户选择，不要自行选定其中一个。
    """
    try:
        matched = search_models(keyword)
    except ValueError as exc:
        return _dump({"error": str(exc)})

    return _dump(
        {
            "keyword": keyword.strip(),
            "count": len(matched),
            "models": [item.get("modelName") for item in matched],
        }
    )


@tool
def get_siliconflow_model_config(model_id: str) -> str:
    """在用户明确选定一个模型 id 之后，返回 model_config 表对应的字段。

    model_id 必须是搜索结果里的完整 id，例如 Qwen/Qwen3.5-35B-A3B。
    价格和上下文长度来自公开模型广场，不需要登录。
    temperature 页面没有，返回 null，不要编造。
    input_price_per_k / output_price_per_k 的单位是元/千 tokens。
    """
    try:
        model = find_model(model_id)
    except ValueError as exc:
        return _dump({"error": str(exc)})

    return _dump({"model_config": to_model_config(model)})
