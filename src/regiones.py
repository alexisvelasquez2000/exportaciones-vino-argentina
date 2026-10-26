"""
Tabla auxiliar: a qué región del mundo pertenece cada país de destino.

El CSV del INV no trae la región, así que la agregamos nosotros. Sirve para
analizar, por ejemplo, cuánto se exporta a Norteamérica vs. Europa.
Los nombres se comparan "normalizados" (minúsculas y sin tildes) porque el
INV escribe los países sin acentos y con mayúsculas propias
(p. ej. "Republica Federal De Alemania").
"""

import unicodedata

REGIONES = {
    "Norteamérica": [
        "estados unidos", "canada", "mexico",
    ],
    "Latinoamérica y Caribe": [
        "brasil", "paraguay", "uruguay", "chile", "bolivia", "peru", "ecuador",
        "colombia", "venezuela", "panama", "costa rica", "nicaragua", "guatemala",
        "honduras", "el salvador", "republica dominicana", "cuba", "puerto rico",
        "haiti", "jamaica", "aruba", "curazao", "bahamas", "barbados", "belice",
        "trinidad y tobago", "guyana", "surinam", "islas caiman", "antigua y barbuda",
        "santa lucia", "granada", "san vicente y las granadinas", "dominica",
        "san cristobal y nevis", "bermudas", "san martin", "islas virgenes",
        "islas virgenes britanicas", "islas virgenes (ee.uu.)", "guadalupe", "martinica",
        "guayana francesa", "antillas holandesas", "bonaire", "trinidad tobago",
        "florida (uruguay)", "puerto rico(estado asociado)", "san martin(parte holandesa)",
    ],
    "Europa": [
        "reino unido", "republica federal de alemania", "alemania", "paises bajos",
        "holanda", "belgica", "francia", "espana", "italia", "portugal", "suiza",
        "austria", "dinamarca", "suecia", "noruega", "finlandia", "irlanda",
        "islandia", "polonia", "republica checa", "chequia", "eslovaquia", "hungria",
        "rumania", "bulgaria", "grecia", "croacia", "eslovenia", "serbia",
        "estonia", "letonia", "lituania", "luxemburgo", "malta", "chipre",
        "ucrania", "rusia", "federacion rusa", "bielorrusia", "belarus", "moldavia",
        "georgia", "armenia", "azerbaiyan", "albania", "montenegro", "macedonia",
        "macedonia del norte", "bosnia y herzegovina", "monaco", "andorra", "republica de croacia",
        "liechtenstein", "gibraltar", "turquia",
    ],
    "Asia y Medio Oriente": [
        "china", "japon", "corea del sur", "corea republicana", "republica de corea",
        "taiwan", "hong kong", "macao", "singapur", "malasia", "tailandia", "vietnam",
        "filipinas", "indonesia", "india", "sri lanka", "bangladesh", "nepal",
        "camboya", "myanmar", "laos", "mongolia", "kazajstan", "uzbekistan",
        "israel", "emiratos arabes unidos", "arabia saudita", "qatar", "katar",
        "kuwait", "bahrein", "oman", "jordania", "libano", "iran", "irak",
        "maldivas", "pakistan", "bahreim", "iraq", "cambodya (ex kampuchea)",
        "hong kong reg.admin.espec.de(china)", "myanmar union de (ex birmania)",
    ],
    "Oceanía": [
        "australia", "nueva zelanda", "nueva zelandia", "fiji", "polinesia francesa",
        "nueva caledonia", "papua nueva guinea",
    ],
    "África": [
        "sudafrica", "republica de sudafrica", "nigeria", "angola", "egipto",
        "marruecos", "argelia", "tunez", "ghana", "kenia", "costa de marfil",
        "senegal", "camerun", "mozambique", "namibia", "mauricio", "tanzania",
        "gabon", "congo", "republica democratica del congo", "etiopia", "uganda",
        "zambia", "zimbabwe", "botswana", "cabo verde", "guinea ecuatorial",
        "seychelles", "togo", "benin", "liberia", "sierra leona", "gambia", "kenya",
        "mauricio, islas",
    ],
}

# Nota: algunos nombres se agregaron tal cual los escribe el INV en el CSV
# (p. ej. "Bahreim", "Kenya", "Florida (Uruguay)"). Los "Terr. Vinculados A ..."
# no son un país concreto, así que quedan en "Otros".

# Se "invierte" el diccionario para buscar rápido: {"brasil": "Latinoamérica y Caribe", ...}
_PAIS_A_REGION = {pais: region for region, paises in REGIONES.items() for pais in paises}


def normalizar(texto: str) -> str:
    """'República Federal De Alemania' -> 'republica federal de alemania'."""
    sin_tildes = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.lower().split())


def obtener_region(pais: str) -> str:
    """Devuelve la región del país o 'Otros' si no está en la lista."""
    return _PAIS_A_REGION.get(normalizar(pais), "Otros")
