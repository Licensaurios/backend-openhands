# Endpoints — Comunidades
**Base URL:** `/api/community`

---

## POST /api/community/create
Crea una nueva comunidad y registra al usuario creador como fundador.

```json
{
    "nombre": "Mi Comunidad",
    "descripcion": "Descripción de la comunidad",
    "pfp_url": "https://url-de-la-foto.com/img.png",
    "banner_url": "https://url-del-banner.com/img.png",
    "tags": ["python", "dev", "backend"]
}
```

**Validación Nombre:** Es el único campo obligatorio; el servidor responde con `400` si se omite.  
**Validación Tags:** Solo se permiten letras y números. Cualquier carácter especial o espacio es eliminado automáticamente con Regex antes de guardar.  
**Acción interna:** Al crear la comunidad, el servidor también genera automáticamente un `Chat` vinculado y registra al creador con el rol `fundador` en la tabla `Usuario_Comunidad`.  
**Resultado:** Recibes un `201` con el `id` UUID de la comunidad recién creada.

======================================================================================================

## GET /api/community/my
Devuelve la lista de comunidades a las que pertenece el usuario autenticado.

```json
// No requiere Body
{}
```

**Filtros aplicados:** Solo retorna comunidades donde la membresía está activa (`Is_Active = True`) y la comunidad no ha sido deshabilitada (`active = True`).  
**Resultado:** Array de objetos con información de cada comunidad, incluyendo el rol del usuario (`miembro`, `moderador`, `fundador`) y si es el administrador principal.

======================================================================================================

## GET /api/community/search?q=\<query\>&page=\<n\>
Busca comunidades activas por nombre o por tag.

```json
// No requiere Body — Parámetros por Query String
// ?q=python&page=1
```

**Búsqueda:** Filtra por nombre (`ilike`) o por tags asociados usando `OR` entre ambos criterios. Devuelve resultados únicos (`distinct`).  
**Paginación:** Devuelve 10 resultados por página. El campo `has_more` indica si existen más páginas.  
**Sin query:** Si `q` se omite, devuelve todas las comunidades activas paginadas.

======================================================================================================

## GET /api/community/trending
Devuelve las 5 comunidades con mayor número de miembros activos.

```json
// No requiere Body
{}
```

**Criterio:** Ordena descendentemente por conteo de miembros en `Usuario_Comunidad`, solo considerando comunidades con `active = True`.  
**Resultado:** Array de hasta 5 objetos con `id`, `nombre`, `descripcion`, `pfp`, `miembros` y `tags`.

======================================================================================================

## GET /api/community/\<comm_id\>
Obtiene la información completa y detallada de una comunidad específica.

```json
// No requiere Body
{}
```

**Incluye:** Datos generales de la comunidad, información del fundador, lista de moderadores, conteo total de miembros, reglas ordenadas y tags.  
**Dato informativo:** El campo `limite_mods` (valor `4`) se devuelve para que el frontend pueda mostrar la capacidad máxima de moderadores.  
**⚠️ Bug conocido:** El `return` del response está dentro del bucle `for` de miembros, por lo que la respuesta se genera en la primera iteración sin terminar de procesar el resto.

======================================================================================================

## POST /api/community/join/\<comm_id\>
Registra al usuario autenticado como miembro de una comunidad.

```json
// No requiere Body
{}
```

**Validación:** Si la comunidad está deshabilitada (`active = False`), responde con `400`.  
**Reingreso:** Si el usuario ya existía en la tabla pero con `Is_Active = False`, se reactiva su membresía con rol `miembro` en lugar de crear un registro duplicado.  
**Resultado:** `200` si ya era miembro activo, `201` si se unió exitosamente.

======================================================================================================

## DELETE /api/community/leave/\<comm_id\>
Permite al usuario salir de una comunidad, con lógica especial para el fundador.

```json
{
    "successor_id": "uuid-del-sucesor"
}
```

**Validación Fundador:** Si el usuario que sale es el fundador, el campo `successor_id` es obligatorio. El sucesor debe ser un miembro activo de la comunidad.  
**Transferencia:** Al confirmar el sucesor, su rol cambia a `fundador` y el campo `ID_Admin` de la comunidad se actualiza al nuevo dueño.  
**Miembros regulares:** El campo `successor_id` puede omitirse; la salida simplemente establece `Is_Active = False`.

======================================================================================================

## GET /api/community/\<comm_id\>/status
Consulta si el usuario autenticado es miembro activo de una comunidad y cuál es su rol.

```json
// No requiere Body
{}
```

**Resultado exitoso:** Devuelve `is_member: true` junto con el `role` (`fundador`, `moderador` o `miembro`) y la `fecha_ingreso`.  
**Sin membresía:** Devuelve `is_member: false` y `role: null` con un `200` (no es un error).

======================================================================================================

## GET /api/community/\<comm_id\>/members
Devuelve la lista de todos los miembros registrados en una comunidad.

```json
// No requiere Body
{}
```

**Permisos:** Solo los miembros de la comunidad pueden ver la lista. Un usuario externo recibe `403 Forbidden`.  
**Resultado:** Objeto con el nombre de la comunidad, el conteo total y el array de miembros con su `id_usuario` y `fecha_ingreso`.

======================================================================================================

## PUT /api/community/edit/\<comm_id\>
Edita la información de una comunidad existente.

```json
{
    "nombre": "Nuevo nombre",
    "descripcion": "Nueva descripción",
    "pfp_url": "https://nueva-foto.com/img.png",
    "banner_url": "https://nuevo-banner.com/img.png",
    "tags": ["newtag", "otro"]
}
```

**Permisos:** Solo el administrador principal (`ID_Admin`) puede ejecutar esta acción; de lo contrario responde `403 Forbidden`.  
**Tags:** Si el campo `tags` está presente en el body, se reemplazan todos los tags anteriores por los nuevos.  
**Campos parciales:** Todos los campos son opcionales. Si se omite alguno, conserva su valor actual.

======================================================================================================

## DELETE /api/community/delete/\<comm_id\>
Deshabilita (soft delete) una comunidad sin eliminarla físicamente de la base de datos.

```json
// No requiere Body
{}
```

**Permisos:** Exclusivo para el administrador principal de la comunidad (`403` si no lo es).  
**Acción:** Establece el campo `active` en `False`. La comunidad deja de aparecer en búsquedas y listados.  
**Resultado:** Recibes un `200` con el `id` y el nuevo `status: "inactive"`.

======================================================================================================

## POST /api/community/\<comm_id\>/promote
Promueve a un miembro activo al rol de moderador.

```json
{
    "target_user_id": "uuid-del-usuario"
}
```

**Permisos:** Solo el `fundador` puede promover miembros (`403` para cualquier otro rol).  
**Límite:** No se pueden tener más de 4 moderadores activos simultáneamente. Superarlo devuelve `400` con `error: "LIMIT_REACHED"`.  
**Validaciones:** El usuario objetivo debe ser miembro activo. Si ya es moderador, responde `200` sin aplicar cambios.  
**Resultado:** Devuelve el nuevo rol asignado y el conteo actualizado de moderadores.

======================================================================================================

## POST /api/community/\<comm_id\>/kick
Expulsa a un miembro activo de la comunidad.

```json
{
    "target_user_id": "uuid-del-usuario"
}
```

**Permisos:** Requiere rol `fundador` o `moderador`. Cualquier otro recibe `403 Forbidden`.  
**Protección:** No es posible expulsar al `fundador` de la comunidad; el servidor responde con `403`.  
**Acción:** Establece `Is_Active = False` en el registro del miembro objetivo, sin eliminarlo de la tabla.

======================================================================================================

## GET /api/community/\<comm_id\>/rules
Devuelve todas las reglas de una comunidad, ordenadas por su campo `Orden`.

```json
// No requiere Body
{}
```

**Resultado:** Array de objetos con `id_regla`, `nombre`, `descripcion` y `orden`.

======================================================================================================

## POST /api/community/\<comm_id\>/rules/create
Añade una nueva regla a la comunidad.

```json
{
    "nombre": "Respeto mutuo",
    "descripcion": "Trata a los demás como quieres ser tratado."
}
```

**Permisos:** Requiere rol `fundador` o `moderador`.  
**Límite:** Máximo 10 reglas por comunidad. Superarlo devuelve `400` con `error: "LIMIT_REACHED"`.  
**Orden:** Se asigna automáticamente como el siguiente número al conteo actual de reglas.  
**Resultado:** `201` con el número de `orden` asignado a la nueva regla.

======================================================================================================

## DELETE /api/community/rules/delete/\<regla_id\>
Elimina permanentemente una regla de la comunidad.

```json
// No requiere Body
{}
```

**Permisos:** Requiere rol `fundador` o `moderador` dentro de la comunidad a la que pertenece la regla.  
**Acción:** Hard delete — el registro se elimina físicamente de la base de datos con `db.session.delete`.

======================================================================================================

## PUT /api/community/rules/edit/\<regla_id\>
Edita el nombre o la descripción de una regla existente.

```json
{
    "nombre": "Nuevo nombre de la regla",
    "descripcion": "Nueva descripción detallada."
}
```

**Permisos:** Requiere rol `fundador` o `moderador` dentro de la comunidad a la que pertenece la regla.  
**Campos parciales:** Si solo se envía `nombre` o solo `descripcion`, el campo omitido conserva su valor anterior.  
**Resultado:** `200` con el objeto de la regla actualizada (`id`, `nombre`, `descripcion`).

======================================================================================================

## GET /api/community/\<comm_id\>/posts/count
Devuelve el conteo total de publicaciones activas en una comunidad.

```json
// No requiere Body
{}
```

**Filtro:** Solo cuenta publicaciones con `active = True` (excluye las eliminadas).  
**Resultado:** Objeto con `id_comunidad` y `total_posts`.

======================================================================================================

## GET /api/community/\<comm_id\>/feed
Devuelve el feed de publicaciones de una comunidad, ordenado del más reciente al más antiguo.

```json
// No requiere Body
{}
```

**Incluye por publicación:** `id_post`, `titulo`, `contenido`, `fecha`, `autor_id`, stats de `likes` y `karma`, e interacciones del usuario actual (`liked`, `saved`).  
**Interacción personalizada:** Consulta `Like_Post` y `Post_Guardado` para determinar si el usuario autenticado ya reaccionó a cada post.  

