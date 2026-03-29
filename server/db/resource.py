import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Recurso(Base):
    __tablename__ = "Recurso"
    __table_args__ = {"schema": "public"}

    ID_Rcrs = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Link = Column(String, nullable=False)
    ID_Usr = Column(UUID(as_uuid=True), ForeignKey("public.user.ID_Usr"), nullable=False)
    Dscrpcn = Column(String, nullable=True)
    Fch_plcn = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    ID_pblcn = Column(UUID(as_uuid=True), ForeignKey("public.Publicacion.ID_pblcn"), nullable=True)

