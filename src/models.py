from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Ciiu(BaseModel):
    """
    Representa el código y la descripción CIIU (Clasificación Industrial Internacional Uniforme).
    """
    codigo: Optional[str] = Field(None, description="Código CIIU.")
    descripcion: Optional[str] = Field(None, description="Descripción del CIIU.")


class Empresa(BaseModel):
    """
    Representa la información consolidada de la empresa de diferentes fuentes de datos.
    """
    razon_social: Optional[str] = Field(None, description="Nombre legal de la empresa.")
    nit: str = Field(..., description="Número de identificación tributaria de la empresa.")
    dv: Optional[str] = Field(None, description="Dígito de verificación del NIT.")
    camara_comercio: Optional[str] = Field(None, description="Cámara de comercio donde está registrada la empresa.")
    matricula: Optional[str] = Field(None, description="Número de matrícula mercantil.")
    estado: Optional[str] = Field(None, description="Estado actual de la matrícula.")
    fecha_matricula: Optional[str] = Field(None, description="Fecha de la primera matrícula.")
    fecha_renovacion: Optional[str] = Field(None, description="Fecha de la última renovación.")
    ultimo_ano_renovado: Optional[str] = Field(None, description="Último año en que se renovó la matrícula.")
    tipo_sociedad: Optional[str] = Field(None, description="Tipo de sociedad (e.g., S.A.S, LTDA).")
    organizacion_juridica: Optional[str] = Field(None, description="Tipo de organización jurídica.")
    ciiu_principal: Optional[Ciiu] = Field(default_factory=Ciiu, description="Información del CIIU principal.")
    cod_ciiu_act_econ_pri: Optional[str] = Field("9999", description="Código CIIU de actividad económica principal.")
    desc_ciiu_act_econ_pri: Optional[str] = Field("Actividad No Homologada CIIU v4", description="Descripción de la actividad económica principal CIIU.")
    ciiu2: Optional[Ciiu] = Field(default_factory=Ciiu, description="Información del CIIU secundario.")
    ciiu3: Optional[Ciiu] = Field(default_factory=Ciiu, description="Información del CIIU  3.")
    ciiu4: Optional[Ciiu] = Field(default_factory=Ciiu, description="Información del CIIU 4.")
        
    fuentes: List[str] = Field(default_factory=list, description="Lista de fuentes de datos donde se encontró la información.")

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True) # Actualizado a la configuración de Pydantic V2