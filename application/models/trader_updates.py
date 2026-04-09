import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, func, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import enum


class UpdateVisibility(str, enum.Enum):
    PUBLIC = "public"
    SUBSCRIBERS_ONLY = "subscribers_only"


class TraderUpdate(Base):
    __tablename__ = "trader_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trader_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trader_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=False)
    visibility = Column(
        Enum(UpdateVisibility, native_enum=True, name="update_visibility"),
        nullable=False,
        default=UpdateVisibility.PUBLIC,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    trader_profile = relationship("TraderProfile", back_populates="updates")
