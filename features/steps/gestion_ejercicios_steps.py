from behave import given, when, then
import os
import shutil
import json

# Simulación de respuestas HTTP
class MockResponse:
    def __init__(self, status_code=200, location=None, data=b''):
        self.status_code = status_code
        self.location = location
        self.data = data

# Datos de prueba guardados en memoria
test_data = {
    'ejercicios_asignados': {}
}

# Configuración de la aplicación simulada
app_config = {
    'UPLOAD_FOLDER': 'tests/tmp'
}

# Configuración inicial para cada escenario
def before_scenario(context):
    context.client = MockClient()  # Cliente simulado
    test_data['ejercicios_asignados'] = {}  # Limpiar datos en memoria
    # Asegurar que la carpeta temporal esté limpia
    if os.path.exists(app_config['UPLOAD_FOLDER']):
        shutil.rmtree(app_config['UPLOAD_FOLDER'])
    os.makedirs(app_config['UPLOAD_FOLDER'], exist_ok=True)

def after_scenario(context):
    # Limpiar carpetas temporales
    if os.path.exists(app_config['UPLOAD_FOLDER']):
        shutil.rmtree(app_config['UPLOAD_FOLDER'])

# Cliente HTTP simulado
class MockClient:
    def post(self, url, data=None, content_type=None):
        if 'guardar_y_ejecutar' in url:
            if data.get('resultado') == 'BUILD SUCCESS':
                return MockResponse(200, data=b'Successful test execution')
            return MockResponse(200, data=b'Test execution failed')
        elif 'procesar_resultado' in url:
            return MockResponse(200, data=b'Successful test processing')
        elif 'crear_ejercicio' in url:
            return MockResponse(201, data=b'Ejercicio asignado creado')
        return MockResponse(200, data=b'Unknown action')

# Simulación de funciones de la aplicación
def guardar_y_ejecutar_tests(archivos, ruta):
    ruta_final = os.path.join(ruta, "ultimo_envio")
    os.makedirs(ruta_final, exist_ok=True)
    for archivo in archivos:
        filename = archivo['filename']
        contenido = archivo['contenido']
        if filename.endswith('.java'):
            with open(os.path.join(ruta_final, filename), 'wb') as f:
                f.write(contenido)
    resultado = "BUILD SUCCESS" if all(f['filename'].endswith('.java') for f in archivos) else "BUILD FAILED"
    return resultado, ruta_final

def procesar_resultado_test(ejercicio_asignado, resultado, ruta_final):
    ejercicio_asignado['estado'] = (resultado == "BUILD SUCCESS")
    ejercicio_asignado['ultimo_envio'] = ruta_final
    ejercicio_asignado['test_output'] = json.dumps({"result": resultado})
    return {"tipo": "success" if resultado == "BUILD SUCCESS" else "danger", "mensaje": resultado}

def crear_nuevo_ejercicio_asignado(id_estudiante, id_ejercicio):
    return {
        'id_estudiante': id_estudiante,
        'id_ejercicio': id_ejercicio,
        'estado': False,
        'contador': 0,
        'ultimo_envio': '',
        'test_output': '{}'
    }

# Escenario: Guardar y ejecutar pruebas unitarias con éxito
@given('que el estudiante ha subido archivos Java válidos')
def step_archivos_java_validos(context):
    context.archivos = [
        {'filename': 'Main.java', 'contenido': b'public class Main { public static void main(String[] args) {} }'}
    ]

@given('que existe una ruta válida para el ejercicio')
def step_ruta_valida(context):
    context.ruta = os.path.join(app_config['UPLOAD_FOLDER'], "ejercicio_101")
    os.makedirs(context.ruta, exist_ok=True)

@when('se guarda el archivo y se ejecutan las pruebas unitarias')
def step_guardar_y_test(context):
    context.resultado, context.ruta_final = guardar_y_ejecutar_tests(context.archivos, context.ruta)
    context.response = context.client.post(
        '/guardar_y_ejecutar',
        data={'resultado': context.resultado}
    )

@then('el sistema debe retornar "BUILD SUCCESS"')
def step_assert_exito(context):
    assert context.resultado == "BUILD SUCCESS", f"Esperado 'BUILD SUCCESS', pero se obtuvo '{context.resultado}'"

@then('debe registrar la ruta del último envío')
def step_assert_ruta_guardada(context):
    assert context.ruta_final is not None, "La ruta del último envío no se registró"
    assert os.path.exists(context.ruta_final), f"La carpeta {context.ruta_final} no existe"
    archivo_guardado = os.path.join(context.ruta_final, context.archivos[0]['filename'])
    assert os.path.exists(archivo_guardado), f"El archivo {archivo_guardado} no se guardó"

# Escenario: Ejecutar pruebas con errores
@when('se ejecutan las pruebas y ocurre un error')
def step_error_en_tests(context):
    context.archivos = [
        {'filename': 'Main.txt', 'contenido': b'public class Main { public static void main(String[] args) {} }'}
    ]
    context.resultado, context.ruta_final = guardar_y_ejecutar_tests(context.archivos, context.ruta)
    context.response = context.client.post(
        '/guardar_y_ejecutar',
        data={'resultado': context.resultado}
    )

@then('el sistema debe retornar un mensaje de error')
def step_mensaje_error(context):
    assert context.resultado == "BUILD FAILED", f"Esperado 'BUILD FAILED', pero se obtuvo '{context.resultado}'"

@then('debe marcar el estado del ejercicio como fallido')
def step_estado_fallido(context):
    ejercicio_id = 'ejercicio_101'
    test_data['ejercicios_asignados'][ejercicio_id] = {
        'id_estudiante': 1,
        'id_ejercicio': 101,
        'estado': False,
        'contador': 0,
        'ultimo_envio': '',
        'test_output': '{}'
    }
    ejercicio_asignado = test_data['ejercicios_asignados'][ejercicio_id]
    errores = procesar_resultado_test(ejercicio_asignado, context.resultado, context.ruta_final)
    assert errores["tipo"] == "danger", f"Esperado mensaje de tipo 'danger', pero se obtuvo '{errores['tipo']}'"
    assert test_data['ejercicios_asignados'][ejercicio_id]['estado'] is False, "El estado del ejercicio debería ser False"

# Escenario: Procesar resultado exitoso
@given('que existe un ejercicio asignado con estado inicial')
def step_mock_ejercicio(context):
    ejercicio_id = 'ejercicio_101'
    test_data['ejercicios_asignados'][ejercicio_id] = {
        'id_estudiante': 1,
        'id_ejercicio': 101,
        'estado': False,
        'contador': 0,
        'ultimo_envio': '',
        'test_output': '{}'
    }
    context.ejercicio_asignado = test_data['ejercicios_asignados'][ejercicio_id]
    context.ejercicio_id = ejercicio_id

@given('que el resultado de prueba es "BUILD SUCCESS"')
def step_resultado_success(context):
    context.resultado = "BUILD SUCCESS"
    context.ruta_final = os.path.join(app_config['UPLOAD_FOLDER'], "ejercicio_101")

@when('se procesa el resultado')
def step_procesar_resultado(context):
    context.errores = procesar_resultado_test(context.ejercicio_asignado, context.resultado, context.ruta_final)
    context.response = context.client.post(
        '/procesar_resultado',
        data={'resultado': context.resultado}
    )

@then('debe actualizarse el estado del ejercicio a exitoso')
def step_estado_exitoso(context):
    assert test_data['ejercicios_asignados'][context.ejercicio_id]['estado'] is True, "El estado del ejercicio debería ser True"

@then('debe mostrarse un mensaje con tipo "success"')
def step_tipo_success(context):
    assert context.errores["tipo"] == "success", f"Esperado mensaje de tipo 'success', pero se obtuvo '{context.errores['tipo']}'"

# Escenario: Crear ejercicio asignado
@given('que se conoce el ID del estudiante y el ID del ejercicio')
def step_ids_conocidos(context):
    context.id_estudiante = 1
    context.id_ejercicio = 101

@when('se llama a la función de creación')
def step_crear_ejercicio(context):
    context.ejercicio_nuevo = crear_nuevo_ejercicio_asignado(context.id_estudiante, context.id_ejercicio)
    ejercicio_id = f"ejercicio_{context.id_ejercicio}"
    test_data['ejercicios_asignados'][ejercicio_id] = {
        'id_estudiante': context.id_estudiante,
        'id_ejercicio': context.id_ejercicio,
        'estado': context.ejercicio_nuevo['estado'],
        'contador': context.ejercicio_nuevo['contador'],
        'ultimo_envio': context.ejercicio_nuevo['ultimo_envio'],
        'test_output': context.ejercicio_nuevo['test_output']
    }
    context.response = context.client.post(
        '/crear_ejercicio',
        data={'id_estudiante': context.id_estudiante, 'id_ejercicio': context.id_ejercicio}
    )

@then('debe crearse un nuevo registro en la base de datos')
def step_creado(context):
    ejercicio_id = f"ejercicio_{context.id_ejercicio}"
    assert test_data['ejercicios_asignados'][ejercicio_id]['id_estudiante'] == context.id_estudiante, "El ID del estudiante no coincide"
    assert test_data['ejercicios_asignados'][ejercicio_id]['id_ejercicio'] == context.id_ejercicio, "El ID del ejercicio no coincide"

@then('el contador debe iniciar en 0')
def step_contador_cero(context):
    ejercicio_id = f"ejercicio_{context.id_ejercicio}"
    assert test_data['ejercicios_asignados'][ejercicio_id]['contador'] == 0, f"Esperado contador 0, pero se obtuvo {test_data['ejercicios_asignados'][ejercicio_id]['contador']}"

@then('el estado debe ser "False"')
def step_estado_false(context):
    ejercicio_id = f"ejercicio_{context.id_ejercicio}"
    assert test_data['ejercicios_asignados'][ejercicio_id]['estado'] is False, f"Esperado estado False, pero se obtuvo {test_data['ejercicios_asignados'][ejercicio_id]['estado']}"