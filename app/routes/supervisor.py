from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_required, current_user
from app import db
from app.models import Supervisor, Grupo, Serie, Estudiante, Ejercicio, Ejercicio_asignado, Curso, serie_asignada, inscripciones, estudiantes_grupos, supervisores_grupos
from app.utils.verification import verify_supervisor
from app.utils.file_handling import procesar_archivo_csv, allowed_file, calcular_calificacion
from funciones_archivo.manejoCarpetas import crearCarpetaSerie, crearCarpetaEjercicio
from werkzeug.utils import secure_filename
import os
import shutil
import markdown
import json
from ansi2html import Ansi2HTMLConverter

supervisor_bp = Blueprint('supervisor', __name__)

@supervisor_bp.route('/<int:supervisor_id>', methods=['GET', 'POST'])
@login_required
def dashDocente(supervisor_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('auth.login'))
    
    series = Serie.query.all()
    cursos = Curso.query.all()
    ejercicios = Ejercicio.query.all()
    curso_seleccionado_id = None
    grupos = []

    if not cursos:
        flash('No existen cursos, por favor crear un curso', 'danger')
    if not series:
        flash('No existen series, por favor crear una serie', 'danger')
    if not ejercicios:
        flash('No existen ejercicios, por favor crear un ejercicio', 'danger')

    if curso_seleccionado_id is None or curso_seleccionado_id == 1:
        primer_curso = session.get(1)
        if primer_curso:
            grupos = Grupo.query.filter_by(id_curso=curso_seleccionado_id).all()

    if request.method == 'POST':
        if request.form['accion'] == 'seleccionarCurso':
            curso_seleccionado_id = int(request.form['curso'])
            grupos = Grupo.query.filter_by(id_curso=curso_seleccionado_id).all()
            series = Serie.query.all()
            return render_template('vistaDocente.html', supervisor_id=supervisor_id, cursos=cursos, grupos=grupos, id_curso_seleccionado=curso_seleccionado_id, series=series)
        if request.form['accion'] == 'asignarSeri189410.pts-0.pa3p2es':
            serie_seleccionada = request.form.get('series')
            grupo_seleccionado = request.form.get('grupos')
            try:
                if serie_seleccionada and grupo_seleccionado:
                    db.session.execute(serie_asignada.insert().values(id_serie=serie_seleccionada, id_grupo=grupo_seleccionado))
                    db.session.commit()
                    flash('Serie asignada con éxito', 'success')
                    grupos = Grupo.query.filter_by(id_curso=curso_seleccionado_id).all()
                    series = Serie.query.all()
                    return redirect(url_for('supervisor.dashDocente', supervisor_id=supervisor_id))
            except Exception as e:
                db.session.rollback()
                flash('Error al asignar la serie', 'danger')
                return redirect(url_for('supervisor.dashDocente', supervisor_id=supervisor_id))

    if curso_seleccionado_id is not None:
        grupos = Grupo.query.filter_by(curso_id=curso_seleccionado_id).all()

    return render_template('vistaDocente.html', supervisor_id=supervisor_id, cursos=cursos, grupos=grupos, curso_seleccionado_id=curso_seleccionado_id, series=series)

@supervisor_bp.route('/<int:supervisor_id>/cuentaDocente', methods=['GET', 'POST'])
@login_required
def cuentaDocente(supervisor_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('auth.login'))
    
    supervisor = Supervisor.query.get(supervisor_id)

    if request.method == 'POST':
        contraseña_actual = request.form.get('contraseña_actual')
        nueva_contraseña = request.form.get('nueva_contraseña')
        confirmar_nueva_contraseña = request.form.get('confirmar_nueva_contraseña')

        if not check_password_hash(supervisor.password, contraseña_actual):
            flash('Contraseña actual incorrecta', 'danger')
        elif len(nueva_contraseña) < 10:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'danger')
        elif nueva_contraseña != confirmar_nueva_contraseña:
            flash('Las nuevas contraseñas no coinciden', 'danger')
        else:
            supervisor.password = generate_password_hash(nueva_contraseña)
            db.session.commit()
            flash('Contraseña actualizada correctamente', 'success')

    return render_template('cuentaDocente.html', supervisor=supervisor, supervisor_id=supervisor_id)

@supervisor_bp.route('/<int:supervisor_id>/agregarSerie', methods=['GET', 'POST'])
@login_required
def agregarSerie(supervisor_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        nombreSerie = request.form.get('nombreSerie')
        activa_value = True if request.form.get('activa') == "true" else False

        if not nombreSerie:
            flash('Por favor, complete todos los campos.', 'danger')
            return redirect(url_for('supervisor.agregarSerie', supervisor_id=supervisor_id))
        try:
            nueva_serie = Serie(nombre=nombreSerie, activa=activa_value)
            db.session.add(nueva_serie)
            db.session.flush()
            try:
                crearCarpetaSerie(nueva_serie.id)
                current_app.logger.info(f'Se creó la carpeta de la serie {nueva_serie.nombre} con éxito.')
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Ocurrió un error al crear la carpeta de la serie: {str(e)}')
                return render_template('agregarSerie.html', supervisor_id=supervisor_id)
        except Exception as e:
            db.session.rollback()
    return render_template('agregarSerie.html', supervisor_id=supervisor_id)

@supervisor_bp.route('/<int:supervisor_id>/agregarEjercicio', methods=['GET', 'POST'])
@login_required
def agregarEjercicio(supervisor_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('auth.login'))

    series = Serie.query.all()
    filepath_ejercicio = None
    rutaEnunciadoEjercicios = None
    if request.method == 'POST':
        try:
            nombreEjercicio = request.form.get('nombreEjercicio')
            id_serie = request.form.get('id_serie')
            enunciadoFile = request.files.get('enunciadoFile')
            imagenesFiles = request.files.getlist('imagenesFiles')
            unitTestFiles = request.files.getlist('archivosJava')
            serie_actual = db.session.get(Serie, int(id_serie))

            if not any(allowed_file(file.filename, {'java'}) for file in unitTestFiles):
                flash('Por favor, carga al menos un archivo .java.', 'danger')
                return render_template('agregarEjercicio.html', supervisor_id=supervisor_id, series=series)

            if not imagenesFiles:
                imagenesFiles = None

            nuevo_ejercicio = Ejercicio(nombre=nombreEjercicio, path_ejercicio="", enunciado="", id_serie=id_serie)
            db.session.add(nuevo_ejercicio)
            db.session.flush()

            rutaEjercicio, rutaEnunciadoEjercicios, mensaje = crearCarpetaEjercicio(nuevo_ejercicio.id, id_serie)

            if rutaEjercicio is None:
                raise Exception(mensaje)

            filepath_ejercicio = rutaEjercicio

            nuevoNombre = str(nuevo_ejercicio.id) + "_" + str(nuevo_ejercicio.nombre) + ".md"
            enunciadoFile.save(os.path.join(rutaEnunciadoEjercicios, nuevoNombre))
            nuevo_ejercicio.path_ejercicio = rutaEjercicio
            nuevo_ejercicio.enunciado = os.path.join(rutaEnunciadoEjercicios, nuevoNombre)

            if imagenesFiles and imagenesFiles[0].filename:
                for imagenFile in imagenesFiles:
                    imagen_filename = secure_filename(imagenFile.filename)
                    imagenFile.save(os.path.join(rutaEnunciadoEjercicios, imagen_filename))
            else:
                current_app.logger.warning('No se encontraron imágenes en el enunciado.')

            ubicacionTest = os.path.join(rutaEjercicio, "src/test/java/org/example")
            os.makedirs(ubicacionTest, exist_ok=True)

            for unitTestFile in unitTestFiles:
                nombre_archivo = secure_filename(unitTestFile.filename)
                unitTestFile.save(os.path.join(ubicacionTest, nombre_archivo))

            db.session.commit()
            flash('Ejercicio agregado con éxito', 'success')
            return redirect(url_for('supervisor.agregarEjercicio', supervisor_id=supervisor_id))

        except Exception as e:
            current_app.logger.error(f'Ocurrió un error al agregar el ejercicio: {str(e)}')
            if filepath_ejercicio is not None and os.path.exists(filepath_ejercicio):
                shutil.rmtree(filepath_ejercicio)
            if rutaEnunciadoEjercicios is not None and os.path.exists(rutaEnunciadoEjercicios):
                shutil.rmtree(rutaEnunciadoEjercicios)
            db.session.rollback()
            return redirect(url_for('supervisor.agregarEjercicio', supervisor_id=supervisor_id, series=series))

    return render_template('agregarEjercicio.html', supervisor_id=supervisor_id, series=series)

@supervisor_bp.route('/<int:supervisor_id>/serie/<int:serie_id>', methods=['GET', 'POST'])
@login_required
def detallesSeries(supervisor_id, serie_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('auth.login'))

    serie = Serie.query.get(serie_id)
    ejercicios = Ejercicio.query.filter_by(id_serie=serie_id).all()
    grupos_asociados = None
    if serie is not None:
        grupos_asociados = Grupo.query.join(serie_asignada).filter(serie_asignada.c.id_serie == serie.id).all()
    if serie is None:
        grupos_asociados = None
        ejercicios = None

    if request.method == 'POST':
        current_app.logger.info(f'Formulario recibido: {request.form}')
        if 'activar_desactivar' in request.form:
            serie.activa = not serie.activa
            db.session.commit()
            return redirect(url_for('supervisor.detallesSeries', supervisor_id=supervisor_id, serie_id=serie_id))
        elif 'eliminar' in request.form:
            try:
                current_app.logger.info(f'Eliminando la serie {serie.nombre}...')
                Ejercicio.query.filter_by(id_serie=serie_id).delete()
                db.session.execute(serie_asignada.delete().where(serie_asignada.c.id_serie == serie.id))
                db.session.delete(serie)
                db.session.commit()
                rutaSerie = 'ejerciciosPropuestos/Serie_' + str(serie.id)
                shutil.rmtree(rutaSerie)
                rutaEnunciadoSerie = 'enunciadosEjercicios/Serie_' + str(serie.id)
                shutil.rmtree(rutaEnunciadoSerie)
                flash('Serie eliminada correctamente.', 'success')
                return redirect(url_for('supervisor.dashDocente', supervisor_id=supervisor_id))
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al eliminar la serie: {str(e)}')
                db.session.rollback()
                flash('Ocurrió un error al eliminar la serie.', 'danger')
                return redirect(url_for('supervisor.detallesSeries', supervisor_id=supervisor_id, serie_id=serie_id))
        elif 'editar' in request.form:
            try:
                current_app.logger.info(f'Editando la serie {serie.nombre}...')
                serie = Serie.query.get(serie_id)
                serie.nombre = request.form.get('nuevo_nombre')
                db.session.commit()
                current_app.logger.info(f'Serie editada correctamente.')
                return redirect(url_for('supervisor.detallesSeries', supervisor_id=supervisor_id, serie_id=serie_id))
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al editar la serie: {str(e)}')
                db.session.rollback()
                return redirect(url_for('supervisor.detallesSeries', supervisor_id=supervisor_id, serie_id=serie_id))
    if serie is None:
        return redirect(url_for('supervisor.dashDocente', supervisor_id=supervisor_id))
    return render_template('detallesSerie.html', serie=serie, ejercicios=ejercicios, supervisor_id=supervisor_id, grupos_asociados=grupos_asociados)

@supervisor_bp.route('/<int:supervisor_id>/serie/<int:serie_id>/ejercicio/<int:ejercicio_id>', methods=['GET', 'POST'])
@login_required
def detallesEjercicio(supervisor_id, serie_id, ejercicio_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('auth.login'))
    ejercicio = Ejercicio.query.get(ejercicio_id)
    serie = Serie.query.get(serie_id)
    if ejercicio and ejercicio.enunciado:
        with open(ejercicio.enunciado, 'r') as enunciado_file:
            enunciado_markdown = enunciado_file.read()
            enunciado_html = markdown.markdown(enunciado_markdown)
    else:
        enunciado_html = "<p>El enunciado no está disponible.</p>"

    if request.method == "POST":
        if 'editar' in request.form:
            current_app.logger.info(f'Editando el ejercicio...{ejercicio.nombre}')
            nombreEjercicio = request.form.get('nuevo_nombre')
            enunciadoFile = request.files.get('enunciadoFile')
            imagenesFiles = request.files.getlist('imagenesFiles')
            unitTestFiles = request.files.getlist('archivosJava')
            current_app.logger.info(f' ENUNCIADO: {enunciadoFile}')
            if nombreEjercicio:
                ejercicio.nombre = nombreEjercicio
                current_app.logger.info(f'nuevo nombre: {nombreEjercicio}')
                db.session.commit()
            if enunciadoFile:
                if os.path.exists(ejercicio.enunciado):
                    path_enunciado = os.path.join("enunciadosEjercicios/", f"Serie_{serie.id}/Ejercicio_{ejercicio.id}/{ejercicio.id}_{ejercicio.nombre}.md")
                    os.remove(ejercicio.enunciado)
                enunciadoFile.save(path_enunciado)
                ejercicio.enunciado = path_enunciado
                current_app.logger.info(f'nuevo enunciado: {ejercicio.enunciado}')
                db.session.commit()

            if unitTestFiles:
                try:
                    ruta_carpeta = os.path.join(ejercicio.path_ejercicio, "src", "test", "java", "org")
                    if os.path.exists(ruta_carpeta):
                        for archivo in os.listdir(ruta_carpeta):
                            ruta_archivo = os.path.join(ruta_carpeta, archivo)
                            if os.path.isfile(ruta_archivo):
                                os.remove(ruta_archivo)
                    for unitTestFile in unitTestFiles:
                        nombre_archivo = secure_filename(unitTestFile.filename)
                        ruta_archivo = os.path.join(ruta_carpeta, nombre_archivo)
                        unitTestFile.save(ruta_archivo)
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(f'Ocurrió un error al guardar los archivos .java: {str(e)}')
        elif 'eliminar' in request.form:
            try:
                current_app.logger.info(f'Eliminando el ejercicio {ejercicio.nombre}...')
                Ejercicio_asignado.query.filter_by(id_ejercicio=ejercicio_id).delete()
                db.session.delete(ejercicio)
                try:
                    shutil.rmtree(ejercicio.path_ejercicio)
                    shutil.rmtree(ejercicio.enunciado)
                except Exception as e:
                    current_app.logger.error(f'Ocurrió un error al eliminar el ejercicio: {str(e)}')
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al eliminar el ejercicio: {str(e)}')
                db.session.rollback()
                flash('Error al eliminar el ejercicio', 'danger')
                return redirect(url_for('supervisor.detallesSerie', supervisor_id=supervisor_id, serie_id=serie_id))
            db.session.commit()
            return redirect(url_for('supervisor.detallesEjercicio', supervisor_id=supervisor_id, serie_id=serie_id, ejercicio_id=ejercicio_id))
    return render_template('detallesEjercicios.html', ejercicio=ejercicio, supervisor_id=supervisor_id, enunciado=enunciado_html, serie=serie)

@supervisor_bp.route('/<int:supervisor_id>/registrarEstudiante', methods=['GET', 'POST'])
@login_required
def registrarEstudiantes(supervisor_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('auth.login'))

    cursos = Curso.query.all()

    if request.method == 'GET':
        return render_template('registrarEstudiantes.html', supervisor_id=supervisor_id, cursos=cursos)
    
    if request.method == 'POST':
        try:
            accion = request.form['accion']
            if accion == 'crearCurso':
                nombre_curso = request.form['nombreCurso']
                activa_value = True if request.form.get('activa') == "true" else False
                if not nombre_curso:
                    flash('Por favor, complete todos los campos.', 'danger')
                nuevo_curso = Curso(nombre=nombre_curso, activa=activa_value)
                db.session.add(nuevo_curso)
                db.session.commit()
                flash('Has creado exitosamente un nuevo Curso', 'success')
                return redirect(url_for('supervisor.registrarEstudiantes', supervisor_id=supervisor_id))
            elif accion == 'registrarEstudiantes':
                id_curso = request.form['curso']
                listaClases = request.files['listaClases']
                if listaClases and allowed_file(listaClases.filename, {'csv'}):
                    filename = secure_filename(listaClases.filename)
                    listaClases.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    procesar_archivo_csv(filename, id_curso)
                    return redirect(url_for('supervisor.dashDocente', supervisor_id=supervisor_id))
        except Exception as e:
            current_app.logger.error(f'Ocurrió un error al registrar los estudiantes: {str(e)}')
            db.session.rollback()
            flash('Error al registrar los estudiantes', 'danger')
            return redirect(url_for('supervisor.registrarEstudiantes', supervisor_id=supervisor_id))
    return render_template('registrarEstudiantes.html', supervisor_id=supervisor_id)

@supervisor_bp.route('/<int:supervisor_id>/detalleCurso/<int:curso_id>', methods=['GET', 'POST'])
@login_required
def detallesCurso(supervisor_id, curso_id):
    curso_actual = Curso.query.get(curso_id)
    grupos = Grupo.query.filter_by(id_curso=curso_id).all()
    series = Serie.query.all()
    estudiantes_curso = Estudiante.query.filter(Estudiante.cursos.any(id=curso_id)).all()
    series_asignadas = Serie.query.join(serie_asignada).filter(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos])).all()

    if request.method == 'POST':
        if 'activar_inactivar' in request.form:
            current_app.logger.info(f'Activando o desactivando el curso {curso_actual.nombre}...')
            accion = request.form['activar_inactivar']
            if accion == 'activar':
                curso_actual.activa = True
            elif accion == 'desactivar':
                curso_actual.activa = False
            db.session.commit()
            return redirect(url_for('supervisor.detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
        elif 'submit_action' in request.form and request.form['submit_action'] == 'asignarSerie':
            current_app.logger.info(f'Asignando serie a grupo...')
            serie_seleccionada = request.form.get('series')
            grupo_seleccionado = request.form.get('grupos')
            try:
                if serie_seleccionada and grupo_seleccionado:
                    db.session.execute(serie_asignada.insert().values(id_serie=serie_seleccionada, id_grupo=grupo_seleccionado))
                    db.session.commit()
                    flash('Serie asignada con éxito', 'success')
                    grupos = Grupo.query.filter_by(id_curso=curso_actual.id).all()
                    series = Serie.query.all()
                    return redirect(url_for('supervisor.detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al agregar el ejercicio: {str(e)}')
                db.session.rollback()
                flash('Error al asignar la serie', 'danger')
                return redirect(url_for('supervisor.detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
        elif 'eliminar' in request.form:
            try:
                current_app.logger.info(f'Eliminando el curso {curso_actual.nombre}...')
                grupos = Grupo.query.filter_by(id_curso=curso_id).all()
                series_asignadas = Serie.query.join(serie_asignada).filter(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos])).all()
                db.session.execute(supervisores_grupos.delete().where(supervisores_grupos.c.id_grupo.in_([grupo.id for grupo in grupos])))
                id_series_asignadas = [serie.id for serie in series_asignadas]
                db.session.execute(serie_asignada.delete().where(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos])))
                estudiantesEnGrupos = db.session.query(estudiantes_grupos).filter(estudiantes_grupos.c.id_grupo.in_([grupo.id for grupo in grupos])).all()
                id_estudiantes_grupos = [estudiante.id_estudiante for estudiante in estudiantesEnGrupos]
                ejercicios_a_eliminar = db.session.query(Ejercicio_asignado).filter(Ejercicio_asignado.id_estudiante.in_(id_estudiantes_grupos)).all()
                if ejercicios_a_eliminar:
                    for ejercicio in ejercicios_a_eliminar:
                        db.session.delete(ejercicio)
                db.session.execute(estudiantes_grupos.delete().where(estudiantes_grupos.c.id_grupo.in_([grupo.id for grupo in grupos])))
                if grupos:
                    for grupo in grupos:
                        db.session.delete(grupo)
                db.session.execute(inscripciones.delete().where(inscripciones.c.id_curso == curso_id))
                for id_estudiante in id_estudiantes_grupos:
                    estudiante = Estudiante.query.get(id_estudiante)
                    if estudiante:
                        db.session.delete(estudiante)
                db.session.delete(curso_actual)
                db.session.commit()
                current_app.logger.info(f'Curso eliminado correctamente.')
                return redirect(url_for('supervisor.dashDocente', supervisor_id=supervisor_id))
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al eliminar el curso: {str(e)}')
                db.session.rollback()
                flash('Ocurrió un error al eliminar el curso.', 'danger')
                return redirect(url_for('supervisor.detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
        else:
            current_app.logger.error(f'Acción no reconocida: {request.form}')
            return redirect(url_for('supervisor.detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
    return render_template('detallesCurso.html', supervisor_id=supervisor_id, curso=curso_actual, grupos=grupos, series_asignadas=series_asignadas, estudiantes_curso=estudiantes_curso, series=series)

@supervisor_bp.route('/<int:supervisor_id>/asignarGrupos/<int:curso_id>', methods=['GET', 'POST'])
@login_required
def asignarGrupos(supervisor_id, curso_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('auth.login'))

    cursos = Curso.query.all()

    if not cursos:
        flash('No existen cursos, por favor crear un curso', 'danger')
        return redirect(url_for('supervisor.dashDocente', supervisor_id=supervisor_id))
    
    estudiantes_curso = Estudiante.query.filter(Estudiante.cursos.any(id=curso_id)).all()
    if request.method == 'POST':
        accion = request.form['accion']
        if accion == 'seleccionarCurso':
            id_curso_seleccionado = request.form['curso']
            flash(f'se cambio el curso a {id_curso_seleccionado}', 'success')
            return redirect(url_for('supervisor.asignarGrupos', supervisor_id=supervisor_id, curso_id=id_curso_seleccionado))
        elif accion == 'seleccionarEstudiantes':
            estudiantes_seleccionados_ids = request.form.getlist('estudiantes[]')
            nombre_grupo = request.form['nombreGrupo']
            id_curso_seleccionado = request.form['curso_seleccionado']
            if not nombre_grupo or not estudiantes_seleccionados_ids or not id_curso_seleccionado:
                flash('Por favor, complete todos los campos.', 'danger')
                return redirect(url_for('supervisor.asignarGrupos', supervisor_id=supervisor_id, curso_id=id_curso_seleccionado))
            try:
                flash(f'estudiantes seleccionados: {estudiantes_seleccionados_ids}', 'danger')
                nuevo_grupo = Grupo(nombre=nombre_grupo, id_curso=id_curso_seleccionado)
                db.session.add(nuevo_grupo)
                db.session.commit()
                flash('Grupo creado con éxito', 'success')
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al agregar el grupo: {str(e)}')
                db.session.rollback()
            if nuevo_grupo:
                for estudiante_id in estudiantes_seleccionados_ids:
                    try:
                        nueva_relacion = estudiantes_grupos.insert().values(id_estudiante=estudiante_id, id_grupo=nuevo_grupo.id)
                        db.session.execute(nueva_relacion)
                        db.session.commit()
                        flash('Estudiantes asignados con éxito', 'success')
                    except Exception as e:
                        current_app.logger.error(f'Ocurrió un error al asignar estudiantes: {str(e)}')
                        db.session.rollback()
                try:
                    nuevo_registro = supervisores_grupos.insert().values(id_supervisor=supervisor_id, id_grupo=nuevo_grupo.id)
                    db.session.execute(nuevo_registro)
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(f'Ocurrió un error al asignar el supervisor al grupo: {str(e)}')
                    db.session.rollback()
    return render_template('asignarGrupos.html', supervisor_id=supervisor_id, cursos=cursos, curso_seleccionado=curso_id, estudiantes_curso=estudiantes_curso)

@supervisor_bp.route('/<int:supervisor_id>/detalleCurso/<int:curso_id>/detalleGrupo/<int:grupo_id>', methods=['GET', 'POST'])
@login_required
def detallesGrupo(supervisor_id, curso_id, grupo_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('auth.login'))
    grupo = Grupo.query.get(grupo_id)
    curso = Curso.query.get(curso_id)
    estudiantes = Estudiante.query.filter(Estudiante.cursos.any(id=curso_id)).all()
    estudiantes_grupo = Estudiante.query.join(estudiantes_grupos).filter(estudiantes_grupos.c.id_grupo == grupo_id).all()

    if request.method == 'POST':
        if 'eliminar' in request.form:
            try:
                db.session.execute(serie_asignada.delete().where(serie_asignada.c.id_grupo == grupo_id))
                db.session.execute(estudiantes_grupos.delete().where(estudiantes_grupos.c.id_grupo == grupo_id))
                db.session.execute(supervisores_grupos.delete().where(supervisores_grupos.c.id_grupo == grupo_id))
                db.session.delete(grupo)
                db.session.commit()
                current_app.logger.info(f'Grupo eliminado correctamente.')
                return redirect(url_for('supervisor.detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al eliminar el grupo: {str(e)}')
                db.session.rollback()
                flash('Ocurrió un error al eliminar el grupo.', 'danger')
                return redirect(url_for('supervisor.detallesGrupo', supervisor_id=supervisor_id, curso_id=curso_id, grupo_id=grupo578_id))
        elif 'renombrar' in request.form:
            current_app.logger.info(f'Recibiendo formulario para renombrar el grupo...')
            try:
                current_app.logger.info(f'Renombrando el grupo {grupo.nombre}...')
                grupo.nombre = request.form.get('nuevo_nombre')
                db.session.commit()
                return redirect(url_for('supervisor.detallesGrupo', supervisor_id=supervisor_id, curso_id=curso_id, grupo_id=grupo_id))
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al renombrar el grupo: {str(e)}')
                db.session.rollback()
                return redirect(url_for('supervisor.detallesGrupo', supervisor_id=supervisor_id, curso_id=curso_id, grupo_id=grupo_id))
        else:
            current_app.logger.error(f'Acción no reconocida: {request.form}')
    return render_template('detallesGrupo.html', supervisor_id=supervisor_id, grupo=grupo, estudiantes_grupo=estudiantes_grupo, curso=curso)

@supervisor_bp.route('/<int:supervisor_id>/detalleCurso/<int:curso_id>/detalleGrupo/<int:grupo_id>/eliminarEstudiante', methods=['GET', 'POST'])
@login_required
def eliminarEstudiante(supervisor_id, curso_id, grupo_id):
    curso = Curso.query.get(curso_id)
    grupo = Grupo.query.get(grupo_id)
    estudiantesEnGrupos = db.session.query(estudiantes_grupos).filter(estudiantes_grupos.c.id_grupo == grupo.id).all()
    id_estudiantes_grupos = [estudiante.id_estudiante for estudiante in estudiantesEnGrupos]
    estudiantes = []
    for estudiante_id in id_estudiantes_grupos:
        estudiante = Estudiante.query.get(estudiante_id)
        if estudiante:
            estudiantes.append(estudiante)
    return render_template('eliminarEstudiante.html', supervisor_id=supervisor_id, curso=curso, grupo=grupo, estudiantes=estudiantes)

@supervisor_bp.route('/<int:supervisor_id>/detalleCurso/<int:curso_id>/detalleEstudiante/<int:estudiante_id>', methods=['GET', 'POST'])
@login_required
def detallesEstudiante(supervisor_id, curso_id, estudiante_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('auth.login'))
    
    estudiante = Estudiante.query.get(estudiante_id)
    cursos = []
    grupos = []
    
    consulta_cursos = db.session.query(inscripciones).filter_by(id_estudiante=estudiante_id, id_curso=curso_id).all()
    if consulta_cursos:
        for consulta in consulta_cursos:
            curso = Curso.query.get(consulta.id_curso)
            cursos.append(curso)
    if not cursos:
        cursos = None
        grupos = None
    
    consulta_grupos = db.session.query(estudiantes_grupos).filter_by(id_estudiante=estudiante_id).all()
    if consulta_grupos:
        for consulta in consulta_grupos:
            grupo = Grupo.query.get(consulta.id_grupo)
            grupos.append(grupo)
    if not grupos:
        grupos = None

    series_asignadas = []
    ejercicios = []
    consulta_id_series = db.session.query(serie_asignada).filter(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos])).all()
    if consulta_id_series:
        for consulta in consulta_id_series:
            serie = Serie.query.get(consulta.id_serie)
            ejercicios = Ejercicio.query.filter_by(id_serie=serie.id).all()
            series_asignadas.append(serie)
    if not series_asignadas:
        series_asignadas = None
    
    ejercicios_asignados = Ejercicio_asignado.query.filter_by(id_estudiante=estudiante_id).all()
    ejercicios = []
    if ejercicios_asignados:
        for ejercicio_asignado in ejercicios_asignados:
            ejercicio = Ejercicio.query.get(ejercicio_asignado.id_ejercicio)
            ejercicios.append(ejercicio)
    
    curso_actual = Curso.query.get(curso_id)
    current_app.logger.info(f'series_asignadas: {series_asignadas}')
    current_app.logger.info(f'cursos: {cursos}, grupos: {grupos}')
    current_app.logger.info(f'ejercicio: {ejercicios}, ejercicios_asignados: {ejercicios_asignados}')
    return render_template('detallesEstudiantes.html', supervisor_id=supervisor_id, estudiante=estudiante, curso_actual=curso_actual, cursos=cursos, grupos=grupos, series_asignadas=series_asignadas, ejercicios_asignados=ejercicios_asignados)

@supervisor_bp.route('/<int:supervisor_id>/detalleCurso/<int:curso_id>/detalleEstudiante/<int:estudiante_id>/examinarEjercicio/<int:ejercicio_id>', methods=['GET', 'POST'])
@login_required
def examinarEjercicio(supervisor_id, curso_id, estudiante_id, ejercicio_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('auth.login'))
    estudiante = Estudiante.query.get(estudiante_id)
    ejercicio = Ejercicio.query.get(ejercicio_id)
    ejercicio_asignado = Ejercicio_asignado.query.filter_by(id_estudiante=estudiante_id, id_ejercicio=ejercicio_id).first()
    serie = Serie.query.get(ejercicio.id_serie)
    grupo = Grupo.query.join(serie_asignada).filter(serie_asignada.c.id_serie == serie.id).first()
    curso = Curso.query.get(curso_id)
    estado = ejercicio_asignado.estado
    test_output = ejercicio_asignado.test_output
    fecha_ultimo_envio = ejercicio_asignado.fecha_ultimo_envio
    contador = ejercicio_asignado.contador
    test_output_dict = json.loads(test_output)
    if ejercicio and ejercicio.enunciado:
        with open(ejercicio.enunciado, 'r') as enunciado_file:
            enunciado_markdown = enunciado_file.read()
            enunciado_html = markdown.markdown(enunciado_markdown)
    else:
        enunciado_html = "<p>El enunciado no está disponible.</p>"

    rutaEnvio = ejercicio_asignado.ultimo_envio
    current_app.logger.info(f'rutaEnvio: {rutaEnvio}')
    archivos_java = []
    for archivo in os.listdir(rutaEnvio):
        if archivo.endswith('.java'):
            with open(os.path.join(rutaEnvio, archivo), 'r') as f:
                contenido = f.read()
                archivos_java.append({'nombre': archivo, 'contenido': contenido})

    return render_template('examinarEjercicio.html', supervisor_id=supervisor_id, estudiante=estudiante, ejercicio=ejercicio, serie=serie, grupo=grupo, curso=curso, ejercicio_asignado=ejercicio_asignado, enunciado=enunciado_html, archivos_java=archivos_java, estado=estado, fecha_ultimo_envio=fecha_ultimo_envio, test_output=test_output_dict, contador=contador)

@supervisor_bp.route('/<int:supervisor_id>/progresoCurso/<int:curso_id>', methods=['GET', 'POST'])
@login_required
def progresoCurso(supervisor_id, curso_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('auth.login'))

    curso = Curso.query.get(curso_id)
    estudiantes_curso = Estudiante.query.filter(Estudiante.cursos.any(id=curso_id)).all()
    grupos_curso = Grupo.query.filter_by(id_curso=curso_id).all()
    series_asignadas = Serie.query.join(serie_asignada).filter(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos_curso])).all()

    if request.method == 'POST':
        serie_seleccionada_id = request.form.get('serie')
        ejercicios = Ejercicio.query.filter_by(id_serie=serie_seleccionada_id).all()
        ejercicios_asignados = Ejercicio_asignado.query.filter(
            Ejercicio_asignado.id_estudiante.in_([estudiante.id for estudiante in estudiantes_curso]),
            Ejercicio_asignado.id_ejercicio.in_([ejercicio.id for ejercicio in ejercicios])
        ).all()

        colores_info = []
        for estudiante in estudiantes_curso:
            estudiante_info = {'nombre': f'{estudiante.nombres} {estudiante.apellidos}', 'ejercicios': [], 'calificacion': None}
            total_puntos = len(ejercicios)
            puntos_obtenidos = 0

            for ejercicio in ejercicios:
                ejercicio_asignado = next(
                    (ea for ea in ejercicios_asignados if ea.id_estudiante == estudiante.id and ea.id_ejercicio == ejercicio.id), None
                )
                if ejercicio_asignado and ejercicio_asignado.estado:
                    puntos_obtenidos += 1
                if ejercicio_asignado:
                    intentos = ejercicio_asignado.contador
                    if ejercicio_asignado.estado:
                        estudiante_info['ejercicios'].append({'id': ejercicio.id, 'color': 'success', 'intentos': intentos})
                    elif not ejercicio_asignado.estado and intentos > 0:
                        estudiante_info['ejercicios'].append({'id': ejercicio.id, 'color': 'danger', 'intentos': intentos})
                    else:
                        estudiante_info['ejercicios'].append({'id': ejercicio.id, 'color': 'info', 'intentos': intentos})
                else:
                    estudiante_info['ejercicios'].append({'id': ejercicio.id, 'color': 'info', 'intentos': 0})

            if puntos_obtenidos is not None:
                estudiante_info['calificacion'] = calcular_calificacion(total_puntos, puntos_obtenidos)
            colores_info.append(estudiante_info)

        return render_template('progresoCurso.html', supervisor_id=supervisor_id, curso=curso, estudiantes_curso=estudiantes_curso, series_asignadas=series_asignadas, ejercicios=ejercicios, colores_info=colores_info)
    return render_template('progresoCurso.html', supervisor_id=supervisor_id, curso=curso, estudiantes_curso=estudiantes_curso, series_asignadas=series_asignadas)