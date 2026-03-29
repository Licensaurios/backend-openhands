from flask import (
    Blueprint, jsonify
)
from sqlalchemy.orm import Session

from server.controllers.health import get_server_status
from server.db.resource import Recurso
from server.db.model import get_db 
resource_router = Blueprint('resources', __name__, url_prefix='/resources')

def recurso_to_dict(recurso: Recurso) -> dict:
    return {
        "ID_Rcrs": str(recurso.ID_Rcrs),
        "Link": recurso.Link,
        "ID_Usr": str(recurso.ID_Usr),
        "Dscrpcn": recurso.Dscrpcn,
        "Fch_plcn": recurso.Fch_plcn.isoformat(),
        "ID_pblcn": str(recurso.ID_pblcn) if recurso.ID_pblcn else None,
    }

def get_all_recursos(db: Session) -> list[dict]:
    recursos = db.query(Recurso).all()
    return [recurso_to_dict(r) for r in recursos]

@resource_router.route("/")
def get_resources():
    db = next(get_db())
    recursos = get_all_recursos(db)
    db.close()
    return jsonify(
        {
            "resources": recursos,
            "count": len(recursos)
        }
    )






