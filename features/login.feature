
Característica: Autenticación de usuarios
  Como usuario del sistema
  Quiero poder iniciar sesión con mis credenciales
  Para acceder a mis funcionalidades según mi rol

  Antecedentes:
    Dado que estoy en la página de inicio de sesión

  Escenario: Login exitoso de estudiante
    Dado que existe un estudiante con correo "juan.perez@universidad.edu" y contraseña "password123"
    Cuando ingreso el correo "juan.perez@universidad.edu"
    Y ingreso la contraseña "password123"
    Y hago clic en el botón de iniciar sesión
    Entonces debo ser redirigido al dashboard del estudiante
    Y debo ver el mensaje "Has iniciado sesión exitosamente"

  Escenario: Login exitoso de supervisor
    Dado que existe un supervisor con correo "prof.garcia@universidad.edu" y contraseña "supervisor123"
    Cuando ingreso el correo "prof.garcia@universidad.edu"
    Y ingreso la contraseña "supervisor123"
    Y hago clic en el botón de iniciar sesión
    Entonces debo ser redirigido al dashboard del supervisor
    Y debo ver el mensaje "Has iniciado sesión exitosamente"

  Escenario: Login con credenciales incorrectas
    Dado que existe un estudiante con correo "maria.lopez@universidad.edu" y contraseña "correcta123"
    Cuando ingreso el correo "maria.lopez@universidad.edu"
    Y ingreso la contraseña "incorrecta999"
    Y hago clic en el botón de iniciar sesión
    Entonces debo permanecer en la página de login
    Y debo ver el mensaje "Credenciales inválidas"

  Escenario: Login con correo no registrado
    Cuando ingreso el correo "noexiste@universidad.edu"
    Y ingreso la contraseña "cualquiera123"
    Y hago clic en el botón de iniciar sesión
    Entonces debo permanecer en la página de login
    Y debo ver el mensaje "Credenciales inválidas"

  Escenario: Login con campos vacíos
    Cuando dejo el campo de correo vacío
    Y dejo el campo de contraseña vacío
    Y hago clic en el botón de iniciar sesión
    Entonces debo permanecer en la página de login
    Y los campos requeridos deben mostrar validación

  Escenario: Logout exitoso
    Dado que he iniciado sesión como estudiante
    Cuando hago clic en cerrar sesión
    Entonces debo ser redirigido a la página de login
    Y debo ver el mensaje "Sesión cerrada"

  Escenario: Acceso directo cuando ya está autenticado
    Dado que ya he iniciado sesión como estudiante
    Cuando intento acceder a la página de login
    Entonces debo ser redirigido automáticamente a mi dashboard de estudiante