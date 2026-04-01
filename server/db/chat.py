import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, DateTime, CheckConstraint,
    UniqueConstraint, ForeignKey, Index, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from server.db.model import db


class ChatDm(db.Model):
    __tablename__ = "chats"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_a_id = Column(UUID(as_uuid=True), ForeignKey("public.user.ID_Usr", ondelete="CASCADE"), nullable=False)
    user_b_id = Column(UUID(as_uuid=True), ForeignKey("public.user.ID_Usr", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relaciones
    user_a   = relationship("User", foreign_keys=[user_a_id])
    user_b   = relationship("User", foreign_keys=[user_b_id])
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan",
                            order_by="Message.created_at")


    __table_args__ = (
        CheckConstraint("user_a_id <> user_b_id", name="no_self_chat"),
        Index("idx_chats_user_a", "user_a_id"),
        Index("idx_chats_user_b", "user_b_id"),
    )

    def to_dict(self):
        return {
            "id":         str(self.id),
            "user_a_id":  str(self.user_a_id),
            "user_b_id":  str(self.user_b_id),
            "created_at": self.created_at.isoformat(),
        }

    @staticmethod
    def get_or_create(user_a_id: uuid.UUID, user_b_id: uuid.UUID) -> "ChatDm":
        """Devuelve el chat existente entre dos usuarios o crea uno nuevo."""
        lo = min(str(user_a_id), str(user_b_id))
        hi = max(str(user_a_id), str(user_b_id))
        chat = (
            db.session.query(ChatDm)
            .filter(
                func.least(func.cast(ChatDm.user_a_id, String), func.cast(ChatDm.user_b_id, String)) == lo,
                func.greatest(func.cast(ChatDm.user_a_id, String), func.cast(ChatDm.user_b_id, String)) == hi,
            )
            .first()
        )
        if not chat:
            chat = ChatDm(user_a_id=user_a_id, user_b_id=user_b_id)
            db.session.add(chat)
            db.session.commit()
        return chat


class Message(db.Model):
    __tablename__ = "messages"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id    = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id  = Column(UUID(as_uuid=True), ForeignKey("public.user.ID_Usr", ondelete="CASCADE"), nullable=False)
    type       = Column(String(10), nullable=False, default="text")
    body       = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relaciones
    chat   = relationship("ChatDm", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

    __table_args__ = (
        CheckConstraint("type IN ('text', 'image')", name="valid_message_type"),
        Index("idx_messages_chat_time", "chat_id", "created_at"),
    )

    def to_dict(self):
        return {
            "id":         str(self.id),
            "chat_id":    str(self.chat_id),
            "sender_id":  str(self.sender_id),
            "type":       self.type,
            "body":       self.body,
            "created_at": self.created_at.isoformat(),
        }
