#routes/resource
from flask import Blueprint
from flask_security import auth_required

from server.controllers.resource import create_resource, get_paginated_resources
from server.controllers.resource import vote_resource

resource_router = Blueprint('resources', __name__, url_prefix='/resources')

@resource_router.route("/", methods=["GET"])
def get_resources():
    """
    Obtener lista de recursos (Paginada y filtrada)
    ---
    tags:
      - Recursos
    parameters:
      - name: page
        in: query
        type: integer
        description: Número de página (por defecto 1)
      - name: tags
        in: query
        type: string
        description: Etiquetas separadas por coma (ej. python,backend)
    responses:
      200:
        description: Lista paginada de recursos formateada para el Frontend
    """
    return get_paginated_resources()

@resource_router.route("/", methods=["POST"])
# @auth_required()
def post_resource():
    """
    Crear un nuevo recurso
    ---
    tags:
      - Recursos
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - link
          properties:
            link:
              type: string
              description: URL del recurso
            title:
              type: string
              description: Título del recurso
            descripcion:
              type: string
              description: Breve descripción (opcional)
            markdown:
              type: boolean
              description: Indica si el recurso usa formato markdown
            tags:
              type: array
              items:
                type: string
              description: Lista de etiquetas
            images:
              type: array
              items:
                type: string
              description: Arreglo de URLs de imágenes alojadas (ej. Cloudinary)
    responses:
      201:
        description: Recurso e imágenes creados exitosamente
      400:
        description: Error de validación
      401:
        description: No autorizado (Falta iniciar sesión)
    """
    return create_resource()

@resource_router.route("/<uuid:recurso_id>/vote", methods=["PATCH"])
@auth_required()
def patch_vote(recurso_id):
    """
    Sumar o restar un voto a un recurso
    ---
    tags:
      - Recursos
    parameters:
      - name: recurso_id
        in: path
        type: string
        required: true
        description: UUID del recurso
      - in: body
        name: body
        schema:
          type: object
          required:
            - value
          properties:
            value:
              type: integer
              description: 1 para upvote, -1 para downvote
    responses:
      200:
        description: Voto registrado, retorna el nuevo conteo
      400:
        description: Valor inválido
      404:
        description: Recurso no encontrado
    """
    return vote_resource(recurso_id)
