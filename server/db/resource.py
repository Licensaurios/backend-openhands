import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID 
from server.db.model import db

class Recurso(db.Model):
    __tablename__ = "Recurso"
    __table_args__ = {"schema": "public"}

    ID_Rcrs = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Link = db.Column(db.String, nullable=False)
    ID_Usr = db.Column(UUID(as_uuid=True), db.ForeignKey("public.user.ID_Usr"), nullable=False)
    Dscrpcn = db.Column(db.String, nullable=True)
    Fch_plcn = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now)
    ID_pblcn = db.Column(UUID(as_uuid=True), db.ForeignKey("public.Publicacion.ID_pblcn"), nullable=True)