import datetime
from typing import Optional, Any
from sqlalchemy import String, Float, DateTime, Boolean, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from models.base import Base


class Chat(Base):
    __tablename__ = "chat"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36))
    session_id: Mapped[str] = mapped_column(String(36))
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    llm_id: Mapped[str] = mapped_column(String(36))
    llm_name: Mapped[Optional[str]] = mapped_column(String(128))
    tool_calls: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    role: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(),
                                                          nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(),
                                                          onupdate=func.now(),
                                                          nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
