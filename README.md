# CodeBending

You need Java JRE > 21 installed and Apache Maven in your computer.

In your favorite virtual env :
`pip install -r requirements.txt`

Then to create the database :
`python .\crear_db.py`

Then to start the project :
`python .\main.py` 

Then you need to connect to http://127.0.0.1:3000/registerSupervisor to create the first supervsor account.

You can encounter an example of exercise for the platform here : https://github.com/GeoffreyHecht/FizzBuzzPasoAPaso

Important: There seems to be a problem with path management under Windows, so I recommend using Linux (or correcting the problem).

# Pruebas de Aceptación 

## Como ejecutarlas

1. Activar el entorno virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Ejecutar las pruebas:
   ```bash
   behave
   ```

   Si se quiere ejecutar una feature específica:
   ```bash
   behave features/login.feature
   ```
    ```bash
   behave features/estudiantes.feature
   ```
    ```bash
   behave features/ejercicios.feature
   ```


## Features implementadas

1. Login de usuarios con escenarios de éxito, error y logout.
2. Registro de estudiantes y asignación a grupos con escenarios de evaluar el csv de registro, evitar duplicidad de datos, fallos en la base de datos y errores de falta de datos.
3. Crear, testear y registrar los ejercicios, cuando estos se testean de manera existosa o con fallas, y el registro de ambas situaciones.

## Notas

- Se usan mocks para simular la lógica y datos.
- Las respuestas y datos se simulan y mantienen en memoria.
