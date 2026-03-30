import datetime
import uuid
import logging
import re 
from flask import request, jsonify
from flask_security import current_user, auth_required
from sqlalchemy import or_, func
from server.db.model import db 
from server.db.community import Comunidad, Chat, Usuario_Comunidad, Tag, Comunidad_Tag

log = logging.getLogger(__name__)

def _handle_community_tags(comm_id, tags_list):
    """Maneja etiquetas permitiendo ÚNICAMENTE letras y números."""
    Comunidad_Tag.query.filter_by(ID_cmnd=comm_id).delete()
    
    if not tags_list:
        return

    tags_unicos = set([t.lower().strip() for t in tags_list if t])

    for t_name in tags_unicos:
        t_name = re.sub(r'[^a-z0-9]', '', t_name)
        if not t_name: 
            continue
        
        tag_obj = Tag.query.filter_by(nombre=t_name).first()
        if not tag_obj:
            tag_obj = Tag(nombre=t_name)
            db.session.add(tag_obj)
            db.session.flush() 
            
        relacion = Comunidad_Tag(ID_cmnd=comm_id, ID_Tag=tag_obj.id)
        db.session.add(relacion)


# --- CREAR COMUNIDAD ---
@auth_required()
def create_community():
    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    pfp_url = data.get('pfp_url')    
    banner_url = data.get('banner_url') 
    tags_recibidos = data.get('tags', [])

    if not nombre:
        return jsonify({"error": "El nombre es obligatorio"}), 400

    comm_id = uuid.uuid4()
    nueva_comunidad = Comunidad(
        iD_cmnd=comm_id,
        Name_cmnd=nombre,
        Dscrpcn=descripcion, 
        ID_Admin=current_user.id,
        pfp_cmnd=pfp_url,
        banner_cmnd=banner_url,
        active=True, 
        Fch_crcn=datetime.datetime.now(datetime.timezone.utc)
    )

    try:
        db.session.add(nueva_comunidad)
        _handle_community_tags(comm_id, tags_recibidos)
        db.session.add(Chat(ID_Chat=uuid.uuid4(), iD_cmnd=comm_id))
        db.session.add(Usuario_Comunidad(
            ID_Usr=current_user.id, 
            ID_cmnd=comm_id, 
            Fch_ingreso=datetime.datetime.now(datetime.timezone.utc)
        ))

        db.session.commit()
        return jsonify({"msg": "Comunidad creada exitosamente", "id": str(comm_id)}), 201

    except Exception as e:
        db.session.rollback()
        log.error(f"Error en creación: {e}")
        return jsonify({"error": "Error interno"}), 500


# --- MIS COMUNIDADES ---
@auth_required()
def get_my_communities():
    try:
        mis_comunidades = (
            db.session.query(Comunidad)
            .join(Usuario_Comunidad, Comunidad.iD_cmnd == Usuario_Comunidad.ID_cmnd)
            .filter(Usuario_Comunidad.ID_Usr == current_user.id)
            .filter(Comunidad.active == True)  
            .all()
        )
    
        resultado = []
        for c in mis_comunidades:
            resultado.append({
                "id_comunidad": str(c.iD_cmnd),
                "nombre": c.Name_cmnd,
                "descripcion": c.Dscrpcn,
                "pfp_url": c.pfp_cmnd,
                "banner_url": c.banner_cmnd,
                "tags": [t.nombre for t in c.tags],
                "es_admin": str(c.ID_Admin) == str(current_user.id),
                "fecha_creacion": c.Fch_crcn.strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify(resultado), 200

    except Exception as e:
        log.error(f"Error al listar comunidades: {e}")
        return jsonify({"error": "No se pudieron obtener las comunidades"}), 500


# --- OBTENER DETALLE ---
@auth_required()
def get_community_detail(comm_id):
    comunidad = Comunidad.query.get_or_404(comm_id)
    return jsonify({
        "id": str(comunidad.iD_cmnd),
        "nombre": comunidad.Name_cmnd,
        "descripcion": comunidad.Dscrpcn,
        "pfp": comunidad.pfp_cmnd,
        "banner": comunidad.banner_cmnd,
        "tags": [t.nombre for t in comunidad.tags],
        "admin": str(comunidad.ID_Admin)
    }), 200


# --- EDITAR COMUNIDAD ---
@auth_required()
def update_community(comm_id):
    comunidad = Comunidad.query.get_or_404(comm_id)
    if str(comunidad.ID_Admin) != str(current_user.id):
        return jsonify({"error": "No tienes permisos"}), 403
        
    data = request.get_json()
    comunidad.Name_cmnd = data.get('nombre', comunidad.Name_cmnd)
    comunidad.Dscrpcn = data.get('descripcion', comunidad.Dscrpcn)
    comunidad.pfp_cmnd = data.get('pfp_url', comunidad.pfp_cmnd)
    comunidad.banner_cmnd = data.get('banner_url', comunidad.banner_cmnd)
    
    if 'tags' in data:
        _handle_community_tags(comunidad.iD_cmnd, data.get('tags'))
    
    db.session.commit()
    return jsonify({"msg": "Comunidad actualizada"}), 200


# --- "ELIMINAR" (DESHABILITAR) COMUNIDAD ---
@auth_required()
def delete_community(comm_id):
    try:
        comunidad = Comunidad.query.get_or_404(comm_id)
        
        if str(comunidad.ID_Admin) != str(current_user.id):
            return jsonify({"error": "No tienes permisos para deshabilitar esta comunidad"}), 403
        comunidad.active = False 
        
        db.session.commit()
        return jsonify({
            "msg": "Comunidad deshabilitada correctamente",
            "id": str(comm_id),
            "status": "inactive"
        }), 200

    except Exception as e:
        db.session.rollback()
        log.error(f"Error al deshabilitar: {e}")
        return jsonify({"error": "Error interno al procesar la solicitud"}), 500


# --- UNIRSE A COMUNIDAD ---
@auth_required()
def join_community(comm_id):
    comunidad = Comunidad.query.get_or_404(comm_id)
    if not comunidad.active:
        return jsonify({"error": "Esta comunidad ya no está disponible"}), 400

    existente = Usuario_Comunidad.query.filter_by(
        ID_Usr=current_user.id, 
        ID_cmnd=comm_id
    ).first()
    
    if existente:
        return jsonify({"msg": "Ya eres miembro de esta comunidad"}), 200

    nuevo_miembro = Usuario_Comunidad(
        ID_Usr=current_user.id,
        ID_cmnd=comm_id,
        Fch_ingreso=datetime.datetime.now(datetime.timezone.utc)
    )

    try:
        db.session.add(nuevo_miembro)
        db.session.commit()
        return jsonify({"msg": "Te has unido a la comunidad con éxito"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al unirse"}), 500


# --- SALIR DE COMUNIDAD ---
@auth_required()
def leave_community(comm_id):
    miembro = Usuario_Comunidad.query.filter_by(
        ID_Usr=current_user.id, 
        ID_cmnd=comm_id
    ).first()

    if not miembro:
        return jsonify({"error": "No eres miembro de esta comunidad"}), 404

    try:
        db.session.delete(miembro)
        db.session.commit()
        return jsonify({"msg": "Has salido de la comunidad"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al procesar la salida"}), 500


# --- BUSCADOR ---
@auth_required()
def search_communities():
    search_query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    per_page = 10 

    stmt = Comunidad.query.filter(Comunidad.active == True)

    if search_query:
        formatted_query = f'%{search_query}%'
        stmt = stmt.join(Comunidad_Tag, isouter=True).join(Tag, isouter=True).filter(
            or_(
                Comunidad.Name_cmnd.ilike(formatted_query),
                Tag.nombre.ilike(formatted_query)
            )
        ).distinct()

    total = stmt.count()
    comunidades = stmt.limit(per_page).offset((page - 1) * per_page).all()

    resultado = []
    for c in comunidades:
        total_miembros = Usuario_Comunidad.query.filter_by(ID_cmnd=c.iD_cmnd).count()
        resultado.append({
            "id": str(c.iD_cmnd),
            "nombre": c.Name_cmnd,
            "descripcion": c.Dscrpcn,
            "tags": [t.nombre for t in c.tags],
            "pfp": c.pfp_cmnd,
            "miembros": total_miembros
        })

    return jsonify({
        "items": resultado,
        "total": total,
        "page": page,
        "has_more": total > (page * per_page)
    }), 200


# --- OBTENER LISTA DE MIEMBROS ---
@auth_required()
def get_community_members(comm_id):
    try:
        comunidad = Comunidad.query.get_or_404(comm_id)
        
        es_miembro = Usuario_Comunidad.query.filter_by(
            ID_Usr=current_user.id, 
            ID_cmnd=comm_id
        ).first()

        if not es_miembro:
            return jsonify({
                "error": "Acceso denegado", 
                "msg": "Debes unirte a la comunidad para ver la lista de miembros."
            }), 403 

        miembros_relacion = Usuario_Comunidad.query.filter_by(ID_cmnd=comm_id).all()
        
        resultado = []
        for m in miembros_relacion:
            resultado.append({
                "id_usuario": str(m.ID_Usr),
                "fecha_ingreso": m.Fch_ingreso.strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify({
            "comunidad": comunidad.Name_cmnd,
            "total_miembros": len(resultado),
            "miembros": resultado
        }), 200

    except Exception as e:
        log.error(f"Error de seguridad en miembros: {e}")
        return jsonify({"error": "Error interno"}), 500


# --- COMUNIDADES TRENDING ---
@auth_required()
def get_trending_communities():
    try:
        query_popular = (
            db.session.query(
                Comunidad, 
                func.count(Usuario_Comunidad.ID_Usr).label('total_miembros')
            )
            .join(Usuario_Comunidad, Comunidad.iD_cmnd == Usuario_Comunidad.ID_cmnd)
            .filter(Comunidad.active == True)
            .group_by(Comunidad.iD_cmnd)
            .order_by(func.count(Usuario_Comunidad.ID_Usr).desc())
            .limit(5)
            .all()
        )
        
        resultado = []
        for comunidad_obj, conteo in query_popular:
            resultado.append({
                "id": str(comunidad_obj.iD_cmnd),
                "nombre": comunidad_obj.Name_cmnd,
                "descripcion": comunidad_obj.Dscrpcn,
                "pfp": comunidad_obj.pfp_cmnd,
                "miembros": conteo,
                "tags": [t.nombre for t in comunidad_obj.tags]
            })
            
        return jsonify(resultado), 200
    except Exception as e:
        log.error(f"Error en ranking de comunidades: {e}")
        return jsonify({"error": "No se pudo generar el ranking"}), 500


# --- ESTADO DE MEMBRESÍA ---
@auth_required()
def get_membership_status(comm_id):
    try:
        membresia = Usuario_Comunidad.query.filter_by(
            ID_Usr=current_user.id, 
            ID_cmnd=comm_id
        ).first()
        
        if not membresia:
            return jsonify({"is_member": False, "role": None}), 200
            
        comunidad = Comunidad.query.get(comm_id)
        es_admin = str(comunidad.ID_Admin) == str(current_user.id)
        
        return jsonify({
            "is_member": True,
            "role": "admin" if es_admin else "member",
            "fecha_ingreso": membresia.Fch_ingreso.strftime('%Y-%m-%d')
        }), 200
    except Exception as e:
        log.error(f"Error en status: {e}")
        return jsonify({"error": str(e)}), 500