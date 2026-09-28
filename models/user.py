import datetime
from typing import Optional
from sqlalchemy import String, Float, TIMESTAMP, DateTime, Boolean, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from models.base import Base


class User(Base):
    __tablename__ = "user"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(36))
    description: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(),
                                                          nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(),
                                                          onupdate=func.now(),
                                                          nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

