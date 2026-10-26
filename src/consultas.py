"""
Consultas SQL del proyecto (Fase 2).

Se guardan como texto en un archivo aparte para que el SQL quede separado
del código Python y sea fácil de leer, probar y modificar.
"""

# ---------------------------------------------------------------------------
# Consulta principal: resumen por país de destino y modalidad de envío
# ---------------------------------------------------------------------------
# - JOIN une la tabla de hechos (exportaciones) con los catálogos paises y
#   productos usando las claves foráneas.
# - GROUP BY agrupa todas las operaciones de un mismo país y modalidad
#   (fraccionado = embotellado / granel = a granel en flexi-tank, tanque...).
# - COUNT, SUM y AVG resumen cada grupo en una sola fila.
RESUMEN_POR_DESTINO = """
SELECT
    p.nombre                        AS pais,
    p.region                        AS region,
    e.modalidad_envio               AS modalidad_envio,
    COUNT(*)                        AS operaciones,
    COUNT(DISTINCT pr.id_producto)  AS productos_distintos,
    SUM(e.litros)                   AS litros_totales,
    SUM(e.fob_usd)                  AS fob_total_usd,
    AVG(e.litros)                   AS litros_promedio_operacion
FROM exportaciones AS e
JOIN paises    AS p  ON p.id_pais      = e.id_pais
JOIN productos AS pr ON pr.id_producto = e.id_producto
GROUP BY p.nombre, p.region, e.modalidad_envio
ORDER BY fob_total_usd DESC;
"""

# ---------------------------------------------------------------------------
# Consulta complementaria: ranking de variedades de vino fraccionado
# ---------------------------------------------------------------------------
# Usa las tres tablas relacionadas a la vez y filtra con WHERE antes de
# agrupar; HAVING filtra después de agrupar (sobre los resultados de SUM).
RANKING_VARIEDADES = """
SELECT
    v.nombre                              AS variedad,
    pr.color                              AS color,
    COUNT(*)                              AS operaciones,
    COUNT(DISTINCT e.id_pais)             AS paises_destino,
    SUM(e.litros)                         AS litros_totales,
    SUM(e.fob_usd)                        AS fob_total_usd,
    ROUND(SUM(e.fob_usd) / SUM(e.litros), 2) AS usd_por_litro
FROM exportaciones AS e
JOIN variedades AS v  ON v.id_variedad  = e.id_variedad
JOIN productos  AS pr ON pr.id_producto = e.id_producto
WHERE e.modalidad_envio = 'fraccionado'
  AND v.nombre <> 'sin variedad'
GROUP BY v.nombre, pr.color
HAVING SUM(e.litros) > 0
ORDER BY fob_total_usd DESC
LIMIT 15;
"""
