from behave import given, when, then
from unittest import mock
from app import create_app, db
from app.models import Ejercicio_asignado
from app.main import guardar_y_ejecutar_tests, procesar_resultado_test, crear_nuevo_ejercicio_asignado
import os
import shutil
from werkzeug.utils import secure_filename

# Crear la aplicación Flask para pruebas
app = create_app('testing')  # Asume una configuración 'testing' en tu app
app.config['WTF_CSRF_ENABLED'] = False  # Deshabilitar CSRF para pruebas
app.config['UPLOAD_FOLDER'] = 'tests/tmp'  # Carpeta temporal para pruebas

# Configuración inicial para cada escenario
def before_scenario(context):
    context.client = app.test_client()
    context.db = db
    with app.app_context():
        db.create_all()
    # Asegurar que la carpeta temporal esté limpia
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        shutil.rmtree(app.config['UPLOAD_FOLDER'])
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def after_scenario(context):
    with app.app_context():
        db.drop_all()
    # Limpiar carpetas temporales
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        shutil.rmtree(app.config['UPLOAD_FOLDER'])

# ---------- Escenario: Guardar y ejecutar pruebas unitarias con éxito ----------

@given('que el estudiante ha subido archivos Java válidos')
def step_archivos_java_validos(context):
    # Simular un archivo Java válido
    mock_file = mock.MagicMock()
    mock_file.filename = "Main.java"
    mock_file.read.return_value = b"public class Main { public static void main(String[] args) {} }"
    context.archivos = [mock_file]

@given('que existe una ruta válida para el ejercicio')
def step_ruta_valida(context):
    context.ruta = os.path.join(app.config['UPLOAD_FOLDER'], "ejercicio_101")
    os.makedirs(context.ruta, exist_ok=True)

@when('se guarda el archivo y se ejecutan las pruebas unitarias')
def step_guardar_y_test(context):
    with mock.patch("app.main.ejecutarTestUnitario", return_value="BUILD SUCCESS"):
        context.resultado, context.ruta_final = guardar_y_ejecutar_tests(context.archivos, context.ruta)

@then('el sistema debe retornar "BUILD SUCCESS"')
def step_assert_exito(context):
    assert context.resultado == "BUILD SUCCESS", f"Esperado 'BUILD SUCCESS', pero se obtuvo '{context.resultado}'"

@then('debe registrar la ruta del último envío')
def step_assert_ruta_guardada(context):
    assert context.ruta_final is not None, "La ruta del último envío no se registró"
    assert os.path.exists(context.ruta_final), f"La carpeta {context.ruta_final} no existe"
    # Verificar que el archivo Java se guardó
    archivo_guardado = os.path.join(context.ruta_final, secure_filename(context.archivos[0].filename))
    assert os.path.exists(archivo_guardado), f"El archivo {archivo_guardado} no se guardó"

# ---------- Escenario: Ejecutar pruebas con errores ----------

@when('se ejecutan las pruebas y ocurre un error')
def step_error_en_tests(context):
    with mock.patch("app.main.ejecutarTestUnitario", return_value="BUILD FAILED"):
        context.resultado, context.ruta_final = guardar_y_ejecutar_tests(context.archivos, context.ruta)

@then('el sistema debe retornar un mensaje de error')
def step_mensaje_error(context):
    assert context.resultado == "BUILD FAILED", f"Esperado 'BUILD FAILED', pero se obtuvo '{context.resultado}'"

@then('debe marcar el estado del ejercicio como fallido')
def step_estado_fallido(context):
    with app.app_context():
        ejercicio_asignado = mock.MagicMock()
        ejercicio_asignado.estado = False
        errores = procesar_resultado_test(ejercicio_asignado, context.resultado, context.ruta_final)
        assert errores["tipo"] == "danger", f"Esperado mensaje de tipo 'danger', pero se obtuvo '{errores['tipo']}'"
        assert ejercicio_asignado.estado is False, "El estado del ejercicio debería ser False"

# ---------- Escenario: Procesar resultado exitoso ----------

@given('que existe un ejercicio asignado con estado inicial')
def step_mock_ejercicio(context):
    with app.app_context():
        context.ejercicio_asignado = Ejercicio_asignado(
            id_estudiante=1,
            id_ejercicio=101,
            estado=False,
            contador=0,
            ultimo_envio="",
            test_output="{}"
        )
        db.session.add(context.ejercicio_asignado)
        db.session.commit()

@given('que el resultado de prueba es "BUILD SUCCESS"')
def step_resultado_success(context):
    context.resultado = "BUILD SUCCESS"
    context.ruta_final = os.path.join(app.config['UPLOAD_FOLDER'], "ejercicio_101")

@when('se procesa el resultado')
def step_procesar_resultado(context):
    with app.app_context():
        context.errores = procesar_resultado_test(context.ejercicio_asignado, context.resultado, context.ruta_final)

@then('debe actualizarse el estado del ejercicio a exitoso')
def step_estado_exitoso(context):
    with app.app_context():
        db.session.refresh(context.ejercicio_asignado)
        assert context.ejercicio_asignado.estado is True, "El estado del ejercicio debería ser True"

@then('debe mostrarse un mensaje con tipo "success"')
def step_tipo_success(context):
    assert context.errores["tipo"] == "success", f"Esperado mensaje de tipo 'success', pero se obtuvo '{context.errores['tipo']}'"

# ---------- Escenario: Crear ejercicio asignado ----------

@given('que se conoce el ID del estudiante y el ID del ejercicio')
def step_ids_conocidos(context):
    context.id_estudiante = 1
    context.id_ejercicio = 101

@when('se llama a la función de creación')
def step_crear_ejercicio(context):
    with app.app_context():
        with mock.patch("app.main.db.session.add"), mock.patch("app.main.db.session.flush"):
            context.ejercicio_nuevo = crear_nuevo_ejercicio_asignado(context.id_estudiante, context.id_ejercicio)

@then('debe crearse un nuevo registro en la base de datos')
def step_creado(context):
    assert context.ejercicio_nuevo.id_estudiante == context.id_estudiante, "El ID del estudiante no coincide"
    assert context.ejercicio_nuevo.id_ejercicio == context.id_ejercicio, "El ID del ejercicio no coincide"

@then('el contador debe iniciar en 0')
def step_contador_cero(context):
    assert context.ejercicio_nuevo.contador == 0, f"Esperado contador 0, pero se obtuvo {context.ejercicio_nuevo.contador}"

@then('el estado debe ser "False"')
def step_estado_false(context):
    assert context.ejercicio_nuevo.estado is False, f"Esperado estado False, pero se obtuvo {context.ejercicio_nuevo.estado}"