import uuid
import datetime
import logging
from flask import request, jsonify
from flask_security import current_user
from server.db.model import db
from server.db.resource import Recurso, Recurso_Tag
from server.db.community import Tag

log = logging.getLogger(__name__)


def _handle_resource_tags(recurso_id, tags_list):
    """Maneja la asignación de tags al recurso (Relación Muchos a Muchos)."""
    if not tags_list:
        return

    # Usamos set para evitar duplicados y normalizamos a minúsculas
    tags_unicos = set([t.lower().strip() for t in tags_list if t])

    for t_name in tags_unicos:
        # 1. Buscamos si el tag ya existe
        tag_obj = Tag.query.filter_by(nombre=t_name).first()

        # 2. Si no existe, lo creamos
        if not tag_obj:
            tag_obj = Tag(nombre=t_name)
            db.session.add(tag_obj)
            db.session.flush()  # Sincroniza para obtener el ID del nuevo Tag

        # 3. Creamos la relación en la tabla puente (Recurso_Tag)
        relacion = Recurso_Tag(ID_Rcrs=recurso_id, id=tag_obj.id)
        db.session.add(relacion)


# --- ENDPOINT: CREAR RECURSO (SIN TOKEN) ---
def create_resource():
    data = request.get_json()
    link = data.get('link')
    descripcion = data.get('descripcion')
    tags_recibidos = data.get('tags', [])

    if not link:
        return jsonify({"error": "El link es obligatorio"}), 400

    # 1. Obtenemos dinámicamente el ID del usuario que inició sesión
    usuario_id_real = current_user.id

    recurso_id = str(uuid.uuid4())  # Generamos el ID único del recurso

    nuevo_recurso = Recurso(
        ID_Rcrs=recurso_id,
        Link=link,
        Dscrpcn=descripcion,
        ID_Usr=usuario_id_real,  # <--- 2. Asignamos el recurso a ese usuario
        Fch_plcn=datetime.datetime.now(datetime.timezone.utc)
    )

    try:
        db.session.add(nuevo_recurso)

        # Procesamos las etiquetas usando la función auxiliar
        _handle_resource_tags(recurso_id, tags_recibidos)

        db.session.commit()

        # 3. Mensaje de éxito limpio
        return jsonify({
            "msg": "Recurso creado exitosamente",
            "id": recurso_id,
            "usuario_asignado": usuario_id_real
        }), 201

    except Exception as e:
        db.session.rollback()
        log.error(f"Error al crear recurso: {e}")
        return jsonify({"error": f"Error interno en Supabase: {str(e)}"}), 500


# --- ENDPOINT: LISTAR Y FILTRAR RECURSOS ---
def get_paginated_resources():
    page = int(request.args.get('page', 1))
    per_page = 10
    tags_param = request.args.get('tags', '')  # Captura ?tags=python,flask

    query = Recurso.query

    # Filtrado por etiquetas
    if tags_param:
        tags_list = [t.strip().lower() for t in tags_param.split(',') if t.strip()]
        if tags_list:
            # Unimos las tablas para filtrar por el nombre del Tag
            query = query.join(Recurso_Tag).join(Tag).filter(
                Tag.nombre.in_(tags_list)
            ).distinct()

            # Ordenamos por fecha de publicación (más recientes primero)
    query = query.order_by(Recurso.Fch_plcn.desc())

    # Paginación manual o usando .paginate()
    total = query.count()
    recursos = query.limit(per_page).offset((page - 1) * per_page).all()

    resultado = []
    for r in recursos:
        resultado.append({
            "id": str(r.ID_Rcrs),
            "link": r.Link,
            "descripcion": r.Dscrpcn,
            "fecha_creacion": r.Fch_plcn.isoformat(),
            "tags": [t.nombre for t in r.tags]  # Asumiendo relación 'tags' en el modelo
        })

    return jsonify({
        "items": resultado,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": total > (page * per_page)
    }), 200