from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config
from .models import db
from .routes.auth import auth_bp
from .routes.supervisor import supervisor_bp
from .routes.estudiante import estudiante_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Cargar usuario
    @login_manager.user_loader
    def load_user(user_id):
        from .models import Estudiante, Supervisor
        if user_id.startswith("e"):
            return db.session.get(Estudiante, int(user_id[1:]))
        elif user_id.startswith("s"):
            return db.session.get(Supervisor, int(user_id[1:]))
        return None

    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(supervisor_bp, url_prefix='/dashDocente')
    app.register_blueprint(estudiante_bp, url_prefix='/dashEstudiante')

    # Manejo de errores
    def pagina_no_encontrada(error):
        from flask import render_template
        return render_template('404.html'), 404

    app.register_error_handler(404, pagina_no_encontrada)

    return app