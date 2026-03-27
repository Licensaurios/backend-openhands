
from flask import (
    Blueprint, jsonify, request
)


from server.controllers.authentication import authorize_user, register_user, login_user
auth_router = Blueprint('auth', __name__, url_prefix='/auth')



@auth_router.route("/login/google")
def google_login():
    #"""
    #Redirect the user to Google OAuth login.

    #:return: A redirect response to Google OAuth.
    #"""
    #return app.google.authorize_redirect(redirect_uri)
    data = authorize_user()

    return jsonify(
        {
            "auth_data": data
        }
    )


@auth_router.route("/")
def auth():
    """
    Handle Google OAuth callback, create user if needed, and log in.

    :return: A redirect response to the index page.
    :raises sqlalchemy.exc.IntegrityError: If database commit fails.
    """

    return jsonify(
        {
            "auth_type": "main"
        }
    )
    #token = app.google.authorize_access_token()

    #user_info = token.get("userinfo")
    #email = user_info.get("email")

    #user = app.user_datastore.find_user(email=email)
    #if not user:
    #    user = app.user_datastore.create_user(
    #        email=email,
    #        password=None,  # OAuth users might not have local passwords
    #        fs_uniquifier=uuid.uuid4().hex,
    #    )
    #    db.session.commit()

    #login_user(user)

    #t = OAuth2Token.query.filter_by(
    #    user_id=user.id,
    #    name="google",
    #).first()
    #if not t:
    #    t = OAuth2Token(
    #        user_id=user.id,
    #        name="google",
    #    )
    #    current_user.tokens.append(t)

    #t.from_token(token)

    #db.session.add(t)
    #try:
    #    db.session.commit()
    #except sqlalchemy.exc.IntegrityError:
    #    log.error("Failed to commit new or updated token...")
    #    db.session.rollback()

    #return redirect(url_for("index"))


@auth_router.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    result = register_user(data)
    return jsonify(result)

@auth_router.route("/login", methods=["POST"]) # <--- Cambiado a POST
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400
        
    result, status_code = login_user(data)
    return jsonify(result), status_code