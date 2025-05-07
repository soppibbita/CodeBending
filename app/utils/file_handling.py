import os
import csv
from flask import current_app
from werkzeug.security import generate_password_hash
from app import db
from app.models import Estudiante, inscripciones
from sqlite3 import IntegrityError

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def procesar_archivo_csv(filename, curso_id):
    with open(os.path.join(current_app.config['UPLOAD_FOLDER'], filename), 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) != 5:
                current_app.logger.warning(f"La fila no tiene el formato esperado: {row}")
                continue
            
            matricula, apellidos, nombres, correo, carrera = row
            password = generate_password_hash(matricula)
            estudiante_existente = Estudiante.query.filter_by(matricula=matricula).first()
            
            if estudiante_existente:
                relacion_existente = db.session.query(inscripciones).filter_by(id_estudiante=estudiante_existente.id, id_curso=curso_id).first()
                if relacion_existente:
                    current_app.logger.warning(f'El estudiante con matrícula {matricula} ya está inscrito en el curso {curso_id}.')
                    continue
                try:
                    nueva_inscripcion = inscripciones.insert().values(id_estudiante=estudiante_existente.id, id_curso=curso_id)
                    db.session.execute(nueva_inscripcion)
                    db.session.commit()
                    current_app.logger.info(f'El estudiante con matrícula {matricula} ha sido inscrito en el curso.')
                except IntegrityError as e:
                    db.session.rollback()
                    current_app.logger.error(f'Error al registrar en el curso {curso_id} al estudiante {matricula}: {str(e)}')
                    continue
            
            elif not estudiante_existente:
                estudiante = Estudiante(
                    matricula=matricula,
                    apellidos=apellidos,
                    nombres=nombres,
                    correo=correo,
                    password=password,
                    carrera=carrera)
                try:
                    db.session.add(estudiante)
                    db.session.flush()
                    estudiante_id = estudiante.id
                    db.session.commit()
                    current_app.logger.info(f'El estudiante con matrícula {matricula} ha sido registrado en la base de datos.')
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f'Error al registrar {nombres} {apellidos}: {str(e)}')
                    continue

                try:
                    nueva_inscripcion = inscripciones.insert().values(id_estudiante=estudiante_id, id_curso=curso_id)
                    db.session.execute(nueva_inscripcion)
                    db.session.commit()
                    current_app.logger.info(f'El estudiante con matrícula {matricula} ha sido inscrito en el curso.')
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f'Error al inscribir a {nombres} {apellidos} en el curso: {str(e)}')
                    continue

def calcular_calificacion(total_puntos, puntos_obtenidos):
    if total_puntos == 0:
        return "No hay ejercicios asignados"
    else:
        porcentaje = (puntos_obtenidos / total_puntos) * 100
        if porcentaje >= 60:
            calificacion = 4 + (3 / 40) * (porcentaje - 60)
        else:
            calificacion = 1 + (3 / 60) * porcentaje
        calificacion = max(1, min(calificacion, 7))
        return round(calificacion, 2)