
### POST /auth/login
Valida credenciales y activa la sesión en el servidor, generando las llaves de acceso.

	{
	    "email": "",
	    "password": ""
	}

# Regresa 200 

{
  "msg": "Login exitoso", 
  "user": {
    "email": "",
    "nombre": ""
  }
}
# 401 / invalidas

{
  "error": "Credenciales inválidas"
}

Funcionamiento: Compara el hash de la base de datos con el password enviado. Al ser exitoso, activa security_login_user(user) y genera un objeto tokens con el access_token y refresh_token.
Resultado: Recibes los tokens necesarios para realizar peticiones protegidas y para el proceso de renovación.

======================================================================================================

### POST /auth/register
Crea la cuenta del usuario con validaciones de identidad y seguridad.

	    {
        		"nombre": "",
        		"apellido1": "",
        		"apellido2": "", 
        		"email": "",
        		"password": "",
        		"password_confirm": ""
	    }
### Exitoso 200
[
  {
    "email": "",
    "status": "registrado"
  },
  201
]

### error 200
[
  {
    "error": "Faltan datos obligatorios"
  },
  400
]

### Error 

[
  {
    "error": "El correo ya está registrado"
  },
  400
]


Validación Apellido2: Puede ir vacío ("") o ser omitido sin causar error, ya que es opcional en el modelo.
Validación Email: El controlador utiliza Regex para asegurar que el formato sea válido (ej. @gmail.com).
Seguridad: Verifica que las contraseñas coincidan y las guarda usando un hash pbkdf2:sha256.

======================================================================================================

### POST /auth/logout
Cierra la sesión y limpia físicamente el rastro de tokens en la base de datos.

	// No requiere Body
	{} 

### EXitoso 200
    {
          "msg": "Sesión cerrada y tokens invalidados con éxito"
    }
### Error 401
{
  "meta": {
    "code": 401
  },
  "response": {
    "errors": [
      "You must sign in to view this resource."
    ]
  }
}
Requisito: Debe llevar la cookie de sesión activa 
Validación: El decorador @auth_required bloquea la petición con un 401 Unauthorized si no hay una sesión activa.
Acción Red Team: Ejecuta un DELETE en la tabla oauth2token de Supabase para invalidar cualquier posibilidad de reutilizar los tokens robados.

======================================================================================================

### POST /auth/renew

Extiende la sesión del usuario intercambiando un token por expirar por uno nuevo.

	{
	    "refresh_token": ""
	}

### Exitoso 200
{
  "status": "success",
  "tokens": {
    "access_token": "",
    "expires_in": 3600,
    "refresh_token": "",
    "token_type": "Bearer"
  }
}
### cierra sesion 
{
  "error": "Token no encontrado o ya fue invalidado"
}



Funcionamiento: El servidor busca el refresh_token exacto en Supabase. Si existe, genera un nuevo par de tokens y actualiza la base de datos.
Rotación de Tokens: Al generar tokens nuevos, el anterior queda invalidado inmediatamente. Si se intenta usar un token viejo o incompleto, el servidor responde con un 401.
Propósito: Permite mantener al usuario conectado sin pedir credenciales constantemente, manteniendo una ventana de exposición corta para el access_token.


======================================================================================================

### POST /auth/pswdreset

Consume el token de seguridad enviado por correo para sobreescribir la credencial del usuario.

{
  "token": "",
  "new_password": "",
  "password_confirm": ""
}

### Exitoso 200
{
  "msg": "Contraseña actualizada correctamente"
}

### Error 400
{
  "error": "Token inválido o expirado"
}

Funcionamiento: Valida que el token coincida con el almacenado en Supabase y que no haya superado el tiempo de vida (15 min). Si es correcto, hashea la nueva clave con pbkdf2:sha256.
Seguridad Post-Acción: Una vez actualizada la contraseña, el token de recuperación se destruye físicamente de la base de datos para prevenir ataques de reutilización.
Propósito: Permitir al usuario recuperar el acceso a su cuenta de forma segura y autónoma, manteniendo la integridad del sistema de autenticación.

======================================================================================================

### POST /auth/pswdrecover

Inicia el flujo de recuperación mediante validación de identidad por correo electrónico.

{
  "email": ""
}

### Exitoso 200

{
  "msg": "Si el correo existe en nuestro sistema, recibirás un enlace de recuperación."
}

### Error 400

{
  "error": "El email es requerido"
}

Funcionamiento: El servidor genera un token criptográfico único con una validez de 15 minutos y lo envía a la bandeja de entrada del usuario a través de Flask-Mail.
Seguridad (Anti-Enumeración): La respuesta es siempre la misma, exista o no el correo en la base de datos, para evitar que atacantes identifiquen cuentas válidas.
Propósito: Validar que quien solicita el cambio de clave tiene acceso real a la cuenta de correo vinculada, sin exponer datos sensibles en el proceso.

======================================================================================================

### GET /auth/check-session
Valida la persistencia de la identidad y la integridad de los tokens de sesión activos en el navegador.
Headers Requeridos:
Cookie: access_token=<jwt_o_uuid_token>
### Exitoso 200
{
  "status": "online",
  "user": {
    "email": "",
    "nombre": ""
  }
}

### Error 401
{
"error": "No hay sesión activa (Falta access_token)" o "Tu sesión ha expirado"
}

Funcionamiento: El decorador @token_required intercepta la petición, extrae el token de la cookie access_token y realiza una búsqueda de coincidencia exacta en la tabla public.oauth2token.
Seguridad (Persistencia): Se valida el timestamp expires_at contra el tiempo real del servidor. Si el token es válido, se inyecta el objeto de usuario completo en el contexto de la petición actual.
Propósito: Permitir al frontend (o cliente) confirmar si el usuario tiene permisos vigentes antes de renderizar componentes protegidos o realizar peticiones de datos privados.



