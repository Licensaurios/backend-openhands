from flask import Blueprint
from flask_security import auth_required  # <-- IMPORTAMOS EL CANDADO AQUÍ

# Importamos las funciones desde el controlador que creamos
from server.controllers.resource import create_resource, get_paginated_resources

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
        description: Lista paginada de recursos
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                properties:
                  id:
                    type: string
                  link:
                    type: string
                  descripcion:
                    type: string
                  tags:
                    type: array
                    items:
                      type: string
            total:
              type: integer
            page:
              type: integer
            has_more:
              type: boolean
    """
    # Llamamos a la función del controlador que maneja la paginación y filtros
    return get_paginated_resources()


@resource_router.route("/", methods=["POST"])
@auth_required()  # <-- PONEMOS EL CANDADO SOLO EN EL POST (DEBE IR DEBAJO DE @route)
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
            descripcion:
              type: string
              description: Breve descripción
            tags:
              type: array
              items:
                type: string
              description: Lista de etiquetas
    responses:
      201:
        description: Recurso creado exitosamente
      400:
        description: Error de validación
      401:
        description: No autorizado (Falta iniciar sesión)
    """
    # Llamamos a la función del controlador que maneja la creación y guardado de tags
    return create_resource()