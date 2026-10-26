"""
FASE 2 - Persistencia en una base de datos SQLite.

La clase BaseDatosExportaciones:
  - crea la base .db y las tablas relacionadas (claves primarias y foráneas),
  - inserta los datos limpios usando sentencias SQL (INSERT),
  - ejecuta consultas y devuelve el resultado como DataFrame de pandas,
  - guarda un DataFrame como tabla nueva (para el resultado del análisis).

Modelo relacional (esquema "estrella"):

    paises (1) ──< exportaciones >── (1) productos
                        │
                        └──────────── (1) variedades

Cada fila de "exportaciones" es una operación de exportación y apunta, por
medio de claves foráneas, a un país, un producto y una variedad. Así cada
país/producto/variedad se guarda UNA sola vez (sin repetir textos) y las
tablas se vuelven a unir con JOIN cuando se consultan.
"""

import sqlite3
from pathlib import Path

import pandas as pd

import config

# ---------------------------------------------------------------------------
# Sentencias SQL de creación de tablas (DDL)
# ---------------------------------------------------------------------------
SQL_CREAR_TABLAS = """
DROP TABLE IF EXISTS exportaciones;
DROP TABLE IF EXISTS paises;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS variedades;

CREATE TABLE paises (
    id_pais     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL UNIQUE,
    region      TEXT NOT NULL
);

CREATE TABLE productos (
    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    color       TEXT NOT NULL,
    UNIQUE (nombre, color)
);

CREATE TABLE variedades (
    id_variedad INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL UNIQUE
);

CREATE TABLE exportaciones (
    id_exportacion          INTEGER PRIMARY KEY AUTOINCREMENT,
    anio                    INTEGER NOT NULL,
    mes                     INTEGER NOT NULL,
    id_pais                 INTEGER NOT NULL,
    id_producto             INTEGER NOT NULL,
    id_variedad             INTEGER NOT NULL,
    anio_elaboracion        INTEGER,
    es_corte                INTEGER NOT NULL DEFAULT 0,
    modalidad_envio         TEXT,
    envase                  TEXT,
    cantidad_envases        INTEGER,
    litros                  REAL NOT NULL,
    fob_usd                 REAL NOT NULL,
    provincia_exportador    TEXT,
    departamento_exportador TEXT,
    FOREIGN KEY (id_pais)     REFERENCES paises (id_pais),
    FOREIGN KEY (id_producto) REFERENCES productos (id_producto),
    FOREIGN KEY (id_variedad) REFERENCES variedades (id_variedad)
);
"""


class BaseDatosExportaciones:
    """Maneja la conexión y todas las operaciones con la base SQLite."""

    def __init__(self, ruta_db: Path = config.RUTA_DB):
        self.ruta_db = Path(ruta_db)
        self.conexion: sqlite3.Connection | None = None

    # --- Conexión -------------------------------------------------------
    def conectar(self) -> None:
        self.ruta_db.parent.mkdir(parents=True, exist_ok=True)
        self.conexion = sqlite3.connect(self.ruta_db)
        # SQLite trae las claves foráneas desactivadas por defecto: las activamos
        self.conexion.execute("PRAGMA foreign_keys = ON;")

    def cerrar(self) -> None:
        if self.conexion is not None:
            self.conexion.close()
            self.conexion = None

    # Estos dos métodos permiten usar la clase con "with", que abre la
    # conexión al entrar y la cierra sola al salir (aunque haya un error):
    #     with BaseDatosExportaciones() as db:
    #         db.crear_tablas()
    def __enter__(self) -> "BaseDatosExportaciones":
        self.conectar()
        return self

    def __exit__(self, tipo_error, error, traza) -> None:
        self.cerrar()

    # --- Estructura -----------------------------------------------------
    def crear_tablas(self) -> None:
        """Borra (si existían) y crea las 4 tablas. Así cada ejecución arranca limpia."""
        self.conexion.executescript(SQL_CREAR_TABLAS)
        self.conexion.commit()
        print(f"[Base de datos] Tablas creadas en {self.ruta_db.name}")

    # --- Carga de datos ---------------------------------------------------
    def _insertar_dimension(self, sql_insert: str, filas: list[tuple],
                            sql_select: str) -> dict:
        """Inserta filas en una tabla "de catálogo" y devuelve {clave: id}.

        INSERT OR IGNORE evita duplicados gracias a la restricción UNIQUE.
        Luego se lee la tabla para saber qué id le asignó SQLite a cada valor.
        """
        cursor = self.conexion.cursor()
        cursor.executemany(sql_insert, filas)
        cursor.execute(sql_select)
        # La primera columna es el id; el resto forma la clave de búsqueda
        return {tuple(fila[1:]): fila[0] for fila in cursor.fetchall()}

    def insertar_datos(self, df: pd.DataFrame) -> None:
        """Carga el DataFrame limpio repartiéndolo en las 4 tablas."""
        # 1) Tablas de catálogo (dimensiones), sin repetidos
        paises = df[["pais", "region"]].drop_duplicates()
        mapa_paises = self._insertar_dimension(
            "INSERT OR IGNORE INTO paises (nombre, region) VALUES (?, ?)",
            list(paises.itertuples(index=False, name=None)),
            "SELECT id_pais, nombre FROM paises",
        )

        productos = df[["producto", "color"]].drop_duplicates()
        mapa_productos = self._insertar_dimension(
            "INSERT OR IGNORE INTO productos (nombre, color) VALUES (?, ?)",
            list(productos.itertuples(index=False, name=None)),
            "SELECT id_producto, nombre, color FROM productos",
        )

        variedades = df[["variedad"]].drop_duplicates()
        mapa_variedades = self._insertar_dimension(
            "INSERT OR IGNORE INTO variedades (nombre) VALUES (?)",
            list(variedades.itertuples(index=False, name=None)),
            "SELECT id_variedad, nombre FROM variedades",
        )

        # 2) Tabla de hechos: cada operación con los id de sus catálogos
        filas = []
        for r in df.itertuples(index=False):
            filas.append((
                int(r.anio), int(r.mes_num),
                mapa_paises[(r.pais,)],
                mapa_productos[(r.producto, r.color)],
                mapa_variedades[(r.variedad,)],
                None if pd.isna(r.anio_elaboracion) else int(r.anio_elaboracion),
                int(r.es_corte), r.modalidad_envio, r.envase,
                None if pd.isna(r.cantidad_envases) else int(r.cantidad_envases),
                float(r.litros), float(r.fob_usd),
                r.provincia_exportador, r.departamento_exportador,
            ))

        # Los "?" son parámetros: SQLite reemplaza cada uno por un valor de la
        # tupla. Es más seguro y rápido que armar el texto del SQL a mano.
        self.conexion.executemany("""
            INSERT INTO exportaciones (
                anio, mes, id_pais, id_producto, id_variedad, anio_elaboracion,
                es_corte, modalidad_envio, envase, cantidad_envases, litros,
                fob_usd, provincia_exportador, departamento_exportador)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, filas)
        self.conexion.commit()

        print(f"[Base de datos] Insertados: {len(mapa_paises)} países, "
              f"{len(mapa_productos)} productos, {len(mapa_variedades)} variedades, "
              f"{len(filas)} exportaciones")

    # --- Consultas --------------------------------------------------------
    def consultar(self, sql: str) -> pd.DataFrame:
        """Ejecuta un SELECT y devuelve el resultado directamente como DataFrame."""
        return pd.read_sql_query(sql, self.conexion)

    def guardar_dataframe(self, df: pd.DataFrame, nombre_tabla: str) -> None:
        """Guarda un DataFrame como tabla nueva (la reemplaza si ya existía)."""
        df.to_sql(nombre_tabla, self.conexion, if_exists="replace", index=False)
        self.conexion.commit()
        print(f"[Base de datos] Tabla '{nombre_tabla}' guardada ({len(df)} filas)")
