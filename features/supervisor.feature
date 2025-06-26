Característica: Gestión de series, ejercicios y cursos por parte del supervisor
  Como supervisor
  Quiero gestionar series, ejercicios, cursos, grupos y estudiantes
  Para administrar eficazmente el proceso educativo

  Escenario: Acceder al panel de control del supervisor
    Dado que existe un supervisor con ID 1 autenticado
    Y que existen cursos, series y grupos en la base de datos
    Cuando el supervisor accede a su panel de control
    Entonces el sistema debe mostrar la página del panel
    Y debe mostrar la lista de cursos disponibles
    Y debe mostrar la lista de series disponibles

  Escenario: Asignar una serie a un grupo exitosamente
    Dado que existe un supervisor con ID 1 autenticado
    Y que existe una serie con ID 1 y un grupo con ID 1
    Cuando el supervisor asigna la serie al grupo
    Entonces el sistema debe registrar la asignación en la base de datos
    Y debe mostrar un mensaje de tipo "success"

  Escenario: Error al asignar una serie sin seleccionar grupo
    Dado que existe un supervisor con ID 1 autenticado
    Y que existe una serie con ID 1
    Y que no se selecciona un grupo
    Cuando el supervisor intenta asignar la serie
    Entonces el sistema no debe registrar la asignación
    Y debe mostrar un mensaje de tipo "danger"

  Escenario: Crear una nueva serie exitosamente
    Dado que existe un supervisor con ID 1 autenticado
    Y que se proporciona un nombre válido para la serie
    Cuando el supervisor crea una nueva serie
    Entonces el sistema debe crear un nuevo registro de serie en la base de datos
    Y debe crear una carpeta para la serie
    Y debe mostrar un mensaje de tipo "success"

  Escenario: Error al crear una serie sin nombre
    Dado que existe un supervisor con ID 1 autenticado
    Y que no se proporciona un nombre para la serie
    Cuando el supervisor intenta crear una nueva serie
    Entonces el sistema no debe crear el registro
    Y debe mostrar un mensaje de tipo "danger"

  Escenario: Agregar un nuevo ejercicio con archivos válidos
    Dado que existe un supervisor con ID 1 autenticado
    Y que existe una serie con ID 1
    Y que se han subido un archivo markdown válido y un archivo Java válido
    Cuando el supervisor agrega un nuevo ejercicio
    Entonces el sistema debe guardar los archivos en la ruta correcta
    Y debe crear un nuevo registro de ejercicio en la base de datos
    Y debe mostrar un mensaje de tipo "success"

  Escenario: Error al agregar ejercicio con archivo Java no válido
    Dado que existe un supervisor con ID 1 autenticado
    Y que existe una serie con ID 1
    Y que se ha subido un archivo con extensión incorrecta
    Cuando el supervisor intenta agregar un nuevo ejercicio
    Entonces el sistema no debe guardar los archivos
    Y debe mostrar un mensaje de tipo "danger"

  Escenario: Actualizar la contraseña del supervisor exitosamente
    Dado que existe un supervisor con ID 1 autenticado
    Y que se proporciona una contraseña actual correcta y una nueva contraseña válida
    Cuando el supervisor actualiza su contraseña
    Entonces el sistema debe actualizar la contraseña en la base de datos
    Y debe mostrar un mensaje de tipo "success"

  Escenario: Error al actualizar contraseña con contraseña actual incorrecta
    Dado que existe un supervisor con ID 1 autenticado
    Y que se proporciona una contraseña actual incorrecta
    Cuando el supervisor intenta actualizar su contraseña
    Entonces el sistema no debe actualizar la contraseña
    Y debe mostrar un mensaje de tipo "danger"

  Escenario: Eliminar una serie existente exitosamente
    Dado que existe un supervisor con ID 1 autenticado
    Y que existe una serie con ID 1 con ejercicios asociados
    Cuando el supervisor elimina la serie
    Entonces el sistema debe eliminar el registro de la serie y sus ejercicios
    Y debe eliminar las carpetas asociadas
    Y debe mostrar un mensaje de tipo "success"

  Escenario: Error al eliminar una serie con problemas de base de datos
    Dado que existe un supervisor con ID 1 autenticado
    Y que existe una serie con ID 1 con ejercicios asociados
    Y que ocurre un error en la base de datos
    Cuando el supervisor intenta eliminar la serie
    Entonces el sistema no debe eliminar el registro
    Y debe mostrar un mensaje de tipo "danger"

  Escenario: Crear un nuevo curso exitosamente
    Dado que existe un supervisor con ID 1 autenticado
    Y que se proporciona un nombre válido para el curso
    Cuando el supervisor crea un nuevo curso
    Entonces el sistema debe crear un nuevo registro de curso en la base de datos
    Y debe mostrar un mensaje de tipo "success"

  Escenario: Asignar estudiantes a un grupo exitosamente
    Dado que existe un supervisor con ID 1 autenticado
    Y que existe un curso con ID 1 y un estudiante con ID 1
    Y que se proporciona un nombre válido para el grupo
    Cuando el supervisor asigna el estudiante a un grupo
    Entonces el sistema debe registrar la asignación en la base de datos
    Y debe mostrar un mensaje de tipo "success"

  Escenario: Examinar la entrega de un ejercicio por un estudiante
    Dado que existe un supervisor con ID 1 autenticado
    Y que existe una entrega de ejercicio para el estudiante con ID 1 y ejercicio con ID 1
    Cuando el supervisor examina la entrega
    Entonces el sistema debe mostrar los detalles de la entrega
    Y debe mostrar el enunciado del ejercicio
    Y debe mostrar los archivos Java enviados