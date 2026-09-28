import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class Session(Base):
    __tablename__ = "session"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(36))
    user_id: Mapped[str] = mapped_column(String(36))
    description: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(),
                                                          nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(),
                                                          onupdate=func.now(),
                                                          nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
