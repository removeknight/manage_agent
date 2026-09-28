"""建表脚本：连接数据库并根据模型创建所有表。

用法（在 manage_agent 目录下）：
    uv run python init_db.py

注意：这是用 create_all 直接建表的快捷方式，适合初始化 / 本地开发。
后续若要用 Alembic 管理表结构变更，可对已存在的表执行 `alembic stamp head`
把当前状态标记为基线，再正常走 revision/upgrade 流程。
"""

import asyncio
import sys

# Windows 控制台默认可能是 cp1252，打印中文会报 UnicodeEncodeError，这里强制 UTF-8。
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from db.session import engine
from models import Base


async def main() -> None:
    url = engine.url
    # 打印时隐藏密码
    print(f"连接数据库：{url.render_as_string(hide_password=True)}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

    tables = ", ".join(sorted(Base.metadata.tables.keys()))
    print(f"建表完成，共 {len(Base.metadata.tables)} 张表：{tables}")


if __name__ == "__main__":
    asyncio.run(main())
