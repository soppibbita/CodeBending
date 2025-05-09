from .auth import *
from .curso import *
from .curso import *
from .ejercicio import *
from .estudiante import *
from .grupo import *
from .serie import *
from .supervisor import *


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('inicio.html')