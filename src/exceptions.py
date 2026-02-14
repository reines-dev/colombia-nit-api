class NitNotFoundError(Exception):
    """
    Se lanza cuando un NIT no se encuentra en ninguna de las fuentes de datos.
    """
    def __init__(self, nit: str):
        self.nit = nit
        super().__init__(f"No se encontró información para el NIT: {nit}")


class DataSourceError(Exception):
    """
    Se lanza cuando una fuente de datos falla o devuelve un error inesperado.
    """
    def __init__(self, source_name: str, original_exception: Exception):
        self.source_name = source_name
        self.original_exception = original_exception
        super().__init__(f"Error en la fuente de datos '{source_name}': {original_exception}")