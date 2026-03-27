
### POST /auth/login
Valida credenciales y activa la sesión en el servidor, generando las llaves de acceso.

	{
	    "email": "",
	    "password": ""
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

Validación Apellido2: Puede ir vacío ("") o ser omitido sin causar error, ya que es opcional en el modelo.
Validación Email: El controlador utiliza Regex para asegurar que el formato sea válido (ej. @gmail.com).
Seguridad: Verifica que las contraseñas coincidan y las guarda usando un hash pbkdf2:sha256.

======================================================================================================

### POST /auth/logout
Cierra la sesión y limpia físicamente el rastro de tokens en la base de datos.

	// No requiere Body
	{} 

Requisito: Debe llevar la cookie de sesión activa 
Validación: El decorador @auth_required bloquea la petición con un 401 Unauthorized si no hay una sesión activa.
Acción Red Team: Ejecuta un DELETE en la tabla oauth2token de Supabase para invalidar cualquier posibilidad de reutilizar los tokens robados.

======================================================================================================

### POST /auth/renew

Extiende la sesión del usuario intercambiando un token por expirar por uno nuevo.

	{
	    "refresh_token": ""
	}

Funcionamiento: El servidor busca el refresh_token exacto en Supabase. Si existe, genera un nuevo par de tokens y actualiza la base de datos.
Rotación de Tokens: Al generar tokens nuevos, el anterior queda invalidado inmediatamente. Si se intenta usar un token viejo o incompleto, el servidor responde con un 401.
Propósito: Permite mantener al usuario conectado sin pedir credenciales constantemente, manteniendo una ventana de exposición corta para el access_token.


======================================================================================================


