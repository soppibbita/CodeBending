
Característica: Registro y asignación de estudiantes a grupos
  Como supervisor
  Quiero registrar estudiantes desde un archivo CSV y asignarlos a grupos
  Para que puedan acceder al sistema y trabajar en sus ejercicios

  Escenario: Registrar un estudiante desde archivo CSV válido
    Dado que el supervisor ha iniciado sesión
    Y que existe un curso activo
    Cuando sube un archivo CSV con datos de un nuevo estudiante
    Entonces el estudiante debe registrarse en la base de datos
    Y debe inscribirse en el curso

  Escenario: Reintentar registrar estudiante ya existente
    Dado que el supervisor ha iniciado sesión
    Y que existe un curso activo
    Y que ya existe un estudiante con la misma matrícula en el sistema
    Cuando sube un archivo CSV con ese estudiante para el mismo curso
    Entonces el sistema no debe duplicar al estudiante
    Y no debe volver a inscribirlo si ya está en el curso

  Escenario: Crear un grupo y asignar estudiantes inscritos
    Dado que el supervisor ha iniciado sesión
    Y que existe un curso activo
    Y que tiene estudiantes inscritos en un curso
    Cuando crea un nuevo grupo y selecciona estudiantes
    Entonces el grupo debe registrarse en la base de datos
    Y los estudiantes deben asociarse al grupo
    Y el grupo debe asociarse al supervisor

  Escenario: Subir CSV con fila malformada
    Dado que el supervisor ha iniciado sesión
    Y que existe un curso activo
    Cuando sube un archivo CSV con una fila con campos faltantes
    Entonces debe verse un mensaje de advertencia en el log
    Y los estudiantes bien formateados deben registrarse normalmente

  Escenario: Crear grupo sin nombre
    Dado que el supervisor ha iniciado sesión
    Y que existe un curso activo
    Cuando intenta crear un grupo sin especificar nombre
    Entonces debe mostrarse un mensaje de error
    Y el grupo no debe ser creado

  Escenario: Crear grupo sin seleccionar estudiantes
    Dado que el supervisor ha iniciado sesión
    Y que existe un curso activo
    Y que tiene estudiantes disponibles
    Cuando crea un grupo sin seleccionar estudiantes
    Entonces debe mostrarse un mensaje de advertencia
    Y el grupo no debe quedar asociado a estudiantes

  Escenario: Reasignar estudiante a mismo grupo
    Dado que el supervisor ha iniciado sesión
    Y que existe un curso activo
    Y que un estudiante ya está asignado a un grupo
    Cuando intenta asignarlo al mismo grupo nuevamente
    Entonces el sistema debe evitar la duplicación en la relación

  Escenario: Falla en base de datos al registrar estudiante
    Dado que el supervisor ha iniciado sesión
    Y que existe un curso activo
    Y que ocurre un error simulado en la base de datos
    Cuando sube un archivo CSV con un estudiante
    Entonces debe mostrarse un mensaje de error
    Y el estudiante no debe registrarse
