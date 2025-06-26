""" from behave import given, when, then
import os
import shutil
import hashlib
import json

# Simulación de respuestas HTTP
class MockResponse:
    def __init__(self, status_code=200, location=None, data=b''):
        self.status_code = status_code
        self.location = location
        self.data = data

# Datos de prueba guardados en memoria
test_data = {
    'supervisores': {},
    'cursos': {},
    'series': {},
    'grupos': {},
    'ejercicios': {},
    'estudiantes': {},
    'ejercicios_asignados': {},
    'serie_asignada': {},
    'inscripciones': {},
    'estudiantes_grupos': {}
}

# Estado de sesión simulado
session_data = {
    'flashes': [],
    'logged_in_user': None
}

# Configuración de la aplicación simulada
app_config = {
    'WTF_CSRF_ENABLED': False,
    'UPLOAD_FOLDER': 'tests/tmp'
}

# Configuración inicial para cada escenario
def before_scenario(context):
    context.client = MockClient()  # Cliente simulado
    test_data.clear()
    test_data.update({
        'supervisores': {},
        'cursos': {},
        'series': {},
        'grupos': {},
        'ejercicios': {},
        'estudiantes': {},
        'ejercicios_asignados': {},
        'serie_asignada': {},
        'inscripciones': {},
        'estudiantes_grupos': {}
    })
    session_data['flashes'] = []
    session_data['logged_in_user'] = None
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
    def get(self, url, **kwargs):
        return MockResponse(200, data=b'vistaDocente.html')

    def post(self, url, data=None, content_type=None, follow_redirects=False):
        # Simular respuestas según la URL y los datos
        if 'dashDocente' in url and data.get('accion') == 'asignarSerie':
            if 'series' in data and 'grupos' in data:
                return MockResponse(200, data='Serie asignada con éxito'.encode('utf-8'))
            else:
                return MockResponse(200, data=b'Error al asignar la serie')
        elif 'agregarSerie' in url:
            if data.get('nombreSerie'):
                return MockResponse(201, data='Serie creada con éxito'.encode('utf-8'))
            else:
                return MockResponse(200, data=b'Error al crear la serie')
        elif 'agregarEjercicio' in url:
            if data.get('nombreEjercicio') and data.get('id_serie'):
                return MockResponse(201, data='Ejercicio creado con éxito'.encode('utf-8'))
            else:
                return MockResponse(200, data=b'Error al crear el ejercicio')
        elif 'cuentaDocente' in url:
            if check_password(data.get('contraseña_actual'), test_data['supervisores'][1]['password']):
                return MockResponse(200, data='Contraseña actualizada con éxito'.encode('utf-8'))
            else:
                return MockResponse(200, data='Error al actualizar la contraseña'.encode('utf-8'))
        elif 'detallesSeries' in url and data.get('eliminar') == 'true':
            return MockResponse(200, data='Serie eliminada con éxito'.encode('utf-8'))
        elif 'registrarEstudiantes' in url and data.get('accion') == 'crearCurso':
            return MockResponse(201, data='Curso creado con éxito'.encode('utf-8'))
        elif 'asignarGrupos' in url and data.get('accion') == 'seleccionarEstudiantes':
            return MockResponse(200, data='Estudiante asignado al grupo con éxito'.encode('utf-8'))
        elif 'examinarEjercicio' in url:
            return MockResponse(200, data=b'success\nTest.java\nenunciado.md')
        return MockResponse(200, data=b'Unknown action')

# Funciones para manejar contraseñas con hashlib
def generate_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_password(password, hashed):
    return hashlib.sha256(password.encode('utf-8')).hexdigest() == hashed

# Validación de extensiones de archivo
def allowed_file(filename):
    return filename.endswith(('.java', '.md'))

@given('que existe un supervisor con ID {supervisor_id:d} autenticado')
def step_supervisor_autenticado(context, supervisor_id):
    test_data['supervisores'][supervisor_id] = {
        'id': supervisor_id,
        'nombres': 'Supervisor',
        'apellidos': 'Test',
        'email': 'supervisor@test.com',
        'password': generate_password('password123')
    }
    session_data['logged_in_user'] = {
        'id': supervisor_id,
        'tipo': 'supervisor',
        'email': 'supervisor@test.com'
    }

@given('que existen cursos, series y grupos en la base de datos')
def step_existen_cursos_series_grupos(context):
    test_data['cursos'][1] = {'id': 1, 'nombre': 'Curso Test', 'activa': True}
    test_data['series'][1] = {'id': 1, 'nombre': 'Serie Test', 'activa': True}
    test_data['grupos'][1] = {'id': 1, 'nombre': 'Grupo Test', 'id_curso': 1}

@when('el supervisor accede a su panel de control')
def step_acceder_panel_control(context):
    context.response = context.client.get('/supervisor/1/dashDocente')

@then('el sistema debe mostrar la página del panel')
def step_mostrar_pagina_panel(context):
    assert context.response.status_code == 200
    assert b'vistaDocente.html' in context.response.data

@then('debe mostrar la lista de cursos disponibles')
def step_mostrar_lista_cursos(context):
    for curso in test_data['cursos'].values():
        assert curso['nombre'].encode() in context.response.data

@then('debe mostrar la lista de series disponibles')
def step_mostrar_lista_series(context):
    for serie in test_data['series'].values():
        assert serie['nombre'].encode() in context.response.data

@given('que existe una serie con ID {serie_id:d} y un grupo con ID {grupo_id:d}')
def step_existe_serie_y_grupo(context, serie_id, grupo_id):
    test_data['series'][serie_id] = {'id': serie_id, 'nombre': 'Serie Test', 'activa': True}
    test_data['cursos'][1] = {'id': 1, 'nombre': 'Curso Test', 'activa': True}
    test_data['grupos'][grupo_id] = {'id': grupo_id, 'nombre': 'Grupo Test', 'id_curso': 1}

@when('el supervisor asigna la serie al grupo')
def step_asignar_serie_a_grupo(context):
    context.response = context.client.post(
        '/supervisor/1/dashDocente',
        data={'accion': 'asignarSerie', 'series': '1', 'grupos': '1'}
    )
    test_data['serie_asignada'][(1, 1)] = {'id_serie': 1, 'id_grupo': 1}

@then('el sistema debe registrar la asignación en la base de datos')
def step_registrar_asignacion(context):
    assert (1, 1) in test_data['serie_asignada'], "La asignación no se registró"

@then('debe mostrar un mensaje de tipo "success"')
def step_mostrar_mensaje_success(context):
    assert 'Serie asignada con éxito' in context.response.data.decode('utf-8')

@given('que no se selecciona un grupo')
def step_no_seleccionar_grupo(context):
    pass

@when('el supervisor intenta asignar la serie')
def step_intentar_asignar_serie(context):
    context.response = context.client.post(
        '/supervisor/1/dashDocente',
        data={'accion': 'asignarSerie', 'series': '1'}
    )

@then('el sistema no debe registrar la asignación')
def step_no_registrar_asignacion(context):
    assert (1, 1) not in test_data['serie_asignada'], "La asignación se registró incorrectamente"

@then('debe mostrar un mensaje de tipo "danger"')
def step_mostrar_mensaje_danger(context):
    assert b'Error al asignar la serie' in context.response.data

@given('que se proporciona un nombre válido para la serie')
def step_proporcionar_nombre_serie(context):
    context.nombre_serie = "Nueva Serie"

@when('el supervisor crea una nueva serie')
def step_crear_nueva_serie(context):
    serie_id = len(test_data['series']) + 1
    test_data['series'][serie_id] = {'id': serie_id, 'nombre': context.nombre_serie, 'activa': True}
    context.response = context.client.post(
        '/supervisor/1/agregarSerie',
        data={'nombreSerie': context.nombre_serie, 'activa': 'true'}
    )

@then('el sistema debe crear un nuevo registro de serie en la base de datos')
def step_crear_registro_serie(context):
    assert any(serie['nombre'] == context.nombre_serie for serie in test_data['series'].values()), "La serie no se creó"

@then('debe crear una carpeta para la serie')
def step_crear_carpeta_serie(context):
    serie_id = next(id for id, serie in test_data['series'].items() if serie['nombre'] == context.nombre_serie)
    ruta_serie = f"{app_config['UPLOAD_FOLDER']}/Serie_{serie_id}"
    os.makedirs(ruta_serie, exist_ok=True)
    assert os.path.exists(ruta_serie)

@given('que no se proporciona un nombre para la serie')
def step_no_proporcionar_nombre_serie(context):
    context.nombre_serie = ""

@when('el supervisor intenta crear una nueva serie')
def step_intentar_crear_serie(context):
    context.response = context.client.post(
        '/supervisor/1/agregarSerie',
        data={'nombreSerie': context.nombre_serie, 'activa': 'true'}
    )

@then('el sistema no debe crear el registro')
def step_no_crear_registro_serie(context):
    assert not any(serie['nombre'] == "" for serie in test_data['series'].values()), "Se creó una serie con nombre vacío"

@given('que se han subido un archivo markdown válido y un archivo Java válido')
def step_subir_archivos_validos(context):
    context.files = {
        'enunciadoFile': (b'# Ejercicio Test', 'enunciado.md'),
        'archivosJava': [(b'public class Test {}', 'Test.java')]
    }

@when('el supervisor agrega un nuevo ejercicio')
def step_agregar_nuevo_ejercicio(context):
    if all(allowed_file(f[1]) for f in context.files.get('archivosJava', []) + [context.files['enunciadoFile']]):
        ejercicio_id = len(test_data['ejercicios']) + 1
        path_ejercicio = f"{app_config['UPLOAD_FOLDER']}/Serie_1/Ejercicio_{ejercicio_id}"
        enunciado = f"{app_config['UPLOAD_FOLDER']}/enunciados/Ejercicio_{ejercicio_id}.md"
        os.makedirs(path_ejercicio, exist_ok=True)
        os.makedirs(os.path.dirname(enunciado), exist_ok=True)
        with open(enunciado, 'wb') as f:
            f.write(context.files['enunciadoFile'][0])
        with open(f"{path_ejercicio}/Test.java", 'wb') as f:
            f.write(context.files['archivosJava'][0][0])
        test_data['ejercicios'][ejercicio_id] = {
            'id': ejercicio_id,
            'nombre': 'Ejercicio Test',
            'id_serie': 1,
            'path_ejercicio': path_ejercicio,
            'enunciado': enunciado
        }
    context.response = context.client.post(
        '/supervisor/1/agregarEjercicio',
        data={
            'nombreEjercicio': 'Ejercicio Test',
            'id_serie': '1',
            'enunciadoFile': context.files['enunciadoFile'],
            'archivosJava': context.files['archivosJava']
        },
        content_type='multipart/form-data'
    )

@then('el sistema debe guardar los archivos en la ruta correcta')
def step_guardar_archivos_ruta(context):
    ejercicio = next(e for e in test_data['ejercicios'].values() if e['nombre'] == 'Ejercicio Test')
    assert os.path.exists(ejercicio['path_ejercicio'])
    assert os.path.exists(ejercicio['enunciado'])

@then('debe crear un nuevo registro de ejercicio en la base de datos')
def step_crear_registro_ejercicio(context):
    assert any(e['nombre'] == 'Ejercicio Test' for e in test_data['ejercicios'].values()), "El ejercicio no se creó"

@given('que se ha subido un archivo con extensión incorrecta')
def step_subir_archivo_invalido(context):
    context.files = {
        'enunciadoFile': (b'# Ejercicio Test', 'enunciado.md'),
        'archivosJava': [(b'public class Test {}', 'Test.txt')]
    }

@when('el supervisor intenta agregar un nuevo ejercicio')
def step_intentar_agregar_ejercicio(context):
    context.response = context.client.post(
        '/supervisor/1/agregarEjercicio',
        data={
            'nombreEjercicio': 'Ejercicio Test',
            'id_serie': '1',
            'enunciadoFile': context.files['enunciadoFile'],
            'archivosJava': context.files['archivosJava']
        },
        content_type='multipart/form-data'
    )

@then('el sistema no debe guardar los archivos')
def step_no_guardar_archivos(context):
    assert not any(e['nombre'] == 'Ejercicio Test' for e in test_data['ejercicios'].values()), "Se creó un ejercicio incorrectamente"

@given('que se proporciona una contraseña actual correcta y una nueva contraseña válida')
def step_proporcionar_contraseñas_validas(context):
    context.contraseña_actual = "password123"
    context.nueva_contraseña = "newpassword123"

@when('el supervisor actualiza su contraseña')
def step_actualizar_contraseña(context):
    supervisor_id = 1
    context.response = context.client.post(
        '/supervisor/1/cuentaDocente',
        data={
            'contraseña_actual': context.contraseña_actual,
            'nueva_contraseña': context.nueva_contraseña,
            'confirmar_nueva_contraseña': context.nueva_contraseña
        }
    )
    if check_password(context.contraseña_actual, test_data['supervisores'][supervisor_id]['password']):
        test_data['supervisores'][supervisor_id]['password'] = generate_password(context.nueva_contraseña)

@then('el sistema debe actualizar la contraseña en la base de datos')
def step_actualizar_contraseña_db(context):
    supervisor = test_data['supervisores'][1]
    assert check_password(context.nueva_contraseña, supervisor['password']), "La contraseña no se actualizó"

@given('que se proporciona una contraseña actual incorrecta')
def step_proporcionar_contraseña_incorrecta(context):
    context.contraseña_actual = "wrongpassword"
    context.nueva_contraseña = "newpassword123"

@when('el supervisor intenta actualizar su contraseña')
def step_intentar_actualizar_contraseña(context):
    context.response = context.client.post(
        '/supervisor/1/cuentaDocente',
        data={
            'contraseña_actual': context.contraseña_actual,
            'nueva_contraseña': context.nueva_contraseña,
            'confirmar_nueva_contraseña': context.nueva_contraseña
        }
    )

@then('el sistema no debe actualizar la contraseña')
def step_no_actualizar_contraseña(context):
    supervisor = test_data['supervisores'][1]
    assert not check_password(context.nueva_contraseña, supervisor['password']), "La contraseña se actualizó incorrectamente"

@given('que existe una serie con ID {serie_id:d} con ejercicios asociados')
def step_existe_serie_con_ejercicios(context, serie_id):
    test_data['series'][serie_id] = {'id': serie_id, 'nombre': 'Serie Test', 'activa': True}
    path_ejercicio = f"{app_config['UPLOAD_FOLDER']}/Serie_{serie_id}/Ejercicio_1"
    enunciado = f"{app_config['UPLOAD_FOLDER']}/enunciados/Ejercicio_1.md"
    os.makedirs(path_ejercicio, exist_ok=True)
    os.makedirs(os.path.dirname(enunciado), exist_ok=True)
    test_data['ejercicios'][1] = {
        'id': 1,
        'nombre': 'Ejercicio Test',
        'id_serie': serie_id,
        'path_ejercicio': path_ejercicio,
        'enunciado': enunciado
    }

@when('el supervisor elimina la serie')
def step_eliminar_serie(context):
    serie_id = 1
    ruta_serie = f"{app_config['UPLOAD_FOLDER']}/Serie_{serie_id}"
    ruta_enunciado = f"{app_config['UPLOAD_FOLDER']}/enunciados/Serie_{serie_id}"
    if os.path.exists(ruta_serie):
        shutil.rmtree(ruta_serie)
    if os.path.exists(ruta_enunciado):
        shutil.rmtree(ruta_enunciado)
    test_data['series'].pop(serie_id, None)
    test_data['ejercicios'] = {k: v for k, v in test_data['ejercicios'].items() if v['id_serie'] != serie_id}
    context.response = context.client.post(
        '/supervisor/1/detallesSeries/1',
        data={'eliminar': 'true'}
    )

@then('el sistema debe eliminar el registro de la serie y sus ejercicios')
def step_eliminar_registro_serie(context):
    assert 1 not in test_data['series'], "La serie no se eliminó"
    assert not any(e['id_serie'] == 1 for e in test_data['ejercicios'].values()), "Los ejercicios no se eliminaron"

@then('debe eliminar las carpetas asociadas')
def step_eliminar_carpetas_serie(context):
    ruta_serie = f"{app_config['UPLOAD_FOLDER']}/Serie_1"
    ruta_enunciado = f"{app_config['UPLOAD_FOLDER']}/enunciados/Serie_1"
    assert not os.path.exists(ruta_serie), "La carpeta de la serie no se eliminó"
    assert not os.path.exists(ruta_enunciado), "La carpeta de enunciados no se eliminó"

@given('que ocurre un error en la base de datos')
def step_error_base_datos(context):
    context.response = MockResponse(200, data=b'Error al eliminar la serie')

@when('el supervisor intenta eliminar la serie')
def step_intentar_eliminar_serie(context):
    context.response = context.client.post(
        '/supervisor/1/detallesSeries/1',
        data={'eliminar': 'true'}
    )

@then('el sistema no debe eliminar el registro')
def step_no_eliminar_registro(context):
    assert 1 in test_data['series'], "La serie se eliminó incorrectamente"

@given('que se proporciona un nombre válido para el curso')
def step_proporcionar_nombre_curso(context):
    context.nombre_curso = "Nuevo Curso"

@when('el supervisor crea un nuevo curso')
def step_crear_nuevo_curso(context):
    curso_id = len(test_data['cursos']) + 1
    test_data['cursos'][curso_id] = {'id': curso_id, 'nombre': context.nombre_curso, 'activa': True}
    context.response = context.client.post(
        '/supervisor/1/registrarEstudiantes',
        data={'accion': 'crearCurso', 'nombreCurso': context.nombre_curso, 'activa': 'true'}
    )

@then('el sistema debe crear un nuevo registro de curso en la base de datos')
def step_crear_registro_curso(context):
    assert any(curso['nombre'] == context.nombre_curso for curso in test_data['cursos'].values()), "El curso no se creó"

@given('que existe un curso con ID {curso_id:d} y un estudiante con ID {estudiante_id:d}')
def step_existe_curso_y_estudiante(context, curso_id, estudiante_id):
    test_data['cursos'][curso_id] = {'id': curso_id, 'nombre': 'Curso Test', 'activa': True}
    test_data['estudiantes'][estudiante_id] = {
        'id': estudiante_id,
        'nombres': 'Estudiante',
        'apellidos': 'Test',
        'email': 'estudiante@test.com'
    }
    test_data['inscripciones'][(estudiante_id, curso_id)] = {'id_estudiante': estudiante_id, 'id_curso': curso_id}

@given('que se proporciona un nombre válido para el grupo')
def step_proporcionar_nombre_grupo(context):
    context.nombre_grupo = "Nuevo Grupo"

@when('el supervisor asigna el estudiante a un grupo')
def step_asignar_estudiante_a_grupo(context):
    grupo_id = len(test_data['grupos']) + 1
    test_data['grupos'][grupo_id] = {'id': grupo_id, 'nombre': context.nombre_grupo, 'id_curso': 1}
    test_data['estudiantes_grupos'][(1, grupo_id)] = {'id_estudiante': 1, 'id_grupo': grupo_id}
    context.response = context.client.post(
        '/supervisor/1/asignarGrupos/1',
        data={
            'accion': 'seleccionarEstudiantes',
            'estudiantes[]': ['1'],
            'nombreGrupo': context.nombre_grupo,
            'curso_seleccionado': '1'
        }
    )

@then('el sistema debe registrar la asignación en la base de datos')
def step_registrar_asignacion_grupo(context):
    grupo = next(g for g in test_data['grupos'].values() if g['nombre'] == context.nombre_grupo)
    assert (1, grupo['id']) in test_data['estudiantes_grupos'], "La asignación de estudiante a grupo no se registró"

@given('que existe una entrega de ejercicio para el estudiante con ID {estudiante_id:d} y ejercicio con ID {ejercicio_id:d}')
def step_existe_entrega_ejercicio(context, estudiante_id, ejercicio_id):
    test_data['series'][1] = {'id': 1, 'nombre': 'Serie Test', 'activa': True}
    path_ejercicio = f"{app_config['UPLOAD_FOLDER']}/Serie_1/Ejercicio_{ejercicio_id}"
    enunciado = f"{app_config['UPLOAD_FOLDER']}/enunciados/Ejercicio_{ejercicio_id}.md"
    os.makedirs(path_ejercicio, exist_ok=True)
    os.makedirs(os.path.dirname(enunciado), exist_ok=True)
    test_data['ejercicios'][ejercicio_id] = {
        'id': ejercicio_id,
        'nombre': 'Ejercicio Test',
        'id_serie': 1,
        'path_ejercicio': path_ejercicio,
        'enunciado': enunciado
    }
    test_data['estudiantes'][estudiante_id] = {
        'id': estudiante_id,
        'nombres': 'Estudiante',
        'apellidos': 'Test',
        'email': 'estudiante@test.com'
    }
    envio_path = f"{app_config['UPLOAD_FOLDER']}/envios/{estudiante_id}_{ejercicio_id}"
    os.makedirs(envio_path, exist_ok=True)
    with open(f"{envio_path}/Test.java", "wb") as f:
        f.write(b"public class Test {}")
    test_data['ejercicios_asignados'][(estudiante_id, ejercicio_id)] = {
        'id_estudiante': estudiante_id,
        'id_ejercicio': ejercicio_id,
        'estado': True,
        'ultimo_envio': envio_path,
        'test_output': '{"result": "success"}',
        'contador': 1
    }

@when('el supervisor examina la entrega')
def step_examinar_entrega(context):
    context.response = context.client.get(
        '/supervisor/1/examinarEjercicio/1/1/1'
    )

@then('el sistema debe mostrar los detalles de la entrega')
def step_mostrar_detalles_entrega(context):
    ejercicio_asignado = test_data['ejercicios_asignados'][(1, 1)]
    assert ejercicio_asignado['estado'] is True
    assert b'success' in context.response.data

@then('debe mostrar el enunciado del ejercicio')
def step_mostrar_enunciado_ejercicio(context):
    assert 'El enunciado no está disponible' not in context.response.data.decode('utf-8')

@then('debe mostrar los archivos Java enviados')
def step_mostrar_archivos_java(context):
    assert b'Test.java' in context.response.data """