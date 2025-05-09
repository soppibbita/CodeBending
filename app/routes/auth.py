from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import Supervisor, Estudiante
from app import db, login_manager

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # si el usuario ya esta autenticado, lo redirige a su dashboard
    if current_user.is_authenticated:
        if isinstance(current_user, Estudiante):
            return redirect(url_for('estudiante.dashEstudiante', estudiante_id=current_user.id))
        elif isinstance(current_user, Supervisor):
            return redirect(url_for('supervisor.dashDocente', supervisor_id=current_user.id))
    
    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']
        
        # buscar usuario
        estudiante = Estudiante.query.filter_by(correo=correo).first()
        supervisor = Supervisor.query.filter_by(correo=correo).first()

        # autenticar usuario
        if estudiante and check_password_hash(estudiante.password, password):
            login_user(estudiante)
            flash('Has iniciado sesión exitosamente', 'success')
            return redirect(url_for('estudiante.dashEstudiante', estudiante_id=estudiante.id))
        
        elif supervisor and check_password_hash(supervisor.password, password):
            login_user(supervisor)
            flash('Has iniciado sesión exitosamente', 'success')
            return redirect(url_for('supervisor.dashDocente', supervisor_id=supervisor.id))
        
        flash('Credenciales inválidas', 'danger')
    
    return render_template('inicio.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/', methods=['GET', 'POST'])
def home():
    return render_template('inicio.html')

@auth_bp.route('/registerSupervisor', methods=['GET'])
def register_page():
    return render_template('register.html')

@auth_bp.route('/registersupervisor', methods=['POST'])
def register():
    nombres = request.form.get('nombres')
    apellidos = request.form.get('apellidos')
    correo = request.form.get('correo')
    password = request.form.get('password')

    # valida los datos
    if not nombres or not apellidos or not correo or not password:
        flash('Todos los campos son requeridos.', 'danger')
        return render_template('registersupervisor.html')  
    
    # comprueba si el correo ya existe
    supervisor = Supervisor.query.filter_by(correo=correo).first()
    if supervisor:
        flash('Ya existe un supervisor con ese correo.', 'warning')
        return render_template('register.html')
    
    # verifica que el correo tenga al menos el formato basico de un correo
    if '@' not in correo or '.' not in correo:
        flash('Formato de correo inválido.', 'danger')
        return render_template('register.html')
    
    # crea nuevo supervisor
    # para evitar que la app se rompa si hay algun problema con la base de datos
    try:
        new_supervisor = Supervisor(
            nombres=nombres,
            apellidos=apellidos,
            correo=correo,
            password=generate_password_hash(password)
        )

        db.session.add(new_supervisor)
        db.session.commit()
        flash('Supervisor registrado exitosamente.', 'success')
        return redirect(url_for('auth.login'))
    except:
        db.session.rollback()
        flash('Error al registrar supervisor. Intente nuevamente.', 'danger')
        return render_template('register.html')

@auth_bp.route('/user_loader')
def user_loader(user_id):
    if user_id.startswith("e"):
        user = db.session.get(Estudiante, int(user_id[1:]))
    elif user_id.startswith("s"):
        user = db.session.get(Supervisor, int(user_id[1:]))
    else:
        return None
    return user