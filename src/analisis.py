"""
FASE 3 - Análisis exploratorio con pandas.

La clase AnalizadorExportaciones recibe el DataFrame que devolvió la
consulta SQL (resumen por país y modalidad de envío) y:
  - muestra una exploración general de los datos,
  - crea columnas nuevas calculadas (precio FOB por litro, participaciones,
    segmento de precio, ranking),
  - filtra con varias condiciones a la vez y ordena,
  - resume por región,
  - deja listo el DataFrame final para guardarlo en la base o en CSV.
"""

from pathlib import Path

import pandas as pd


class AnalizadorExportaciones:

    # Rangos de precio FOB por litro (USD) para clasificar destinos.
    # Son una referencia práctica: el granel suele estar por debajo de 1 USD/l
    # y el vino embotellado de gama media/alta por encima de 3-5 USD/l.
    LIMITES_PRECIO = [0, 1, 3, 5, float("inf")]
    ETIQUETAS_PRECIO = ["Bajo (<1)", "Medio (1-3)", "Medio-alto (3-5)", "Alto (>5)"]

    def __init__(self, df: pd.DataFrame):
        # Se trabaja sobre una copia para no modificar el DataFrame original
        self.df = df.copy()

    # ------------------------------------------------------------------
    def explorar(self) -> None:
        """Primer vistazo: tamaño, tipos de datos y estadísticas básicas."""
        print(f"\n[Análisis] Filas x columnas: {self.df.shape}")
        print("[Análisis] Tipos de datos:")
        print(self.df.dtypes.to_string())
        print("\n[Análisis] Estadísticas descriptivas de las columnas numéricas:")
        print(self.df.describe().round(2).to_string())
        print(f"\n[Análisis] Valores nulos por columna: {self.df.isna().sum().sum()}")

    # ------------------------------------------------------------------
    def agregar_columnas(self) -> "AnalizadorExportaciones":
        """Crea columnas nuevas a partir de cálculos sobre las existentes."""
        df = self.df
        total_fob = df["fob_total_usd"].sum()
        total_litros = df["litros_totales"].sum()

        # 1) Precio FOB promedio por litro: cuánto se cobra cada litro en ese destino.
        #    .where(...) evita dividir por cero (deja NaN si no hubo litros).
        df["usd_por_litro"] = (df["fob_total_usd"] /
                               df["litros_totales"].where(df["litros_totales"] > 0)).round(2)

        # 2) y 3) Participación de cada fila sobre el total exportado (en %)
        df["participacion_fob_pct"] = (df["fob_total_usd"] / total_fob * 100).round(2)
        df["participacion_litros_pct"] = (df["litros_totales"] / total_litros * 100).round(2)

        # 4) Ticket promedio: dólares FOB por operación
        df["fob_promedio_operacion"] = (df["fob_total_usd"] / df["operaciones"]).round(2)

        # 5) Segmento de precio: pd.cut clasifica cada valor en un rango
        df["segmento_precio"] = pd.cut(df["usd_por_litro"], bins=self.LIMITES_PRECIO,
                                       labels=self.ETIQUETAS_PRECIO, right=False)

        # 6) Ranking por facturación FOB (1 = el que más factura)
        df["ranking_fob"] = df["fob_total_usd"].rank(ascending=False, method="min").astype(int)

        print("\n[Análisis] Columnas nuevas creadas: usd_por_litro, participacion_fob_pct, "
              "participacion_litros_pct, fob_promedio_operacion, segmento_precio, ranking_fob")
        return self

    # ------------------------------------------------------------------
    def mercados_premium_fraccionado(self, minimo_operaciones: int = 3) -> pd.DataFrame:
        """Filtro con varias condiciones (todas deben cumplirse, operador &):
           - vino fraccionado (embotellado),
           - con al menos `minimo_operaciones` operaciones (destino recurrente),
           - y precio por litro mayor al promedio del fraccionado.
        Ordenado de mayor a menor precio por litro.
        """
        df = self.df
        es_fraccionado = df["modalidad_envio"] == "fraccionado"
        precio_promedio = df.loc[es_fraccionado, "usd_por_litro"].mean()

        filtro = (
            es_fraccionado
            & (df["operaciones"] >= minimo_operaciones)
            & (df["usd_por_litro"] > precio_promedio)
        )
        resultado = df[filtro].sort_values("usd_por_litro", ascending=False)
        print(f"\n[Análisis] Precio promedio del fraccionado: {precio_promedio:.2f} USD/l")
        print(f"[Análisis] Mercados de fraccionado con precio sobre el promedio y "
              f">= {minimo_operaciones} operaciones: {len(resultado)}")
        return resultado

    def destinos_granel_grandes(self, minimo_litros: float = 100_000) -> pd.DataFrame:
        """Destinos de granel con volumen alto. Usa | (o) y & (y) combinados:
           granel  Y  (más de `minimo_litros` litros  O  más del 5% del FOB total).
        """
        df = self.df
        filtro = (df["modalidad_envio"] == "granel") & (
            (df["litros_totales"] > minimo_litros) | (df["participacion_fob_pct"] > 5)
        )
        return df[filtro].sort_values(["litros_totales", "fob_total_usd"], ascending=False)

    # ------------------------------------------------------------------
    def resumen_por_region(self) -> pd.DataFrame:
        """Agrupa por región del mundo y modalidad, con totales y precio medio."""
        resumen = (self.df
                   .groupby(["region", "modalidad_envio"], as_index=False)
                   .agg(paises=("pais", "nunique"),
                        litros=("litros_totales", "sum"),
                        fob_usd=("fob_total_usd", "sum")))
        resumen["usd_por_litro"] = (resumen["fob_usd"] / resumen["litros"]).round(2)
        return resumen.sort_values("fob_usd", ascending=False)

    # ------------------------------------------------------------------
    def resultado_final(self) -> pd.DataFrame:
        """DataFrame procesado completo, ordenado por ranking de facturación."""
        df = self.df.sort_values("ranking_fob").reset_index(drop=True)
        # La columna categórica se pasa a texto para guardarla sin problemas en SQLite/CSV
        df["segmento_precio"] = df["segmento_precio"].astype("string")
        return df

    def exportar_csv(self, ruta: Path) -> None:
        # utf-8-sig agrega una marca al inicio para que Excel muestre bien las tildes
        self.resultado_final().to_csv(ruta, index=False, encoding="utf-8-sig")
        print(f"[Análisis] CSV exportado: {Path(ruta).name}")

    def graficar_top_destinos(self, ruta: Path, top: int = 10) -> None:
        """Gráfico de barras con los destinos que más facturan (opcional)."""
        try:
            import matplotlib
            matplotlib.use("Agg")          # dibuja en archivo, sin abrir ventanas
            import matplotlib.pyplot as plt
        except ImportError:
            print("[Análisis] matplotlib no está instalado: se omite el gráfico.")
            return

        por_pais = (self.df.groupby("pais")["fob_total_usd"].sum()
                    .sort_values(ascending=True).tail(top) / 1_000_000)
        fig, ax = plt.subplots(figsize=(9, 5.5))
        por_pais.plot.barh(ax=ax, color="#7b1e3a")
        ax.set_title(f"Top {top} destinos de exportación vitivinícola por valor FOB (fuente: INV)")
        ax.set_xlabel("Millones de USD FOB")
        ax.set_ylabel("")
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(ruta, dpi=120)
        plt.close(fig)
        print(f"[Análisis] Gráfico guardado: {Path(ruta).name}")
