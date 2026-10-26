"""
Limpieza y normalización de los datos crudos (paso entre la Fase 1 y la 2).

Los CSV del INV vienen con algunos detalles que conviene corregir antes de
guardarlos en la base de datos:
  - Codificación de texto: a veces vienen en latin-1 ("España" se ve mal
    si se lee como UTF-8).
  - Espacios sobrantes en textos (por ejemplo "flexi-tank ").
  - El mes viene abreviado ("Ene", "Feb"...), lo pasamos también a número.
  - La columna "valor_fob_litros", pese al nombre, es el valor FOB total en
    dólares de la operación (equivale a valor_fob_miles x 1000). La
    renombramos a fob_usd para que no confunda.
"""

from pathlib import Path

import pandas as pd

from regiones import obtener_region

MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
         "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}

SIN_VARIEDAD = "sin variedad"


class LimpiadorExportaciones:
    """Lee uno o varios CSV del INV y devuelve un único DataFrame limpio."""

    def __init__(self, archivos: list[Path]):
        self.archivos = archivos
        self.df: pd.DataFrame | None = None

    @staticmethod
    def _leer_csv(ruta: Path) -> pd.DataFrame:
        """Intenta leer en UTF-8 y, si falla, en latin-1."""
        for codificacion in ("utf-8", "latin-1"):
            try:
                return pd.read_csv(ruta, encoding=codificacion)
            except UnicodeDecodeError:
                continue
        raise ValueError(f"No se pudo leer {ruta}")

    def leer(self) -> "LimpiadorExportaciones":
        """Une todos los CSV en un solo DataFrame (uno debajo del otro)."""
        partes = [self._leer_csv(ruta) for ruta in self.archivos]
        self.df = pd.concat(partes, ignore_index=True)
        print(f"[Limpieza] Filas leídas: {len(self.df)}")
        return self      # devolver self permite encadenar: limpiador.leer().limpiar()

    def limpiar(self) -> pd.DataFrame:
        df = self.df.copy()

        # 1) Nombres de columnas en minúscula y sin espacios
        df.columns = df.columns.str.strip().str.lower()

        # 2) Quitar espacios sobrantes en todas las columnas de texto
        columnas_texto = df.select_dtypes(include=["object", "string"]).columns
        for col in columnas_texto:
            df[col] = df[col].astype("string").str.strip()

        # 3) Mes abreviado -> número (Ene -> 1)
        df["mes_num"] = df["mes"].str.lower().str[:3].map(MESES)

        # 4) Columnas numéricas: forzamos el tipo; lo que no sea número queda NaN
        for col in ["litros_exportados", "cantidad_envases", "valor_fob_litros",
                    "anio", "anio_elaboracion"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # 5) Renombrar a nombres más claros
        df = df.rename(columns={
            "litros_exportados": "litros",
            "valor_fob_litros": "fob_usd",
            "variedad_1": "variedad",
        })

        # 6) Columnas derivadas sencillas
        #    - es_corte: el vino lleva más de una variedad (blend)
        df["es_corte"] = (df["variedad_2"] != SIN_VARIEDAD).astype(int)
        #    - region: agrupamos los países de destino por región del mundo
        df["region"] = df["pais"].map(obtener_region)

        # 7) Descartar filas sin datos esenciales
        antes = len(df)
        df = df.dropna(subset=["pais", "producto", "litros", "fob_usd", "mes_num"])
        print(f"[Limpieza] Filas descartadas por datos incompletos: {antes - len(df)}")

        columnas_finales = [
            "anio", "mes_num", "mes", "pais", "region", "producto", "color",
            "anio_elaboracion", "variedad", "es_corte", "modalidad_envio",
            "envase", "cantidad_envases", "litros", "fob_usd",
            "provincia_exportador", "departamento_exportador",
        ]
        self.df = df[columnas_finales].reset_index(drop=True)
        print(f"[Limpieza] Filas limpias: {len(self.df)}")
        return self.df
