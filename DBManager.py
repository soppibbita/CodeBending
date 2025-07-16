from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_app(app):
    import os
    # Crear directorio data si no existe
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Usar ruta absoluta para la base de datos
    db_path = os.path.join(data_dir, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    