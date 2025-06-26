from behave import given, when, then
from app import create_app, db
from app.models import Supervisor, Serie, Grupo, Curso, Ejercicio, Ejercicio_asignado, Estudiante
from flask_login import login_user
from werkzeug.security import generate_password_hash
import os
from flask import url_for
from app.utils.file_handling import allowed_file
from werkzeug.utils import secure_filename
from flask.testing import FlaskClient
import shutil

# Crear la aplicación Flask para pruebas
app = create_app('testing')  # Asume que tienes una configuración 'testing' en tu app
app.config['WTF_CSRF_ENABLED'] = False  # Deshabilitar CSRF para pruebas

# Contexto para pruebas
def before_scenario(context):
    context.client = app.test_client()
    context.db = db
    with app.app_context():
        db.create_all()

def after_scenario(context):
    with app.app_context():
        db.drop_all()

@given('que existe un supervisor con ID {supervisor_id:d} autenticado')
def step_supervisor_autenticado(context, supervisor_id):
    with app.app_context():
        supervisor = Supervisor(
            id=supervisor_id,
            nombres="Supervisor",
            apellidos="Test",
            email="supervisor@test.com",
            password=generate_password_hash("password123")
        )
        db.session.add(supervisor)
        db.session.commit()
        login_user(supervisor)

@given('que existen cursos, series y grupos en la base de datos')
def step_existen_cursos_series_grupos(context):
    with app.app_context():
        curso = Curso(nombre="Curso Test", activa=True)
        serie = Serie(nombre="Serie Test", activa=True)
        grupo = Grupo(nombre="Grupo Test", id_curso=1)
        db.session.add_all([curso, serie, grupo])
        db.session.commit()

@when('el supervisor accede a su panel de control')
def step_acceder_panel_control(context):
    with app.app_context():
        context.response = context.client.get(url_for('supervisor.dashDocente', supervisor_id=1))

@then('el sistema debe mostrar la página del panel')
def step_mostrar_pagina_panel(context):
    assert context.response.status_code == 200
    assert b'vistaDocente.html' in context.response.data  # Verifica que se renderice la plantilla correcta

@then('debe mostrar la lista de cursos disponibles')
def step_mostrar_lista_cursos(context):
    with app.app_context():
        cursos = Curso.query.all()
        for curso in cursos:
            assert curso.nombre.encode() in context.response.data

@then('debe mostrar la lista de series disponibles')
def step_mostrar_lista_series(context):
    with app.app_context():
        series = Serie.query.all()
        for serie in series:
            assert serie.nombre.encode() in context.response.data

@given('que existe una serie con ID {serie_id:d} y un grupo con ID {grupo_id:d}')
def step_existe_serie_y_grupo(context, serie_id, grupo_id):
    with app.app_context():
        serie = Serie(id=serie_id, nombre="Serie Test", activa=True)
        curso = Curso(id=1, nombre="Curso Test", activa=True)
        grupo = Grupo(id=grupo_id, nombre="Grupo Test", id_curso=1)
        db.session.add_all([serie, curso, grupo])
        db.session.commit()

@when('el supervisor asigna la serie al grupo')
def step_asignar_serie_a_grupo(context):
    with app.app_context():
        context.response = context.client.post(
            url_for('supervisor.dashDocente', supervisor_id=1),
            data={'accion': 'asignarSeri189410.pts-0.pa3p2es', 'series': '1', 'grupos': '1'},
            follow_redirects=True
        )

@then('el sistema debe registrar la asignación en la base de datos')
def step_registrar_asignacion(context):
    with app.app_context():
        asignacion = db.session.execute(
            db.select(db.text('id_serie, id_grupo')).from_table('serie_asignada').where(
                db.text('id_serie = :serie_id AND id_grupo = :grupo_id'),
                {'serie_id': 1, 'grupo_id': 1}
            )
        ).fetchone()
        assert asignacion is not None

@then('debe mostrar un mensaje de tipo "success"')
def step_mostrar_mensaje_success(context):
    assert 'Serie asignada con éxito' in context.response.data.decode('utf-8')

@given('que no se selecciona un grupo')
def step_no_seleccionar_grupo(context):
    pass  # No se selecciona grupo, simulado en el POST

@when('el supervisor intenta asignar la serie')
def step_intentar_asignar_serie(context):
    with app.app_context():
        context.response = context.client.post(
            url_for('supervisor.dashDocente', supervisor_id=1),
            data={'accion': 'asignarSeri189410.pts-0.pa3p2es', 'series': '1'},
            follow_redirects=True
        )

@then('el sistema no debe registrar la asignación')
def step_no_registrar_asignacion(context):
    with app.app_context():
        asignacion = db.session.execute(
            db.select(db.text('id_serie')).from_table('serie_asignada').where(
                db.text('id_serie = :serie_id'),
                {'serie_id': 1}
            )
        ).fetchone()
        assert asignacion is None

@then('debe mostrar un mensaje de tipo "danger"')
def step_mostrar_mensaje_danger(context):
    assert b'Error al asignar la serie' in context.response.data

@given('que se proporciona un nombre válido para la serie')
def step_proporcionar_nombre_serie(context):
    context.nombre_serie = "Nueva Serie"

@when('el supervisor crea una nueva serie')
def step_crear_nueva_serie(context):
    with app.app_context():
        context.response = context.client.post(
            url_for('supervisor.agregarSerie', supervisor_id=1),
            data={'nombreSerie': context.nombre_serie, 'activa': 'true'},
            follow_redirects=True
        )

@then('el sistema debe crear un nuevo registro en la base de datos')
def step_crear_registro_serie(context):
    with app.app_context():
        serie = Serie.query.filter_by(nombre=context.nombre_serie).first()
        assert serie is not None

@then('debe crear una carpeta para la serie')
def step_crear_carpeta_serie(context):
    with app.app_context():
        serie = Serie.query.filter_by(nombre=context.nombre_serie).first()
        ruta_serie = f"ejerciciosPropuestos/Serie_{serie.id}"
        assert os.path.exists(ruta_serie)

@given('que no se proporciona un nombre para la serie')
def step_no_proporcionar_nombre_serie(context):
    context.nombre_serie = ""

@when('el supervisor intenta crear una nueva serie')
def step_intentar_crear_serie(context):
    with app.app_context():
        context.response = context.client.post(
            url_for('supervisor.agregarSerie', supervisor_id=1),
            data={'nombreSerie': context.nombre_serie, 'activa': 'true'},
            follow_redirects=True
        )

@then('el sistema no debe crear el registro')
def step_no_crear_registro_serie(context):
    with app.app_context():
        serie = Serie.query.filter_by(nombre="").first()
        assert serie is None

@given('que se han subido un archivo markdown válido y un archivo Java válido')
def step_subir_archivos_validos(context):
    context.files = {
        'enunciadoFile': (b'# Ejercicio Test', 'enunciado.md'),
        'archivosJava': [(b'public class Test {}', 'Test.java')]
    }

@when('el supervisor agrega un nuevo ejercicio')
def step_agregar_nuevo_ejercicio(context):
    with app.app_context():
        context.response = context.client.post(
            url_for('supervisor.agregarEjercicio', supervisor_id=1),
            data={
                'nombreEjercicio': 'Ejercicio Test',
                'id_serie': '1',
                'enunciadoFile': context.files['enunciadoFile'],
                'archivosJava': context.files['archivosJava']
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )

@then('el sistema debe guardar los archivos en la ruta correcta')
def step_guardar_archivos_ruta(context):
    with app.app_context():
        ejercicio = Ejercicio.query.filter_by(nombre="Ejercicio Test").first()
        assert os.path.exists(ejercicio.path_ejercicio)
        assert os.path.exists(ejercicio.enunciado)

@then('debe crear un nuevo registro de ejercicio en la base de datos')
def step_crear_registro_ejercicio(context):
    with app.app_context():
        ejercicio = Ejercicio.query.filter_by(nombre="Ejercicio Test").first()
        assert ejercicio is not None

@given('que se ha subido un archivo con extensión incorrecta')
def step_subir_archivo_invalido(context):
    context.files = {
        'enunciadoFile': (b'# Ejercicio Test', 'enunciado.md'),
        'archivosJava': [(b'public class Test {}', 'Test.txt')]
    }

@when('el supervisor intenta agregar un nuevo ejercicio')
def step_intentar_agregar_ejercicio(context):
    with app.app_context():
        context.response = context.client.post(
            url_for('supervisor.agregarEjercicio', supervisor_id=1),
            data={
                'nombreEjercicio': 'Ejercicio Test',
                'id_serie': '1',
                'enunciadoFile': context.files['enunciadoFile'],
                'archivosJava': context.files['archivosJava']
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )

@then('el sistema no debe guardar los archivos')
def step_no_guardar_archivos(context):
    with app.app_context():
        ejercicio = Ejercicio.query.filter_by(nombre="Ejercicio Test").first()
        assert ejercicio is None

@given('que se proporciona una contraseña actual correcta y una nueva contraseña válida')
def step_proporcionar_contraseñas_validas(context):
    context.contraseña_actual = "password123"
    context.nueva_contraseña = "newpassword123"

@when('el supervisor actualiza su contraseña')
def step_actualizar_contraseña(context):
    with app.app_context():
        context.response = context.client.post(
            url_for('supervisor.cuentaDocente', supervisor_id=1),
            data={
                'contraseña_actual': context.contraseña_actual,
                'nueva_contraseña': context.nueva_contraseña,
                'confirmar_nueva_contraseña': context.nueva_contraseña
            },
            follow_redirects=True
        )

@then('el sistema debe actualizar la contraseña en la base de datos')
def step_actualizar_contraseña_db(context):
    with app.app_context():
        supervisor = Supervisor.query.get(1)
        assert check_password_hash(supervisor.password, context.nueva_contraseña)

@given('que se proporciona una contraseña actual incorrecta')
def step_proporcionar_contraseña_incorrecta(context):
    context.contraseña_actual = "wrongpassword"
    context.nueva_contraseña = "newpassword123"

@when('el supervisor intenta actualizar su contraseña')
def step_intentar_actualizar_contraseña(context):
    with app.app_context():
        context.response = context.client.post(
            url_for('supervisor.cuentaDocente', supervisor_id=1),
            data={
                'contraseña_actual': context.contraseña_actual,
                'nueva_contraseña': context.nueva_contraseña,
                'confirmar_nueva_contraseña': context.nueva_contraseña
            },
            follow_redirects=True
        )

@then('el sistema no debe actualizar la contraseña')
def step_no_actualizar_contraseña(context):
    with app.app_context():
        supervisor = Supervisor.query.get(1)
        assert not check_password_hash(supervisor.password, context.nueva_contraseña)

@given('que existe una serie con ID {serie_id:d} con ejercicios asociados')
def step_existe_serie_con_ejercicios(context, serie_id):
    with app.app_context():
        serie = Serie(id=serie_id, nombre="Serie Test", activa=True)
        ejercicio = Ejercicio(nombre="Ejercicio Test", id_serie=serie_id, path_ejercicio="path/test", enunciado="enunciado/test.md")
        db.session.add_all([serie, ejercicio])
        db.session.commit()

@when('el supervisor elimina la serie')
def step_eliminar_serie(context):
    with app.app_context():
        context.response = context.client.post(
            url_for('supervisor.detallesSeries', supervisor_id=1, serie_id=1),
            data={'eliminar': 'true'},
            follow_redirects=True
        )

@then('el sistema debe eliminar el registro de la serie y sus ejercicios')
def step_eliminar_registro_serie(context):
    with app.app_context():
        serie = Serie.query.get(1)
        ejercicio = Ejercicio.query.filter_by(id_serie=1).first()
        assert serie is None
        assert ejercicio is None

@then('debe eliminar las carpetas asociadas')
def step_eliminar_carpetas_serie(context):
    with app.app_context():
        ruta_serie = 'ejerciciosPropuestos/Serie_1'
        ruta_enunciado = 'enunciadosEjercicios/Serie_1'
        assert not os.path.exists(ruta_serie)
        assert not os.path.exists(ruta_enunciado)

@given('que ocurre un error en la base de datos')
def step_error_base_datos(context):
    # Simular error en la base de datos (por ejemplo, desconectar la base de datos)
    with app.app_context():
        db.session.remove()  # Simula un problema al cerrar la sesión

@when('el supervisor intenta eliminar la serie')
def step_intentar_eliminar_serie(context):
    with app.app_context():
        context.response = context.client.post(
            url_for('supervisor.detallesSeries', supervisor_id=1, serie_id=1),
            data={'eliminar': 'true'},
            follow_redirects=True
        )

@given('que se proporciona un nombre válido para el curso')
def step_proporcionar_nombre_curso(context):
    context.nombre_curso = "Nuevo Curso"

@when('el supervisor crea un nuevo curso')
def step_crear_nuevo_curso(context):
    with app.app_context():
        context.response = context.client.post(
            url_for('supervisor.registrarEstudiantes', supervisor_id=1),
            data={'accion': 'crearCurso', 'nombreCurso': context.nombre_curso, 'activa': 'true'},
            follow_redirects=True
        )

@then('el sistema debe crear un nuevo registro en la base de datos')
def step_crear_registro_curso(context):
    with app.app_context():
        curso = Curso.query.filter_by(nombre=context.nombre_curso).first()
        assert curso is not None

@given('que existe un curso con ID {curso_id:d} y un estudiante con ID {estudiante_id:d}')
def step_existe_curso_y_estudiante(context, curso_id, estudiante_id):
    with app.app_context():
        curso = Curso(id=curso_id, nombre="Curso Test", activa=True)
        estudiante = Estudiante(id=estudiante_id, nombres="Estudiante", apellidos="Test", email="estudiante@test.com")
        db.session.add_all([curso, estudiante])
        db.session.execute(db.insert(inscripciones).values(id_estudiante=estudiante_id, id_curso=curso_id))
        db.session.commit()

@given('que se proporciona un nombre válido para el grupo')
def step_proporcionar_nombre_grupo(context):
    context.nombre_grupo = "Nuevo Grupo"

@when('el supervisor asigna el estudiante a un grupo')
def step_asignar_estudiante_a_grupo(context):
    with app.app_context():
        context.response = context.client.post(
            url_for('supervisor.asignarGrupos', supervisor_id=1, curso_id=1),
            data={
                'accion': 'seleccionarEstudiantes',
                'estudiantes[]': ['1'],
                'nombreGrupo': context.nombre_grupo,
                'curso_seleccionado': '1'
            },
            follow_redirects=True
        )

@then('el sistema debe registrar la asignación en la base de datos')
def step_registrar_asignacion_grupo(context):
    with app.app_context():
        grupo = Grupo.query.filter_by(nombre=context.nombre_grupo).first()
        asignacion = db.session.execute(
            db.select(db.text('id_estudiante, id_grupo')).from_table('estudiantes_grupos').where(
                db.text('id_estudiante = :estudiante_id AND id_grupo = :grupo_id'),
                {'estudiante_id': 1, 'grupo_id': grupo.id}
            )
        ).fetchone()
        assert asignacion is not None

@given('que existe una entrega de ejercicio para el estudiante con ID {estudiante_id:d} y ejercicio con ID {ejercicio_id:d}')
def step_existe_entrega_ejercicio(context, estudiante_id, ejercicio_id):
    with app.app_context():
        serie = Serie(id=1, nombre="Serie Test", activa=True)
        ejercicio = Ejercicio(id=ejercicio_id, nombre="Ejercicio Test", id_serie=1, path_ejercicio="path/test", enunciado="enunciado/test.md")
        estudiante = Estudiante(id=estudiante_id, nombres="Estudiante", apellidos="Test", email="estudiante@test.com")
        ejercicio_asignado = Ejercicio_asignado(
            id_estudiante=estudiante_id,
            id_ejercicio=ejercicio_id,
            estado=True,
            ultimo_envio="path/envio",
            test_output='{"result": "success"}',
            contador=1
        )
        db.session.add_all([serie, ejercicio, estudiante, ejercicio_asignado])
        db.session.commit()
        os.makedirs("path/envio", exist_ok=True)
        with open("path/envio/Test.java", "w") as f:
            f.write("public class Test {}")

@when('el supervisor examina la entrega')
def step_examinar_entrega(context):
    with app.app_context():
        context.response = context.client.get(
            url_for('supervisor.examinarEjercicio', supervisor_id=1, curso_id=1, estudiante_id=1, ejercicio_id=1),
            follow_redirects=True
        )

@then('el sistema debe mostrar los detalles de la entrega')
def step_mostrar_detalles_entrega(context):
    with app.app_context():
        ejercicio_asignado = Ejercicio_asignado.query.filter_by(id_estudiante=1, id_ejercicio=1).first()
        assert ejercicio_asignado.estado == True
        assert b'success' in context.response.data

@then('debe mostrar el enunciado del ejercicio')
def step_mostrar_enunciado_ejercicio(context):
    assert 'El enunciado no está disponible' not in context.response.data.decode('utf-8')  # Verifica que el enunciado se renderice

@then('debe mostrar los archivos Java enviados')
def step_mostrar_archivos_java(context):
    assert b'Test.java' in context.response.data