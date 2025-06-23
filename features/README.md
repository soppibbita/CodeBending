# Pruebas de Aceptación - CodeBending

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


## Features implementadas

1. Login de usuarios con escenarios de éxito, error y logout.

## Notas

- Se usan mocks para simular la lógica y datos.
- Las respuestas y datos se simulan y mantienen en memoria.