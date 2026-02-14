import requests
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from src.models import Empresa, Ciiu
from src.exceptions import NitNotFoundError, DataSourceError


class DataSource(ABC):
    """
    Clase base abstracta para una fuente de datos de empresas.
    """
    @abstractmethod
    def consultar(self, nit: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Consulta la fuente de datos para obtener información sobre un NIT dado.

        Args:
            nit: El número de identificación tributaria de la empresa.

        Returns:
            Un diccionario con los datos de la empresa o None si no se encuentra.
        """
        pass


class DatosGovCoService(DataSource):
    """
    Implementación de fuente de datos para datos.gov.co.
    """
    def __init__(self, base_url: str = "https://www.datos.gov.co/resource/c82u-588k.json"):
        self.base_url = base_url

    def consultar(self, nit: str, **kwargs) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}?nit={nit}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Lanza una excepción para códigos de estado erróneos
            data = response.json()
            if not data:
                return None
            
            # Esta fuente devuelve una lista, tomamos el primer elemento
            return data[0]
        except requests.exceptions.RequestException as e:
            logging.error(f"Error al consultar Datos.gov.co: {e}")
            raise DataSourceError(source_name="datos.gov.co", original_exception=e)
        except (ValueError, IndexError) as e:
            logging.error(f"Error al analizar la respuesta de Datos.gov.co para el NIT {nit}")
            raise DataSourceError(source_name="datos.gov.co", original_exception=e)


class RuesService(DataSource):
    """
    Implementación de fuente de datos para rues.org.co.
    
    Este servicio requiere que 'codigo_camara' y 'matricula' se pasen a través de argumentos de palabra clave.
    """
    def __init__(self, base_url: str = "https://ruesapi.rues.org.co/WEB2/api/Expediente/DetalleRM"):
        self.base_url = base_url

    def consultar(self, nit: str, **kwargs) -> Optional[Dict[str, Any]]:
        codigo_camara = kwargs.get('codigo_camara')
        matricula = kwargs.get('matricula')

        if not codigo_camara or not matricula:
            # Esto no es un error, solo un caso en el que no tenemos suficiente información para consultar
            return None

        # Lógica para crear el código RUES
        union_len = len(str(codigo_camara)) + len(str(matricula))
        relleno = '0' * (12 - union_len)
        codigo_rues = f"{codigo_camara}{relleno}{matricula}"
        
        url = f"{self.base_url}/{codigo_rues}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("codigo_error") == '0000':
                return data.get("registros", {})
            else:
                logging.warning(f"La API de RUES devolvió un error de negocio para el NIT {nit}: {data.get('mensaje_error')}")
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Error al consultar RUES: {e}")
            raise DataSourceError(source_name="rues.org.co", original_exception=e)
        except ValueError as e:
            logging.error(f"Error al analizar la respuesta de RUES para el NIT {nit}")
            raise DataSourceError(source_name="rues.org.co", original_exception=e)


class ConsultaNitService:
    """
    Orquesta la recuperación de datos de empresas de múltiples fuentes.
    """
    def __init__(self, datos_gov_co_service: DataSource, rues_service: DataSource):
        self.datos_gov_co_service = datos_gov_co_service
        self.rues_service = rues_service

    def consultar_nit(self, nit: str) -> Empresa:
        """
        Realiza una búsqueda exhaustiva de un NIT en todas las fuentes de datos disponibles.
        """
        gov_data = self.datos_gov_co_service.consultar(nit)
        
        rues_data = None
        if gov_data:
            rues_data = self.rues_service.consultar(
                nit,
                codigo_camara=gov_data.get("codigo_camara"),
                matricula=gov_data.get("matricula")
            )

        if not gov_data and not rues_data:
            raise NitNotFoundError(nit)

        return self._unificar_datos(nit, gov_data or {}, rues_data or {})

    def _unificar_datos(self, nit: str, gov_data: Dict, rues_data: Dict) -> Empresa:
        """
        Fusiona los datos de todas las fuentes en un único modelo Empresa, dando prioridad a gov_data.
        """
        fuentes = []
        if gov_data:
            fuentes.append('datos.gov.co')
        if rues_data:
            fuentes.append('rues.org.co')
        
        # Ayudante para obtener el primer valor disponible
        def get_valor(key_gov: str, key_rues: str):
            return gov_data.get(key_gov) or rues_data.get(key_rues)

        # Mapear claves de RUES a claves de GOV donde difieren
        empresa_data = {
            "nit": nit,
            "razon_social": get_valor("razon_social", "razon_social"),
            "dv": get_valor("digito_verificacion", "dv"),
            "camara_comercio": get_valor("camara_comercio", "camara"),
            "matricula": get_valor("matricula", "matricula"),
            "estado": get_valor("estado_matricula", "estado"),
            "fecha_matricula": get_valor("fecha_matricula", "fecha_matricula"),
            "fecha_renovacion": get_valor("fecha_renovacion", "fecha_renovacion"),
            "ultimo_ano_renovado": get_valor("ultimo_ano_renovado", "ultimo_ano_renovado"),
            "tipo_sociedad": get_valor("tipo_sociedad", "tipo_sociedad"),
            "organizacion_juridica": get_valor("organizacion_juridica", "organizacion_juridica"),
            "fuentes": fuentes
        }

        # Poblamos los campos CIIU primarios
        empresa_data["cod_ciiu_act_econ_pri"] = get_valor("cod_ciiu_act_econ_pri", "cod_ciiu_act_econ_pri") or "9999"
        empresa_data["desc_ciiu_act_econ_pri"] = get_valor("desc_ciiu_act_econ_pri", "desc_ciiu_act_econ_pri") or "Actividad No Homologada CIIU v4"

        # Populate ciiu_principal using the already determined primary CIIU fields
        ciiu_principal_codigo = empresa_data.get("cod_ciiu_act_econ_pri")
        ciiu_principal_descripcion = empresa_data.get("desc_ciiu_act_econ_pri")

        if ciiu_principal_codigo or ciiu_principal_descripcion:
            empresa_data["ciiu_principal"] = Ciiu(
                codigo=ciiu_principal_codigo,
                descripcion=ciiu_principal_descripcion
            )
        else:
            empresa_data["ciiu_principal"] = Ciiu() # Default empty Ciiu object
        
        # Poblamos ciiu2, ciiu3, ciiu4 como objetos Ciiu
        # Para ciiu2 (secundario)
        cod_ciiu_sec = rues_data.get("cod_ciiu_act_econ_sec")
        desc_ciiu_sec = rues_data.get("desc_ciiu_act_econ_sec")
        if cod_ciiu_sec or desc_ciiu_sec:
            empresa_data["ciiu2"] = Ciiu(codigo=cod_ciiu_sec, descripcion=desc_ciiu_sec)
        else:
            empresa_data["ciiu2"] = Ciiu() # Default empty Ciiu object

        # Para ciiu3
        cod_ciiu3 = rues_data.get("ciiu3")
        desc_ciiu3 = rues_data.get("desc_ciiu3")
        if cod_ciiu3 or desc_ciiu3:
            empresa_data["ciiu3"] = Ciiu(codigo=cod_ciiu3, descripcion=desc_ciiu3)
        else:
            empresa_data["ciiu3"] = Ciiu() # Default empty Ciiu object

        # Para ciiu4
        cod_ciiu4 = rues_data.get("ciiu4")
        desc_ciiu4 = rues_data.get("desc_ciiu4")
        if cod_ciiu4 or desc_ciiu4:
            empresa_data["ciiu4"] = Ciiu(codigo=cod_ciiu4, descripcion=desc_ciiu4)
        else:
            empresa_data["ciiu4"] = Ciiu() # Default empty Ciiu object


        return Empresa(**empresa_data)
