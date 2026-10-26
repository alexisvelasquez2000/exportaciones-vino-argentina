"""
Configuración central del proyecto.

Acá se definen las rutas de carpetas y archivos, y los datos de la fuente
(la API del portal de datos abiertos del Ministerio de Agricultura, donde
el INV publica sus datasets). Tener todo en un solo lugar evita "números
mágicos" repartidos por el código: si cambia una ruta, se cambia acá.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------------
# __file__ es este archivo (src/config.py). .parent es src/ y .parent.parent
# es la raíz del proyecto. Así las rutas funcionan sin importar desde qué
# carpeta se ejecute el programa.
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
CARPETA_DATA = RAIZ_PROYECTO / "data"
CARPETA_RAW = CARPETA_DATA / "raw"          # datos crudos tal como se descargan

RUTA_DB = CARPETA_DATA / "exportaciones_vino.db"
RUTA_CSV_RESUMEN = CARPETA_DATA / "resumen_destinos_sql.csv"
RUTA_CSV_ANALISIS = CARPETA_DATA / "analisis_destinos.csv"
RUTA_GRAFICO = CARPETA_DATA / "top_destinos_fob.png"

# ---------------------------------------------------------------------------
# Fuente de datos: API CKAN de datos.magyp.gob.ar
# ---------------------------------------------------------------------------
# CKAN es el software que usan casi todos los portales de datos abiertos del
# Estado. Tiene una API que devuelve en JSON la información de cada dataset,
# incluyendo los links de descarga de sus archivos ("resources").
URL_API_CKAN = "https://datos.magyp.gob.ar/api/3/action/package_show"
ID_DATASET_INV = "inv-actividad-vitivinicola"

# Texto que buscamos en el nombre del recurso para elegir el CSV correcto
PALABRA_CLAVE_RECURSO = "export"

# Tiempo máximo de espera de cada pedido HTTP (segundos)
TIMEOUT_HTTP = 60
