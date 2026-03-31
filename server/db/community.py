from server.db.model import db
import datetime
import uuid

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
    
    ID_cmnd = db.Column(db.UUID(as_uuid=True), db.ForeignKey('public.Comunidad.iD_cmnd', ondelete="CASCADE"), primary_key=True)
    ID_Tag = db.Column(db.Integer, db.ForeignKey('public.Tag.id', ondelete="CASCADE"), primary_key=True)
    tag = db.relationship("Tag")

# --- MODELO DE COMUNIDAD ---
class Comunidad(db.Model):
    __tablename__ = 'Comunidad'
    __table_args__ = {"schema": "public"}
    
    iD_cmnd = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name_cmnd = db.Column(db.Text, nullable=False)
    Dscrpcn = db.Column(db.Text)
    Fch_crcn = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    active = db.Column(db.Boolean(), default=True, nullable=False)
    ID_Admin = db.Column(db.UUID(as_uuid=True), db.ForeignKey('public.user.ID_Usr'), nullable=False)
    
    pfp_cmnd = db.Column(db.Text)
    banner_cmnd = db.Column(db.Text)
    tags = db.relationship('Tag', secondary='public.Comunidad_Tag', backref=db.backref('comunidades', lazy='dynamic', overlaps="tags"), overlaps="tags")
    reglas = db.relationship('Regla_Comunidad', backref='comunidad', lazy=True, cascade="all, delete-orphan")
    miembros = db.relationship('Usuario_Comunidad', backref='comunidad', lazy=True)

# --- MODELO DE REGLAS ---
class Regla_Comunidad(db.Model):
    __tablename__ = 'regla_comunidad'
    
    id_regla = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_cmnd = db.Column(db.UUID(as_uuid=True), db.ForeignKey('public.Comunidad.iD_cmnd'), nullable=False)
    nombre_regla = db.Column(db.String, nullable=False) 
    dscrpcn = db.Column(db.Text)
    orden = db.Column(db.Integer, nullable=False)

# --- TABLA INTERMEDIA (MIEMBROS CON ROLES Y SOFT DELETE) ---
class Usuario_Comunidad(db.Model):
    __tablename__ = 'Usuario_Comunidad'
    __table_args__ = {"schema": "public"}
    
    ID_Usr = db.Column(db.UUID(as_uuid=True), db.ForeignKey('public.user.ID_Usr'), primary_key=True)
    ID_cmnd = db.Column(db.UUID(as_uuid=True), db.ForeignKey('public.Comunidad.iD_cmnd'), primary_key=True)
    Fch_ingreso = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    Rol = db.Column(db.String(20), default='miembro', nullable=False) # 'fundador', 'moderador', 'miembro'
    Is_Active = db.Column(db.Boolean, default=True, nullable=False) 

# --- MODELO DE CHAT ---
class Chat(db.Model):
    __tablename__ = 'Chat'
    __table_args__ = {"schema": "public"}
    ID_Chat = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iD_cmnd = db.Column(db.UUID(as_uuid=True), db.ForeignKey('public.Comunidad.iD_cmnd'))
    ID_Pryct = db.Column(db.UUID(as_uuid=True))
    
    mensajes = db.relationship('Registro_Chat', backref='chat', lazy=True)

# --- MODELO DE MENSAJES ---
class Registro_Chat(db.Model):
    __tablename__ = 'Registro_Chat'
    __table_args__ = {"schema": "public"}
    ID_Mnsj = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ID_Usr = db.Column(db.UUID(as_uuid=True), db.ForeignKey('public.user.ID_Usr'), nullable=False)
    ID_Chat = db.Column(db.UUID(as_uuid=True), db.ForeignKey('public.Chat.ID_Chat'), nullable=False)
    Dscrpcn = db.Column(db.String, nullable=False)
    Fch_envio = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)