from sqlalchemy import Column, String, Text, DateTime, Integer, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    channel = Column(String(50), nullable=False)  # webchat, wechat
    user_id = Column(String(255), nullable=False, index=True)

    session_id = Column(String(255), nullable=False, index=True)
    messages = Column(JSON, default=[])  # [{"role": "user|assistant", "content": "...", "timestamp": "..."}]

    turn_count = Column(Integer, default=0)
    last_message_at = Column(DateTime(timezone=True), server_default=func.now())

    created_at = Column(DateTime(timezone=True), server_default=func.now())
