# API Documentación — Recursos

## Tabla de contenidos
- [Esquema de la base de datos](#esquema-de-la-base-de-datos)
- [GET /resources/](#get-resources)
- [POST /resources/](#post-resources)
- [PATCH /resources/{id}/vote](#patch-resourcesidvote)

---

## Esquema de la base de datos

### Tabla `Recurso`

| Columna | Tipo | Nullable | Default | Descripción |
|---|---|---|---|---|
| `ID_Rcrs` | uuid | No | gen_random_uuid() | Primary key |
| `Link` | varchar | No | — | URL del recurso |
| `ID_Usr` | uuid | No | — | FK al usuario autor |
| `title` | varchar(255) | Sí | — | Título del recurso |
| `markdown` | bool | No | false | Si el contenido usa formato markdown |
| `Dscrpcn` | varchar | Sí | — | Descripción corta |
| `Fch_plcn` | timestamptz | No | now() | Fecha de publicación |
| `ID_pblcn` | uuid | Sí | — | ID de publicación externa |
| `featured` | bool | Sí | false | Si el recurso está destacado |
| `rating` | int4 | Sí | — | Rating del recurso |
| `votes` | int4 | Sí | 0 | Conteo de votos |
| `hascode` | bool | Sí | false | Si incluye un bloque de código |
| `refs` | jsonb | Sí | `'[]'` | Array de URLs de referencia |
| `codelines` | jsonb | Sí | `'[]'` | Array de líneas de código con color |
| `codelang` | varchar(50) | Sí | — | Lenguaje del bloque de código |

### Tabla `RecursoImg`

| Columna | Tipo | Descripción |
|---|---|---|
| `id_img` | uuid | Primary key |
| `url` | text | URL de la imagen (ej. Cloudinary) |
| `ID_Rcrs` | uuid | FK a `Recurso` con CASCADE delete |

### Tabla `Recurso_Tag` (pivot)

| Columna | Tipo | Descripción |
|---|---|---|
| `ID_Rcrs` | uuid | FK a `Recurso` |
| `id` | int | FK a `Tag` |

---

## GET /resources/

Retorna la lista paginada de recursos, con soporte de filtro por tags.

**Método:** `GET`  
**Auth requerida:** No  
**URL:** `/resources/`

### Query params

| Param | Tipo | Requerido | Descripción |
|---|---|---|---|
| `page` | integer | No (default: 1) | Número de página |
| `tags` | string | No | Tags separados por coma (ej. `nginx,bash`) |

### Ejemplo de request

```
GET /resources/?page=1&tags=nginx,bash
```

### Ejemplo de response `200`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "featured": false,
      "title": "Automated Nginx + UFW Firewall Config",
      "author": "u/devjorge",
      "community": "d/React Hub",
      "time": "1h ago",
      "tags": ["#nginx", "#bash", "#devops"],
      "rating": null,
      "votes": 87,
      "hasCode": true,
      "codeLines": [
        { "text": "$ bash",                               "color": "#FF6D2D" },
        { "text": "#import /u/bain",                      "color": "#FF6D6D" },
        { "text": "automated Nginx + UFW Firewall Config", "color": "#6EE7B7" }
      ],
      "codeLang": "bash",
      "markdown": false,
      "refs": [
        "https://nginx.org/docs",
        "https://help.ubuntu.com/ufw"
      ],
      "images": [
        "https://res.cloudinary.com/demo/image/upload/sample.jpg"
      ]
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 10,
  "has_more": true
}
```

---

## POST /resources/

Crea un nuevo recurso.

**Método:** `POST`  
**Auth requerida:** Sí (`@auth_required`)  
**URL:** `/resources/`

### Body (JSON)

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `link` | string | **Sí** | URL del recurso |
| `title` | string | No | Título del recurso |
| `descripcion` | string | No | Descripción corta |
| `markdown` | boolean | No (default: false) | Si usa formato markdown |
| `featured` | boolean | No (default: false) | Si está destacado |
| `rating` | integer | No | Rating inicial |
| `votes` | integer | No (default: 0) | Votos iniciales |
| `hasCode` | boolean | No (default: false) | Si incluye código |
| `codeLang` | string | No | Lenguaje del código (ej. `"bash"`) |
| `codeLines` | array | No | Líneas de código con color |
| `refs` | array | No | URLs de referencia |
| `tags` | array | No | Lista de etiquetas |
| `images` | array | No | URLs de imágenes (ej. Cloudinary) |

### Ejemplo de request

```json
{
  "link": "https://github.com/ejemplo/repo",
  "title": "Automated Nginx + UFW Firewall Config",
  "descripcion": "Script para configurar Nginx y UFW automáticamente",
  "markdown": false,
  "featured": false,
  "rating": null,
  "votes": 0,
  "hasCode": true,
  "codeLang": "bash",
  "codeLines": [
    { "text": "$ bash",                               "color": "#FF6D2D" },
    { "text": "#import /u/bain",                      "color": "#FF6D6D" },
    { "text": "automated Nginx + UFW Firewall Config", "color": "#6EE7B7" },
    { "text": "automated Nginx + UFW Firewall",        "color": "#6EE7B7" }
  ],
  "refs": [
    "https://nginx.org/docs",
    "https://help.ubuntu.com/ufw"
  ],
  "tags": ["nginx", "bash", "devops", "firewall"],
  "images": [
    "https://res.cloudinary.com/demo/image/upload/sample.jpg"
  ]
}
```

### Ejemplo de response `201`

```json
{
  "msg": "Recurso creado exitosamente",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "usuario_asignado": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Errores

| Código | Descripción |
|---|---|
| `400` | El campo `link` es obligatorio |
| `401` | No autenticado |
| `500` | Error interno en base de datos |

---

## PATCH /resources/{id}/vote

Suma o resta un voto al recurso indicado.

**Método:** `PATCH`  
**Auth requerida:** Sí (`@auth_required`)  
**URL:** `/resources/{recurso_id}/vote`

### Path params

| Param | Tipo | Descripción |
|---|---|---|
| `recurso_id` | uuid | ID del recurso obtenido del GET |

### Body (JSON)

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `value` | integer | **Sí** | `1` para upvote, `-1` para downvote |

### Ejemplo upvote

```
PATCH /resources/550e8400-e29b-41d4-a716-446655440000/vote
```

```json
{ "value": 1 }
```

### Ejemplo downvote

```json
{ "value": -1 }
```

### Ejemplo de response `200`

```json
{
  "msg": "Voto registrado",
  "votes": 88
}
```

### Errores

| Código | Descripción |
|---|---|
| `400` | El valor no es `1` ni `-1` |
| `401` | No autenticado |
| `404` | Recurso no encontrado |
| `500` | Error interno en base de datos |

### Uso desde el frontend (React)

```javascript
const handleVote = async (recursoId, value) => {
  const res = await fetch(`/resources/${recursoId}/vote`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value }) // 1 o -1
  });
  const data = await res.json();
  console.log(data.votes); // nuevo conteo
};

// En la card
<button onClick={() => handleVote(resource.id, 1)}>▲</button>
<button onClick={() => handleVote(resource.id, -1)}>▼</button>
```
