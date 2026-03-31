from flask import Blueprint
from server.controllers.post import (
    create_post, edit_post, delete_post, 
    my_posts, get_user_posts, user_feed,
    toggle_like, toggle_save
)
from server.controllers.comment import (
    add_comment, get_post_comments, delete_comment
)

post_router = Blueprint('post', __name__, url_prefix='/api/post')

post_router.route('/create', methods=['POST'])(create_post)
post_router.route('/feed', methods=['GET'])(user_feed)
post_router.route('/my', methods=['GET'])(my_posts)
post_router.route('/user/<uuid:user_id>', methods=['GET'])(get_user_posts)

post_router.route('/edit/<uuid:post_id>', methods=['PUT'])(edit_post)
post_router.route('/delete/<uuid:post_id>', methods=['DELETE'])(delete_post)
post_router.route('/like/<uuid:post_id>', methods=['POST'])(toggle_like)
post_router.route('/save/<uuid:post_id>', methods=['POST'])(toggle_save)

post_router.route('/<uuid:post_id>/comment', methods=['POST'])(add_comment)
post_router.route('/<uuid:post_id>/comments', methods=['GET'])(get_post_comments)
post_router.route('/comment/delete/<uuid:comment_id>', methods=['DELETE'])(delete_comment)