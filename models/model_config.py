import datetime
from typing import Optional, Any
from sqlalchemy import String, Float, DateTime, Integer, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from models.base import Base


class ModelConfig(Base):
    __tablename__ = "model_config"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(36))
    provider: Mapped[str] = mapped_column(String(50))
    api_base: Mapped[str] = mapped_column(String(255))
    temperature: Mapped[float] = mapped_column(Float)
    max_tokens: Mapped[int] = mapped_column(Integer)
    input_price_per_k: Mapped[float] = mapped_column(Float)
    output_price_per_k: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    extra_params: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(),
                                                          nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(),
                                                          onupdate=func.now(),
                                                          nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
