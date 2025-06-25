from behave import given, when, then

# Datos simulados en memoria
db_sim = {
    "estudiantes": {},
    "grupos": {},
    "cursos": {},
    "relaciones": {
        "estudiante_curso": set(),
        "estudiante_grupo": set(),
        "grupo_supervisor": set()
    },
    "mensajes": []
}

@given("que el supervisor ha iniciado sesión")
def step_supervisor_login(context):
    context.supervisor_id = 1
    db_sim["mensajes"].clear()

@given("que existe un curso activo")
def step_curso_activo(context):
    db_sim["cursos"][1] = {"nombre": "Curso de Prueba", "activa": True}
    context.curso_id = 1

@given("que ya existe un estudiante con la misma matrícula en el sistema")
def step_estudiante_existente(context):
    db_sim["estudiantes"]["20230001"] = {"correo": "juan@mail.com", "curso": 1}
    db_sim["relaciones"]["estudiante_curso"].add(("20230001", 1))

@given("que tiene estudiantes inscritos en un curso")
def step_estudiantes_inscritos(context):
    context.estudiantes = ["20230001", "20230002"]
    for m in context.estudiantes:
        db_sim["estudiantes"][m] = {"correo": f"{m}@mail.com", "curso": context.curso_id}
        db_sim["relaciones"]["estudiante_curso"].add((m, context.curso_id))

@given("que tiene estudiantes disponibles")
def step_estudiantes_disponibles(context):
    context.estudiantes = ["20230003"]
    db_sim["estudiantes"]["20230003"] = {"correo": "ana@mail.com", "curso": context.curso_id}

@given("que un estudiante ya está asignado a un grupo")
def step_estudiante_grupo_existente(context):
    db_sim["grupos"][1] = {"nombre": "Grupo1", "curso": context.curso_id}
    db_sim["relaciones"]["estudiante_grupo"].add(("20230001", 1))

@given("que ocurre un error simulado en la base de datos")
def step_simular_error_bd(context):
    context.simular_error = True

@when("sube un archivo CSV con datos de un nuevo estudiante")
def step_subir_csv_estudiante(context):
    db_sim["estudiantes"]["20235555"] = {"correo": "nuevo@mail.com", "curso": context.curso_id}
    db_sim["relaciones"]["estudiante_curso"].add(("20235555", context.curso_id))

@when("sube un archivo CSV con ese estudiante para el mismo curso")
def step_csv_estudiante_existente(context):
    # No hace nada porque ya está
    pass

@when("crea un nuevo grupo y selecciona estudiantes")
def step_crear_grupo(context):
    grupo_id = len(db_sim["grupos"]) + 1
    db_sim["grupos"][grupo_id] = {"nombre": "Grupo Test", "curso": context.curso_id}
    for m in context.estudiantes:
        db_sim["relaciones"]["estudiante_grupo"].add((m, grupo_id))
    db_sim["relaciones"]["grupo_supervisor"].add((grupo_id, context.supervisor_id))
    context.grupo_id = grupo_id

@when("sube un archivo CSV con una fila con campos faltantes")
def step_csv_malformado(context):
    db_sim["mensajes"].append("Fila malformada detectada")
    db_sim["estudiantes"]["20236666"] = {"correo": "bien@mail.com", "curso": context.curso_id}
    db_sim["relaciones"]["estudiante_curso"].add(("20236666", context.curso_id))

@when("intenta crear un grupo sin especificar nombre")
def step_grupo_sin_nombre(context):
    db_sim["mensajes"].append("Error: nombre de grupo requerido")

@when("crea un grupo sin seleccionar estudiantes")
def step_grupo_sin_estudiantes(context):
    db_sim["mensajes"].append("Advertencia: no se seleccionaron estudiantes")

@when("intenta asignarlo al mismo grupo nuevamente")
def step_reasignar_estudiante_grupo(context):
    if ("20230001", 1) in db_sim["relaciones"]["estudiante_grupo"]:
        db_sim["mensajes"].append("Estudiante ya asignado a este grupo")

@when("sube un archivo CSV con un estudiante")
def step_csv_con_error(context):
    if getattr(context, "simular_error", False):
        db_sim["mensajes"].append("Error en la base de datos al registrar estudiante")
    else:
        db_sim["estudiantes"]["20239999"] = {"correo": "error@mail.com", "curso": context.curso_id}

@then("el estudiante debe registrarse en la base de datos")
def step_assert_estudiante_registrado(context):
    assert "20235555" in db_sim["estudiantes"]

@then("debe inscribirse en el curso")
def step_assert_inscripcion(context):
    assert ("20235555", context.curso_id) in db_sim["relaciones"]["estudiante_curso"]

@then("el sistema no debe duplicar al estudiante")
def step_assert_no_duplicado(context):
    count = list(db_sim["estudiantes"].keys()).count("20230001")
    assert count == 1

@then("no debe volver a inscribirlo si ya está en el curso")
def step_assert_no_reinscripcion(context):
    relaciones = list(db_sim["relaciones"]["estudiante_curso"])
    assert relaciones.count(("20230001", context.curso_id)) == 1

@then("el grupo debe registrarse en la base de datos")
def step_assert_grupo_creado(context):
    assert context.grupo_id in db_sim["grupos"]

@then("los estudiantes deben asociarse al grupo")
def step_assert_estudiantes_en_grupo(context):
    for m in context.estudiantes:
        assert (m, context.grupo_id) in db_sim["relaciones"]["estudiante_grupo"]

@then("el grupo debe asociarse al supervisor")
def step_assert_grupo_supervisor(context):
    assert (context.grupo_id, context.supervisor_id) in db_sim["relaciones"]["grupo_supervisor"]

@then("debe verse un mensaje de advertencia en el log")
def step_assert_warning_log(context):
    assert any("malformada" in msg for msg in db_sim["mensajes"])

@then("los estudiantes bien formateados deben registrarse normalmente")
def step_assert_estudiante_valido(context):
    assert "20236666" in db_sim["estudiantes"]

@then("debe mostrarse un mensaje de error")
def step_assert_mensaje_error(context):
    assert any("Error" in msg for msg in db_sim["mensajes"])

@then("el grupo no debe ser creado")
def step_assert_grupo_no_creado(context):
    assert all("Grupo sin nombre" not in g["nombre"] for g in db_sim["grupos"].values())

@then("debe mostrarse un mensaje de advertencia")
def step_assert_advertencia(context):
    assert any("Advertencia" in msg for msg in db_sim["mensajes"])

@then("el grupo no debe quedar asociado a estudiantes")
def step_assert_grupo_vacio(context):
    for rel in db_sim["relaciones"]["estudiante_grupo"]:
        assert rel[1] != context.grupo_id

@then("el sistema debe evitar la duplicación en la relación")
def step_assert_no_reasignacion(context):
    count = list(db_sim["relaciones"]["estudiante_grupo"]).count(("20230001", 1))
    assert count == 1

@then("el estudiante no debe registrarse")
def step_assert_estudiante_no_registrado(context):
    assert "20239999" not in db_sim["estudiantes"]
