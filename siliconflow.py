"""读取 SiliconFlow 模型列表。

公司网络会用 Cisco Secure Access 做 TLS 拦截，Python 自带的 CA 包里没有这张
企业根证书，直接 requests 会报 CERTIFICATE_VERIFY_FAILED。这里改用操作系统
证书库校验证书，而不是关闭校验。
"""

import json
import os
import re
from typing import Any

import requests
import truststore

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_BASE = "https://api.siliconflow.cn/v1"
MODELS_URL = f"{API_BASE}/models"
CATALOG_URL = "https://www.siliconflow.cn/models"
PROVIDER = "siliconflow"

# 公开页面不提供默认 temperature，这是调用参数，不是模型属性。
_UNAVAILABLE_FIELDS = ("temperature",)

_tls_ready = False
_models_cache: list[dict[str, Any]] | None = None
_catalog_cache: list[dict[str, Any]] | None = None


def configure_tls() -> None:
    """让后续 HTTPS 请求使用 Windows 证书库（含企业根证书）。"""
    global _tls_ready
    if _tls_ready:
        return
    truststore.inject_into_ssl()
    _tls_ready = True


def fetch_models(api_key: str | None = None, timeout: float = 30) -> list[dict[str, Any]]:
    """拉取当前账号可见的模型列表。

    cloud.siliconflow.cn/me/models 是登录后的前端页面，未带会话时会跳到登录页，
    页面 HTML 里没有模型数据。模型信息走官方接口 /v1/models。
    """
    global _models_cache
    configure_tls()
    key = api_key or os.getenv("SILICONFLOW_API_KEY")
    if not key:
        raise RuntimeError(
            "缺少环境变量 SILICONFLOW_API_KEY，请写入 manage_agent/.env，不要写进源码。"
        )

    response = requests.get(
        MODELS_URL,
        headers={"Authorization": f"Bearer {key}"},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data")
    if not isinstance(data, list):
        raise RuntimeError(f"SiliconFlow 模型列表响应异常: {payload!r}")
    _models_cache = data
    return data


def list_models(api_key: str | None = None, timeout: float = 30) -> list[dict[str, Any]]:
    """返回模型列表，同一次进程内复用已拉取的结果。"""
    if _models_cache is not None and api_key is None:
        return _models_cache
    return fetch_models(api_key=api_key, timeout=timeout)


def fetch_public_catalog(timeout: float = 30) -> list[dict[str, Any]]:
    """读取公开模型广场，不需要登录，也不需要 API Key。

    cloud.siliconflow.cn 会跳到登录页。www.siliconflow.cn/models 把模型目录
    直接嵌在页面脚本里，其中包含价格、上下文长度和简介。
    """
    global _catalog_cache
    configure_tls()
    response = _get_with_retry(CATALOG_URL, timeout=timeout)
    response.raise_for_status()
    catalog = _parse_catalog(response.text)
    if not catalog:
        raise RuntimeError("公开模型广场页面里没有解析到模型目录")
    _catalog_cache = catalog
    return catalog


def list_catalog(timeout: float = 30) -> list[dict[str, Any]]:
    """返回公开模型目录，同一次进程内复用已拉取的结果。"""
    if _catalog_cache is not None:
        return _catalog_cache
    return fetch_public_catalog(timeout=timeout)


def search_models(keyword: str) -> list[dict[str, Any]]:
    """按模型名做不区分大小写的包含匹配，例如 qwen、deepseek。"""
    needle = keyword.strip().lower()
    if not needle:
        raise ValueError("关键词不能为空")
    return [item for item in list_catalog() if needle in _model_name(item).lower()]


def find_model(model_id: str) -> dict[str, Any]:
    """按模型名精确查找。大小写不一致但唯一时也接受。"""
    target = model_id.strip()
    if not target:
        raise ValueError("模型 id 不能为空")

    models = list_catalog()
    exact = [item for item in models if _model_name(item) == target]
    if len(exact) == 1:
        return exact[0]

    folded = [item for item in models if _model_name(item).lower() == target.lower()]
    if len(folded) == 1:
        return folded[0]
    if len(folded) > 1:
        ids = ", ".join(_model_name(item) for item in folded)
        raise ValueError(f"模型 id 不唯一，请指定完整 id: {ids}")

    partial = search_models(target)
    if partial:
        ids = ", ".join(_model_name(item) for item in partial[:20])
        raise ValueError(f"没有名为 {target!r} 的模型。相近结果: {ids}")
    raise ValueError(f"没有名为 {target!r} 的模型")


def to_model_config(model: dict[str, Any]) -> dict[str, Any]:
    """整理成 model_config 表的业务字段。

    广场价格单位是元 / 百万 tokens，表字段是元 / 千 tokens，所以除以 1000。
    max_tokens 取页面上的上下文长度。temperature 页面没有，保持 null。
    """
    context_len = _as_int(model.get("contextLen"))
    input_per_m = _as_float(model.get("inputPrice"))
    output_per_m = _as_float(model.get("outputPrice"))
    description = model.get("desc") or None
    return {
        "name": _model_name(model),
        "provider": PROVIDER,
        "api_base": API_BASE,
        "temperature": None,
        "max_tokens": context_len,
        "input_price_per_k": None if input_per_m is None else input_per_m / 1000,
        "output_price_per_k": None if output_per_m is None else output_per_m / 1000,
        "is_active": not bool(model.get("deprecatedTime")),
        "extra_params": {
            "size": model.get("size"),
            "type": model.get("type"),
            "sub_type": model.get("subType"),
            "context_len": context_len,
            "currency": model.get("currency"),
            "input_price_per_m": input_per_m,
            "output_price_per_m": output_per_m,
            "price_unit": model.get("inputPriceUnit") or "/ M Tokens",
            "features": model.get("_func") or [],
        },
        "description": description,
        "unavailable_fields": list(_UNAVAILABLE_FIELDS),
    }


def _get_with_retry(url: str, timeout: float) -> requests.Response:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            return requests.get(url, timeout=timeout)
        except requests.exceptions.SSLError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


def _parse_catalog(html: str) -> list[dict[str, Any]]:
    """从页面脚本里的转义 JSON 抽出模型对象。"""
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
    if not scripts:
        return []
    text = max(scripts, key=len).replace('\\"', '"').replace("\\\\", "\\")
    decoder = json.JSONDecoder()
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    idx = 0
    while True:
        marker = text.find('"modelName"', idx)
        if marker < 0:
            break
        start = text.rfind("{", 0, marker)
        try:
            obj, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            idx = marker + 12
            continue
        name = obj.get("modelName") if isinstance(obj, dict) else None
        if name and name not in seen and "contextLen" in obj:
            seen.add(name)
            found.append(obj)
        idx = max(end, marker + 12)
    return found


def _model_name(model: dict[str, Any]) -> str:
    return str(model.get("modelName") or model.get("id") or "")


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)
