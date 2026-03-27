import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_security import RoleMixin, UserMixin
from sqlalchemy.dialects.postgresql import UUID

db = SQLAlchemy()

roles_users = db.Table(
    "roles_users",
    db.Column("user_id", UUID(as_uuid=True), db.ForeignKey("public.user.ID_Usr")),
    db.Column("role_id", db.Integer(), db.ForeignKey("public.role.id")),
    schema="public"
)

class Role(db.Model, RoleMixin):
    __tablename__ = "role"
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    __tablename__ = "user"
    __table_args__ = {"schema": "public"}

    id = db.Column("ID_Usr", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = db.Column("Nombre", db.String(), nullable=False)
    apellido1 = db.Column("Ap_1", db.String(), nullable=False)
    apellido2 = db.Column("Ap_2", db.String(), nullable=True)
    email = db.Column("Correo", db.String(), unique=True, nullable=False)
    password = db.Column("Psswrd", db.Text, nullable=False)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    active = db.Column(db.Boolean(), default=True)

    roles = db.relationship("Role", secondary=roles_users, backref=db.backref("users", lazy="dynamic"))
    tokens = db.relationship("OAuth2Token", back_populates="user", cascade="all, delete-orphan")

class OAuth2Token(db.Model):
    __tablename__ = "oauth2token"
    __table_args__ = {"schema": "public"}

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("public.user.ID_Usr"), primary_key=True)
    name = db.Column(db.String(40), primary_key=True)
    token_type = db.Column(db.String(40))
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text)
    expires_at = db.Column(db.Integer, default=0)
    
    user = db.relationship("User", back_populates="tokens")