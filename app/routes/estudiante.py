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

from ..utils import verify_supervisor, procesar_archivo_csv, allowed_file, verify_estudiante
from ..app import app, ALLOWED_EXTENSIONS

@app.route('/dashDocente/<int:supervisor_id>/registrarEstudiante', methods=['GET', 'POST'])
@login_required
def registrarEstudiantes(supervisor_id):
    # Ruta para recibir un archivo csv con los datos de los estudiantes y registrarlos en la base de datos
    # Usa la función de verificación
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))

    cursos = Curso.query.all()

    if request.method == 'GET':
        cursos = Curso.query.all()
        return render_template('registrarEstudiantes.html', supervisor_id=supervisor_id, cursos=cursos)
    
    if request.method == 'POST':
        try:
            accion= request.form['accion']
            
            if accion == 'crearCurso':
                #Procesar el formulario y agregarlo a la base de datos
                nombre_curso = request.form['nombreCurso']
                activa_value = True if request.form.get('activa') == "true" else False
                if not (nombre_curso) :
                    flash('Por favor, complete todos los campos.', 'danger')
                nuevo_curso= Curso(
                    nombre=nombre_curso,
                    activa=activa_value
                )
                db.session.add(nuevo_curso)
                db.session.commit()
                flash('Has creado exitosamente un nuevo Curso', 'success')
                return redirect(url_for('registrarEstudiantes', supervisor_id=supervisor_id))
            
            elif accion == 'registrarEstudiantes':
                id_curso=request.form['curso']
                listaClases = request.files['listaClases']
                if listaClases and allowed_file(listaClases.filename, ALLOWED_EXTENSIONS):
                    filename = secure_filename(listaClases.filename)
                    listaClases.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                    # Procesa el archivo y agrega a la bd
                    procesar_archivo_csv(filename, id_curso)

                    return redirect(url_for('dashDocente', supervisor_id=supervisor_id))
        except Exception as e:
            current_app.logger.error(f'Ocurrió un error al registrar los estudiantes: {str(e)}')
            db.session.rollback()
            flash('Error al registrar los estudiantes', 'danger')
            return redirect(url_for('registrarEstudiantes', supervisor_id=supervisor_id))
    return render_template('registrarEstudiantes.html', supervisor_id=supervisor_id)


@app.route('/dashDocente/<int:supervisor_id>/detalleCurso/<int:curso_id>/detalleEstudiante/<int:estudiante_id>', methods=['GET', 'POST'])
@login_required
def detallesEstudiante(supervisor_id, curso_id, estudiante_id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))
    
    estudiante = Estudiante.query.get(estudiante_id)
    cursos = []
    grupos = []
    
    # Obtener cursos
    consulta_cursos = db.session.query(inscripciones).filter_by(id_estudiante=estudiante_id, id_curso=curso_id).all()
    if consulta_cursos:
        for consulta in consulta_cursos:
            curso = Curso.query.get(consulta.id_curso)
            cursos.append(curso)
    if not cursos:
        cursos = None
        grupos = None
    # Obtener grupos
    consulta_grupos = db.session.query(estudiantes_grupos).filter_by(id_estudiante=estudiante_id).all()
    if consulta_grupos:
        for consulta in consulta_grupos:
            grupo = Grupo.query.get(consulta.id_grupo)
            grupos.append(grupo)
    if not grupos:
        grupos = None

    # Obtener series asignadas
    series_asignadas = []
    ejercicios= []
    consulta_id_series = db.session.query(serie_asignada).filter(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos])).all()
    if consulta_id_series:
        for consulta in consulta_id_series:
            serie = Serie.query.get(consulta.id_serie)
            ejercicios = Ejercicio.query.filter_by(id_serie=serie.id).all()
            series_asignadas.append(serie)
    if not series_asignadas:
        series_asignadas = None
    
    # Obtener ejercicios asignados al estudiante
    ejercicios_asignados = Ejercicio_asignado.query.filter_by(id_estudiante=estudiante_id).all()
    
    # Obtener los ejercicios de las series
    # Crear una lista para almacenar los datos de los ejercicios
    ejercicios = []
    if ejercicios_asignados:
        for ejercicio_asignado in ejercicios_asignados:
            ejercicio = Ejercicio.query.get(ejercicio_asignado.id_ejercicio)
            ejercicios.append(ejercicio)
    
    curso_actual = Curso.query.get(curso_id)
    current_app.logger.info(f'series_asignadas: {series_asignadas}')
    curso_actual = Curso.query.get(curso_id)
    current_app.logger.info(f'cursos: {cursos}, grupos: {grupos}')
    current_app.logger.info(f'ejercicio: {ejercicios}, ejercicios_asignados: {ejercicios_asignados}')
    return render_template('detallesEstudiantes.html', supervisor_id=supervisor_id, estudiante=estudiante, curso_actual=curso_actual, cursos=cursos, grupos=grupos,series_asignadas=series_asignadas, ejercicios_asignados=ejercicios_asignados)




@app.route('/dashEstudiante/<int:estudiante_id>', methods=['GET', 'POST'])
@login_required
def dashEstudiante(estudiante_id):

    if not verify_estudiante(estudiante_id):
        return redirect(url_for('login'))

    estudiante = db.session.get(Estudiante, int(estudiante_id))

    curso = (
        Curso.query
        .join(inscripciones)
        .filter(inscripciones.c.id_estudiante == estudiante_id)
        .filter(Curso.activa == True)
        .first()
    )
    if not curso:
        return render_template('vistaEstudiante.html', estudiante_id=estudiante_id, estudiante=estudiante, curso=None, grupo=None, supervisor=None, seriesAsignadas=None, ejerciciosPorSerie=None)
    # Obtiene el grupo asociado al estudiante
    grupo = (
        Grupo.query
        .join(estudiantes_grupos)  # Join con la tabla estudiantes_grupos
        .filter(estudiantes_grupos.c.id_grupo == Grupo.id)
        .filter(estudiantes_grupos.c.id_estudiante == estudiante_id)
        .first()
    )
    # Si no se encuentra ningún grupo asignado, grupo será None
    if not grupo:
        grupo_nombre = "Ningún grupo asignado"
    else:
        grupo_nombre = grupo.nombre

    supervisor = None

    # Obtiene el supervisor asignado si grupo no es None
    if grupo:
        supervisor = (
            Supervisor.query
            .join(supervisores_grupos)
            .filter(supervisores_grupos.c.id_supervisor == Supervisor.id)
            .filter(supervisores_grupos.c.id_grupo == grupo.id)
            .first()
        )

    seriesAsignadas = []

    # Obtiene las series asignadas solo si grupo no es None
    if grupo:
        seriesAsignadas = (
        Serie.query
        .join(serie_asignada)
        .filter(serie_asignada.c.id_grupo == grupo.id)
        .filter(Serie.activa)  # Filtrar por series activas
        .all()
    )


    # A continuación, puedes obtener los ejercicios para cada serie en series_asignadas
    ejerciciosPorSerie = {}
    for serieAsignada in seriesAsignadas:
        ejercicios = Ejercicio.query.filter_by(id_serie=serieAsignada.id).all()
        ejerciciosPorSerie[serieAsignada] = ejercicios

    return render_template('vistaEstudiante.html', estudiante_id=estudiante_id, estudiante=estudiante,grupo=grupo, curso=curso, supervisor=supervisor,seriesAsignadas=seriesAsignadas,ejerciciosPorSerie=ejerciciosPorSerie)

@app.route('/dashEstudiante/<int:estudiante_id>/cuentaEstudiante', methods=['GET', 'POST'])
@login_required
def cuentaEstudiante(estudiante_id):
    if not verify_estudiante(estudiante_id):
        return redirect(url_for('login'))
    
    estudiante = Estudiante.query.get(estudiante_id)

    if request.method == 'POST':
        contraseña_actual = request.form.get('contraseña_actual')
        nueva_contraseña = request.form.get('nueva_contraseña')
        confirmar_nueva_contraseña = request.form.get('confirmar_nueva_contraseña')

        # Validaciones
        if not check_password_hash(estudiante.password, contraseña_actual):
            flash('Contraseña actual incorrecta', 'danger')
        elif len(nueva_contraseña) < 10:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'danger')
        elif nueva_contraseña != confirmar_nueva_contraseña:
            flash('Las nuevas contraseñas no coinciden', 'danger')
        else:
            # Cambiar la contraseña
            estudiante.password = generate_password_hash(nueva_contraseña)
            db.session.commit()
            flash('Contraseña actualizada correctamente', 'success')

    return render_template('cuentaEstudiante.html', estudiante=estudiante, estudiante_id=estudiante_id)

