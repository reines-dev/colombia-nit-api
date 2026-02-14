import logging
import os
import sys
import json
import functions_framework
from flask import jsonify

# Agrega el directorio raíz al path para encontrar el módulo 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services import ConsultaNitService, DatosGovCoService, RuesService
from src.exceptions import NitNotFoundError, DataSourceError

# --- Instanciación de Servicios ---
datos_gov_co_url = os.environ.get("DATOS_GOV_CO_URL", "https://www.datos.gov.co/resource/c82u-588k.json")
rues_url = os.environ.get("RUES_URL", "https://ruesapi.rues.org.co/WEB2/api/Expediente/DetalleRM")

datos_gov_co_service = DatosGovCoService(base_url=datos_gov_co_url)
rues_service = RuesService(base_url=rues_url)
consulta_nit_service = ConsultaNitService(datos_gov_co_service, rues_service)

# --- Handler de Google Cloud Function ---
@functions_framework.http
def consulta_nit_gcp(request):
    """
    Punto de entrada para Google Cloud Function (HTTP).
    """
    logging.info('La función de Google Cloud para Consulta NIT procesó una solicitud.')
    
    try:
        # 1. Extraer NIT de la solicitud (objeto tipo Flask)
        request_json = request.get_json(silent=True)
        request_args = request.args

        nit = None
        if request_args and 'nit' in request_args:
            nit = request_args['nit']
        elif request_json and 'nit' in request_json:
            nit = request_json['nit']
        
        # 2. Validar NIT
        if not nit or not str(nit).strip():
            return (jsonify({"error": "El NIT es requerido."}), 400)

        nit = str(nit).strip()
        if not nit.isdigit() or not (8 <= len(nit) <= 10):
            return (jsonify({"error": "Formato de NIT inválido. Debe ser un número entre 8 y 10 dígitos."}), 400)

        # 3. Delegar a la Capa de Lógica de Negocio
        empresa = consulta_nit_service.consultar_nit(nit)
        
        # 4. Devolver Respuesta Exitosa
        # Usamos jsonify para establecer Content-Type a application/json
        return (empresa.model_dump_json(), 200)

    # 5. Manejar Errores Específicos
    except NitNotFoundError as e:
        logging.warning(str(e))
        return (jsonify({"error": str(e)}), 404)
    except DataSourceError as e:
        logging.error(f"Falló una fuente de datos: {str(e)}")
        return (jsonify({"error": "Una fuente de datos externa no está disponible. Por favor, intente de nuevo más tarde."}), 502)
    except Exception as e:
        logging.error(f"Ocurrió un error inesperado: {str(e)}")
        return (jsonify({"error": "Ocurrió un error interno en el servidor."}), 500)
