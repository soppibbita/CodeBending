from datetime import datetime, timedelta
import os, shutil
from sqlite3 import IntegrityError
from click import DateTime
from flask import Flask, make_response, render_template, request, url_for, redirect, jsonify, session, flash, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from wtforms import FileField, SubmitField, PasswordField, StringField, DateField, BooleanField, validators, FileField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, Length, ValidationError
from funciones_archivo.manejoArchivosJava import eliminarPackages, agregarPackage
from funciones_archivo.manejoCarpetas import agregarCarpetaSerieEstudiante,crearCarpetaSerie, crearCarpetaEjercicio, crearArchivadorEstudiante, agregarCarpetaEjercicioEstudiante
from funciones_archivo.manejoMaven import ejecutarTestUnitario
from werkzeug.security import check_password_hash, generate_password_hash, check_password_hash
from DBManager import db, init_app
from basedatos.modelos import Supervisor, Grupo, Serie, Estudiante, Ejercicio, Ejercicio_asignado, Curso, serie_asignada, inscripciones, estudiantes_grupos, supervisores_grupos
from pathlib import Path
import markdown
import csv
import logging
from logging.config import dictConfig
from ansi2html import Ansi2HTMLConverter
import json

from ...app.app import app
from ...app.utils import verify_supervisor, verify_estudiante, calcular_calificacion

@app.route('/dashDocente/<int:supervisor_id>/serie/<int:serie_id>/ejercicio/<int:ejercicio_id>', methods=['GET','POST'])
@login_required
def detallesEjercicio(supervisor_id, serie_id, ejercicio_id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))
    ejercicio = Ejercicio.query.get(ejercicio_id)
    serie= Serie.query.get(serie_id)
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
                ejercicio.nombre=nombreEjercicio
                current_app.logger.info(f'nuevo nombre: {nombreEjercicio}')
                db.session.commit()
            if enunciadoFile :
                if os.path.exists(ejercicio.enunciado):
                    path_enunciado = os.path.join("enunciadosEjercicios/", f"Serie_{serie.id}"+"/"+f"Ejercicio_{ejercicio.id}"+"/"+ str(ejercicio.id) + "_" + ejercicio.nombre + ".md")
                    os.remove(ejercicio.enunciado)
                enunciadoFile.save(path_enunciado)
                ejercicio.enunciado = path_enunciado
                current_app.logger.info(f'nuevo enunciado: {ejercicio.enunciado}')  
                db.session.commit()

            # if imagenesFiles :
            #     for imagenFile in imagenesFiles:
            #         imagen_filename = secure_filename(imagenFile.filename)
            #         imagenFile.save(os.path.join(ejercicio.enunciado, imagen_filename))


            if unitTestFiles :
                try:
                    # Define la ruta de la carpeta org/example
                    ruta_carpeta = os.path.join(ejercicio.path_ejercicio , "src", "test", "java", "org")

                    # Verifica si la carpeta existe
                    if os.path.exists(ruta_carpeta):
                        # Elimina todos los archivos en la carpeta
                        for archivo in os.listdir(ruta_carpeta):
                            ruta_archivo = os.path.join(ruta_carpeta, archivo)
                            # Verifica si es un archivo y lo elimina
                            if os.path.isfile(ruta_archivo):
                                os.remove(ruta_archivo)

                    # Guarda los nuevos archivos .java en la carpeta org/example
                    for unitTestFile in unitTestFiles:
                        nombre_archivo = secure_filename(unitTestFile.filename)
                        # Construye la ruta completa para guardar el archivo en la carpeta org/example
                        ruta_archivo = os.path.join(ruta_carpeta, nombre_archivo)
                        # Guarda el archivo en la ruta construida
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
                return redirect(url_for('detallesSerie', supervisor_id=supervisor_id, serie_id=serie_id))
            db.session.commit()
            
            return redirect(url_for('detallesEjercicio', supervisor_id=supervisor_id,serie_id=serie_id, ejercicio_id=ejercicio_id))
    return render_template('detallesEjercicios.html', ejercicio=ejercicio, supervisor_id=supervisor_id, enunciado=enunciado_html, serie=serie)


@app.route('/dashDocente/<int:supervisor_id>/detalleCurso/<int:curso_id>/detalleEstudiante/<int:estudiante_id>/examinarEjercicio/<int:ejercicio_id>', methods=['GET', 'POST'])
@login_required
def examinarEjercicio(supervisor_id, curso_id, estudiante_id, ejercicio_id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))
    estudiante = Estudiante.query.get(estudiante_id)
    ejercicio = Ejercicio.query.get(ejercicio_id)
    ejercicio_asignado= Ejercicio_asignado.query.filter_by(id_estudiante=estudiante_id, id_ejercicio=ejercicio_id).first()
    serie = Serie.query.get(ejercicio.id_serie)
    grupo = Grupo.query.join(serie_asignada).filter(serie_asignada.c.id_serie == serie.id).first()
    curso= Curso.query.get(curso_id)
    estado = ejercicio_asignado.estado
    test_output= ejercicio_asignado.test_output
    fecha_ultimo_envio= ejercicio_asignado.fecha_ultimo_envio
    contador= ejercicio_asignado.contador
    test_output_dict = json.loads(test_output)
    if ejercicio and ejercicio.enunciado:
        with open(ejercicio.enunciado, 'r') as enunciado_file:
            enunciado_markdown = enunciado_file.read()
            enunciado_html = markdown.markdown(enunciado_markdown)
    else:
        enunciado_html = "<p>El enunciado no está disponible.</p>"

    rutaEnvio = ejercicio_asignado.ultimo_envio
    current_app.logger.info(f'rutaEnvio: {rutaEnvio}')
    archivos_java=[]
    # Obtener la lista de archivos .java en la carpeta
    for archivo in os.listdir(rutaEnvio):
        if archivo.endswith('.java'):
            with open(os.path.join(rutaEnvio, archivo), 'r') as f:
                contenido = f.read()
                archivos_java.append({'nombre': archivo, 'contenido': contenido})

    return render_template('examinarEjercicio.html', supervisor_id=supervisor_id, estudiante=estudiante, ejercicio=ejercicio, serie=serie, grupo=grupo, curso=curso, ejercicio_asignado=ejercicio_asignado, enunciado=enunciado_html, archivos_java=archivos_java, estado=estado, fecha_ultimo_envio=fecha_ultimo_envio, test_output=test_output_dict, contador=contador)


@app.route('/dashEstudiante/<int:estudiante_id>/serie/<int:serie_id>/ejercicio/<int:ejercicio_id>', methods=['GET', 'POST'])
@login_required
def detallesEjerciciosEstudiantes(estudiante_id, serie_id, ejercicio_id):
    if not verify_estudiante(estudiante_id):
        return redirect(url_for('login'))

    serie = Serie.query.get(serie_id)
    ejercicio = Ejercicio.query.get(ejercicio_id)
    matricula= Estudiante.query.get(estudiante_id).matricula
    ejercicios = Ejercicio.query.filter_by(id_serie=serie_id).all()
    ejercicios_asignados = (
        Ejercicio_asignado.query
        .filter(Ejercicio_asignado.id_estudiante == estudiante_id)
        .filter(Ejercicio_asignado.id_ejercicio.in_([ejercicio.id for ejercicio in ejercicios]))
        .all()
    )
    
    colors_info = []

    for ejercicio_disponible in ejercicios:
        ejercicio_info = {'nombre': ejercicio_disponible.nombre, 'id': ejercicio_disponible.id, 'color': 'bg-persian-indigo-opaco'}
            
        for ejercicio_asignado in ejercicios_asignados:
            if ejercicio_disponible.id == ejercicio_asignado.id_ejercicio:
                if ejercicio_asignado.estado:
                    ejercicio_info['color'] = 'bg-success-custom'
                elif not ejercicio_asignado.estado and ejercicio_asignado.contador > 0:
                    ejercicio_info['color'] = 'bg-danger-custom'
                    
        colors_info.append(ejercicio_info)

    ejercicios_aprobados = sum(1 for ea in ejercicios_asignados if ea.estado)

    total_ejercicios = len(ejercicios)
    if total_ejercicios == 0:
        calificacion=0
    else:
        calificacion = calcular_calificacion(total_ejercicios, ejercicios_aprobados)
    
    if ejercicio and ejercicio.enunciado:
        with open(ejercicio.enunciado, 'r') as enunciado_file:
            enunciado_markdown = enunciado_file.read()
            enunciado_html = markdown.markdown(enunciado_markdown)
    else:
        enunciado_html = "<p>El enunciado no está disponible.</p>"

    if request.method == 'POST':
        archivos_java = request.files.getlist('archivo_java')
        rutaArchivador=None
        try:
            rutaArchivador = crearArchivadorEstudiante(matricula)
            flash('Se creo exitosamente el archivador', 'success')
        except Exception as e:
            current_app.logger.error(f'Ocurrió un error al crear el archivador: {str(e)}')
            return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)

        if os.path.exists(rutaArchivador):
            ejercicioAsignado = Ejercicio_asignado.query.filter_by(id_estudiante=estudiante_id, id_ejercicio=ejercicio.id).first()
            if not ejercicioAsignado:
                try:
                    nuevoEjercicioAsignado = Ejercicio_asignado(
                    id_estudiante=estudiante_id,
                    id_ejercicio=ejercicio_id,
                    contador=0,
                    estado=False,
                    ultimo_envio=None,
                    fecha_ultimo_envio=datetime.now(),
                    test_output=None)
                    db.session.add(nuevoEjercicioAsignado)
                    db.session.flush()
                    try:
                        rutaSerieEstudiante = agregarCarpetaSerieEstudiante(rutaArchivador, serie.id)
                        current_app.logger.info(f'Ruta serie estudiante: {rutaSerieEstudiante}')
                        if os.path.exists(rutaSerieEstudiante):
                            try:
                                rutaEjercicioEstudiante = agregarCarpetaEjercicioEstudiante(rutaSerieEstudiante, ejercicio.id,  ejercicio.path_ejercicio)
                                current_app.logger.info(f'Ruta ejercicio estudiante: {rutaEjercicioEstudiante}')
                                if os.path.exists(rutaEjercicioEstudiante):
                                    for archivo_java in archivos_java:
                                        rutaFinal = os.path.join(rutaEjercicioEstudiante, 'src/main/java/org/example')
                                        if archivo_java and archivo_java.filename.endswith('.java'):
                                            archivo_java.save(os.path.join(rutaFinal, archivo_java.filename))
                                            current_app.logger.info(f'Archivo guardado en: {rutaFinal}')
                                    resultadoTest= ejecutarTestUnitario(rutaEjercicioEstudiante)
                                    current_app.logger.info(f'Resultado test: {resultadoTest}')
                                    if resultadoTest == 'BUILD SUCCESS':
                                        current_app.logger.info(f'El test fue exitoso')
                                        nuevoEjercicioAsignado.contador += 1
                                        nuevoEjercicioAsignado.ultimo_envio = rutaFinal
                                        nuevoEjercicioAsignado.fecha_ultimo_envio = datetime.now()
                                        nuevoEjercicioAsignado.test_output = json.dumps(resultadoTest)
                                        nuevoEjercicioAsignado.estado = True
                                        db.session.commit()
                                        errores = {"tipo": "success", "titulo": "Todos los test aprobados", "mensaje": resultadoTest}
                                        return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, errores=errores ,estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                                    else:
                                        current_app.logger.info(f'El test no fue exitoso')
                                        nuevoEjercicioAsignado.contador += 1
                                        nuevoEjercicioAsignado.ultimo_envio = rutaFinal
                                        nuevoEjercicioAsignado.fecha_ultimo_envio = datetime.now()
                                        nuevoEjercicioAsignado.test_output = json.dumps(resultadoTest)
                                        nuevoEjercicioAsignado.estado = False
                                        db.session.commit()
                                        errores= {"tipo": "danger", "titulo": "Errores en la ejecución de pruebas unitarias", "mensaje": resultadoTest}
                                        return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, errores=errores ,estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                            except Exception as e:
                                current_app.logger.error(f'Ocurrió un error al agregar la carpeta del ejercicio: {str(e)}')
                                db.session.rollback()
                                return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                    except Exception as e:
                        current_app.logger.error(f'Ocurrió un error al agregar la carpeta de la serie: {str(e)}')
                        db.session.rollback()
                        # Agregar la eliminación de la carpeta??
                        return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                except Exception as e:
                    current_app.logger.error(f'Ocurrió un error al agregar el ejercicio asignado: {str(e)}')
                    db.session.rollback()
                    # Agregar la eliminación de la carpeta??
                    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
            else:
                try:
                    rutaSerieEstudiante = agregarCarpetaSerieEstudiante(rutaArchivador, serie.id)
                    if os.path.exists(rutaSerieEstudiante):
                        try:
                            rutaEjercicioEstudiante = agregarCarpetaEjercicioEstudiante(rutaSerieEstudiante, ejercicio.id,  ejercicio.path_ejercicio)
                            if os.path.exists(rutaEjercicioEstudiante):
                                for archivo_java in archivos_java:
                                    rutaFinal = os.path.join(rutaEjercicioEstudiante, 'src/main/java/org/example')
                                    if archivo_java and archivo_java.filename.endswith('.java'):
                                        archivo_java.save(os.path.join(rutaFinal, archivo_java.filename))
                                resultadoTest= ejecutarTestUnitario(rutaEjercicioEstudiante)
                                if resultadoTest == 'BUILD SUCCESS':
                                    ejercicioAsignado.contador += 1
                                    ejercicioAsignado.ultimo_envio = rutaFinal
                                    ejercicioAsignado.fecha_ultimo_envio = datetime.now()
                                    ejercicioAsignado.test_output = json.dumps(resultadoTest)
                                    ejercicioAsignado.estado = True
                                    db.session.commit()
                                    errores = {"tipo": "success", "titulo": "Todos los test aprobados", "mensaje": resultadoTest}
                                    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, errores=errores ,estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                                else:
                                    ejercicioAsignado.contador += 1
                                    ejercicioAsignado.ultimo_envio = rutaFinal
                                    ejercicioAsignado.fecha_ultimo_envio = datetime.now()
                                    ejercicioAsignado.test_output = json.dumps(resultadoTest)
                                    ejercicioAsignado.estado = False
                                    db.session.commit()
                                    errores= {"tipo": "danger", "titulo": "Errores en la ejecución de pruebas unitarias", "mensaje": resultadoTest}
                                    current_app.logger.info(f'resultadoTest: {resultadoTest}')
                                    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, errores=errores ,estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                        except Exception as e:
                            db.session.rollback()
                            current_app.logger.error(f'Ocurrió un error al agregar la carpeta del ejercicio: {str(e)}')
                            return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, errores=resultadoTest, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                except Exception as e:
                    current_app.logger.error(f'Ocurrió un error al agregar la carpeta de la serie: {str(e)}')
                    db.session.rollback()

    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados, colors_info=colors_info, calificacion=calificacion)
