from behave import given, when, then
from unittest.mock import MagicMock
from datetime import datetime

# Simulación de DB y logs
mock_db = {}
mock_logs = []
mock_archivos_guardados = []

# ------------------------
# Objetos simulados
# ------------------------

class MockEjercicioAsignado:
    def __init__(self, estudiante_id, ejercicio_id):
        self.id_estudiante = estudiante_id
        self.id_ejercicio = ejercicio_id
        self.contador = 0
        self.estado = False
        self.ultimo_envio = None
        self.fecha_ultimo_envio = None
        self.test_output = None

# ------------------------
# Simulaciones de funciones
# ------------------------

def sim_guardar_y_ejecutar_tests(archivos_java, ruta_ejercicio, resultado_simulado='BUILD SUCCESS'):
    ruta_final = ruta_ejercicio + '/src/main/java/org/example'
    for archivo in archivos_java:
        if archivo.filename.endswith('.java'):
            archivo.save(ruta_final + '/' + archivo.filename)
        else:
            mock_logs.append("Archivo inválido")
    if "invalida" in ruta_ejercicio:
        raise FileNotFoundError("Ruta inválida")
    return resultado_simulado, ruta_final

def sim_procesar_resultado_test(ejercicio, resultado_test, ruta_final):
    exito = resultado_test == 'BUILD SUCCESS'
    ejercicio.contador += 1
    ejercicio.ultimo_envio = ruta_final
    ejercicio.fecha_ultimo_envio = datetime.now()
    ejercicio.test_output = resultado_test
    ejercicio.estado = exito
    return {
        "tipo": "success" if exito else "danger",
        "titulo": "Todos los test aprobados" if exito else "Errores en la ejecución de pruebas unitarias",
        "mensaje": resultado_test
    }

def sim_crear_nuevo_ejercicio_asignado(estudiante_id, ejercicio_id):
    return MockEjercicioAsignado(estudiante_id, ejercicio_id)

# ------------------------
# Steps
# ------------------------

@given('que el estudiante ha subido archivos Java válidos')
def step_impl(context):
    archivo = MagicMock()
    archivo.filename = 'Main.java'
    archivo.save = lambda path: mock_archivos_guardados.append(path)
    context.archivos_java = [archivo]

@given('que el estudiante ha subido múltiples archivos Java válidos')
def step_impl(context):
    context.archivos_java = []
    for nombre in ['Main.java', 'Util.java', 'Test.java']:
        archivo = MagicMock()
        archivo.filename = nombre
        archivo.save = lambda path, nombre=nombre: mock_archivos_guardados.append(path)
        context.archivos_java.append(archivo)


@given('que existe una ruta válida para el ejercicio')
def step_impl(context):
    context.ruta_ejercicio = '/ruta/valida/ejercicio'


@given('que existe un ejercicio asignado con estado inicial')
def step_impl(context):
    context.ejercicio = sim_crear_nuevo_ejercicio_asignado(1, 101)

@given('que se conoce el ID del estudiante y el ID del ejercicio')
def step_impl(context):
    context.estudiante_id = 5
    context.ejercicio_id = 202

@given('que el resultado de prueba es "BUILD SUCCESS"')
def step_impl(context):
    context.resultado_test = 'BUILD SUCCESS'
    context.ruta_final = '/ruta/final'

@given('que el resultado de prueba contiene errores')
def step_impl(context):
    context.resultado_test = 'BUILD FAILURE'
    context.ruta_final = '/ruta/final'

@given('que la ruta del ejercicio está correctamente configurada')
def step_impl(context):
    context.ruta_ejercicio = '/ruta/valida/ejercicio'

@when('se guarda el archivo y se ejecutan las pruebas unitarias')
def step_impl(context):
    context.resultado, context.ruta_final = sim_guardar_y_ejecutar_tests(context.archivos_java, context.ruta_ejercicio)

@when('se ejecutan las pruebas y ocurre un error')
def step_impl(context):
    context.resultado, ruta_final = sim_guardar_y_ejecutar_tests(context.archivos_java, context.ruta_ejercicio, resultado_simulado='BUILD FAILURE')
    context.errores = sim_procesar_resultado_test(sim_crear_nuevo_ejercicio_asignado(1, 101), context.resultado, ruta_final)

@when('se procesa el resultado')
def step_impl(context):
    context.errores = sim_procesar_resultado_test(context.ejercicio, context.resultado_test, context.ruta_final)

@when('se llama a la función de creación')
def step_impl(context):
    context.nuevo = sim_crear_nuevo_ejercicio_asignado(context.estudiante_id, context.ejercicio_id)

@when('se procesa el archivo')
def step_impl(context):
    try:
        context.resultado, _ = sim_guardar_y_ejecutar_tests(context.archivos_java, '/ruta/carpeta')
    except Exception as e:
        context.resultado = str(e)

@when('se llama a la función de ejecución')
def step_impl(context):
    try:
        context.resultado, _ = sim_guardar_y_ejecutar_tests(context.archivos_java, context.ruta_ejercicio)
    except Exception as e:
        context.resultado = str(e)
        mock_logs.append(f"Error ejecutando pruebas: {e}")

@when('se guardan todos los archivos y se ejecutan los tests')
def step_impl(context):
    context.resultado, context.ruta_final = sim_guardar_y_ejecutar_tests(context.archivos_java, context.ruta_ejercicio)

@then('el sistema debe retornar "BUILD SUCCESS"')
def step_impl(context):
    assert context.resultado == 'BUILD SUCCESS'

@then('el sistema debe retornar un mensaje de error')
def step_impl(context):
    assert 'BUILD FAILURE' in context.errores['mensaje']

@then('debe marcar el estado del ejercicio como fallido')
def step_impl(context):
    assert context.errores['tipo'] == 'danger'

@then('debe registrar la ruta del último envío')
def step_impl(context):
    assert context.ruta_final.endswith('/src/main/java/org/example')

@then('debe actualizarse el estado del ejercicio a exitoso')
def step_impl(context):
    assert context.ejercicio.estado is True

@then('debe mostrarse un mensaje con tipo "success"')
def step_impl(context):
    assert context.errores['tipo'] == 'success'

@then('debe actualizarse el estado del ejercicio a fallido')
def step_impl(context):
    assert context.ejercicio.estado is False

@then('debe mostrarse un mensaje con tipo "danger"')
def step_impl(context):
    assert context.errores['tipo'] == 'danger'

@then('debe crearse un nuevo registro en la base de datos')
def step_impl(context):
    assert context.nuevo.id_estudiante == context.estudiante_id
    assert context.nuevo.id_ejercicio == context.ejercicio_id

@then('el contador debe iniciar en 0')
def step_impl(context):
    assert context.nuevo.contador == 0

@then('el estado debe ser "False"')
def step_impl(context):
    assert context.nuevo.estado is False

@then('no debe guardarse en el sistema')
def step_impl(context):
    assert len(mock_archivos_guardados) == 0

@then('debe mostrarse un mensaje de advertencia en el log')
def step_impl(context):
    assert "Archivo inválido" in mock_logs[-1]

@then('debe lanzarse una excepción')
def step_impl(context):
    assert "Ruta inválida" in context.resultado

@then('debe registrarse el error en los logs')
def step_impl(context):
    assert "Error ejecutando pruebas" in mock_logs[-1]

@then('todos los archivos deben guardarse en la ruta final')
def step_impl(context):
    for archivo in context.archivos_java:
        assert any(archivo.filename in path for path in mock_archivos_guardados)

@then('debe devolverse el resultado general de la ejecución')
def step_impl(context):
    assert context.resultado == 'BUILD SUCCESS'