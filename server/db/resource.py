import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from server.db.model import db  # Importamos la base de datos principal


# 1. Creamos la tabla puente (Recurso_Tag)
class Recurso_Tag(db.Model):
    __tablename__ = "recurso_tag"
    __table_args__ = {"schema": "public"}

    ID_Rcrs = Column(UUID(as_uuid=True), ForeignKey('public.Recurso.ID_Rcrs'), primary_key=True)
    id = Column(Integer, ForeignKey('public.Tag.id'), primary_key=True)


# 2. Nueva tabla de imágenes
class RecursoImg(db.Model):
    __tablename__ = 'recurso_img'
    __table_args__ = {"schema": "public"}

    id_img = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False)  # Ideal para Cloudinary
    # Corregido: UUID y ruta al     esquema
    ID_Rcrs = Column(UUID(as_uuid=True), ForeignKey('public.Recurso.ID_Rcrs', ondelete='CASCADE'), nullable=False)


# 3. Creamos la tabla principal
class Recurso(db.Model):
    __tablename__ = "Recurso"
    __table_args__ = {"schema": "public"}

    ID_Rcrs = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Link = Column(String, nullable=False)
    ID_Usr = Column(UUID(as_uuid=True), ForeignKey("public.user.ID_Usr"), nullable=False)

    title = Column(String(255), nullable=True)
    markdown = Column(Boolean, nullable=False, default=False)

    Dscrpcn = Column(String, nullable=True)
    Fch_plcn = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    ID_pblcn = Column(UUID(as_uuid=True), nullable=True)

    # Relación para acceder a los tags
    tags = relationship("Tag", secondary="public.recurso_tag", backref="recursos")
    # Relación para acceder a las imágenes
    imagenes = relationship('RecursoImg', backref='recurso', lazy=True, cascade="all, delete-orphan")


# 4. Importamos Tag hasta el final
from server.db.community import Tag