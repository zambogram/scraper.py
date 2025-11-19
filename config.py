"""
Configuración del scraper de la Gaceta Oficial de Bolivia
"""
import os

# URL base de la Gaceta Oficial de Bolivia
BASE_URL = "https://www.gacetaoficialdebolivia.gob.bo"

# URLs específicas (ajustar según el sitio real)
LISTADO_URL = f"{BASE_URL}/normas/buscar"
BUSQUEDA_URL = f"{BASE_URL}/normas/buscar"

# Directorios del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PDFS_DIR = os.path.join(DATA_DIR, "pdfs")
TEXT_DIR = os.path.join(DATA_DIR, "text")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
JSON_DIR = os.path.join(EXPORTS_DIR, "json")
CSV_DIR = os.path.join(EXPORTS_DIR, "csv")

# Configuración de scraping
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

# Configuración de reintentos
MAX_RETRIES = 3
TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 1  # segundos

# Tipos de normas reconocidas
TIPOS_NORMAS = [
    "LEY",
    "DECRETO SUPREMO",
    "RESOLUCIÓN SUPREMA",
    "RESOLUCIÓN MINISTERIAL",
    "RESOLUCIÓN ADMINISTRATIVA",
    "RESOLUCIÓN BI-MINISTERIAL",
    "AUTO SUPREMO",
    "SENTENCIA CONSTITUCIONAL",
    "ORDENANZA MUNICIPAL",
]

# Secciones jurídicas esperadas
SECCIONES_JURIDICAS = [
    "VISTOS",
    "CONSIDERANDO",
    "POR TANTO",
    "DECRETA",
    "RESUELVE",
    "ARTÍCULO",
    "ARTÍCULOS",
    "DISPOSICIONES FINALES",
    "DISPOSICIONES TRANSITORIAS",
    "DISPOSICIONES ADICIONALES",
    "DISPOSICIONES ABROGATORIAS",
    "DISPOSICIÓN FINAL",
    "DISPOSICIÓN TRANSITORIA",
    "DISPOSICIÓN ADICIONAL",
    "DISPOSICIÓN ABROGATORIA",
]

# Configuración de exportación
ENCODING = 'utf-8'
CSV_DELIMITER = ','
CSV_QUOTECHAR = '"'

# Configuración de logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
