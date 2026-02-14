# Makefile para el Proyecto Multicloud de Consulta de NIT

.PHONY: help install test run-azure run-aws run-gcp

# Variables (pueden ser personalizadas)
PYTHON_VENV = .venv
PIP = $(PYTHON_VENV)/bin/pip

help:
	@echo "Comandos disponibles:"
	@echo "  make install             Instala las dependencias de Python en el entorno virtual."
	@echo "  make test                Ejecuta las pruebas unitarias del proyecto."
	@echo "  make run-azure           Ejecuta la función de Azure localmente."
	@echo "  make run-aws             Ejecuta la función de AWS Lambda localmente a través de SAM."
	@echo "  make run-gcp             Ejecuta la función de Google Cloud localmente."
	@echo "---------------------------------------------------------------------"

test:
	@echo "--- Ejecutando pruebas unitarias ---"
	$(PYTHON_VENV)/bin/pytest

	@echo "Nota: Asegúrate de tener las herramientas CLI correspondientes (func, sam, gcloud) y Docker instalados y configurados."

install:
	@echo "--- Instalando dependencias de Python ---"
	python3 -m venv $(PYTHON_VENV)
	$(PIP) install -r requirements.txt
	@echo "Instalación completada."

run-azure:
	@echo "--- Ejecutando Azure Function localmente (puerto 7071) ---"
	@echo "Accede a: http://localhost:7071/api/consulta_nit"
	. $(PYTHON_VENV)/bin/activate && cd azure_function && func start

run-aws:
	@echo "--- Ejecutando AWS Lambda localmente con SAM (puerto 3000) ---"
	@echo "Accede a: http://localhost:3000/consulta_nit"
	. $(PYTHON_VENV)/bin/activate && cd aws_lambda && sam local start-api

run-gcp:
	@echo "--- Ejecutando Google Cloud Function localmente (puerto 8080) ---"
	@echo "Accede a: http://localhost:8080"
	@echo "Nota: El endpoint es la raíz '/'."
	. $(PYTHON_VENV)/bin/activate && cd google_cloud_function && functions-framework --target=consulta_nit_gcp --debug

