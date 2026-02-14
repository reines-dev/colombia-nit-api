import json
import logging
import os
import sys

# Agrega el directorio raíz al path para encontrar el módulo 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services import ConsultaNitService, DatosGovCoService, RuesService
from src.exceptions import NitNotFoundError, DataSourceError

# --- Instanciación de Servicios ---
# En un escenario real, esto podría ser más sofisticado (ej. singleton)
datos_gov_co_url = os.environ.get("DATOS_GOV_CO_URL", "https://www.datos.gov.co/resource/c82u-588k.json")
rues_url = os.environ.get("RUES_URL", "https://ruesapi.rues.org.co/WEB2/api/Expediente/DetalleRM")

datos_gov_co_service = DatosGovCoService(base_url=datos_gov_co_url)
rues_service = RuesService(base_url=rues_url)
consulta_nit_service = ConsultaNitService(datos_gov_co_service, rues_service)

# --- Handler de AWS Lambda ---
def lambda_handler(event, context):
    """
    Punto de entrada para AWS Lambda con trigger de API Gateway.
    """
    logging.info('La función Lambda para Consulta NIT procesó una solicitud.')
    headers = {"Content-Type": "application/json"}
    
    try:
        # 1. Extraer NIT del evento de API Gateway
        nit = None
        if event.get('queryStringParameters') and 'nit' in event['queryStringParameters']:
            nit = event['queryStringParameters']['nit']
        elif event.get('body'):
            try:
                body = json.loads(event['body'])
                nit = body.get('nit')
            except (json.JSONDecodeError, AttributeError):
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "Cuerpo JSON malformado."})
                }

        # 2. Validar NIT
        if not nit or not str(nit).strip():
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "El NIT es requerido."})}

        nit = str(nit).strip()
        if not nit.isdigit() or not (8 <= len(nit) <= 10):
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Formato de NIT inválido. Debe ser un número entre 8 y 10 dígitos."})}

        # 3. Delegar a la Capa de Lógica de Negocio
        empresa = consulta_nit_service.consultar_nit(nit)
        
        # 4. Devolver Respuesta Exitosa
        return {
            "statusCode": 200,
            "headers": headers,
            "body": empresa.model_dump_json()
        }
    
    # 5. Manejar Errores Específicos
    except NitNotFoundError as e:
        logging.warning(str(e))
        return {"statusCode": 404, "headers": headers, "body": json.dumps({"error": str(e)})}
    except DataSourceError as e:
        logging.error(f"Falló una fuente de datos: {str(e)}")
        return {"statusCode": 502, "headers": headers, "body": json.dumps({"error": "Una fuente de datos externa no está disponible. Por favor, intente de nuevo más tarde."})}
    except Exception as e:
        logging.error(f"Ocurrió un error inesperado: {str(e)}")
        return {"statusCode": 500, "headers": headers, "body": json.dumps({"error": "Ocurrió un error interno en el servidor."})}
