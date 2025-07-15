.PHONY: format format-check lint check help

help:
	@echo "Comandos disponibles:"
	@echo "  make format       - Formatear código con black"
	@echo "  make format-check - Verificar formato sin modificar archivos"
	@echo "  make lint         - Ejecutar análisis con flake8"
	@echo "  make check        - Ejecutar format-check y lint"

format:
	@echo "Formateando código con black..."
	black .

format-check:
	@echo "Verificando formato con black..."
	black --check --diff .

lint:
	@echo "Analizando código con flake8..."
	flake8 .

check: format-check lint
	@echo "Análisis completo finalizado."