from sqlalchemy import Column, String, DateTime, Boolean, JSON, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class ChannelConfig(Base):
    __tablename__ = "channel_configs"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'channel', name='uix_tenant_channel'),
    )

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    channel = Column(String(50), nullable=False)  # webchat, wechat

    config = Column(JSON, default={})  # channel-specific config
    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
