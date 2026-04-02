# Endpoints — Posts y Comentarios
**Base URL:** `/api/post`

---

## POST /api/post/create
Crea una nueva publicación, opcionalmente vinculada a una comunidad o proyecto.

```json
{
    "title": "Título del post",
    "content": "Contenido del post",
    "id_cmnd": "uuid-de-la-comunidad",
    "id_pryct": "uuid-del-proyecto",
    "is_anonymous": false,
    "hasCode": true,
    "codeLang": "python",
    "codeLines": [
        { "text": "print('hola')", "color": "#fff" }
    ],
    "refs": [
        { "label": "Referencia", "sub": "Subtítulo" }
    ],
    "featured": false
}
```

**Validación Título:** Mínimo 5 caracteres; responde `400` si es más corto.  
**Campos opcionales:** `id_cmnd` e `id_pryct` pueden omitirse para posts globales (sin comunidad ni proyecto).  
**Metadata UI:** Los campos `is_anonymous`, `hasCode`, `codeLang`, `codeLines`, `refs` y `featured` se guardan en `Extra_Metadata` para que el frontend renderice el post correctamente.  
**Resultado:** `201` con el `id` UUID del post recién creado.

======================================================================================================

## GET /api/post/feed
Devuelve un feed personalizado de hasta 30 posts para el usuario autenticado.

```json
// No requiere Body
{}
```

**Criterios de inclusión (OR):** Posts propios del usuario, posts globales (sin comunidad), posts de comunidades donde es miembro activo, posts de las 5 comunidades con más miembros (trending), y posts con 5 o más votos de karma.  
**Orden:** Del más reciente al más antiguo (`Fch_pblcn DESC`).  

======================================================================================================

## GET /api/post/my
Devuelve todos los posts publicados por el usuario autenticado.

```json
// No requiere Body
{}
```

**Orden:** Del más reciente al más antiguo.  
**Resultado:** Array de objetos formateados con `format_post_output`, incluyendo autor, metadata UI y stats.

======================================================================================================

## GET /api/post/user/\<user_id\>
Devuelve todos los posts publicados por un usuario específico.

```json
// No requiere Body
{}
```

**Acceso público:** Esta ruta no requiere autenticación (`@auth_required()` ausente).  
**Anonimato:** Si el post tiene `is_anonymous` o `user_removed` en su metadata, el campo `posted_by` se muestra como `"Anónimo"` en lugar del nombre real.

======================================================================================================

## PUT /api/post/edit/\<post_id\>
Edita el título, contenido o metadata UI de un post existente.

```json
{
    "title": "Nuevo título",
    "content": "Nuevo contenido",
    "ui_data": {
        "hasCode": false,
        "featured": true
    }
}
```

**Permisos:** Solo el autor del post puede editarlo (`403` si no lo es).  
**Campos parciales:** Todos los campos son opcionales; los omitidos conservan su valor actual.  
**ui_data:** Si se envía, se hace un `merge` con la metadata existente sin reemplazarla completamente.  

======================================================================================================

## DELETE /api/post/delete/\<post_id\>
Anonimiza un post sin eliminarlo físicamente de la base de datos.

```json
// No requiere Body
{}
```

**Permisos:** Solo el autor del post puede ejecutar esta acción (`403` si no lo es).  
**Acción (soft delete):** No elimina el registro. Establece `is_anonymous: true` y `user_removed: true` en `Extra_Metadata`, ocultando la identidad del autor en el feed.  

======================================================================================================

## POST /api/post/like/\<post_id\>
Alterna el like del usuario autenticado en un post (toggle).

```json
// No requiere Body
{}
```

**Toggle:** Si el like ya existe, lo elimina (`unliked`). Si no existe, lo crea (`liked`).  
**Resultado:** `200` al quitar el like, `201` al añadirlo, ambos con el campo `status` indicando el estado resultante.

======================================================================================================

## POST /api/post/save/\<post_id\>
Alterna el guardado del usuario autenticado en un post (toggle).

```json
// No requiere Body
{}
```

**Toggle:** Si el post ya estaba guardado, lo elimina de favoritos. Si no, lo guarda.  
**Resultado:** `200` al quitar de favoritos, `201` al guardar.

======================================================================================================

## POST /api/post/\<post_id\>/comment
Añade un comentario a un post, con soporte de respuestas anidadas.

```json
{
    "content": "Texto del comentario",
    "parent_id": "uuid-del-comentario-padre"
}
```

**Respuestas:** El campo `parent_id` es opcional. Si se envía, el comentario queda vinculado como respuesta a otro comentario.  
**⚠️
**Resultado:** `201` con el `id` UUID del comentario creado.

======================================================================================================

## GET /api/post/\<post_id\>/comments
Devuelve todos los comentarios de un post, ordenados cronológicamente.

```json
// No requiere Body
{}
```

**Acceso público:** Esta ruta no requiere autenticación.  
**Orden:** Del más antiguo al más reciente (`Fch_creacion ASC`).  
**Anonimato:** Si el usuario autor no existe en la base de datos, el nombre se muestra como `"Anónimo"`.  
**Resultado:** Array con `id`, `author`, `pfp`, `content`, `date` y `parent_id` por cada comentario.

======================================================================================================

## DELETE /api/post/comment/delete/\<comment_id\>
Anonimiza el contenido de un comentario sin eliminarlo físicamente.

```json
// No requiere Body
{}
```

**Permisos:** Solo el autor del comentario puede eliminarlo (`403` si no lo es).  
**Acción (soft delete):** Reemplaza el campo `Contenido` con el texto fijo `"[Este comentario ha sido eliminado]"`, preservando la estructura del hilo de respuestas.
