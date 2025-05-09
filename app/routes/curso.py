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

from ..app import app
from ..utils import verify_supervisor, calcular_calificacion

@app.route('/dashDocente/<int:supervisor_id>/detalleCurso/<int:curso_id>', methods=['GET','POST'])
@login_required
def detallesCurso(supervisor_id, curso_id):
    curso_actual=Curso.query.get(curso_id)
    grupos=Grupo.query.filter_by(id_curso=curso_id).all()
    series=Serie.query.all()
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
            return redirect(url_for('detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
        elif 'submit_action' in request.form and request.form['submit_action'] == 'asignarSerie':
            current_app.logger.info(f'Asignando serie a grupo...')
            serie_seleccionada= request.form.get('series')
            grupo_seleccionado = request.form.get('grupos')
            try:
                if serie_seleccionada and grupo_seleccionado: 
                    db.session.execute(serie_asignada.insert().values(id_serie=serie_seleccionada, id_grupo=grupo_seleccionado))
                    db.session.commit()
                    flash('Serie asignada con éxito', 'success')
                    grupos = Grupo.query.filter_by(id_curso=curso_actual.id).all()
                    series = Serie.query.all()
                    return redirect(url_for('detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al agregar el ejercicio: {str(e)}')
                db.session.rollback()
                flash('Error al asignar la serie', 'danger')
                return redirect(url_for('detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))    
        elif 'eliminar' in request.form:
            try:
                current_app.logger.info(f'Eliminando el curso {curso_actual.nombre}...')

                # Obtener grupos, y series asignadas a el id_curso
                grupos=Grupo.query.filter_by(id_curso=curso_id).all()
                series_asignadas = Serie.query.join(serie_asignada).filter(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos])).all()
                
                # Borrar los supervisores de los grupos                
                db.session.execute(supervisores_grupos.delete().where(supervisores_grupos.c.id_grupo.in_([grupo.id for grupo in grupos])))
                
                # Guardar el id de las series asignadas a los grupos.
                id_series_asignadas = [serie.id for serie in series_asignadas]

                # Borrar las series asignadas a los grupos
                db.session.execute(serie_asignada.delete().where(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos])))
                
                # Obtener los id_estudiante de los grupos
                estudiantesEnGrupos = db.session.query(estudiantes_grupos).filter(estudiantes_grupos.c.id_grupo.in_([grupo.id for grupo in grupos])).all()
                
                id_estudiantes_grupos = [estudiante.id_estudiante for estudiante in estudiantesEnGrupos]
                
                # Borrar en Ejercicio_asignado todos los registros que tengan el id_estudiante en estudiantesEnGrupos
                ejercicios_a_eliminar=db.session.query(Ejercicio_asignado).filter(Ejercicio_asignado.id_estudiante.in_(id_estudiantes_grupos)).all()
                if ejercicios_a_eliminar:
                    for ejercicio in ejercicios_a_eliminar:
                        db.session.delete(ejercicio)
                        
                # Borrar en tabla estudiantes_grupos, todos los grupos.
                db.session.execute(estudiantes_grupos.delete().where(estudiantes_grupos.c.id_grupo.in_([grupo.id for grupo in grupos])))

                # Borrar los grupos del curso
                if grupos:
                    for grupo in grupos:
                        db.session.delete(grupo)

                # Borrar las inscripciones de los estudiantes en el curso
                db.session.execute(inscripciones.delete().where(inscripciones.c.id_curso == curso_id))

                for id_estudiante in id_estudiantes_grupos:
                    estudiante = Estudiante.query.get(id_estudiante)
                    if estudiante:
                        db.session.delete(estudiante)

                # Borrar el curso
                db.session.delete(curso_actual)

                db.session.commit()
                current_app.logger.info(f'Curso eliminado correctamente.')
                return redirect(url_for('dashDocente', supervisor_id=supervisor_id))
            except Exception as e:
                # Manejar errores y realizar rollback en caso de error
                current_app.logger.error(f'Ocurrió un error al eliminar el curso: {str(e)}')
                db.session.rollback()
                flash('Ocurrió un error al eliminar el curso.', 'danger')
                return redirect(url_for('detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
        else:
            current_app.logger.error(f'Acción no reconocida: {request.form}')
            return redirect(url_for('detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
    return render_template('detallesCurso.html', supervisor_id=supervisor_id, curso=curso_actual, grupos=grupos, series_asignadas=series_asignadas, estudiantes_curso=estudiantes_curso, series=series)




# Ruta para ver el progreso de los estudiantes de un curso
@app.route('/dashDocente/<int:supervisor_id>/progresoCurso/<int:curso_id>', methods=['GET', 'POST'])
@login_required
def progresoCurso(supervisor_id, curso_id):

    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))

    curso = Curso.query.get(curso_id)

    # Recuperar los estudiantes del curso
    estudiantes_curso = Estudiante.query.filter(Estudiante.cursos.any(id=curso_id)).all()

    # Recuperar los grupos del curso
    grupos_curso = Grupo.query.filter_by(id_curso=curso_id).all()

    # Recuperar todas las series asignadas de todos los grupos
    series_asignadas = Serie.query.join(serie_asignada).filter(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos_curso])).all()

    if request.method == 'POST':
        # Obtener el ID de la serie seleccionada desde el formulario
        serie_seleccionada_id = request.form.get('serie')

        # Filtrar ejercicios por la serie seleccionada
        ejercicios = Ejercicio.query.filter_by(id_serie=serie_seleccionada_id).all()

        # Filtrar ejercicios asignados por estudiante y ejercicios de la serie
        ejercicios_asignados = Ejercicio_asignado.query.filter(
            Ejercicio_asignado.id_estudiante.in_([estudiante.id for estudiante in estudiantes_curso]),
            Ejercicio_asignado.id_ejercicio.in_([ejercicio.id for ejercicio in ejercicios])
        ).all()

        # Lógica para asignar colores a las celdas en la tabla
        colores_info = []

        for estudiante in estudiantes_curso:
            estudiante_info = {'nombre': f'{estudiante.nombres} {estudiante.apellidos}', 'ejercicios': [], 'calificacion': None}

            total_puntos = len(ejercicios)  # Total de puntos igual a la cantidad total de ejercicios
            puntos_obtenidos = 0

            for ejercicio in ejercicios:
                ejercicio_asignado = next(
                    (ea for ea in ejercicios_asignados if ea.id_estudiante == estudiante.id and ea.id_ejercicio == ejercicio.id), None
                )

                if ejercicio_asignado and ejercicio_asignado.estado:
                    puntos_obtenidos += 1  # Sumar 1 punto por cada ejercicio aprobado

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

            # Calcula la calificación usando la función calcular_calificacion
            if puntos_obtenidos is not None:
                estudiante_info['calificacion'] = calcular_calificacion(total_puntos, puntos_obtenidos)

            colores_info.append(estudiante_info)

        return render_template('progresoCurso.html', supervisor_id=supervisor_id, curso=curso, estudiantes_curso=estudiantes_curso, series_asignadas=series_asignadas, ejercicios=ejercicios, colores_info=colores_info)
    return render_template('progresoCurso.html', supervisor_id=supervisor_id, curso=curso, estudiantes_curso=estudiantes_curso, series_asignadas=series_asignadas)
