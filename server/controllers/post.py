from flask import request, jsonify
from server.db.community import Usuario_Comunidad, Comunidad
from server.db.model import db, User, Publicacion, Comentario, Like_Post, Post_Guardado
from flask_security import auth_required, current_user
from sqlalchemy import or_, desc
from datetime import datetime,timezone  
@auth_required()
def my_posts():
    posts = Publicacion.query.filter_by(ID_Usr=current_user.id).order_by(desc(Publicacion.Fch_pblcn)).all()
    return jsonify([format_post_output(p) for p in posts]), 200

def get_user_posts(user_id):
    posts = Publicacion.query.filter_by(ID_Usr=user_id).order_by(desc(Publicacion.Fch_pblcn)).all()
    return jsonify([format_post_output(p) for p in posts]), 200


@auth_required()
def create_post():
    data = request.get_json()
    titulo = data.get('title', '').strip()
    if len(titulo) < 5:
        return jsonify({"error": "Título demasiado corto"}), 400
    id_cmnd = data.get('id_cmnd') 

    nuevo_post = Publicacion(
        ID_Usr=current_user.id,
        Titulo=titulo,
        Dscrpcn=data.get('content', ''),
        ID_cmnd=id_cmnd, 
        ID_Pryct=data.get('id_pryct'), 
        
        Extra_Metadata={
            "is_anonymous": data.get('is_anonymous', False),
            "hasCode": data.get('hasCode', False),
            "codeLang": data.get('codeLang', 'text'),
            "codeLines": data.get('codeLines', []), # Arreglo de {text, color}
            "refs": data.get('refs', []),           # Arreglo de {label, sub}
            "featured": data.get('featured', False)
        },
        Votos_Karma=0,
        Fch_pblcn=datetime.utcnow()
    )
    
    db.session.add(nuevo_post)
    db.session.commit()
    return jsonify({"mensaje": "Post publicado", "id": str(nuevo_post.ID_pblcn)}), 201

def user_feed():
    user_id = current_user.id
    
    mis_cmnds = db.session.query(Usuario_Comunidad.ID_cmnd).filter_by(ID_Usr=user_id, Is_Active=True).subquery()
    trending = db.session.query(Comunidad.iD_cmnd).limit(5).subquery()
    posts = Publicacion.query.filter(
        or_(
            Publicacion.ID_Usr == user_id,            
            Publicacion.ID_cmnd.is_(None),            
            Publicacion.ID_cmnd.in_(mis_cmnds),
            Publicacion.ID_cmnd.in_(trending),
            Publicacion.Votos_Karma >= 5 
        )
    ).order_by(desc(Publicacion.Fch_pblcn)).limit(30).all()

    return jsonify([format_post_output(p) for p in posts]), 200
auth_required()
def delete_post(post_id):
    post = Publicacion.query.get_or_404(post_id)
    if post.ID_Usr != current_user.id:
        return jsonify({"error": "No tienes permisos para realizar esta acción"}), 403
    meta = dict(post.Extra_Metadata or {})
    meta['is_anonymous'] = True
    meta['user_removed'] = True 
    
    post.Extra_Metadata = meta
  
    if hasattr(post, 'Fch_edicion'):
        post.Fch_edicion = datetime.now(timezone.utc)
    
    try:
        db.session.commit()
        return jsonify({
            "mensaje": "Post desvinculado. El contenido ahora es anónimo.",
            "status": "success"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al procesar la solicitud en la base de datos"}), 500

@auth_required()
def toggle_like(post_id):
    like = Like_Post.query.filter_by(ID_Usr=current_user.id, ID_pblcn=post_id).first()
    
    if like:
        db.session.delete(like)
        db.session.commit()
        return jsonify({"message": "Like eliminado", "status": "unliked"}), 200
    else:
        new_like = Like_Post(ID_Usr=current_user.id, ID_pblcn=post_id)
        db.session.add(new_like)
        db.session.commit()
        return jsonify({"message": "Like añadido", "status": "liked"}), 201

@auth_required()
def toggle_save(post_id):
    guardado = Post_Guardado.query.filter_by(
        ID_Usr=current_user.id, 
        ID_pblcn=post_id
    ).first()
    
    if guardado:
        db.session.delete(guardado)
        db.session.commit()
        return jsonify({"message": "Eliminado de favoritos"}), 200
    else:
        nuevo_guardado = Post_Guardado(ID_Usr=current_user.id, ID_pblcn=post_id)
        db.session.add(nuevo_guardado)
        db.session.commit()
        return jsonify({"message": "Guardado en favoritos"}), 201

def format_post_output(p):
    meta = p.Extra_Metadata or {}
    
    if meta.get('user_removed') or meta.get('is_anonymous'):
        author = "Anónimo"
    else:
        user_obj = User.query.get(p.ID_Usr)
        author = f"{user_obj.nombre} {user_obj.apellido1}" if user_obj else "Usuario"

    edit_label = None
    if hasattr(p, 'Fch_edicion') and p.Fch_edicion:
        edit_label = f"Editado {tiempo_hace(p.Fch_edicion)}"

    return {
        "id": str(p.ID_pblcn),
        "title": p.Titulo,
        "content": p.Dscrpcn,
        "posted_by": author,
        "edit_info": edit_label, 
        "ui_data": meta,
        "stats": {
            "likes": Like_Post.query.filter_by(ID_pblcn=p.ID_pblcn).count(),
            "comments": Comentario.query.filter_by(ID_pblcn=p.ID_pblcn).count()
        }
    }
@auth_required()
def edit_post(post_id):
    post = Publicacion.query.get_or_404(post_id)
    
    if post.ID_Usr != current_user.id:
        return jsonify({"error": "No tienes permisos"}), 403

    data = request.get_json()
    
    post.Titulo = data.get('title', post.Titulo)
    post.Dscrpcn = data.get('content', post.Dscrpcn)
    if 'ui_data' in data:
        meta = dict(post.Extra_Metadata or {})
        meta.update(data['ui_data'])
        post.Extra_Metadata = meta

    db.session.commit()
    
    return jsonify({
        "mensaje": "Post actualizado",
        "post": format_post_output(post)
    }), 200
