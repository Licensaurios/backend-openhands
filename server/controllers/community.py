import datetime
import uuid
import logging
import re 
from flask import request, jsonify
from flask_security import current_user, auth_required
from sqlalchemy import or_, func
from server.db.model import db 
from sqlalchemy.orm import joinedload
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
        ID_Admin=current_user.id, # Sigue siendo el Admin principal
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
            Rol='fundador',    
            Is_Active=True,     
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
            .filter(Usuario_Comunidad.Is_Active == True) # <--- Solo activos
            .filter(Comunidad.active == True)  
            .all()
        )
    
        resultado = []
        for c in mis_comunidades:
            membresia = next((m for m in c.miembros if str(m.ID_Usr) == str(current_user.id)), None)
            
            resultado.append({
                "id_comunidad": str(c.iD_cmnd),
                "nombre": c.Name_cmnd,
                "descripcion": c.Dscrpcn,
                "pfp_url": c.pfp_cmnd,
                "banner_url": c.banner_cmnd,
                "tags": [t.nombre for t in c.tags],
                "rol": membresia.Rol if membresia else "miembro",
                "es_admin": str(c.ID_Admin) == str(current_user.id),
                "fecha_creacion": c.Fch_crcn.strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify(resultado), 200
    except Exception as e:
        log.error(f"Error al listar comunidades: {e}")
        return jsonify({"error": "Error al obtener comunidades"}), 500

# --- OBTENER INFORMACIÓN COMPLETA DE LA COMUNIDAD ---
@auth_required()
def get_community_detail(comm_id):
    try:
        comunidad = Comunidad.query.get_or_404(comm_id)
        from server.db.community import Regla_Comunidad # Importa si es necesario
        reglas_raw = Regla_Comunidad.query.filter_by(ID_cmnd=comm_id).order_by(Regla_Comunidad.Orden).all()
        miembros_activos = Usuario_Comunidad.query.filter_by(
            ID_cmnd=comm_id, 
            Is_Active=True
        ).all()

        fundador = None
        moderadores = []
        conteo_miembros = 0

        for m in miembros_activos:
            conteo_miembros += 1
            user_info = {"id_user": str(m.ID_Usr), "fecha_unido": m.Fch_ingreso.strftime('%Y-%m-%d')}
            
            if m.Rol == 'fundador':
                fundador = user_info
            elif m.Rol == 'moderador':
                moderadores.append(user_info)

        return jsonify({
            "comunidad": {
                "id": str(comunidad.iD_cmnd),
                "nombre": comunidad.Name_cmnd,
                "descripcion": comunidad.Dscrpcn,
                "pfp": comunidad.pfp_cmnd,
                "banner": comunidad.banner_cmnd,
                "fecha_creacion": comunidad.Fch_crcn.strftime('%Y-%m-%d'),
                "id_admin_principal": str(comunidad.ID_Admin), # Sincronizado con fundador
                "estado_activa": comunidad.active
            },
            "administracion": {
                "fundador": fundador,
                "moderadores": moderadores,
                "total_miembros": conteo_miembros,
                "limite_mods": 4 # Dato informativo para el front
            },
            "reglas": [
                {
                    "nombre": r.Nombre_Regla,
                    "descripcion": r.Dscrpcn,
                    "orden": r.Orden
                } for r in reglas_raw
            ],
            "tags": [t.nombre for t in comunidad.tags]
        }), 200

    except Exception as e:
        log.error(f"Error al obtener info de comunidad {comm_id}: {e}")
        return jsonify({"error": "No se pudo cargar la información de la comunidad"}), 500


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
        if existente.Is_Active:
            return jsonify({"msg": "Ya eres miembro activo de esta comunidad"}), 200
        else:
            existente.Is_Active = True
            existente.Rol = 'miembro' 
            existente.Fch_ingreso = datetime.datetime.now(datetime.timezone.utc)
            db.session.commit()
            return jsonify({"msg": "Has reingresado a la comunidad"}), 200

    nuevo_miembro = Usuario_Comunidad(
        ID_Usr=current_user.id,
        ID_cmnd=comm_id,
        Rol='miembro',
        Is_Active=True,
        Fch_ingreso=datetime.datetime.now(datetime.timezone.utc)
    )

    try:
        db.session.add(nuevo_miembro)
        db.session.commit()
        return jsonify({"msg": "Te has unido a la comunidad con éxito"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al unirse"}), 500

# cambiar de false a true
# --- SALIR DE COMUNIDAD ---
@auth_required()
def leave_community(comm_id):
    data = request.get_json() or {}
    successor_id = data.get('successor_id')

    miembro = Usuario_Comunidad.query.filter_by(
        ID_Usr=current_user.id, 
        ID_cmnd=comm_id,
        Is_Active=True 
    ).first()

    if not miembro:
        return jsonify({"error": "No eres miembro activo"}), 404

    try:
        if miembro.Rol == 'fundador':
            if not successor_id:
                return jsonify({
                    "error": "TRANSFER_REQUIRED",
                    "msg": "Debes asignar a un sucesor antes de salir."
                }), 400
            
            nuevo_jefe = Usuario_Comunidad.query.filter_by(
                ID_Usr=successor_id, ID_cmnd=comm_id, Is_Active=True
            ).first()

            if not nuevo_jefe:
                return jsonify({"error": "Sucesor inválido"}), 404
            nuevo_jefe.Rol = 'fundador'
            comunidad = Comunidad.query.get(comm_id)
            if comunidad:
                comunidad.ID_Admin = successor_id

        miembro.Is_Active = False
        db.session.commit()
        return jsonify({"msg": "Salida procesada correctamente"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al procesar salida"}), 500

# --- BUSCADOR ---
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
    comunidades = stmt.options(joinedload(Comunidad.tags))\
                  .limit(per_page)\
                  .offset((page - 1) * per_page).all()
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
        miembros_relacion = Usuario_Comunidad.query.filter_by(ID_cmnd=comm_id,Is_Active=True).all()
        
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


@auth_required()
def get_membership_status(comm_id):
    try:
        membresia = Usuario_Comunidad.query.filter_by(
            ID_Usr=current_user.id, 
            ID_cmnd=comm_id,
            Is_Active=True # Importante: Solo si es activo
        ).first()
        
        if not membresia:
            return jsonify({"is_member": False, "role": None}), 200
            
        return jsonify({
            "is_member": True,
            "role": membresia.Rol, # 'fundador', 'moderador' o 'miembro'
            "fecha_ingreso": membresia.Fch_ingreso.strftime('%Y-%m-%d')
        }), 200
    except Exception as e:
        log.error(f"Error en status: {e}")
        return jsonify({"error": "Error al consultar estado"}), 500



# --- PROMOVER A MODERADOR ---
@auth_required()
def promote_to_moderator(comm_id):
    data = request.get_json()
    target_user_id = data.get('target_user_id')

    if not target_user_id:
        return jsonify({"error": "Se requiere el ID del usuario a promover"}), 400

    try:
      
        # (Solo el fundador puede nombrar moderadores)
        quien_promueve = Usuario_Comunidad.query.filter_by(
            ID_Usr=current_user.id, 
            ID_cmnd=comm_id,
            Is_Active=True
        ).first()

        if not quien_promueve or quien_promueve.Rol != 'fundador':
            return jsonify({"error": "No tienes permisos. Solo el fundador puede promover miembros."}), 403

        conteo_mods = Usuario_Comunidad.query.filter_by(
            ID_cmnd=comm_id,
            Rol='moderador',
            Is_Active=True
        ).count()

        if conteo_mods >= 4:
            return jsonify({
                "error": "LIMIT_REACHED",
                "msg": "Esta comunidad ya tiene el máximo de 4 moderadores."
            }), 400

      
        miembro_objetivo = Usuario_Comunidad.query.filter_by(
            ID_Usr=target_user_id,
            ID_cmnd=comm_id,
            Is_Active=True
        ).first()

        if not miembro_objetivo:
            return jsonify({"error": "El usuario no es miembro activo de esta comunidad"}), 404

        if miembro_objetivo.Rol == 'moderador':
            return jsonify({"msg": "El usuario ya es moderador"}), 200

        miembro_objetivo.Rol = 'moderador'
        db.session.commit()

        log.info(f"Usuario {target_user_id} promovido a Moderador en {comm_id} por {current_user.id}")
        return jsonify({
            "msg": "Usuario promovido exitosamente",
            "nuevo_rol": "moderador",
            "mods_actuales": conteo_mods + 1
        }), 200

    except Exception as e:
        db.session.rollback()
        log.error(f"Error en promoción: {e}")
        return jsonify({"error": "Error interno al procesar el ascenso"}), 500


# --- EXPULSAR MIEMBRO (KICK) ---
@auth_required()
def kick_member(comm_id):
    data = request.get_json()
    target_user_id = data.get('target_user_id')

    if not target_user_id:
        return jsonify({"error": "ID de usuario requerido"}), 400

    try:
        
        ejecutor = Usuario_Comunidad.query.filter_by(
            ID_Usr=current_user.id, 
            ID_cmnd=comm_id,
            Is_Active=True
        ).first()

        if not ejecutor or ejecutor.Rol not in ['fundador', 'moderador']:
            return jsonify({"error": "No tienes permisos de moderación"}), 403

        objetivo = Usuario_Comunidad.query.filter_by(
            ID_Usr=target_user_id,
            ID_cmnd=comm_id,
            Is_Active=True
        ).first()

        if not objetivo:
            return jsonify({"error": "El usuario no es miembro activo"}), 404

        if objetivo.Rol == 'fundador':
            return jsonify({"error": "No puedes expulsar al fundador de la comunidad"}), 403

        objetivo.Is_Active = False
        db.session.commit()

        return jsonify({"msg": f"Usuario {target_user_id} ha sido expulsado"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# --- AÑADIR REGLA A LA COMUNIDAD ---
@auth_required()
def add_community_rule(comm_id):
    data = request.get_json()
    nombre_regla = data.get('nombre')
    descripcion = data.get('descripcion')

    if not nombre_regla:
        return jsonify({"error": "El nombre de la regla es obligatorio"}), 400

    try:
        autor = Usuario_Comunidad.query.filter_by(
            ID_Usr=current_user.id, ID_cmnd=comm_id, Is_Active=True
        ).first()

        if not autor or autor.Rol not in ['fundador', 'moderador']:
            return jsonify({"error": "No tienes permisos para gestionar reglas"}), 403

        conteo_reglas = Regla_Comunidad.query.filter_by(ID_cmnd=comm_id).count()
        if conteo_reglas >= 10:
            return jsonify({
                "error": "LIMIT_REACHED",
                "msg": "Has alcanzado el máximo de 10 reglas por comunidad."
            }), 400

       
        nueva_regla = Regla_Comunidad(
            ID_cmnd=comm_id,
            Nombre_Regla=nombre_regla,
            Dscrpcn=descripcion,
            Orden=conteo_reglas + 1 # Se asigna el siguiente número
        )

        db.session.add(nueva_regla)
        db.session.commit()

        return jsonify({"msg": "Regla añadida con éxito", "orden": nueva_regla.Orden}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# --- ELIMINAR REGLA ---
@auth_required()
def delete_community_rule(regla_id):
    try:
        regla = Regla_Comunidad.query.get_or_404(regla_id)
        
        autor = Usuario_Comunidad.query.filter_by(
            ID_Usr=current_user.id, ID_cmnd=regla.ID_cmnd, Is_Active=True
        ).first()

        if not autor or autor.Rol not in ['fundador', 'moderador']:
            return jsonify({"error": "Sin permisos para eliminar"}), 403

        db.session.delete(regla)
        db.session.commit()
        return jsonify({"msg": "Regla eliminada exitosamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
        
@auth_required()
def get_community_rules(comm_id):
    try:
        reglas = Regla_Comunidad.query.filter_by(ID_cmnd=comm_id).order_by(Regla_Comunidad.Orden).all()
        return jsonify([
            {
                "id_regla": str(r.ID_Regla),
                "nombre": r.Nombre_Regla,
                "descripcion": r.Dscrpcn,
                "orden": r.Orden
            } for r in reglas
        ]), 200
    except Exception as e:
        return jsonify({"error": "Error al obtener reglas"}), 500

# --- EDITAR REGLA ---
@auth_required()
def update_community_rule(regla_id):
    data = request.get_json()
    nuevo_nombre = data.get('nombre')
    nueva_dscrpcn = data.get('descripcion')

    try:
        regla = Regla_Comunidad.query.get_or_404(regla_id)
        
        autor = Usuario_Comunidad.query.filter_by(
            ID_Usr=current_user.id, 
            ID_cmnd=regla.ID_cmnd, 
            Is_Active=True
        ).first()

        if not autor or autor.Rol not in ['fundador', 'moderador']:
            return jsonify({"error": "No tienes permisos para editar reglas"}), 403

        if nuevo_nombre:
            regla.Nombre_Regla = nuevo_nombre
        if nueva_dscrpcn:
            regla.Dscrpcn = nueva_dscrpcn
            
        db.session.commit()
        
        return jsonify({
            "msg": "Regla actualizada con éxito",
            "regla": {
                "id": str(regla.ID_Regla),
                "nombre": regla.Nombre_Regla,
                "descripcion": regla.Dscrpcn
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar: {str(e)}"}), 500



#
# --- OBTENER CONTEO DE POSTS ---
@auth_required()
def get_community_post_count(comm_id):
    try:
        from server.db.community import Publicacion 

        total_posts = Publicacion.query.filter_by(
            ID_cmnd=comm_id,
            active=True # Solo contamos los que no han sido borrados
        ).count()

        return jsonify({
            "id_comunidad": str(comm_id),
            "total_posts": total_posts
        }), 200

    except Exception as e:
        log.error(f"Error al contar posts: {e}")
        return jsonify({"error": "No se pudo obtener el conteo de publicaciones"}), 500
#

@auth_required()
def get_community_feed(comm_id):
    try:
        publicaciones = Publicacion.query.filter_by(
            ID_cmnd=comm_id,
            active=True
        ).order_by(Publicacion.Fch_pblcn.desc()).all()

        feed = []
        for p in publicaciones:
            num_likes = p.likes.count()
            
            user_liked = Like_Post.query.filter_by(
                ID_Usr=current_user.id, 
                ID_pblcn=p.ID_pblcn
            ).first() is not None

            user_saved = Post_Guardado.query.filter_by(
                ID_Usr=current_user.id, 
                ID_pblcn=p.ID_pblcn
            ).first() is not None

            feed.append({
                "id_post": str(p.ID_pblcn),
                "titulo": p.Titulo,
                "contenido": p.Dscrpcn,
                "fecha": p.Fch_pblcn.isoformat(),
                "autor_id": str(p.ID_Usr),
                "stats": {
                    "likes": num_likes,
                    "karma": p.Votos_Karma
                },
                "interaccion_usuario": {
                    "liked": user_liked,
                    "saved": user_saved
                }
            })

        return jsonify(feed), 200

    except Exception as e:
        return jsonify({"error": f"Error al cargar el feed: {str(e)}"}), 500
