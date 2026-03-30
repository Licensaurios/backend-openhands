import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from server.db.model import db  # Importamos la base de datos principal

# 1. Creamos la tabla puente (Recurso_Tag)
# Usamos db.Model en lugar de Base
class Recurso_Tag(db.Model):
    __tablename__ = "recurso_tag"
    __table_args__ = {"schema": "public"}

    ID_Rcrs = Column(UUID(as_uuid=True), ForeignKey('public.Recurso.ID_Rcrs'), primary_key=True)
    id = Column(Integer, ForeignKey('public.Tag.id'), primary_key=True)

# 2. Creamos la tabla principal
# Usamos db.Model en lugar de Base
class Recurso(db.Model):
    __tablename__ = "Recurso"
    __table_args__ = {"schema": "public"}

    ID_Rcrs = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Link = Column(String, nullable=False)
    ID_Usr = Column(UUID(as_uuid=True), ForeignKey("public.user.ID_Usr"), nullable=False)
    Dscrpcn = Column(String, nullable=True)
    Fch_plcn = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    ID_pblcn = Column(UUID(as_uuid=True), nullable=True)
    # Relación para poder acceder a los tags fácilmente
    tags = relationship("Tag", secondary="public.recurso_tag", backref="recursos")

# 3. Importamos Tag hasta el final, sin sangría, pegado a la izquierda
from server.db.community import Tag