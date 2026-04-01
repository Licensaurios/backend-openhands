from flask import Blueprint, jsonify, request
from flask_socketio import join_room, emit
from server.db.model import db
from server.db.chat import ChatDm, Message
from server.extensiones import socketio
import uuid

chat_router = Blueprint('chat', __name__, url_prefix='/chat')

@chat_router.route("/")
def chat_test():
    return "This is chat endpoint!"


@chat_router.route("/<chat_id>/messages", methods=["GET"])
def get_messages(chat_id):
    messages = (
        db.session.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .limit(50)
        .all()
    )
    return jsonify([m.to_dict() for m in messages])


@chat_router.route("/start", methods=["POST"])
def start_chat():
    """Crea o devuelve el chat entre dos usuarios."""
    data = request.get_json()
    user_a_id = uuid.UUID(data["user_a_id"])
    user_b_id = uuid.UUID(data["user_b_id"])
    chat = ChatDm.get_or_create(user_a_id, user_b_id)
    return jsonify(chat.to_dict())


@socketio.on("join_chat")
def on_join(data):
    """El cliente se une a la room del chat."""
    join_room(data["chat_id"])


@socketio.on("send_message")
def on_message(data):
    """
    Espera: { chat_id, sender_id, body, type? }
    sender_id viene del cliente por ahora — reemplazar
    con current_user.ID_Usr cuando conectes tu auth.
    """
    msg = Message(
        chat_id=uuid.UUID(data["chat_id"]),
        sender_id=uuid.UUID(data["sender_id"]),
        type=data.get("type", "text"),
        body=data["body"]
    )
    db.session.add(msg)
    db.session.commit()
    emit("new_message", msg.to_dict(), to=data["chat_id"])


@socketio.on("disconnect")
def on_disconnect():
    pass  # flask-socketio limpia las rooms automáticamente

