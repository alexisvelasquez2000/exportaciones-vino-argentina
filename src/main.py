"""
Punto de entrada del proyecto. Ejecuta el flujo completo:

    Fase 1  Extracción  -> ExtractorINV           (extractor.py)
            Limpieza    -> LimpiadorExportaciones (limpieza.py)
    Fase 2  Base SQLite -> BaseDatosExportaciones (base_datos.py + consultas.py)
    Fase 3  Análisis    -> AnalizadorExportaciones (analisis.py)

Uso (desde la carpeta raíz del proyecto):
    python src/main.py
"""

import pandas as pd

import config
import consultas
from analisis import AnalizadorExportaciones
from base_datos import BaseDatosExportaciones
from extractor import ExtractorINV
from limpieza import LimpiadorExportaciones

# Opciones de pandas para que las tablas se vean completas en la consola
pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")


class PipelineExportaciones:
    """Coordina las tres fases. Cada clase hace una sola cosa; esta las une."""

    def __init__(self):
        self.extractor = ExtractorINV()
        self.base_datos = BaseDatosExportaciones(config.RUTA_DB)

    def ejecutar(self) -> None:
        titulo("FASE 1 - Extracción de datos (API CKAN del INV)")
        archivos = self.extractor.extraer()
        datos_limpios = LimpiadorExportaciones(archivos).leer().limpiar()

        titulo("FASE 2 - Persistencia en SQLite")
        with self.base_datos as db:
            db.crear_tablas()
            db.insertar_datos(datos_limpios)

            resumen = db.consultar(consultas.RESUMEN_POR_DESTINO)
            print("\nConsulta JOIN + GROUP BY (primeras 10 filas):")
            print(resumen.head(10).to_string(index=False))
            resumen.to_csv(config.RUTA_CSV_RESUMEN, index=False, encoding="utf-8-sig")

            variedades = db.consultar(consultas.RANKING_VARIEDADES)
            print("\nRanking de variedades (vino fraccionado):")
            print(variedades.to_string(index=False))

            titulo("FASE 3 - Análisis con pandas")
            analizador = AnalizadorExportaciones(resumen)
            analizador.explorar()
            analizador.agregar_columnas()

            premium = analizador.mercados_premium_fraccionado(minimo_operaciones=10)
            print(premium[["pais", "operaciones", "litros_totales", "fob_total_usd",
                           "usd_por_litro", "segmento_precio"]].head(15).to_string(index=False))

            granel = analizador.destinos_granel_grandes(minimo_litros=100_000)
            print(f"\n[Análisis] Destinos de granel de gran volumen: {len(granel)}")
            print(granel[["pais", "litros_totales", "fob_total_usd", "usd_por_litro",
                          "participacion_fob_pct"]].head(10).to_string(index=False))

            print("\n[Análisis] Resumen por región y modalidad:")
            print(analizador.resumen_por_region().to_string(index=False))

            # Guardado del resultado: como tabla nueva en la base y como CSV
            final = analizador.resultado_final()
            db.guardar_dataframe(final, "analisis_destinos")
            analizador.exportar_csv(config.RUTA_CSV_ANALISIS)
            analizador.graficar_top_destinos(config.RUTA_GRAFICO)

        titulo("Proceso terminado")
        print(f"Base de datos: {config.RUTA_DB}")
        print(f"CSV de análisis: {config.RUTA_CSV_ANALISIS}")


def titulo(texto: str) -> None:
    print("\n" + "=" * 70 + f"\n{texto}\n" + "=" * 70)


if __name__ == "__main__":
    # Este bloque solo corre si se ejecuta el archivo directamente
    # (no cuando otro archivo lo importa).
    PipelineExportaciones().ejecutar()
