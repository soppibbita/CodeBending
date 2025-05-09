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
from ..utils import verify_supervisor, verify_estudiante, calcular_calificacion

@app.route('/dashDocente/<int:supervisor_id>/serie/<int:serie_id>', methods=['GET', 'POST'])
@login_required
def detallesSeries(supervisor_id, serie_id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))

    serie = Serie.query.get(serie_id)
    ejercicios = Ejercicio.query.filter_by(id_serie=serie_id).all()
    grupos_asociados = None
    if serie is not None:
        grupos_asociados = Grupo.query.join(serie_asignada).filter(serie_asignada.c.id_serie == serie.id).all()
    if serie is None:
        grupos_asociados = None
        ejercicios= None

    if request.method == 'POST':
        current_app.logger.info(f'Formulario recibido: {request.form}')
        if 'activar_desactivar' in request.form:
            serie.activa = not serie.activa
            db.session.commit()
            return redirect(url_for('detallesSeries', supervisor_id=supervisor_id, serie_id=serie_id))
        elif 'eliminar' in request.form:
            try:
                current_app.logger.info(f'Eliminando la serie {serie.nombre}...')

                # Eliminar los ejercicios asociados a la serie
                Ejercicio.query.filter_by(id_serie=serie_id).delete()

                # Eliminar las asignaciones de serie a grupos
                db.session.execute(serie_asignada.delete().where(serie_asignada.c.id_serie == serie.id))

                # Eliminar la serie
                db.session.delete(serie)

                # Confirmar los cambios en la base de datos
                db.session.commit()

                # Eliminar los archivos asociados a la serie
                rutaSerie = 'ejerciciosPropuestos/Serie_' + str(serie.id)
                shutil.rmtree(rutaSerie)
                rutaEnunciadoSerie = 'enunciadosEjercicios/Serie_' + str(serie.id)
                shutil.rmtree(rutaEnunciadoSerie)
                # Redireccionar y mostrar un mensaje de éxito
                flash('Serie eliminada correctamente.', 'success')
                return redirect(url_for('dashDocente', supervisor_id=supervisor_id))
            except Exception as e:
                # Manejar errores y realizar rollback en caso de error
                current_app.logger.error(f'Ocurrió un error al eliminar la serie: {str(e)}')
                db.session.rollback()
                flash('Ocurrió un error al eliminar la serie.', 'danger')
                return redirect(url_for('detallesSeries', supervisor_id=supervisor_id, serie_id=serie_id))

        elif 'editar' in request.form:
            try:
                current_app.logger.info(f'Editando la serie {serie.nombre}...')
                serie = Serie.query.get(serie_id)
                serie.nombre = request.form.get('nuevo_nombre')
                db.session.commit()
                current_app.logger.info(f'Serie editada correctamente.')
                return redirect(url_for('detallesSeries', supervisor_id=supervisor_id, serie_id=serie_id))
            except Exception as e:
                current_app.logger.danger(f'Ocurrió un error al editar la serie: {str(e)}')
                db.session.rollback()
                return redirect(url_for('detallesSeries', supervisor_id=supervisor_id, serie_id=serie_id))
    if serie is None:
        return redirect(url_for('dashDocente', supervisor_id=supervisor_id))
    return render_template('detallesSerie.html', serie=serie, ejercicios=ejercicios, supervisor_id=supervisor_id, grupos_asociados=grupos_asociados)




@app.route('/dashEstudiante/<int:estudiante_id>/serie/<int:serie_id>', methods=['GET', 'POST'])
@login_required
def detallesSeriesEstudiantes(estudiante_id, serie_id):

    if not verify_estudiante(estudiante_id):
        return redirect(url_for('login'))
    serie = db.session.get(Serie, serie_id)
    ejercicios = Ejercicio.query.filter_by(id_serie=serie_id).all()
    ejercicios_asignados = (
        Ejercicio_asignado.query
        .filter(Ejercicio_asignado.id_estudiante == estudiante_id)
        .filter(Ejercicio_asignado.id_ejercicio.in_([ejercicio.id for ejercicio in ejercicios]))
        .all()
    )
    ejercicios_aprobados = sum(1 for ea in ejercicios_asignados if ea.estado)

    total_ejercicios = len(ejercicios)
    if total_ejercicios == 0:
        calificacion = 0
    else:
        calificacion = calcular_calificacion(total_ejercicios, ejercicios_aprobados)

    return render_template('detallesSerieEstudiante.html', serie=serie, ejercicios=ejercicios, estudiante_id=estudiante_id,calificacion=calificacion)
