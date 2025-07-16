FROM python:3.11-slim

# Instalar Java y Maven
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    maven \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 3000

# Comando para ejecutar la aplicación
CMD ["python", "main.py"]