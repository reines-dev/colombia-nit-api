# tests/conftest.py
# Los fixtures para la configuración de pruebas compartidas pueden ir aquí.
import pytest
import os

# Asegurarse de que src esté en el path para las importaciones
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(autouse=True)
def setup_env():
    """
    Configura las variables de entorno para probar los servicios que dependen de os.environ.get.
    """
    original_datos_gov_co_url = os.environ.get("DATOS_GOV_CO_URL")
    original_rues_url = os.environ.get("RUES_URL")

    os.environ["DATOS_GOV_CO_URL"] = "http://mock-datos-gov.co"
    os.environ["RUES_URL"] = "http://mock-rues.org.co"

    yield

    if original_datos_gov_co_url is not None:
        os.environ["DATOS_GOV_CO_URL"] = original_datos_gov_co_url
    else:
        del os.environ["DATOS_GOV_CO_URL"]
    
    if original_rues_url is not None:
        os.environ["RUES_URL"] = original_rues_url
    else:
        del os.environ["RUES_URL"]