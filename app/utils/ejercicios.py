import os
from flask import current_app
from app import db
import json
from datetime import datetime

def guardar_y_ejecutar_tests(archivos_java, ruta_ejercicio):
    ruta_final = os.path.join(ruta_ejercicio, 'src/main/java/org/example')
    for archivo_java in archivos_java:
        if archivo_java and archivo_java.filename.endswith('.java'):
            archivo_path = os.path.join(ruta_final, archivo_java.filename)
            archivo_java.save(archivo_path)
            current_app.logger.info(f'Archivo guardado en: {archivo_path}')
    
    from funciones_archivo.manejoMaven import ejecutarTestUnitario
    resultado_test = ejecutarTestUnitario(ruta_ejercicio)
    current_app.logger.info(f'Resultado test: {resultado_test}')
    
    return resultado_test, ruta_final

def procesar_resultado_test(ejercicio_asignado, resultado_test, ruta_final):
    exito = resultado_test == 'BUILD SUCCESS'
    
    ejercicio_asignado.contador += 1
    ejercicio_asignado.ultimo_envio = ruta_final
    ejercicio_asignado.fecha_ultimo_envio = datetime.now()
    ejercicio_asignado.test_output = json.dumps(resultado_test)
    ejercicio_asignado.estado = exito
    db.session.commit()

    tipo = "success" if exito else "danger"
    titulo = "Todos los test aprobados" if exito else "Errores en la ejecución de pruebas unitarias"

    errores = {
        "tipo": tipo,
        "titulo": titulo,
        "mensaje": resultado_test
    }

    return errores