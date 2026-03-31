from flask import request, jsonify
from flask_security import auth_required, current_user
from datetime import datetime
from server.db.model import db, Comentario, User
@auth_required()
def add_comment(post_id):
    data = request.get_json()
    
    content = data.get('content', '').strip()
    if not content:
        return jsonify({"error": "El comentario no puede estar vacío"}), 400
    
    # --- CREACIÓN DEL REGISTRO ---
    nuevo_comentario = Comentario(
        ID_pblcn=post_id,
        ID_Usr=current_user.id,
        Contenido=content,
        Respuesta_A_ID=data.get('parent_id')
    )
    
    try:
        db.session.add(nuevo_comentario)
        db.session.commit()
        
        return jsonify({
            "mensaje": "Comentario creado exitosamente",
            "id": str(nuevo_comentario.ID_Cmmnt)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error interno al guardar el comentario"}), 500
def get_post_comments(post_id):
    comentarios = Comentario.query.filter_by(ID_pblcn=post_id).order_by(Comentario.Fch_creacion.asc()).all()
    
    res = []
    for c in comentarios:
        user = User.query.get(c.ID_Usr)
        
        author_name = f"{user.nombre} {user.apellido1}" if user else "Anónimo"
        
        res.append({
            "id": str(c.ID_Cmmnt),
            "author": author_name,
            "pfp": getattr(user, 'pfp_usr', None),
            "content": c.Contenido,
            "date": c.Fch_creacion.isoformat() if c.Fch_creacion else None,
            "parent_id": str(c.Respuesta_A_ID) if c.Respuesta_A_ID else None
        })
        
    return jsonify(res), 200

@auth_required()
def delete_comment(comment_id):
    cm = Comentario.query.get_or_404(comment_id)
    
    if cm.ID_Usr != current_user.id:
        return jsonify({"error": "No autorizado"}), 403

    cm.Contenido = "[Este comentario ha sido eliminado]"
    db.session.commit()
    return jsonify({"mensaje": "Comentario anonimizado"}), 200