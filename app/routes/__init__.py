from .auth import *
from ...basedatos.modelos.curso import *
from ...basedatos.modelos.curso import *
from ...basedatos.modelos.ejercicio import *
from ...basedatos.modelos.estudiante import *
from ...basedatos.modelos.grupo import *
from ...basedatos.modelos.serie import *
from ...basedatos.modelos.supervisor import *


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('inicio.html')