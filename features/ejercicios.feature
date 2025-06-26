Característica: Gestión de ejercicios y pruebas unitarias
  Como estudiante
  Quiero guardar ejercicios, ejecutar pruebas y registrar sus resultados
  Para hacer seguimiento del avance y desempeño del estudiante

  Escenario: Guardar archivos Java y ejecutar pruebas exitosamente
    Dado que el estudiante ha subido archivos Java válidos
    Y que existe una ruta válida para el ejercicio
    Cuando se guarda el archivo y se ejecutan las pruebas unitarias
    Entonces el sistema debe retornar "BUILD SUCCESS"
    Y debe registrar la ruta del último envío

  Escenario: Ejecutar pruebas con errores
    Dado que el estudiante ha subido archivos Java válidos
    Y que existe una ruta válida para el ejercicio
    Cuando se ejecutan las pruebas y ocurre un error
    Entonces el sistema debe retornar un mensaje de error
    Y debe marcar el estado del ejercicio como fallido

  Escenario: Procesar resultado de pruebas exitosas
    Dado que existe un ejercicio asignado con estado inicial
    Y que el resultado de prueba es "BUILD SUCCESS"
    Cuando se procesa el resultado
    Entonces debe actualizarse el estado del ejercicio a exitoso
    Y debe mostrarse un mensaje con tipo "success"

  Escenario: Procesar resultado de pruebas con fallas
    Dado que existe un ejercicio asignado con estado inicial
    Y que el resultado de prueba contiene errores
    Cuando se procesa el resultado
    Entonces debe actualizarse el estado del ejercicio a fallido
    Y debe mostrarse un mensaje con tipo "danger"

  Escenario: Crear un nuevo ejercicio asignado
    Dado que se conoce el ID del estudiante y el ID del ejercicio
    Cuando se llama a la función de creación
    Entonces debe crearse un nuevo registro en la base de datos
    Y el contador debe iniciar en 0
    Y el estado debe ser "False"

  Escenario: Error al guardar archivo Java no válido
    Dado que el estudiante intenta subir un archivo con extensión incorrecta
    Cuando se procesa el archivo
    Entonces no debe guardarse en el sistema
    Y debe mostrarse un mensaje de advertencia en el log

  Escenario: Error al ejecutar pruebas por ruta inexistente
    Dado que el sistema intenta ejecutar pruebas en una ruta inválida
    Cuando se llama a la función de ejecución
    Entonces debe lanzarse una excepción
    Y debe registrarse el error en los logs

  Escenario: Guardar múltiples archivos y ejecutar tests
    Dado que el estudiante ha subido múltiples archivos Java válidos
    Y que la ruta del ejercicio está correctamente configurada
    Cuando se guardan todos los archivos y se ejecutan los tests
    Entonces todos los archivos deben guardarse en la ruta final
    Y debe devolverse el resultado general de la ejecución
