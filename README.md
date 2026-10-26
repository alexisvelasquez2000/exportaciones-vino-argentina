Exportaciones vitivinícolas de arg



Proyecto en Python que automatiza la descarga, procesamiento y análisis de las exportaciones de vinos y mostos argentinos usando datos oficiales del INV. Nació de la necesidad en el área de comercio exterior de una bodega.



El objetivo principal de esta aplicación es responder a la pregunta de cuáles son los mercados internacionales más rentables para el vino argentino, cómo se distribuye el valor comercial entre el vino fraccionado y el vino a granel, y qué variedades logran los mejores precios promedio por litro en el mercado exterior.



Los datos oficiales provienen del portal de datos abiertos disponible AQUÍ https://datos.gob.ar



La aplicación realiza una descarga automática conectándose a la API para bajar los archivos en formato CSV más recientes. Luego efectúa la limpieza y estructuración normalizando nombres, corrigiendo tipos de datos, detectando regiones geográficas y preparando la información. Almacena todo en una base de datos relacional SQLite bajo un esquema estrella con tablas separadas para países, productos, variedades y operaciones. Finalmente realiza el análisis de negocio procesando las exportaciones con pandas y consultas SQL para calcular precios promedio por litro, comparar envíos fraccionados contra granel, segmentar mercados premium y elaborar rankings.



En cuanto a los CONCLUSIONES con datos correspondientes al período de enero a abril de 2025, se analizaron 22520 operaciones hacia 109 países sumando 78,5 millones de litros y 237,4 millones de dólares FOB. Estados Unidos encabeza las compras con el 28,7 por ciento del valor en dólares, seguido por Reino Unido con 12 por ciento, Brasil con 10,7 por ciento y Canadá con 6,6 por ciento. El vino embotellado o fraccionado representa el 56 por ciento del volumen pero genera el 78,5 por ciento de los ingresos, vendiéndose a un promedio de 4,24 dólares por litro frente a 1,48 dólares del vino a granel. El Malbec tinto lidera en volumen total con 110,7 millones de dólares en 102 países, aunque el Cabernet Franc con 6,98 dólares por litro y el Pinot Negro con 6,57 dólares por litro consiguen los mejores precios promedio.



El sistema sigue una arquitectura limpia distribuida en la carpeta de código fuente. El archivo config.py gestiona los parámetros generales y rutas. El archivo extractor.py descarga los datos desde la API. El archivo limpieza.py lee y normaliza los archivos crudos. El archivo regiones.py mapea los países con sus regiones. El archivo base_datos.py crea y gestiona la base SQLite. El archivo consultas.py ejecuta las sentencias SQL de agregación y filtrado. El archivo analisis.py calcula los indicadores comerciales y genera gráficos en pandas. El archivo main.py funciona como el orquestador central que ejecuta todo el proceso en orden.



Durante la fase de corrección de errores del proyecto se utilizaron asistentes de Inteligencia Artificial como Gemini para las consultas SQL y el diseño del esquema estrella de la base de datos.



Para ejecutar este proyecto se requiere Python