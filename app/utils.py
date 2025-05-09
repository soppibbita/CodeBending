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

from app import app

# Se define que tipo de arhivos se pueden recibir
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def procesar_archivo_csv(filename, curso_id):
    # ----->>>Falta borrar los flash de depuracion :)<<<<------
    # Procesa el archivo
    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Saltar la primera fila
        for row in reader:
            if len(row) != 5:
                # Manejar el error, por ejemplo, omitiendo esta fila o mostrando un mensaje de advertencia
                current_app.logger.warning(f"La fila no tiene el formato esperado: {row}")
                continue  # Saltar esta fila y continuar con la próxima
            
            # Por cada fila, extraer los datos
            matricula, apellidos, nombres, correo, carrera = row
            password = generate_password_hash(matricula)  # Contraseña por defecto: hash de la matrícula
            # Verificar si el estudiante ya existe en la base de datos:
            estudiante_existente = Estudiante.query.filter_by(matricula=matricula).first()
            
            if estudiante_existente:
                # El estudiante con el mismo correo ya existe
                #flash(f'El estudiante con matrícula {matricula} ya está registrado en la base de datos.', 'warning')
                # Revisar si el estudiante ya está asignado a curso_id
                # Usando tabla de inscripciones
                relacion_existente = db.session.query(inscripciones).filter_by(id_estudiante=estudiante_existente.id, id_curso=curso_id).first()
                if relacion_existente:
                    flash(f'El estudiante con matrícula {matricula} ya está inscrito en el curso {curso_id}.', 'warning')
                    continue

                try:
                    nueva_inscripcion = inscripciones.insert().values(id_estudiante=estudiante_existente.id, id_curso=curso_id)
                    db.session.execute(nueva_inscripcion)
                    db.session.commit()
                    flash(f'El estudiante con matrícula {matricula} ha sido inscrito en el curso.', 'success')
                except IntegrityError as e:
                    db.session.rollback()
                    flash(f'Error al registrar en el curso {curso_id} al estudiante {matricula} .', 'warning')
                    continue
            
            # Si el estudiantes no existe, se crea
            elif not estudiante_existente:

                estudiante = Estudiante(
                matricula=matricula,
                apellidos=apellidos,
                nombres=nombres,
                correo=correo,
                password=password,
                carrera=carrera)
                # Crear el nuevo estudiante en la base de datos
                try:
                    db.session.add(estudiante)
                    db.session.flush()  # Esto genera el id sin confirmar en la base de datos
                    estudiante_id = estudiante.id  # Obtener el id del estudiante recién creado
                    db.session.commit()
                    flash(f'El estudiante con matrícula {matricula} ha sido registrado en la base de datos.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error al crear al registrar {nombres} {apellidos} .', 'warning')
                    continue

                # Si el estudiante se creó correctamente en la bd, se inscribe en el curso
                try:
                    nueva_inscripcion = inscripciones.insert().values(id_estudiante=estudiante_id, id_curso=curso_id)
                    db.session.execute(nueva_inscripcion)
                    db.session.commit()
                    flash(f'El estudiante con matrícula {matricula} ha sido inscrito en el curso.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error al inscribir a {nombres} {apellidos} en el curso.', 'warning')
                    continue

def calcular_calificacion(total_puntos, puntos_obtenidos):
    if total_puntos == 0:
        return "No hay ejercicios asignados"  # O cualquier mensaje de error adecuado
    else:
        porcentaje = (puntos_obtenidos / total_puntos) * 100

        if porcentaje >= 60:
            # Calcular la calificación para el rango de 4 a 7
            calificacion = 4 + (3 / 40) * (porcentaje - 60)
        else:
            # Calcular la calificación para el rango de 1 a 4
            calificacion = 1 + (3 / 60) * porcentaje

        calificacion = max(1, min(calificacion, 7))

        # Redondear a dos decimales
        calificacion = round(calificacion, 2)

        return calificacion
    


# Verifica que el usuario logueado es un Supervisor
def verify_supervisor(supervisor_id):

    if not isinstance(current_user, Supervisor):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return False

    # Asegura que el Supervisor está tratando de acceder a su propio dashboard
    if current_user.id != supervisor_id:
        flash('No tienes permiso para acceder a este dashboard.', 'danger')
        return False

    return True

# Verifica que el usuario logueado es un Estudiante


def verify_estudiante(estudiante_id):

    if not isinstance(current_user, Estudiante):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Estudiante.', 'danger')
        return False
    # Asegura que el Estudiante está tratando de acceder a su propio dashboard
    if current_user.id != estudiante_id:
        flash('No tienes permiso para acceder a este dashboard.', 'danger')
        return False
    return True


def verify_ayudante(supervisor_id):

    if not isinstance(current_user, Supervisor):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return False
    if current_user.id != supervisor_id:
        flash('No tienes permiso para acceder a este dashboard.', 'danger')
        return False