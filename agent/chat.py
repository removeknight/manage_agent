import os
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent


def build_agent(model_name, base_url, temperature):
    SYSTEM_PROMPT = """你是一个旅游助手，你需要给我提供一些旅游建议"""
    model = ChatOpenAI(
        model="Qwen/Qwen3.5-35B-A3B",
        api_key=os.getenv("SILICONFLOW_API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
    )

    return create_deep_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
    )
