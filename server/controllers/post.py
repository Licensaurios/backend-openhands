import logging 
import re
from datetime import datetime, timedelta, timezone
from flask import request, jsonify
from flask_security import auth_required, current_user
from sqlalchemy import or_, desc, func

from server.db.community import Usuario_Comunidad, Comunidad, Tag

from server.db.model import db, Publicacion, Post_Tag, Publicacion_Tema, Tema, Like_pblcn, Post_Guardado

from server.db.resource import Recurso

log = logging.getLogger(__name__)
@auth_required()
def my_posts():
    posts = Publicacion.query.filter_by(ID_Usr=current_user.id).order_by(desc(Publicacion.Fch_pblcn)).all()
    return jsonify([format_post_output(p) for p in posts]), 200

def get_user_posts(user_id):
    posts = Publicacion.query.filter_by(ID_Usr=user_id).order_by(desc(Publicacion.Fch_pblcn)).all()
    return jsonify([format_post_output(p) for p in posts]), 200
    
def get_single_post(post_id):
    post = Publicacion.query.get_or_404(post_id)
    return jsonify(format_post_output(post)), 200

def _handle_post_metadata(id_recurso, id_publicacion, tags_list, topics_ids):
    with db.session.no_autoflush:
        for tag_name in (tags_list or []):
            t_clean = re.sub(r'[^a-z0-9]', '', tag_name.lower().strip())
            if not t_clean: continue
            
            tag_obj = Tag.query.filter_by(nombre=t_clean).first()
            if not tag_obj:
                tag_obj = Tag(nombre=t_clean)
                db.session.add(tag_obj)
                db.session.flush()
            
            db.session.add(Post_Tag(ID_Rcrs=id_recurso, id=tag_obj.id))

        for t_id in (topics_ids or []):
            db.session.add(Publicacion_Tema(ID_pblcn=id_publicacion, id_tema=t_id))
@auth_required()
def create_post():
    data = request.get_json() or {}
    
    try:
        nueva_pblcn = Publicacion(
            ID_Usr=current_user.id,
            Titulo=data.get('title', 'Sin título'),
            Dscrpcn=data.get('content', ''),
            ID_cmnd=data.get('community_id'),
            ID_Pryct=data.get('id_pryct'),
            Extra_Metadata=data.get('extra', {}),
            Fch_pblcn=datetime.now(timezone.utc)
        )
        db.session.add(nueva_pblcn)
        db.session.flush() 

        nuevo_recurso = Recurso(
            ID_pblcn=nueva_pblcn.ID_pblcn,
            ID_Usr=current_user.id,
            Link=f"post/{nueva_pblcn.ID_pblcn}",
            Dscrpcn=nueva_pblcn.Dscrpcn,
            Fch_plcn=datetime.now(timezone.utc)
        )
        db.session.add(nuevo_recurso)
        db.session.flush() 

        tags = data.get('tags', [])
        for tag_name in tags:
            t_clean = re.sub(r'[^a-z0-9]', '', tag_name.lower().strip())
            if not t_clean: continue
            
            tag_obj = Tag.query.filter_by(nombre=t_clean).first()
            if not tag_obj:
                tag_obj = Tag(nombre=t_clean)
                db.session.add(tag_obj)
                db.session.flush()
            
            db.session.add(Post_Tag(ID_pblcn=nuevo_recurso.ID_Rcrs, ID_Tag=tag_obj.id))

        topics = data.get('topics', [])
        for t_id in topics:
            db.session.add(Publicacion_Tema(ID_pblcn=nueva_pblcn.ID_pblcn, id_tema=t_id))

        db.session.commit()
        return jsonify({
            "mensaje": "Post creado exitosamente",
            "id_pblcn": str(nueva_pblcn.ID_pblcn)
        }), 201

    except Exception as e:
        db.session.rollback()
        log.error(f"Error en create_post: {str(e)}")
        return jsonify({"error": str(e)}), 500
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
@auth_required()
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
    like = Like_pblcn.query.filter_by(ID_Usr=current_user.id, ID_pblcn=post_id).first()
    
    if like:
        db.session.delete(like)
        db.session.commit()
        return jsonify({"message": "Like eliminado", "status": "unliked"}), 200
    else:
        new_like = Like_pblcn(ID_Usr=current_user.id, ID_pblcn=post_id)
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
    """Convierte el objeto Post a un diccionario con nombres en español para el Front."""
    meta = p.Extra_Metadata or {}
    
    author_obj = p.autor
    raw_name = getattr(author_obj, 'nombre', 'usuario')
    username = raw_name.replace(' ', '').lower()
    
    id_comunidad = getattr(p, 'ID_cmnd', None)
    if id_comunidad and hasattr(p, 'comunidad') and p.comunidad:
        nombre_comunidad = getattr(p.comunidad, 'Name_cmnd', 'comunidad')
        origin_label = f"c/{nombre_comunidad.replace(' ', '').lower()}"
    else:
        origin_label = f"u/{username}"

    is_anon = meta.get('user_removed') or meta.get('is_anonymous')
    author_display = "u/anonimo" if is_anon else f"u/{username}"

    return {
        "id_post": str(p.ID_pblcn),
        "titulo": p.Titulo,
        "contenido": p.Dscrpcn,
        "origen": origin_label,
        "autor_display": author_display,
        "autor_id": str(p.ID_Usr),
        "fecha": p.Fch_pblcn.isoformat() if p.Fch_pblcn else None,
        "stats": {
            "likes": getattr(p, 'total_likes', 0),      
            "comentarios": getattr(p, 'total_comments', 0),
            "karma": getattr(p, 'Votos_Karma', 0)
        },
        "ui_data": meta
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


@auth_required()
def get_all_topics():
    """Retorna todos los temas oficiales (UUID) para el selector de creación."""
    try:
        temas = Tema.query.order_by(Tema.dscrpcn.asc()).all()
        return jsonify([
            {"id": str(t.id_tema), "nombre": t.dscrpcn} 
            for t in temas
        ]), 200
    except Exception as e:
        log.error(f"Error al obtener temas: {e}")
        return jsonify({"error": "No se pudieron cargar los temas"}), 500

@auth_required()
def get_trending_topics():
    hace_48h = datetime.utcnow() - timedelta(days=2)
    
    try:
        # 1. Intentar obtener actividad reciente (48h)
        trending = (
            db.session.query(Tema.dscrpcn, func.count(Publicacion_Tema.ID_pblcn).label('total'))
            .join(Publicacion_Tema)
            .join(Publicacion)
            .filter(Publicacion.Fch_pblcn >= hace_48h)
            .group_by(Tema.dscrpcn)
            .order_by(desc('total'))
            .limit(5).all()
        )

        # 2. Si está vacío, traer los más populares de la historia (Fallback)
        if not trending:
            trending = (
                db.session.query(Tema.dscrpcn, func.count(Publicacion_Tema.ID_pblcn).label('total'))
                .join(Publicacion_Tema)
                .group_by(Tema.dscrpcn)
                .order_by(desc('total'))
                .limit(5).all()
            )
        
        return jsonify([{"topic": t[0], "count": t[1]} for t in trending]), 200

    except Exception as e:
        # Aquí faltaba el import de 'log' o usar 'current_app.logger'
        print(f"Error: {e}") 
        return jsonify([]), 200