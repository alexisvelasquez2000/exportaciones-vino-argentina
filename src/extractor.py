"""
FASE 1 - Extracción de datos.

La clase ExtractorINV consume la API CKAN del portal de datos abiertos
del Ministerio de Agricultura (datos.magyp.gob.ar) para:
  1. Pedir la ficha (metadatos) del dataset "INV - Actividad vitivinícola".
  2. Encontrar dentro de esa ficha los archivos CSV de exportaciones.
  3. Descargarlos a la carpeta data/raw/.

Si no hay conexión a internet, usa los CSV que ya estén descargados en
data/raw/, para que el resto del proyecto se pueda ejecutar igual.
"""

from pathlib import Path

import requests

import config


class ExtractorINV:
    """Se encarga solamente de traer los datos crudos desde la web."""

    def __init__(self, url_api: str = config.URL_API_CKAN,
                 id_dataset: str = config.ID_DATASET_INV,
                 carpeta_destino: Path = config.CARPETA_RAW):
        self.url_api = url_api
        self.id_dataset = id_dataset
        self.carpeta_destino = Path(carpeta_destino)
        self.carpeta_destino.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Métodos "privados" (por convención empiezan con _): pasos internos
    # ------------------------------------------------------------------
    def _consultar_api(self) -> dict:
        """Llama a la API y devuelve el JSON con la ficha del dataset.

        Ejemplo de URL que se arma:
        https://datos.magyp.gob.ar/api/3/action/package_show?id=inv-actividad-vitivinicola
        """
        respuesta = requests.get(self.url_api, params={"id": self.id_dataset},
                                 timeout=config.TIMEOUT_HTTP)
        respuesta.raise_for_status()          # si la API devuelve error, corta acá
        datos = respuesta.json()
        if not datos.get("success"):          # CKAN responde {"success": true, "result": {...}}
            raise RuntimeError("La API respondió, pero sin éxito: " + str(datos.get("error")))
        return datos["result"]

    def _filtrar_recursos_exportacion(self, ficha: dict) -> list[dict]:
        """De todos los archivos del dataset, se queda con los CSV de exportaciones."""
        recursos = ficha.get("resources", [])
        return [
            r for r in recursos
            if r.get("format", "").upper() == "CSV"
            and config.PALABRA_CLAVE_RECURSO in (r.get("name", "") + r.get("url", "")).lower()
        ]

    def _descargar_archivo(self, url: str) -> Path:
        """Descarga un archivo y lo guarda en data/raw/ con su nombre original."""
        nombre_archivo = url.split("/")[-1]
        ruta_local = self.carpeta_destino / nombre_archivo
        respuesta = requests.get(url, timeout=config.TIMEOUT_HTTP)
        respuesta.raise_for_status()
        ruta_local.write_bytes(respuesta.content)   # se guarda tal cual (bytes)
        return ruta_local

    def _archivos_locales(self) -> list[Path]:
        """Lista los CSV de exportaciones que ya están en data/raw/."""
        return sorted(p for p in self.carpeta_destino.glob("*.csv")
                      if config.PALABRA_CLAVE_RECURSO in p.name.lower())

    # ------------------------------------------------------------------
    # Método público: el único que necesita llamar el resto del programa
    # ------------------------------------------------------------------
    def extraer(self) -> list[Path]:
        """Ejecuta toda la fase 1 y devuelve la lista de CSV disponibles."""
        try:
            print(f"[Extracción] Consultando API CKAN: {self.url_api}?id={self.id_dataset}")
            ficha = self._consultar_api()
            print(f"[Extracción] Dataset encontrado: '{ficha.get('title')}' "
                  f"({len(ficha.get('resources', []))} recursos)")

            recursos = self._filtrar_recursos_exportacion(ficha)
            if not recursos:
                raise RuntimeError("No se encontraron CSV de exportaciones en el dataset.")

            archivos = []
            for recurso in recursos:
                print(f"[Extracción] Descargando: {recurso.get('name')}")
                archivos.append(self._descargar_archivo(recurso["url"]))
            return archivos

        except (requests.RequestException, RuntimeError) as error:
            # Plan B: trabajar con lo que ya está descargado
            print(f"[Extracción] No se pudo descargar ({error}).")
            locales = self._archivos_locales()
            if not locales:
                raise FileNotFoundError(
                    "No hay conexión y tampoco hay CSV en data/raw/. Descargá el archivo "
                    "manualmente desde https://datos.magyp.gob.ar/dataset/inv-actividad-vitivinicola"
                ) from error
            print(f"[Extracción] Se usan {len(locales)} archivo(s) local(es) de data/raw/.")
            return locales
