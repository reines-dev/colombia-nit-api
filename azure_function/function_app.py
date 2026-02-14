import azure.functions as func
import logging
import json
import os
import sys

# Agrega el directorio raíz al path para encontrar el módulo 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services import ConsultaNitService, DatosGovCoService, RuesService
from src.exceptions import NitNotFoundError, DataSourceError

# --- Instanciación de Servicios ---
# En un escenario real, podrías usar un contenedor de inyección de dependencias más sofisticado.
# Para Azure Functions, leer desde variables de entorno es una práctica común.
datos_gov_co_url = os.environ.get("DATOS_GOV_CO_URL")
rues_url = os.environ.get("RUES_URL")

datos_gov_co_service = DatosGovCoService(base_url=datos_gov_co_url)
rues_service = RuesService(base_url=rues_url)
consulta_nit_service = ConsultaNitService(datos_gov_co_service, rues_service)

# --- Azure Function App ---
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="consulta_nit", methods=["GET", "POST"])
def consulta_nit(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger para consultar información de una empresa por su NIT.
    """
    logging.info('La función Consulta NIT procesó una solicitud.')

    # 1. Extraer NIT de la solicitud
    nit = req.params.get('nit')
    if not nit:
        try:
            req_body = req.get_json()
            nit = req_body.get('nit')
        except (ValueError, AttributeError):
            return func.HttpResponse(
                json.dumps({"error": "Por favor, proporcione un NIT en la cadena de consulta o en un cuerpo JSON."}),
                status_code=400,
                mimetype="application/json"
            )

    # 2. Validar NIT
    if not nit or not str(nit).strip():
        return func.HttpResponse(
            json.dumps({"error": "El NIT es requerido."}),
            status_code=400,
            mimetype="application/json"
        )
    
    nit = str(nit).strip()
    # Una validación simple, puede mejorarse con un validador dedicado
    if not nit.isdigit() or not (8 <= len(nit) <= 10):
        return func.HttpResponse(
            json.dumps({"error": "Formato de NIT inválido. Debe ser un número entre 8 y 10 dígitos."}),
            status_code=400,
            mimetype="application/json"
        )

    # 3. Delegar a la Capa de Lógica de Negocio
    try:
        empresa = consulta_nit_service.consultar_nit(nit)
        
        # 4. Devolver Respuesta Exitosa
        return func.HttpResponse(
            empresa.model_dump_json(),
            status_code=200,
            mimetype="application/json"
        )
        
    # 5. Manejar Errores Específicos
    except NitNotFoundError as e:
        logging.warning(str(e))
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=404,
            mimetype="application/json"
        )
    except DataSourceError as e:
        logging.error(f"Falló una fuente de datos: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Una fuente de datos externa no está disponible. Por favor, intente de nuevo más tarde."}),
            status_code=502, # Bad Gateway es apropiado para fallas en el upstream
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Ocurrió un error inesperado: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Ocurrió un error interno en el servidor."}),
            status_code=500,
            mimetype="application/json"
        )