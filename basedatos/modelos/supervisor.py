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
from ...app.utils import verify_supervisor, allowed_file

@app.route('/dashDocente/<int:supervisor_id>', methods=['GET', 'POST'])
@login_required
def dashDocente(supervisor_id):
    # Usa la función de verificación
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('login'))
    
    series = Serie.query.all()
    cursos = Curso.query.all()
    ejercicios = Ejercicio.query.all()
    ejercicios_por_serie = {}

    # Verificar si hay cursos, series y ejercicios
    curso_seleccionado_id=None
    grupos = []
    if not cursos:
        flash('No existen cursos, por favor crear un curso', 'danger')
        id_curso_seleccionado=None

    if not series:
        flash('No existen series, por favor crear una serie', 'danger')

    if not ejercicios:
        flash('No existen ejercicios, por favor crear un ejercicio', 'danger')

    # Si no se selecciona un curso o se selecciona el primer curso, busca los grupos del primer curso en tu base de datos.
    if curso_seleccionado_id is None or curso_seleccionado_id == 1:  # Ajusta el 1 al ID del primer curso en tu base de datos
        # primer_curso = Curso.query.get(1)  # Obtén el primer curso por ID
        primer_curso = session.get(1)
        if primer_curso:
            grupos = Grupo.query.filter_by(id_curso=curso_seleccionado_id)

    if request.method == 'POST':
        if request.form['accion']=='seleccionarCurso':
            curso_seleccionado_id = int(request.form['curso'])
            # Con el ID del curso seleccionado, se obtienen los grupos asociados
            grupos = Grupo.query.filter_by(id_curso=curso_seleccionado_id).all()
            series = Serie.query.all()
            return render_template('vistaDocente.html', supervisor_id=supervisor_id, cursos=cursos, grupos=grupos, id_curso_seleccionado=curso_seleccionado_id,series=series)
        if request.form['accion']=='asignarSeri189410.pts-0.pa3p2es':
            serie_seleccionada= request.form.get('series')
            grupo_seleccionado= request.form.get('grupos')
            try:
                if serie_seleccionada and grupo_seleccionado: 
                    db.session.execute(serie_asignada.insert().values(id_serie=serie_seleccionada, id_grupo=grupo_seleccionado))
                    db.session.commit()
                    flash('Serie asignada con éxito', 'success')
                    grupos = Grupo.query.filter_by(id_curso=curso_seleccionado_id).all()
                    series = Serie.query.all()
                    return redirect(url_for('dashDocente', supervisor_id=supervisor_id))
            except Exception as e:
                db.session.rollback()
                flash('Error al asignar la serie', 'danger')
                return redirect(url_for('dashDocente', supervisor_id=supervisor_id))

    # Luego, busca los grupos asociados al curso seleccionado, si hay uno.
    grupos = []
    if curso_seleccionado_id is not None:
        grupos = Grupo.query.filter_by(curso_id=curso_seleccionado_id).all()

    return render_template('vistaDocente.html', supervisor_id=supervisor_id, cursos=cursos, grupos=grupos, curso_seleccionado_id=curso_seleccionado_id,series=series)

@app.route('/dashDocente/<int:supervisor_id>/cuentaDocente', methods=['GET', 'POST'])
@login_required
def cuentaDocente(supervisor_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('login'))
    
    supervisor = Supervisor.query.get(supervisor_id)

    if request.method == 'POST':
        contraseña_actual = request.form.get('contraseña_actual')
        nueva_contraseña = request.form.get('nueva_contraseña')
        confirmar_nueva_contraseña = request.form.get('confirmar_nueva_contraseña')

        # Validaciones
        if not check_password_hash(supervisor.password, contraseña_actual):
            flash('Contraseña actual incorrecta', 'danger')
        elif len(nueva_contraseña) < 10:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'danger')
        elif nueva_contraseña != confirmar_nueva_contraseña:
            flash('Las nuevas contraseñas no coinciden', 'danger')
        else:
            # Cambiar la contraseña
            supervisor.password = generate_password_hash(nueva_contraseña)
            db.session.commit()
            flash('Contraseña actualizada correctamente', 'success')

    return render_template('cuentaDocente.html', supervisor=supervisor, supervisor_id=supervisor_id)


@app.route('/dashDocente/<int:supervisor_id>/agregarSerie', methods=['GET', 'POST'])
@login_required
def agregarSerie(supervisor_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombreSerie= request.form.get('nombreSerie')
        activa_value = True if request.form.get('activa') == "true" else False

        if not (nombreSerie):
            flash('Por favor, complete todos los campos.', 'danger')
            return redirect(url_for('agregarSerie', supervisor_id=supervisor_id))
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
    
@app.route('/dashDocente/<int:supervisor_id>/agregarEjercicio', methods=['GET', 'POST'])
@login_required
def agregarEjercicio(supervisor_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('login'))

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

            if not any(allowed_file(file.filename, '.java') for file in unitTestFiles):
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

            # Guardar enunciado
            nuevoNombre = str(nuevo_ejercicio.id) + "_" + str(nuevo_ejercicio.nombre) + ".md"
            enunciadoFile.save(os.path.join(rutaEnunciadoEjercicios, nuevoNombre))
            nuevo_ejercicio.path_ejercicio = rutaEjercicio
            nuevo_ejercicio.enunciado = os.path.join(rutaEnunciadoEjercicios, nuevoNombre)


            if imagenesFiles[0].filename:
                for imagenFile in imagenesFiles:
                    imagen_filename = secure_filename(imagenFile.filename)
                    imagenFile.save(os.path.join(rutaEnunciadoEjercicios, imagen_filename))
            else:
                current_app.logger.warning('No se encontraron imágenes en el enunciado.')

            ubicacionTest = os.path.join(rutaEjercicio, "src/test/java/org/example")
            os.makedirs(ubicacionTest, exist_ok=True)

            # Guardar archivos .java en la carpeta
            for unitTestFile in unitTestFiles:
                nombre_archivo = secure_filename(unitTestFile.filename)
                unitTestFile.save(os.path.join(ubicacionTest, nombre_archivo))

            db.session.commit()
            flash('Ejercicio agregado con éxito', 'success')
            return redirect(url_for('agregarEjercicio', supervisor_id=supervisor_id))

        except Exception as e:
            current_app.logger.error(f'Ocurrió un error al agregar el ejercicio: {str(e)}')
            # Si se produce un error, revertir y eliminar carpetas
            if filepath_ejercicio is not None and os.path.exists(filepath_ejercicio):
                shutil.rmtree(filepath_ejercicio)
            if rutaEnunciadoEjercicios is not None and os.path.exists(rutaEnunciadoEjercicios):
                shutil.rmtree(rutaEnunciadoEjercicios)
            db.session.rollback()
            return redirect(url_for('agregarEjercicio', supervisor_id=supervisor_id, series=series))

    return render_template('agregarEjercicio.html', supervisor_id=supervisor_id, series=series)