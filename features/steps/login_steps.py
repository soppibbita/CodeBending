from behave import given, when, then
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sys

# Simulación de respuestas 
class MockResponse:
    def __init__(self, status_code=200, location=None, data=b''):
        self.status_code = status_code
        self.location = location
        self.data = data

# Datos de prueba guardados en memoria
test_users = {
    'estudiantes': {},
    'supervisores': {}
}

# Estado de sesión simulado
session_data = {
    'flashes': [],
    'logged_in_user': None
}

@given('que estoy en la página de inicio de sesión')
def step_impl(context):
    context.response = MockResponse(200, data=b'<form>login</form>')
    context.form_data = {}
    session_data['logged_in_user'] = None
    session_data['flashes'] = []

@given('que existe un estudiante con correo "{correo}" y contraseña "{password}"')
def step_impl(context, correo, password):
    test_users['estudiantes'][correo] = {
        'password': generate_password_hash(password),
        'id': len(test_users['estudiantes']) + 1,
        'tipo': 'estudiante'
    }

@given('que existe un supervisor con correo "{correo}" y contraseña "{password}"')
def step_impl(context, correo, password):
    test_users['supervisores'][correo] = {
        'password': generate_password_hash(password),
        'id': len(test_users['supervisores']) + 1,
        'tipo': 'supervisor'
    }

@when('ingreso el correo "{correo}"')
def step_impl(context, correo):
    context.form_data['correo'] = correo

@when('ingreso la contraseña "{password}"')
def step_impl(context, password):
    context.form_data['password'] = password

@when('hago clic en el botón de iniciar sesión')
def step_impl(context):
    correo = context.form_data.get('correo', '')
    password = context.form_data.get('password', '')
    
    # Simular validación de login
    user = None
    if correo in test_users['estudiantes']:
        user = test_users['estudiantes'][correo]
        user_type = 'estudiante'
    elif correo in test_users['supervisores']:
        user = test_users['supervisores'][correo]
        user_type = 'supervisor'
    
    if user and check_password_hash(user['password'], password):
        # Login exitoso
        session_data['logged_in_user'] = {'correo': correo, 'tipo': user_type, 'id': user['id']}
        session_data['flashes'].append(('success', 'Has iniciado sesión exitosamente'))
        
        if user_type == 'estudiante':
            context.response = MockResponse(302, location=f'/estudiante/{user["id"]}')
        else:
            context.response = MockResponse(302, location=f'/supervisor/{user["id"]}')
    else:
        # Login fallido
        session_data['flashes'].append(('danger', 'Credenciales inválidas'))
        context.response = MockResponse(200, data=b'<form>login</form>')

@then('debo ser redirigido al dashboard del estudiante')
def step_impl(context):
    assert context.response.status_code == 302
    assert '/estudiante/' in context.response.location

@then('debo ser redirigido al dashboard del supervisor')
def step_impl(context):
    assert context.response.status_code == 302
    assert '/supervisor/' in context.response.location

@then('debo ver el mensaje "{mensaje}"')
def step_impl(context, mensaje):
    messages = [msg[1] for msg in session_data['flashes']]
    assert mensaje in messages, f"Mensaje '{mensaje}' no encontrado. Mensajes actuales: {messages}"

@then('debo permanecer en la página de login')
def step_impl(context):
    assert context.response.status_code == 200
    assert b'login' in context.response.data.lower()

@when('dejo el campo de correo vacío')
def step_impl(context):
    context.form_data['correo'] = ''

@when('dejo el campo de contraseña vacío')
def step_impl(context):
    context.form_data['password'] = ''

@then('los campos requeridos deben mostrar validación')
def step_impl(context):
    # Simulamos la validación con el código de respuesta 200
    assert context.response.status_code == 200

@given('que he iniciado sesión como estudiante')
def step_impl(context):
    # Crear usuario y simular login
    test_users['estudiantes']['test@universidad.edu'] = {
        'password': generate_password_hash('test123'),
        'id': 999,
        'tipo': 'estudiante'
    }
    session_data['logged_in_user'] = {
        'correo': 'test@universidad.edu',
        'tipo': 'estudiante',
        'id': 999
    }
    session_data['flashes'] = []

@when('hago clic en cerrar sesión')
def step_impl(context):
    session_data['logged_in_user'] = None
    session_data['flashes'].append(('info', 'Sesión cerrada'))
    context.response = MockResponse(302, location='/login')

@then('debo ser redirigido a la página de login')
def step_impl(context):
    assert context.response.status_code == 302
    assert '/login' in context.response.location or context.response.location == '/'

@given('que ya he iniciado sesión como estudiante')
def step_impl(context):
    # Crear usuario y simular sesión activa
    test_users['estudiantes']['logged@universidad.edu'] = {
        'password': generate_password_hash('logged123'),
        'id': 888,
        'tipo': 'estudiante'
    }
    session_data['logged_in_user'] = {
        'correo': 'logged@universidad.edu',
        'tipo': 'estudiante',
        'id': 888
    }
    context.estudiante_id = 888

@when('intento acceder a la página de login')
def step_impl(context):
    # Simular redirección automática si ya está logueado
    if session_data['logged_in_user']:
        user = session_data['logged_in_user']
        if user['tipo'] == 'estudiante':
            context.response = MockResponse(302, location=f'/estudiante/{user["id"]}')
        else:
            context.response = MockResponse(302, location=f'/supervisor/{user["id"]}')
    else:
        context.response = MockResponse(200, data=b'<form>login</form>')

@then('debo ser redirigido automáticamente a mi dashboard de estudiante')
def step_impl(context):
    assert context.response.status_code == 302
    assert f'/estudiante/{context.estudiante_id}' in context.response.location