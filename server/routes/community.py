from flask import Blueprint
from server.controllers.community import (
    create_community,
    get_user_communities, 
    get_community_detail,
    update_community,
    delete_community,
    join_community,
    leave_community,
    search_communities,
    get_community_members,
    get_trending_communities,
    get_membership_status,
    promote_to_moderator,
    kick_member,
    get_community_rules,
    add_community_rule,
    delete_community_rule,
    update_community_rule,
    get_community_post_count,
    get_community_feed,
    get_popular_tags

)

community_router = Blueprint('community', __name__, url_prefix='/api/community')


community_router.route('/my', methods=['GET'])(get_user_communities)

community_router.route('/user/<uuid:user_id>', methods=['GET'])(get_user_communities)

    
# --- CRUD Y BÚSQUEDA ---
community_router.route('/create', methods=['POST'])(create_community)
community_router.route('/search', methods=['GET'])(search_communities)
community_router.route('/trending', methods=['GET'])(get_trending_communities)
community_router.route('/<uuid:comm_id>', methods=['GET'])(get_community_detail)

# --- GESTIÓN DE MEMBRESÍA ---
community_router.route('/join/<uuid:comm_id>', methods=['POST'])(join_community)
community_router.route('/leave/<uuid:comm_id>', methods=['DELETE'])(leave_community)
community_router.route('/<uuid:comm_id>/status', methods=['GET'])(get_membership_status)
community_router.route('/<uuid:comm_id>/members', methods=['GET'])(get_community_members)

# --- EDICIÓN Y BORRADO (COMUNIDAD) ---
community_router.route('/edit/<uuid:comm_id>', methods=['PUT'])(update_community)
community_router.route('/delete/<uuid:comm_id>', methods=['DELETE'])(delete_community)

# --- MODERACIÓN Y JERARQUÍAS ---
community_router.route('/<uuid:comm_id>/promote', methods=['POST'])(promote_to_moderator)
community_router.route('/<uuid:comm_id>/kick', methods=['POST'])(kick_member)

# --- GESTIÓN DE REGLAS ---
community_router.route('/<uuid:comm_id>/rules', methods=['GET'])(get_community_rules)
community_router.route('/<uuid:comm_id>/rules/create', methods=['POST'])(add_community_rule)
community_router.route('/rules/delete/<uuid:regla_id>', methods=['DELETE'])(delete_community_rule)
community_router.route('/rules/edit/<uuid:regla_id>', methods=['PUT'])(update_community_rule)

# --- ESTADÍSTICAS Y FEED ---
community_router.route('/<uuid:comm_id>/posts/count', methods=['GET'])(get_community_post_count)
community_router.route('/<uuid:comm_id>/feed', methods=['GET'])(get_community_feed)

community_router.route('/tags/trending', methods=['GET'])(get_popular_tags)