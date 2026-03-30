from flask_socketio import emit, join_room
from flask_security import current_user
from server.db.model import db
from server.db.community import Registro_Chat, Usuario_Comunidad, Chat
import datetime

def register_chat_events(socketio):
    @socketio.on('join')
    def handle_join(data):
        comm_id = data.get('comm_id')
        if not comm_id: return
        
        miembro = Usuario_Comunidad.query.filter_by(
            ID_Usr=current_user.id, ID_cmnd=comm_id
        ).first()
        
        if miembro:
            join_room(comm_id)
            print(f"[WS] {current_user.nombre} entró a sala {comm_id}")

    @socketio.on('send_msg')
    def handle_send_msg(data):
        comm_id = data.get('comm_id')
        mensaje_texto = data.get('mensaje', '').strip()

        # VALIDACIÓN 2000 CARACTERES
        if len(mensaje_texto) > 2000:
            emit('error', {'msg': 'El mensaje excede los 2000 caracteres.'})
            return

        if not mensaje_texto: return

        sala = Chat.query.filter_by(iD_cmnd=comm_id).first()
        
        if not sala:
            emit('error', {'msg': 'Chat no encontrado'})
            return

        nuevo_mnsj = Registro_Chat(
            ID_Usr=current_user.id,
            ID_Chat=sala.ID_Chat,
            Dscrpcn=mensaje_texto, 
            Fch_envio=datetime.datetime.now(datetime.timezone.utc)
        )

        db.session.add(nuevo_mnsj)
        db.session.commit()

        # BROADCAST
        emit('receive_msg', {
            'texto': mensaje_texto,
            'autor': current_user.nombre,
            'fecha': nuevo_mnsj.Fch_envio.isoformat()
        }, room=comm_id)