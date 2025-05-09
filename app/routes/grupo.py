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
from ..utils import verify_supervisor


@app.route('/dashDocente/<int:supervisor_id>/asignarGrupos/<int:curso_id>', methods=['GET', 'POST'])
@login_required
def asignarGrupos(supervisor_id, curso_id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))

    cursos = Curso.query.all()

    if not cursos:
        flash('No existen cursos, por favor crear un curso', 'danger')
        return redirect(url_for('dashDocente', supervisor_id=supervisor_id))
    
    estudiantes_curso = Estudiante.query.filter(Estudiante.cursos.any(id=curso_id)).all()
    if request.method == 'POST':
        accion = request.form['accion']
        if accion == 'seleccionarCurso':
            id_curso_seleccionado = request.form['curso']
            flash('se cambio el curso a {curso_id}', 'success')
            return redirect(url_for('asignarGrupos', supervisor_id=supervisor_id, curso_id=id_curso_seleccionado))

        elif accion == 'seleccionarEstudiantes':
            # Recibir los estudiantes seleccionados
            estudiantes_seleccionados_ids= request.form.getlist('estudiantes[]')
            # Recibir el nombre del grupo
            nombre_grupo = request.form['nombreGrupo']
            # Recibir el id del curso
            id_curso_seleccionado = request.form['curso_seleccionado']
            if not nombre_grupo or not estudiantes_seleccionados_ids or not id_curso_seleccionado :
                flash('Por favor, complete todos los campos.', 'danger')
                return redirect(url_for('asignarGrupos', supervisor_id=supervisor_id, curso_id=id_curso_seleccionado))

            try:
                # Verificar si el grupo ya existe
                flash(f'estudiantes seleccionados: {estudiantes_seleccionados_ids}', 'danger')
                nuevo_grupo=Grupo(nombre=nombre_grupo, id_curso=id_curso_seleccionado)
                db.session.add(nuevo_grupo)
                db.session.commit()
                flash('Grupo creado con éxito', 'success')

            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al agregar el grupo: {str(e)}')
                db.session.rollback()
            if nuevo_grupo:
                # Con los estudiantes que se seleccionaron, se asocian al grupo creado utilizando tabla asociacion estudiantes_grupos
                for estudiante_id in estudiantes_seleccionados_ids:
                    try:
                        nueva_relacion=estudiantes_grupos.insert().values(id_estudiante=estudiante_id, id_grupo=nuevo_grupo.id)
                        db.session.execute(nueva_relacion)
                        db.session.commit()
                        flash('Estudiantes asignados con éxito', 'success')
                    except Exception as e:
                        current_app.logger.error(f'Ocurrió un error al asignar estudiantes: {str(e)}')
                        db.session.rollback()
                try:
                    nuevo_registro= supervisores_grupos.insert().values(
                        id_supervisor=supervisor_id,
                        id_grupo=nuevo_grupo.id
                    )
                    db.session.execute(nuevo_registro)
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(f'Ocurrió un error al asignar el supervisor al grupo: {str(e)}')
                    db.session.rollback()

    return render_template('asignarGrupos.html', supervisor_id=supervisor_id, cursos=cursos, curso_seleccionado=curso_id,estudiantes_curso=estudiantes_curso)

@app.route('/dashDocente/<int:supervisor_id>/detalleCurso/<int:curso_id>/detalleGrupo/<int:grupo_id>', methods=['GET', 'POST'])
@login_required
def detallesGrupo(supervisor_id, curso_id, grupo_id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))
    grupo=Grupo.query.get(grupo_id)
    curso=Curso.query.get(curso_id)
    estudiantes = Estudiante.query.filter(Estudiante.cursos.any(id=curso_id)).all()
    # Obtener todos los estudiantes que pertenecen al grupo usando tabla asociacion estudiantes_grupos
    estudiantes_grupo = Estudiante.query.join(estudiantes_grupos).filter(estudiantes_grupos.c.id_grupo == grupo_id).all()
    curso=Curso.query.get(curso_id)

    if request.method == 'POST':
        if 'eliminar' in request.form:
            try:
                # Eliminar serie_asignada
                db.session.execute(serie_asignada.delete().where(serie_asignada.c.id_grupo.in_(grupo_id)))
                
                # Eliminar estudiantes_grupos
                db.session.execute(estudiantes_grupos.delete().where(estudiantes_grupos.c.id_grupo.in_(grupo_id)))

                # Eliminar en supervisores_grupos
                db.session.execute(supervisores_grupos.delete().where(supervisores_grupos.c.id_grupo.in_(grupo_id)))

                # Eliminar el grupo
                db.session.delete(grupo)
                db.session.commit()
                current_app.logger.info(f'Grupo eliminado correctamente.')
                return redirect(url_for('detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al eliminar el grupo: {str(e)}')
                db.session.rollback()
                flash('Ocurrió un error al eliminar el grupo.', 'danger')
                return redirect(url_for('detallesGrupo', supervisor_id=supervisor_id, curso_id=curso_id, grupo_id=grupo_id))
        elif 'renombrar' in request.form:
            current_app.logger.info(f'Recibiendo formulario para renombrar el grupo...')
            try:
                current_app.logger.info(f'Renombrando el grupo {grupo.nombre}...')
                grupo.nombre = request.form.get('nuevo_nombre')
                db.session.commit()
                return redirect(url_for('detallesGrupo', supervisor_id=supervisor_id, curso_id=curso_id, grupo_id=grupo_id))
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al renombrar el grupo: {str(e)}')
                db.session.rollback()
                return redirect(url_for('detallesGrupo', supervisor_id=supervisor_id, curso_id=curso_id, grupo_id=grupo_id))
        else :
            current_app.logger.error(f'Acción no reconocida: {request.form}')
    grupo=Grupo.query.get(grupo_id)
    curso=Curso.query.get(curso_id)
    # Obtener todos los estudiantes que pertenecen al grupo usando tabla asociacion estudiantes_grupos
    estudiantes_grupo = Estudiante.query.join(estudiantes_grupos).filter(estudiantes_grupos.c.id_grupo == grupo_id).all()
    return render_template('detallesGrupo.html', supervisor_id=supervisor_id, grupo=grupo, estudiantes_grupo=estudiantes_grupo, curso=curso)

@app.route('/dashDocente/<int:supervisor_id>/detalleCurso/<int:curso_id>/detalleGrupo/<int:grupo_id>/eliminarEstudiante', methods=['GET', 'POST'])
@login_required
def eliminarEstudiante(supervisor_id, curso_id, grupo_id):
    curso= Curso.query.get(curso_id)
    grupo=Grupo.query.get(grupo_id)

    estudiantesEnGrupos = db.session.query(estudiantes_grupos).filter(estudiantes_grupos.c.id_grupo.in_([grupo.id])).all()
    
    id_estudiantes_grupos = [estudiante.id_estudiante for estudiante in estudiantesEnGrupos]
    estudiantes=[]
    for estudiante_id in id_estudiantes_grupos:
        estudiante = Estudiante.query.get(estudiante_id)
        if estudiante:
            estudiantes.append(estudiante)
            

    return render_template('eliminarEstudiante.html', supervisor_id=supervisor_id, curso=curso, grupo=grupo, estudiantes=estudiantes)