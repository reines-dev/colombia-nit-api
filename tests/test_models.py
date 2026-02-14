# tests/test_models.py
import pytest
from pydantic import ValidationError
from src.models import Empresa, Ciiu


def test_ciiu_model_valid_data():
    """Prueba el modelo Ciiu con datos válidos."""
    ciiu = Ciiu(codigo="A0111", descripcion="Cultivo de cereales")
    assert ciiu.codigo == "A0111"
    assert ciiu.descripcion == "Cultivo de cereales"

def test_ciiu_model_partial_data():
    """Prueba el modelo Ciiu con solo un código."""
    ciiu = Ciiu(codigo="A0111")
    assert ciiu.codigo == "A0111"
    assert ciiu.descripcion is None

def test_ciiu_model_empty_data():
    """Prueba el modelo Ciiu con datos vacíos."""
    ciiu = Ciiu()
    assert ciiu.codigo is None
    assert ciiu.descripcion is None

def test_empresa_model_valid_data():
    """Prueba el modelo Empresa con datos válidos, incluyendo CIIU."""
    ciiu_data = Ciiu(codigo="A0111", descripcion="Cultivo de cereales")
    empresa = Empresa(
        nit="900123456",
        razon_social="Empresa Ejemplo S.A.S.",
        dv="1",
        ciiu_principal=ciiu_data,
        fuentes=["datos.gov.co"]
    )
    assert empresa.nit == "900123456"
    assert empresa.razon_social == "Empresa Ejemplo S.A.S."
    assert empresa.ciiu_principal.codigo == "A0111"
    assert "datos.gov.co" in empresa.fuentes
    # Assert primary CIIU string fields are at their default values
    assert empresa.cod_ciiu_act_econ_pri == "9999"
    assert empresa.desc_ciiu_act_econ_pri == "Actividad No Homologada CIIU v4"
    # Assert new CIIU object fields are at their default values (which are Ciiu objects with None/None)
    assert isinstance(empresa.ciiu2, Ciiu)
    assert empresa.ciiu2.codigo is None
    assert empresa.ciiu2.descripcion is None
    assert isinstance(empresa.ciiu3, Ciiu)
    assert empresa.ciiu3.codigo is None
    assert empresa.ciiu3.descripcion is None
    assert isinstance(empresa.ciiu4, Ciiu)
    assert empresa.ciiu4.codigo is None
    assert empresa.ciiu4.descripcion is None

def test_empresa_model_minimal_data():
    """Prueba el modelo Empresa con los datos mínimos requeridos (NIT)."""
    empresa = Empresa(nit="123456789")
    assert empresa.nit == "123456789"
    assert empresa.razon_social is None
    assert isinstance(empresa.ciiu_principal, Ciiu)
    assert empresa.ciiu_principal.codigo is None
    assert empresa.fuentes == []
    # Assert primary CIIU string fields are at their default values
    assert empresa.cod_ciiu_act_econ_pri == "9999"
    assert empresa.desc_ciiu_act_econ_pri == "Actividad No Homologada CIIU v4"
    # Assert new CIIU object fields are at their default values (which are Ciiu objects with None/None)
    assert isinstance(empresa.ciiu2, Ciiu)
    assert empresa.ciiu2.codigo is None
    assert empresa.ciiu2.descripcion is None
    assert isinstance(empresa.ciiu3, Ciiu)
    assert empresa.ciiu3.codigo is None
    assert empresa.ciiu3.descripcion is None
    assert isinstance(empresa.ciiu4, Ciiu)
    assert empresa.ciiu4.codigo is None
    assert empresa.ciiu4.descripcion is None

def test_empresa_model_ciiu_objects_assignment():
    """Test Empresa model can assign Ciiu objects to ciiu2, ciiu3, ciiu4."""
    ciiu2_data = Ciiu(codigo="H5220", descripcion="Actividades de almacenamiento y depósito")
    ciiu3_data = Ciiu(codigo="A0111", descripcion="Cultivo de cereales (excepto arroz), legumbres y semillas oleaginosas")
    ciiu4_data = Ciiu(codigo="Z9999", descripcion="Actividades económicas no clasificadas en otra parte")

    empresa = Empresa(
        nit="123",
        cod_ciiu_act_econ_pri="G4711",
        desc_ciiu_act_econ_pri="Comercio al por menor en establecimientos no especializados",
        ciiu2=ciiu2_data,
        ciiu3=ciiu3_data,
        ciiu4=ciiu4_data
    )
    assert empresa.cod_ciiu_act_econ_pri == "G4711"
    assert empresa.desc_ciiu_act_econ_pri == "Comercio al por menor en establecimientos no especializados"
    assert empresa.ciiu2.codigo == "H5220"
    assert empresa.ciiu2.descripcion == "Actividades de almacenamiento y depósito"
    assert empresa.ciiu3.codigo == "A0111"
    assert empresa.ciiu3.descripcion == "Cultivo de cereales (excepto arroz), legumbres y semillas oleaginosas"
    assert empresa.ciiu4.codigo == "Z9999"
    assert empresa.ciiu4.descripcion == "Actividades económicas no clasificadas en otra parte"

def test_empresa_model_ciiu_dicts_parsing():
    """Test Empresa model can parse dictionaries into Ciiu objects for ciiu2, ciiu3, ciiu4."""
    empresa = Empresa(
        nit="123",
        ciiu2={"codigo": "B0810", "descripcion": "Extracción de piedra"},
        ciiu3={"codigo": "C1011"},
        ciiu4={"descripcion": "Fabricación de productos químicos básicos"}
    )
    assert isinstance(empresa.ciiu2, Ciiu)
    assert empresa.ciiu2.codigo == "B0810"
    assert empresa.ciiu2.descripcion == "Extracción de piedra"
    assert isinstance(empresa.ciiu3, Ciiu)
    assert empresa.ciiu3.codigo == "C1011"
    assert empresa.ciiu3.descripcion is None
    assert isinstance(empresa.ciiu4, Ciiu)
    assert empresa.ciiu4.codigo is None
    assert empresa.ciiu4.descripcion == "Fabricación de productos químicos básicos"


def test_empresa_model_invalid_nit_type():
    """Prueba el modelo Empresa con un tipo de NIT inválido."""
    with pytest.raises(ValidationError):
        Empresa(nit=12345) # NIT debería ser una cadena de texto

def test_empresa_model_ciiu_dict_parsing():
    """Prueba que el modelo Empresa puede analizar un diccionario en un modelo Ciiu."""
    empresa = Empresa(nit="123", ciiu_principal={"codigo": "A123"})
    assert isinstance(empresa.ciiu_principal, Ciiu)
    assert empresa.ciiu_principal.codigo == "A123"

def test_empresa_model_invalid_ciiu_primitive_type():
    """Prueba que el modelo Empresa lanza ValidationError para un tipo primitivo inválido para ciiu_principal."""
    with pytest.raises(ValidationError):
        Empresa(nit="123", ciiu_principal="invalid_string")


def test_empresa_model_fuentes_default():
    """Prueba que 'fuentes' por defecto es una lista vacía."""
    empresa = Empresa(nit="123")
    assert empresa.fuentes == []

def test_empresa_model_ciiu_default():
    """Prueba que 'ciiu_principal' por defecto es un objeto Ciiu vacío."""
    empresa = Empresa(nit="123")
    assert isinstance(empresa.ciiu_principal, Ciiu)
    assert empresa.ciiu_principal.codigo is None
    assert empresa.ciiu_principal.descripcion is None