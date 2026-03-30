from flask import Blueprint
from server.controllers.community import (
        create_community,
        get_my_communities,
        get_community_detail,
        update_community,
        delete_community,
        join_community,
        leave_community,
        search_communities,
        get_community_members,
        get_trending_communities,
        get_membership_status      
)

community_router = Blueprint('community', __name__, url_prefix='/api/community')

# CRUD y Búsqueda
community_router.route('/create', methods=['POST'])(create_community)
community_router.route('/my', methods=['GET'])(get_my_communities)
community_router.route('/search', methods=['GET'])(search_communities)
community_router.route('/trending', methods=['GET'])(get_trending_communities)
community_router.route('/<uuid:comm_id>', methods=['GET'])(get_community_detail)

# Gestión de Membresía
community_router.route('/join/<uuid:comm_id>', methods=['POST'])(join_community)
community_router.route('/leave/<uuid:comm_id>', methods=['DELETE'])(leave_community)
community_router.route('/<uuid:comm_id>/status', methods=['GET'])(get_membership_status)
community_router.route('/<uuid:comm_id>/members', methods=['GET'])(get_community_members)

# Edición y Borrado
community_router.route('/edit/<uuid:comm_id>', methods=['PUT'])(update_community)
community_router.route('/delete/<uuid:comm_id>', methods=['DELETE'])(delete_community)