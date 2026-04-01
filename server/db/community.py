from server.db.model import db  
import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID 
# --- MODELO DE TAGS ---
class Tag(db.Model):
    __tablename__ = 'Tag'
    __table_args__ = {"schema": "public"}
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, unique=True, nullable=False)

# --- TABLA INTERMEDIA COMUNIDAD-TAG ---
class Comunidad_Tag(db.Model):
    __tablename__ = 'Comunidad_Tag'
    __table_args__ = {"schema": "public"}
    
    ID_cmnd = db.Column(UUID(as_uuid=True), db.ForeignKey('public.Comunidad.iD_cmnd', ondelete="CASCADE"), primary_key=True)
    ID_Tag = db.Column(db.Integer, db.ForeignKey('public.Tag.id', ondelete="CASCADE"), primary_key=True)

# --- MODELO DE COMUNIDAD ---
class Comunidad(db.Model):
    __tablename__ = 'Comunidad'
    __table_args__ = {"schema": "public"}
    
    iD_cmnd = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name_cmnd = db.Column(db.Text, nullable=False)
    Dscrpcn = db.Column(db.Text)
    
    # Mapeado del Tema
    id_tema = db.Column(UUID(as_uuid=True), db.ForeignKey('public.tema.id_tema'), nullable=True)
    tema = db.relationship('Tema', backref='comunidades', lazy=True)

    Fch_crcn = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    active = db.Column(db.Boolean(), default=True, nullable=False)
    ID_Admin = db.Column(UUID(as_uuid=True), db.ForeignKey('public.user.ID_Usr'), nullable=False)
    
    pfp_cmnd = db.Column(db.Text)
    banner_cmnd = db.Column(db.Text)
    
    # Relaciones
    tags = db.relationship('Tag', secondary='public.Comunidad_Tag', backref=db.backref('comunidades', overlaps="tags"), overlaps="tags")
    reglas = db.relationship('Regla_Comunidad', backref='comunidad', lazy=True, cascade="all, delete-orphan")
    miembros = db.relationship('Usuario_Comunidad', backref='comunidad', lazy=True)
    total_miembros = db.Column(db.Integer, default=0)
class Regla_Comunidad(db.Model):
    __tablename__ = 'regla_comunidad'
    __table_args__ = {"schema": "public"}
    
    id_regla = db.Column('id_regla', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    ID_cmnd = db.Column('id_cmnd', UUID(as_uuid=True), db.ForeignKey('public.Comunidad.iD_cmnd'), nullable=False)
    
    nombre_regla = db.Column('nombre_regla', db.String, nullable=False) 
    dscrpcn = db.Column('dscrpcn', db.Text)
    orden = db.Column('orden', db.Integer, nullable=False)
    
class Usuario_Comunidad(db.Model):
    __tablename__ = 'Usuario_Comunidad'
    __table_args__ = {"schema": "public"}
    
    ID_Usr = db.Column(UUID(as_uuid=True), db.ForeignKey('public.user.ID_Usr'), primary_key=True)
    ID_cmnd = db.Column(UUID(as_uuid=True), db.ForeignKey('public.Comunidad.iD_cmnd'), primary_key=True)
    Fch_ingreso = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    Rol = db.Column(db.String(20), default='miembro', nullable=False)
    Is_Active = db.Column(db.Boolean, default=True, nullable=False) 

# --- MODELO DE CHAT ---
class Chat(db.Model):
    __tablename__ = 'Chat'
    __table_args__ = {"schema": "public"}
    
    ID_Chat = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iD_cmnd = db.Column(UUID(as_uuid=True), db.ForeignKey('public.Comunidad.iD_cmnd'))
    ID_Pryct = db.Column(UUID(as_uuid=True))
    
    mensajes = db.relationship('Registro_Chat', backref='chat', lazy=True)

# --- MODELO DE MENSAJES ---
class Registro_Chat(db.Model):
    __tablename__ = 'Registro_Chat'
    __table_args__ = {"schema": "public"}
    
    ID_Mnsj = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ID_Usr = db.Column(UUID(as_uuid=True), db.ForeignKey('public.user.ID_Usr'), nullable=False)
    ID_Chat = db.Column(UUID(as_uuid=True), db.ForeignKey('public.Chat.ID_Chat'), nullable=False)
    Dscrpcn = db.Column(db.String, nullable=False)
    Fch_envio = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)