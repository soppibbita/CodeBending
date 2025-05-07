from app import db

class Supervisor(db.Model):
    __tablename__ = 'supervisores'
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    
    def get_id(self):
        return f"s{self.id}"
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return False

class Estudiante(db.Model):
    __tablename__ = 'estudiantes'
    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(20), unique=True, nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    carrera = db.Column(db.String(100))
    
    cursos = db.relationship('Curso', secondary='inscripciones', backref=db.backref('estudiantes', lazy='dynamic'))
    
    def get_id(self):
        return f"e{self.id}"
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return False

class Curso(db.Model):
    __tablename__ = 'cursos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    activa = db.Column(db.Boolean, default=True)

class Grupo(db.Model):
    __tablename__ = 'grupos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    id_curso = db.Column(db.Integer, db.ForeignKey('cursos.id'), nullable=False)

class Serie(db.Model):
    __tablename__ = 'series'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    activa = db.Column(db.Boolean, default=True)

class Ejercicio(db.Model):
    __tablename__ = 'ejercicios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    path_ejercicio = db.Column(db.String(255))
    enunciado = db.Column(db.String(255))
    id_serie = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=False)

class Ejercicio_asignado(db.Model):
    __tablename__ = 'ejercicios_asignados'
    id = db.Column(db.Integer, primary_key=True)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    id_ejercicio = db.Column(db.Integer, db.ForeignKey('ejercicios.id'), nullable=False)
    contador = db.Column(db.Integer, default=0)
    estado = db.Column(db.Boolean, default=False)
    ultimo_envio = db.Column(db.String(255))
    fecha_ultimo_envio = db.Column(db.DateTime)
    test_output = db.Column(db.Text)

# Association tables
inscripciones = db.Table('inscripciones',
    db.Column('id_estudiante', db.Integer, db.ForeignKey('estudiantes.id'), primary_key=True),
    db.Column('id_curso', db.Integer, db.ForeignKey('cursos.id'), primary_key=True)
)

estudiantes_grupos = db.Table('estudiantes_grupos',
    db.Column('id_estudiante', db.Integer, db.ForeignKey('estudiantes.id'), primary_key=True),
    db.Column('id_grupo', db.Integer, db.ForeignKey('grupos.id'), primary_key=True)
)

supervisores_grupos = db.Table('supervisores_grupos',
    db.Column('id_supervisor', db.Integer, db.ForeignKey('supervisores.id'), primary_key=True),
    db.Column('id_grupo', db.Integer, db.ForeignKey('grupos.id'), primary_key=True)
)

serie_asignada = db.Table('serie_asignada',
    db.Column('id_serie', db.Integer, db.ForeignKey('series.id'), primary_key=True),
    db.Column('id_grupo', db.Integer, db.ForeignKey('grupos.id'), primary_key=True)
)