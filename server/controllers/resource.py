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
    """Maneja la asignación de tags al recurso (Relación Muchos a Muchos)."""
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

# --- ENDPOINT: CREAR RECURSO ---
def create_resource():
    data = request.get_json()
    link = data.get('link')
    descripcion = data.get('descripcion')
    tags_recibidos = data.get('tags', [])
    imagenes_recibidas = data.get('images', [])  # Extraemos las URLs de imágenes

    if not link:
        return jsonify({"error": "El link es obligatorio"}), 400

    usuario_id_real = current_user.id
    recurso_id = uuid.uuid4()

    nuevo_recurso = Recurso(
        ID_Rcrs=recurso_id,
        Link=link,
        Dscrpcn=descripcion,
        ID_Usr=usuario_id_real,
        Fch_plcn=datetime.datetime.now(datetime.timezone.utc)
    )

    try:
        db.session.add(nuevo_recurso)
        db.session.flush() # Sincroniza para usar el recurso_id en las imágenes

        # Procesamos etiquetas
        _handle_resource_tags(recurso_id, tags_recibidos)

        # Procesamos y guardamos las imágenes
        for img_url in imagenes_recibidas:
            nueva_imagen = RecursoImg(url=img_url, ID_Rcrs=recurso_id)
            db.session.add(nueva_imagen)

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


# --- ENDPOINT: LISTAR Y FILTRAR RECURSOS ---
def get_paginated_resources():
    page = int(request.args.get('page', 1))
    per_page = 10
    tags_param = request.args.get('tags', '')

    query = Recurso.query

    if tags_param:
        tags_list = [t.strip().lower() for t in tags_param.split(',') if t.strip()]
        if tags_list:
            query = query.join(Recurso_Tag).join(Tag).filter(
                Tag.nombre.in_(tags_list)
            ).distinct()

    query = query.order_by(Recurso.Fch_plcn.desc())

    total = query.count()
    recursos = query.limit(per_page).offset((page - 1) * per_page).all()

    resultado = []
    for r in recursos:
        # 1. Buscamos al usuario usando el ID (mapeado como 'id' en tu clase)
        usuario = User.query.get(r.ID_Usr)

        # 2. Usamos el atributo 'nombre' que es el que tienes definido en el código
        nombre_autor = usuario.nombre if (usuario and usuario.nombre) else "anonymous"

        # 3. Construcción del JSON con la estructura exacta de la imagen
        resultado.append({
            "id": str(r.ID_Rcrs),
            "featured": False,
            "title": r.Dscrpcn or "Untitled",
            "author": f"u/{nombre_autor}",  # Formato u/nombre
            "community": "d/React Hub",  # Formato d/comunidad
            "time": "1h ago",
            "tags": [f"#{t.nombre}" for t in r.tags],
            "rating": None,
            "votes": 87,
            "comments": 15,
            "hasCode": False,
            "refs": [],
            "images": [img.url for img in r.imagenes]
        })

    return jsonify({
        "items": resultado,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": total > (page * per_page)
    }), 200