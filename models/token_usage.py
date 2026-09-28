import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class TokenUsage(Base):
    __tablename__ = "token_usage"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36))
    llm_id: Mapped[str] = mapped_column(String(36))
    llm_name: Mapped[Optional[str]] = mapped_column(String(100))
    session_id: Mapped[str] = mapped_column(String(36))
    chat_id: Mapped[str] = mapped_column(String(36))
    token_cost: Mapped[float] = mapped_column(Float)
    price_cose: Mapped[float] = mapped_column(Float)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(),
                                                          nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(),
                                                          onupdate=func.now(),
                                                          nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
