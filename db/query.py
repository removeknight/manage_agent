"""动态查询构造器。

根据一个过滤字典拼出带 WHERE / ORDER BY / LIMIT / OFFSET 的 Select 语句。

基本用法：
    build_sql_stmt(
        User,
        filters={
            "name": {"operator": "ilike", "value": "%bob%"},
            "is_deleted": False,                       # 普通值 = 等值(eq)
            "id": {"operator": "in", "value": ["u1", "u2"]},
        },
        order_by=[
            {"key": "created_at", "sort_order": "desc"},
            {"key": "name", "sort_order": "asc"},
        ],
        limit=20,
        offset=0,
    )

字段值的两种形式：
1) 普通值            -> 等值(eq)
2) {"operator": X, "value": Y} -> 按 operator 查询

operator 一个名字对应一种查询（无别名）：
    eq        col =  value
    ne        col != value
    gt        col >  value
    ge        col >= value
    lt        col <  value
    le        col <= value
    in        col IN value           value 为列表
    notin     col NOT IN value       value 为列表
    like      col LIKE value
    ilike     col ILIKE value
    between   col BETWEEN v0 AND v1   value 为 [v0, v1]
    isnull    value 为真 -> IS NULL；为假 -> IS NOT NULL

AND / OR 组合（可嵌套）：
    filters 顶层是各条件的 AND。用保留键 "and" / "or" 传入子过滤字典列表来组合：
    {
        "is_deleted": False,                 # 与下面的 or 一起 AND
        "or": [
            {"name": {"operator": "like", "value": "a%"}},
            {"name": {"operator": "like", "value": "b%"}},
        ],
    }
    => WHERE is_deleted = false AND (name LIKE 'a%' OR name LIKE 'b%')

说明：
- filters 的列名必须是该模型的合法列，否则抛 ValueError。
- 值为 None 的字段跳过（想查 IS NULL 用 {"operator": "isnull", "value": True}）。
- 返回 Select 对象（非字符串），同步/异步都能执行。
"""

from typing import Any, Optional

from sqlalchemy import Select, and_, inspect, or_, select
from sqlalchemy.orm import InstrumentedAttribute

# 保留键：用于逻辑组合，不当作列名
_AND = "and"
_OR = "or"

# operator 规范名 -> 构造条件的函数 (列, 值) -> 条件表达式（一个名字一种查询，无别名）
_OPERATORS: dict[str, Any] = {
    "eq": lambda col, v: col == v,
    "ne": lambda col, v: col != v,
    "gt": lambda col, v: col > v,
    "ge": lambda col, v: col >= v,
    "lt": lambda col, v: col < v,
    "le": lambda col, v: col <= v,
    "in": lambda col, v: col.in_(v),
    "notin": lambda col, v: col.notin_(v),
    "like": lambda col, v: col.like(v),
    "ilike": lambda col, v: col.ilike(v),
    "between": lambda col, v: col.between(v[0], v[1]),
    "isnull": lambda col, v: col.is_(None) if v else col.isnot(None),
}


def build_sql_stmt(
    model: type,
    filters: Optional[dict[str, Any]] = None,
    *,
    order_by: Optional[list[dict[str, str]]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Select:
    """按过滤字典拼出 Select 查询。

    :param model: 映射模型类（如 User）
    :param filters: 过滤字典，见模块文档
    :param order_by: 排序，形如 [{"key": "列名", "sort_order": "asc"/"desc"}]，
                     sort_order 省略时默认 asc
    :param limit: LIMIT
    :param offset: OFFSET
    :return: sqlalchemy.Select 对象
    """
    valid_columns = {attr.key for attr in inspect(model).column_attrs}

    stmt = select(model)

    if filters:
        condition = _build_node(model, filters, valid_columns)
        if condition is not None:
            stmt = stmt.where(condition)

    if order_by:
        stmt = stmt.order_by(*_build_order_by(model, order_by, valid_columns))

    if offset is not None:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)

    return stmt


def _build_node(model: type, node: dict[str, Any], valid_columns: set[str]):
    """把一个过滤字典（可含 and/or 嵌套）转成一个条件表达式；空则返回 None。"""
    if not isinstance(node, dict):
        raise ValueError(f"过滤条件必须是 dict，得到 {type(node).__name__}")

    conditions = []
    for key, value in node.items():
        if key in (_AND, _OR):
            subs = [_build_node(model, sub, valid_columns) for sub in value]
            subs = [c for c in subs if c is not None]
            if not subs:
                continue
            conditions.append(and_(*subs) if key == _AND else or_(*subs))
        else:
            if key not in valid_columns:
                raise ValueError(
                    f"{model.__name__} 没有列 {key!r}，可用列: {sorted(valid_columns)}"
                )
            if value is None:
                continue  # 没有值，跳过
            column: InstrumentedAttribute = getattr(model, key)
            conditions.append(_build_condition(column, value))

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return and_(*conditions)  # 同一层多个条件默认 AND


def _build_condition(column: InstrumentedAttribute, value: Any):
    """把 (列, 值) 转成一个 SQL 条件表达式。"""
    if isinstance(value, dict) and "operator" in value:
        op = value["operator"]
        func = _OPERATORS.get(op)
        if func is None:
            raise ValueError(
                f"不支持的 operator: {op!r}，可用: {sorted(_OPERATORS)}"
            )
        return func(column, value.get("value"))

    # 普通值（含不带 operator 的 dict，如 JSONB 值）-> 等值
    return column == value


def _build_order_by(
    model: type,
    order_by: list[dict[str, str]],
    valid_columns: set[str],
) -> list:
    """把 order_by 参数转成排序表达式列表。

    order_by 形如 [{"key": "列名", "sort_order": "asc"/"desc"}]，
    sort_order 省略时默认 asc。
    """
    result = []
    for item in order_by:
        if not isinstance(item, dict) or "key" not in item:
            raise ValueError(
                f"order_by 元素必须是 {{'key': 列名, 'sort_order': 'asc'/'desc'}}，"
                f"得到 {item!r}"
            )
        name = item["key"]
        if name not in valid_columns:
            raise ValueError(
                f"{model.__name__} 没有列 {name!r}，可用列: {sorted(valid_columns)}"
            )

        sort_order = str(item.get("sort_order", "asc")).strip().lower()
        if sort_order not in ("asc", "desc"):
            raise ValueError(
                f"sort_order 只能是 'asc' 或 'desc'，得到 {item.get('sort_order')!r}"
            )

        column: InstrumentedAttribute = getattr(model, name)
        result.append(column.desc() if sort_order == "desc" else column.asc())
    return result
