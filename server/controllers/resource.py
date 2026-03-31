import uuid
import datetime
import logging
from flask import request, jsonify
from flask_security import current_user
from server.db.model import db, User
from server.db.resource import Recurso, Recurso_Tag, RecursoImg
from server.db.community import Tag

log = logging.getLogger(__name__)


def _handle_resource_tags(recurso_id, tags_list):
    if not tags_list:
        return

    tags_unicos = set([t.lower().strip() for t in tags_list if t])

    for t_name in tags_unicos:
        tag_obj = Tag.query.filter_by(nombre=t_name).first()
        if not tag_obj:
            tag_obj = Tag(nombre=t_name)
            db.session.add(tag_obj)
            db.session.flush()

        relacion = Recurso_Tag(ID_Rcrs=recurso_id, id=tag_obj.id)
        db.session.add(relacion)


def create_resource():
    data = request.get_json()

    link               = data.get('link')
    descripcion        = data.get('descripcion')
    tags_recibidos     = data.get('tags', [])
    imagenes_recibidas = data.get('images', [])
    title              = data.get('title')
    is_markdown        = data.get('markdown', False)
    is_featured        = data.get('featured', False)
    rating             = data.get('rating', None)
    votes              = data.get('votes', 0)
    has_code           = data.get('hasCode', False)
    refs               = data.get('refs', [])
    code_lines         = data.get('codeLines', [])
    code_lang          = data.get('codeLang', None)

    if not link:
        return jsonify({"error": "El link es obligatorio"}), 400

    usuario_id_real = current_user.id
    recurso_id = uuid.uuid4()

    nuevo_recurso = Recurso(
        ID_Rcrs   = recurso_id,
        Link      = link,
        Dscrpcn   = descripcion,
        title     = title,
        markdown  = is_markdown,
        ID_Usr    = usuario_id_real,
        Fch_plcn  = datetime.datetime.now(datetime.timezone.utc),
        featured  = is_featured,
        rating    = rating,
        votes     = votes,
        hascode   = has_code,
        refs      = refs,
        codelines = code_lines,
        codelang  = code_lang,
    )

    try:
        db.session.add(nuevo_recurso)
        db.session.flush()

        _handle_resource_tags(recurso_id, tags_recibidos)

        for img_url in imagenes_recibidas:
            db.session.add(RecursoImg(url=img_url, ID_Rcrs=recurso_id))

        db.session.commit()

        return jsonify({
            "msg": "Recurso creado exitosamente",
            "id": str(recurso_id),
            "usuario_asignado": str(usuario_id_real)
        }), 201

    except Exception as e:
        db.session.rollback()
        log.error(f"Error al crear recurso: {e}")
        return jsonify({"error": f"Error interno en base de datos: {str(e)}"}), 500


def vote_resource(recurso_id):
    data      = request.get_json()
    value     = data.get('value')  # Solo acepta 1 o -1

    if value not in (1, -1):
        return jsonify({"error": "El valor debe ser 1 o -1"}), 400

    recurso = Recurso.query.get(recurso_id)
    if not recurso:
        return jsonify({"error": "Recurso no encontrado"}), 404

    recurso.votes = (recurso.votes or 0) + value

    try:
        db.session.commit()
        return jsonify({
            "msg": "Voto registrado",
            "votes": recurso.votes
        }), 200
    except Exception as e:
        db.session.rollback()
        log.error(f"Error al votar: {e}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

def get_paginated_resources():
    page       = int(request.args.get('page', 1))
    per_page   = 10
    tags_param = request.args.get('tags', '')
    query      = Recurso.query

    if tags_param:
        tags_list = [t.strip().lower() for t in tags_param.split(',') if t.strip()]
        if tags_list:
            query = query.join(Recurso_Tag).join(Tag).filter(
                Tag.nombre.in_(tags_list)
            ).distinct()

    query    = query.order_by(Recurso.Fch_plcn.desc())
    total    = query.count()
    recursos = query.limit(per_page).offset((page - 1) * per_page).all()

    resultado = []
    for r in recursos:
        usuario      = User.query.get(r.ID_Usr)
        nombre_autor = usuario.nombre if (usuario and usuario.nombre) else "anonymous"

        resultado.append({
            "id":        str(r.ID_Rcrs),
            "featured":  r.featured  or False,
            "title":     r.title or r.Dscrpcn or "Untitled",
            "author":    f"u/{nombre_autor}",
            "community": "d/React Hub",
            "time":      "1h ago",
            "tags":      [f"#{t.nombre}" for t in r.tags],
            "rating":    r.rating,
            "votes":     r.votes     or 0,
            "hasCode":   r.hascode   or False,
            "codeLines": r.codelines or [],
            "codeLang":  r.codelang,
            "markdown":  r.markdown,
            "refs":      r.refs      or [],
            "images":    [img.url for img in r.imagenes],
        })

    return jsonify({
        "items":    resultado,
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "has_more": total > (page * per_page)
    }), 200