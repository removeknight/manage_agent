import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.model_tools import get_siliconflow_model_config, search_siliconflow_models
from siliconflow import configure_tls

load_dotenv()
configure_tls()

model = ChatOpenAI(
    model="Qwen/Qwen3.5-35B-A3B",
    api_key=os.getenv("SILICONFLOW_API_KEY"),
    base_url="https://api.siliconflow.cn/v1",
)

SYSTEM_PROMPT = """你是模型配置助手。
用户询问某一系列有哪些模型时，调用 search_siliconflow_models，把模型 id 列出来，然后停下来等用户选择。
只有用户明确选定一个模型 id 之后，才调用 get_siliconflow_model_config，并原样说明返回的字段。
价格单位是元/千 tokens。temperature 为 null 时不要编造。
不要把结果写入数据库。"""


def build_agent():
    from deepagents import create_deep_agent

    return create_deep_agent(
        model=model,
        tools=[search_siliconflow_models, get_siliconflow_model_config],
        system_prompt=SYSTEM_PROMPT,
    )


if __name__ == "__main__":
    print(search_siliconflow_models.invoke({"keyword": "qwen"}))
    print(get_siliconflow_model_config.invoke({"model_id": "Qwen/Qwen3.5-35B-A3B"}))
