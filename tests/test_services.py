# tests/test_services.py
import pytest # Importación añadida
import requests_mock
import json
import requests


from src.services import DatosGovCoService, RuesService, ConsultaNitService, DataSource
from src.exceptions import NitNotFoundError, DataSourceError
from src.models import Empresa, Ciiu


# --- Fixtures para Servicios ---
@pytest.fixture
def datos_gov_co_service():
    return DatosGovCoService(base_url="http://mock-datos-gov.co/resource")

@pytest.fixture
def rues_service():
    return RuesService(base_url="http://mock-rues.org.co/api")

@pytest.fixture
def consulta_nit_service(datos_gov_co_service, rues_service):
    return ConsultaNitService(datos_gov_co_service, rues_service)


# --- Pruebas para DatosGovCoService ---
def test_datos_gov_co_service_success(datos_gov_co_service, requests_mock):
    nit = "900123456"
    mock_response = [
        {
            "razon_social": "EMPRESA MOCK SAS",
            "nit": nit,
            "digito_verificacion": "1",
            "camara_comercio": "BOGOTA",
            "matricula": "12345",
            "cod_ciiu_act_econ_pri": "G4711",
            "codigo_camara": "12"
        }
    ]
    requests_mock.get(f"http://mock-datos-gov.co/resource?nit={nit}", json=mock_response, status_code=200)
    
    result = datos_gov_co_service.consultar(nit)
    assert result is not None
    assert result["nit"] == nit
    assert result["razon_social"] == "EMPRESA MOCK SAS"
    assert result["cod_ciiu_act_econ_pri"] == "G4711"

def test_datos_gov_co_service_no_data(datos_gov_co_service, requests_mock):
    nit = "111111111"
    requests_mock.get(f"http://mock-datos-gov.co/resource?nit={nit}", json=[], status_code=200)
    
    result = datos_gov_co_service.consultar(nit)
    assert result is None

def test_datos_gov_co_service_api_error(datos_gov_co_service, requests_mock):
    nit = "900123456"
    requests_mock.get(f"http://mock-datos-gov.co/resource?nit={nit}", status_code=500)
    
    with pytest.raises(DataSourceError) as excinfo:
        datos_gov_co_service.consultar(nit)
    assert "datos.gov.co" in str(excinfo.value)
    assert isinstance(excinfo.value.original_exception, requests.exceptions.HTTPError)

def test_datos_gov_co_service_network_error(datos_gov_co_service, requests_mock): # Nombre del fixture corregido
    nit = "900123456"
    requests_mock.get(f"http://mock-datos-gov.co/resource?nit={nit}", exc=requests.exceptions.ConnectionError)
    
    with pytest.raises(DataSourceError) as excinfo:
        datos_gov_co_service.consultar(nit)
    assert "datos.gov.co" in str(excinfo.value)
    assert isinstance(excinfo.value.original_exception, requests.exceptions.ConnectionError)


# --- Pruebas para RuesService ---
def test_rues_service_success(rues_service, requests_mock):
    nit = "900123456"
    codigo_camara = "12"
    matricula = "12345"
    codigo_rues = f"{codigo_camara}00000{matricula}" # Asumiendo 12 - 2 - 5 = 5 ceros
    mock_response = {
        "codigo_error": "0000",
        "mensaje_error": "OK",
        "registros": {
            "razon_social": "EMPRESA MOCK RUES",
            "numero_identificacion": nit,
            "dv": "1",
            "camara": "BOGOTA",
            "matricula": matricula,
            "cod_ciiu_act_econ_pri": "A0112",
            "desc_ciiu_act_econ_pri": "Cultivo de arroz"
        }
    }
    requests_mock.get(f"http://mock-rues.org.co/api/{codigo_rues}", json=mock_response, status_code=200)
    
    result = rues_service.consultar(nit, codigo_camara=codigo_camara, matricula=matricula)
    assert result is not None
    assert result["razon_social"] == "EMPRESA MOCK RUES"
    assert result["cod_ciiu_act_econ_pri"] == "A0112"

def test_rues_service_missing_params(rues_service):
    nit = "900123456"
    result = rues_service.consultar(nit) # Faltan codigo_camara y matricula
    assert result is None
    result = rues_service.consultar(nit, codigo_camara="12") # Falta matricula
    assert result is None

def test_rues_service_api_business_error(rues_service, requests_mock):
    nit = "900123456"
    codigo_camara = "12"
    matricula = "99999" # Simula NIT no encontrado en RUES
    codigo_rues = f"{codigo_camara}00000{matricula}"
    mock_response = {
        "codigo_error": "1001",
        "mensaje_error": "No se encontró registro para los datos suministrados"
    }
    requests_mock.get(f"http://mock-rues.org.co/api/{codigo_rues}", json=mock_response, status_code=200)

    result = rues_service.consultar(nit, codigo_camara=codigo_camara, matricula=matricula)
    assert result is None

def test_rues_service_api_http_error(rues_service, requests_mock):
    nit = "900123456"
    codigo_camara = "12"
    matricula = "12345"
    codigo_rues = f"{codigo_camara}00000{matricula}"
    requests_mock.get(f"http://mock-rues.org.co/api/{codigo_rues}", status_code=500)
    
    with pytest.raises(DataSourceError) as excinfo:
        rues_service.consultar(nit, codigo_camara=codigo_camara, matricula=matricula)
    assert "rues.org.co" in str(excinfo.value)
    assert isinstance(excinfo.value.original_exception, requests.exceptions.HTTPError)

# --- Pruebas para ConsultaNitService ---
def test_consulta_nit_service_both_sources_success(consulta_nit_service, requests_mock):
    nit = "900123456"
    
    # Mock para DatosGovCo
    gov_mock_response = [
        {
            "razon_social": "EMPRESA GOV",
            "nit": nit,
            "digito_verificacion": "1",
            "camara_comercio": "BOGOTA",
            "matricula": "12345",
            "cod_ciiu_act_econ_pri": "G4711",
            "desc_ciiu_act_econ_pri": "Actividades de consultoría informática y actividades de administración de instalaciones informáticas", # Added
            "codigo_camara": "12",
            "organizacion_juridica": "SAS"
        }
    ]
    requests_mock.get(f"http://mock-datos-gov.co/resource?nit={nit}", json=gov_mock_response, status_code=200)

    # Mock para RUES
    codigo_camara = "12"
    matricula = "12345"
    codigo_rues = f"{codigo_camara}00000{matricula}"
    rues_mock_response = {
        "codigo_error": "0000",
        "registros": {
            "razon_social": "EMPRESA RUES", # Debería ser sobreescrito por GOV
            "numero_identificacion": nit,
            "dv": "1",
            "camara": "BOGOTA",
            "matricula": matricula,
            "cod_ciiu_act_econ_pri": "A0112",
            "desc_ciiu_act_econ_pri": "Cultivo de arroz",
            "cod_ciiu_act_econ_sec": "B0810",
            "desc_ciiu_act_econ_sec": "Extracción de piedra, arena, arcilla, caolín, yeso, sal",
            "ciiu3": "C1011",
            "desc_ciiu3": "Procesamiento y conservación de carne y productos cárnicos",
            "ciiu4": "D2000",
            "desc_ciiu4": "Fabricación de productos químicos básicos",
            "tipo_sociedad": "Sociedad Anonima"
        }
    }
    requests_mock.get(f"http://mock-rues.org.co/api/{codigo_rues}", json=rues_mock_response, status_code=200)
    
    empresa = consulta_nit_service.consultar_nit(nit)
    
    assert isinstance(empresa, Empresa)
    assert empresa.nit == nit
    assert empresa.razon_social == "EMPRESA GOV" # Prioridad para GOV
    assert empresa.ciiu_principal.codigo == "G4711" # Prioridad para GOV
    assert empresa.ciiu_principal.descripcion == "Actividades de consultoría informática y actividades de administración de instalaciones informáticas" # Should be populated from desc_ciiu_act_econ_pri
    assert empresa.organizacion_juridica == "SAS" # Desde GOV
    assert empresa.tipo_sociedad == "Sociedad Anonima" # Desde RUES
    assert "datos.gov.co" in empresa.fuentes
    assert "rues.org.co" in empresa.fuentes
    # Assert new CIIU string fields (which are still present)
    assert empresa.cod_ciiu_act_econ_pri == "G4711" # From GOV
    assert empresa.desc_ciiu_act_econ_pri == "Actividades de consultoría informática y actividades de administración de instalaciones informáticas" # From GOV
    
    # Assert new CIIU objects
    assert isinstance(empresa.ciiu2, Ciiu)
    assert empresa.ciiu2.codigo == "B0810" # From RUES
    assert empresa.ciiu2.descripcion == "Extracción de piedra, arena, arcilla, caolín, yeso, sal" # From RUES

    assert isinstance(empresa.ciiu3, Ciiu)
    assert empresa.ciiu3.codigo == "C1011" # From RUES
    assert empresa.ciiu3.descripcion == "Procesamiento y conservación de carne y productos cárnicos" # From RUES

    assert isinstance(empresa.ciiu4, Ciiu)
    assert empresa.ciiu4.codigo == "D2000" # From RUES
    assert empresa.ciiu4.descripcion == "Fabricación de productos químicos básicos" # From RUES


def test_consulta_nit_service_only_gov_success(consulta_nit_service, requests_mock):
    nit = "900123456"
    
    # Mock para DatosGovCo
    gov_mock_response = [
        {
            "razon_social": "EMPRESA GOV ONLY",
            "nit": nit,
            "cod_ciiu_act_econ_pri": "G4711",
            "codigo_camara": "12",
            "matricula": "12345" # Necesario para el intento de RUES
        }
    ]
    requests_mock.get(f"http://mock-datos-gov.co/resource?nit={nit}", json=gov_mock_response, status_code=200)

    # Mock para que RUES no devuelva datos
    codigo_camara = "12"
    matricula = "12345"
    codigo_rues = f"{codigo_camara}00000{matricula}"
    requests_mock.get(f"http://mock-rues.org.co/api/{codigo_rues}", json={"codigo_error": "1001"}, status_code=200)
    
    empresa = consulta_nit_service.consultar_nit(nit)
    
    assert isinstance(empresa, Empresa)
    assert empresa.nit == nit
    assert empresa.razon_social == "EMPRESA GOV ONLY"
    assert empresa.ciiu_principal.codigo == "G4711"
    assert empresa.ciiu_principal.descripcion == "Actividad No Homologada CIIU v4" # Should be populated from default
    assert "datos.gov.co" in empresa.fuentes
    assert "rues.org.co" not in empresa.fuentes # RUES no proporcionó datos
    # Assert new CIIU string fields default values
    assert empresa.cod_ciiu_act_econ_pri == "G4711" # From GOV
    assert empresa.desc_ciiu_act_econ_pri == "Actividad No Homologada CIIU v4" # Default
    
    # Assert new CIIU objects default values
    assert isinstance(empresa.ciiu2, Ciiu)
    assert empresa.ciiu2.codigo is None
    assert empresa.ciiu2.descripcion is None
    assert isinstance(empresa.ciiu3, Ciiu)
    assert empresa.ciiu3.codigo is None
    assert empresa.ciiu3.descripcion is None
    assert isinstance(empresa.ciiu4, Ciiu)
    assert empresa.ciiu4.codigo is None
    assert empresa.ciiu4.descripcion is None

def test_consulta_nit_service_no_ciiu_data_defaults(consulta_nit_service, requests_mock):
    """Test that new CIIU fields get default values when no source provides them."""
    nit = "900123456"
    
    # Mock DatosGovCo to return minimal data without CIIU
    gov_mock_response = [
        {
            "razon_social": "EMPRESA SIN CIIU",
            "nit": nit,
            "digito_verificacion": "1",
            "camara_comercio": "BOGOTA",
            "matricula": "12345",
            "codigo_camara": "12",
            "organizacion_juridica": "SAS"
        }
    ]
    requests_mock.get(f"http://mock-datos-gov.co/resource?nit={nit}", json=gov_mock_response, status_code=200)

    # Mock RUES to return no data
    codigo_camara = "12"
    matricula = "12345"
    codigo_rues = f"{codigo_camara}00000{matricula}"
    requests_mock.get(f"http://mock-rues.org.co/api/{codigo_rues}", json={"codigo_error": "1001"}, status_code=200)

    empresa = consulta_nit_service.consultar_nit(nit)

    assert isinstance(empresa, Empresa)
    assert empresa.nit == nit
    assert empresa.razon_social == "EMPRESA SIN CIIU"
    assert empresa.ciiu_principal.codigo == "9999" # No primary CIIU from sources
    assert empresa.ciiu_principal.descripcion == "Actividad No Homologada CIIU v4" # Default
    assert empresa.cod_ciiu_act_econ_pri == "9999" # Default
    assert empresa.desc_ciiu_act_econ_pri == "Actividad No Homologada CIIU v4" # Default
    
    # Assert new CIIU objects default values
    assert isinstance(empresa.ciiu2, Ciiu)
    assert empresa.ciiu2.codigo is None
    assert empresa.ciiu2.descripcion is None
    assert isinstance(empresa.ciiu3, Ciiu)
    assert empresa.ciiu3.codigo is None
    assert empresa.ciiu3.descripcion is None
    assert isinstance(empresa.ciiu4, Ciiu)
    assert empresa.ciiu4.codigo is None
    assert empresa.ciiu4.descripcion is None


def test_consulta_nit_service_only_rues_success(consulta_nit_service, requests_mock):
    nit = "900123456"
    
    # Mock para que DatosGovCo no devuelva datos
    requests_mock.get(f"http://mock-datos-gov.co/resource?nit={nit}", json=[], status_code=200)

    # Mock para RUES (necesita algunos parámetros por defecto, el NIT no coincidirá si no mockeamos gov.co primero, o pasamos kwargs explícitos)
    # Este escenario es un poco complicado, ya que la consulta a RUES necesita codigo_camara y matricula de gov.co.
    # Para una prueba robusta, necesitaríamos mockear la llamada intermedia a gov.co para proporcionar estos, incluso si no hay datos completos.
    # Sin embargo, dada la lógica actual, si gov.co no devuelve nada, RUES no será llamado con parámetros.
    # Probaremos el NitNotFoundError directamente a continuación.
    # Por lo tanto, este caso de prueba para "éxito solo de RUES" no es directamente alcanzable con la lógica actual del orquestador.
    # Requeriría que RUES fuera una fuente primaria, o que el orquestador tuviera una forma alternativa de obtener los parámetros de RUES.
    
    # Re-evaluando: si gov_data es None, entonces se llama a rues_service.consultar sin codigo_camara y matricula.
    # lo cual devolverá None. Por lo tanto, este escenario debería conducir a NitNotFoundError.
    with pytest.raises(NitNotFoundError):
        consulta_nit_service.consultar_nit(nit)

def test_consulta_nit_service_nit_not_found(consulta_nit_service, requests_mock):
    nit = "999999999"
    
    # Ambos servicios no devuelven datos
    requests_mock.get(f"http://mock-datos-gov.co/resource?nit={nit}", json=[], status_code=200)
    # RUES no será llamado con parámetros válidos si gov.co no devuelve datos (sin codigo_camara/matricula)
    
    with pytest.raises(NitNotFoundError) as excinfo:
        consulta_nit_service.consultar_nit(nit)
    assert nit in str(excinfo.value)

def test_consulta_nit_service_data_source_error_propagation(consulta_nit_service, requests_mock):
    nit = "900123456"
    requests_mock.get(f"http://mock-datos-gov.co/resource?nit={nit}", status_code=500) # Simula un error de API
    
    with pytest.raises(DataSourceError) as excinfo:
        consulta_nit_service.consultar_nit(nit)
    assert "datos.gov.co" in str(excinfo.value)