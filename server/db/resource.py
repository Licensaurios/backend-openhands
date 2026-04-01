import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from server.db.model import db


class Recurso_Tag(db.Model):
    __tablename__ = "recurso_tag"
    __table_args__ = {"schema": "public"}

    ID_Rcrs = Column(UUID(as_uuid=True), ForeignKey('public.Recurso.ID_Rcrs'), primary_key=True)
    id = Column(Integer, ForeignKey('public.Tag.id'), primary_key=True)


class RecursoImg(db.Model):
    __tablename__ = 'recurso_img'
    __table_args__ = {"schema": "public"}

    id_img  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url     = Column(Text, nullable=False)
    ID_Rcrs = Column(UUID(as_uuid=True), ForeignKey('public.Recurso.ID_Rcrs', ondelete='CASCADE'), nullable=False)


class Recurso(db.Model):
    __tablename__ = "Recurso"
    __table_args__ = {"schema": "public"}

    ID_Rcrs   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Link      = Column(String,       nullable=False)
    ID_Usr    = Column(UUID(as_uuid=True), ForeignKey("public.user.ID_Usr"), nullable=False)
    title     = Column(String(255),  nullable=True)
    markdown  = Column(Boolean,      nullable=False, default=False)
    Dscrpcn   = Column(String,       nullable=True)
    Fch_plcn  = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    ID_pblcn  = Column(UUID(as_uuid=True), nullable=True)
    featured  = Column(Boolean,      nullable=True,  default=False)
    rating    = Column(Integer,      nullable=True)
    votes     = Column(Integer,      nullable=True,  default=0)
    hascode   = Column(Boolean,      nullable=True,  default=False)
    refs      = Column(JSONB,        nullable=True,  default=list)
    codelines = Column(JSONB,        nullable=True,  default=list)
    codelang  = Column(String(50),   nullable=True)
    community_id = Column(UUID(as_uuid=True), ForeignKey("public.Comunidad.iD_cmnd"), nullable=False)

    tags     = relationship("Tag", secondary="public.recurso_tag", backref="recursos")
    imagenes = relationship('RecursoImg', backref='recurso', lazy=True, cascade="all, delete-orphan")


from server.db.community import Tag
