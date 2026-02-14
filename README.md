# Plataforma de Consolidación de Datos Empresariales (NIT)

## Objetivo del Proyecto

Este proyecto es una API multicloud para consultar información detallada de empresas colombianas utilizando su Número de Identificación Tributaria (NIT). El servicio consolida datos de múltiples fuentes públicas, proporcionando una vista unificada y enriquecida para cada NIT consultado.

## Arquitectura Multicloud

La clave de este proyecto es su arquitectura, que separa la lógica de negocio principal del código específico de cada proveedor de nube. Esto permite que el núcleo de la aplicación se ejecute en Azure, AWS y Google Cloud con mínimos cambios.

*   **Núcleo de Lógica Compartida (`src/`):** Contiene toda la lógica de negocio, modelos de datos (Pydantic), servicios de consulta a APIs externas y excepciones. Es 100% agnóstico a la nube.
*   **Adaptadores de Nube:** Pequeñas capas de código que actúan como punto de entrada para cada plataforma serverless y "traducen" las solicitudes y respuestas al formato nativo de la nube.
    *   `azure_function/`: Adaptador para Azure Functions.
    *   `aws_lambda/`: Adaptador para AWS Lambda.
    *   `google_cloud_function/`: Adaptador para Google Cloud Functions.

## Características Principales

*   **Multicloud:** Desplegable en Azure, AWS y Google Cloud.
*   **Consulta por NIT:** La función principal (`consulta_nit`) acepta un NIT y devuelve un objeto `Empresa` con datos consolidados.
*   **Fuentes de Datos Múltiples:** Integra información de `datos.gov.co` y `rues.org.co`.
*   **Consolidación Inteligente:** Unifica y prioriza los datos obtenidos de las diferentes fuentes.
*   **Validación de NIT:** Realiza validaciones básicas sobre el formato y la longitud del NIT.
*   **Códigos CIIU Detallados:** Incluye objetos CIIU para la actividad principal, secundaria y otras.
*   **Manejo de Errores:** Proporciona respuestas claras para NIT no encontrados o problemas con las fuentes de datos externas.

## Primeros Pasos

### 1. Clonar el Repositorio

```bash
git clone <URL_DEL_REPOSITORIO> # Reemplaza con la URL real de tu repositorio
cd consulta_ciuu
```

### 2. Entorno de Desarrollo

#### Prerrequisitos

*   **Python 3.8+:** Se recomienda usar un entorno virtual.
*   **Herramientas de Nube (según la plataforma a probar):**
    *   **Azure:** [Azure Functions Core Tools](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local)
        *   **Nota para WSL:** Si ejecutas Azure Functions desde WSL y encuentras errores como "node: not found", necesitarás instalar Node.js y npm directamente en tu entorno WSL:
            ```bash
            sudo apt update
            sudo apt install nodejs npm
            ```
    *   **AWS:** [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) o [Serverless Framework](https://www.serverless.com/).
    *   **Google Cloud:** [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).

#### Variables de Entorno

El servicio utiliza variables de entorno para las URLs de las fuentes de datos. Debes configurarlas según la plataforma que estés usando.
*   `DATOS_GOV_CO_URL`: URL base para la API de datos.gov.co.
*   `RUES_URL`: URL base para la API de rues.org.co.

### 3. Instalación de Dependencias

```bash
pip install -r requirements.txt
```

## Puesta en Marcha en Ambiente de Desarrollo

### 1. Azure Functions

El punto de entrada es `azure_function/function_app.py`. Para ejecutarlo localmente:

```bash
# Asegúrate de tener local.settings.json configurado
func start
```
La función estará disponible en `http://localhost:7071/api/consulta_nit`.

### 2. AWS Lambda

El punto de entrada es `aws_lambda/lambda_handler.py`. Para invocarlo localmente (ejemplo con AWS SAM):

```bash
# Necesitarás un archivo template.yaml para definir la función
sam local invoke ConsultaNitFunction --event events/event.json
```
Donde `event.json` contiene un payload de API Gateway:
```json
{
  "httpMethod": "POST",
  "body": "{\"nit\": \"900485747\"}"
}
```

### 3. Google Cloud Functions

El punto de entrada es `google_cloud_function/main.py` (función `consulta_nit_gcp`). Para ejecutarlo localmente:

```bash
# En el directorio google_cloud_function/
functions-framework --target=consulta_nit_gcp --debug
```
La función estará disponible en `http://localhost:8080`.

## Estructura del Proyecto

*   `src/`: Directorio con la lógica de negocio agnóstica a la nube.
*   `azure_function/`: Adaptador y configuración para Azure Functions.
*   `aws_lambda/`: Adaptador para AWS Lambda.
*   `google_cloud_function/`: Adaptador para Google Cloud Functions.
*   `tests/`: Pruebas unitarias para el núcleo de lógica en `src/`.
*   `requirements.txt`: Dependencias Python compartidas para todas las plataformas.

## Ejecución de Pruebas

Para ejecutar las pruebas unitarias del núcleo de lógica:

```bash
pytest
```

---

**Autor:** Rafael Reines, asistido por qwen3 y Gemini Asistant
**Fecha:** 07 de febrero de 2026