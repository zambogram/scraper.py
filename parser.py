"""
Parser de documentos legales de la Gaceta Oficial de Bolivia
Extrae secciones jurídicas y artículos de textos legales
"""
import re
import logging
from PyPDF2 import PdfReader

import config

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


def extraer_texto_de_pdf(ruta_pdf, usar_ocr_fallback=True):
    """
    Extrae texto de un archivo PDF.

    Args:
        ruta_pdf (str): Ruta al archivo PDF
        usar_ocr_fallback (bool): Si True, usa OCR si PyPDF2 falla

    Returns:
        str: Texto extraído del PDF o None si falla
    """
    try:
        logger.info(f"Extrayendo texto de PDF: {ruta_pdf}")

        reader = PdfReader(ruta_pdf)
        texto_completo = []

        for i, page in enumerate(reader.pages):
            try:
                texto = page.extract_text()
                if texto:
                    texto_completo.append(texto)
            except Exception as e:
                logger.warning(f"Error extrayendo página {i + 1}: {e}")
                continue

        texto_final = '\n'.join(texto_completo)

        if texto_final.strip():
            logger.info(f"Texto extraído con PyPDF2: {len(texto_final)} caracteres")
            return texto_final
        else:
            # PyPDF2 no pudo extraer texto, intentar OCR
            if usar_ocr_fallback:
                logger.warning(f"PyPDF2 no extrajo texto. Intentando OCR...")
                return extraer_texto_pdf_con_ocr(ruta_pdf)
            else:
                logger.warning(f"No se pudo extraer texto del PDF: {ruta_pdf}")
                return None

    except Exception as e:
        logger.error(f"Error leyendo PDF {ruta_pdf}: {e}")

        # Intentar OCR como última opción
        if usar_ocr_fallback:
            logger.info("Intentando OCR como fallback...")
            return extraer_texto_pdf_con_ocr(ruta_pdf)

        return None


def extraer_texto_pdf_con_ocr(ruta_pdf):
    """
    Extrae texto de PDF usando OCR (para PDFs escaneados).

    Requiere: pytesseract, pdf2image, tesseract-ocr instalado en el sistema

    Args:
        ruta_pdf (str): Ruta al archivo PDF

    Returns:
        str: Texto extraído o None si falla
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
        from PIL import Image

        logger.info(f"Extrayendo texto con OCR: {ruta_pdf}")

        # Convertir PDF a imágenes
        imagenes = convert_from_path(ruta_pdf, dpi=300)

        texto_completo = []

        for i, imagen in enumerate(imagenes):
            try:
                # Aplicar OCR a cada página
                texto = pytesseract.image_to_string(imagen, lang='spa')
                if texto:
                    texto_completo.append(texto)
                logger.info(f"OCR página {i+1}/{len(imagenes)}")
            except Exception as e:
                logger.warning(f"Error OCR en página {i+1}: {e}")
                continue

        texto_final = '\n'.join(texto_completo)

        if texto_final.strip():
            logger.info(f"Texto extraído con OCR: {len(texto_final)} caracteres")
            return texto_final
        else:
            logger.warning("OCR no pudo extraer texto")
            return None

    except ImportError:
        logger.warning("pytesseract o pdf2image no están instalados")
        logger.warning("Para usar OCR, instala:")
        logger.warning("  pip install pytesseract pdf2image Pillow")
        logger.warning("  Y también: sudo apt-get install tesseract-ocr tesseract-ocr-spa")
        return None

    except Exception as e:
        logger.error(f"Error en OCR: {e}")
        return None


def parsear_documento(texto):
    """
    Parsea un documento legal y extrae sus secciones jurídicas.

    Args:
        texto (str): Texto completo del documento

    Returns:
        dict: Diccionario con secciones identificadas
    """
    if not texto:
        return {}

    logger.info("Parseando documento legal")

    secciones = {
        'texto_completo': texto,
        'vistos': extraer_seccion_vistos(texto),
        'considerando': extraer_seccion_considerando(texto),
        'por_tanto': extraer_seccion_por_tanto(texto),
        'decreta_resuelve': extraer_seccion_decreta_resuelve(texto),
        'articulos': extraer_articulos(texto),
        'disposiciones_finales': extraer_disposiciones(texto, 'FINALES'),
        'disposiciones_transitorias': extraer_disposiciones(texto, 'TRANSITORIAS'),
        'disposiciones_adicionales': extraer_disposiciones(texto, 'ADICIONALES'),
        'disposiciones_abrogatorias': extraer_disposiciones(texto, 'ABROGATORIAS'),
    }

    return secciones


def extraer_seccion_vistos(texto):
    """
    Extrae la sección VISTOS del documento.

    Args:
        texto (str): Texto completo

    Returns:
        str: Contenido de la sección VISTOS o None
    """
    # Patrones para identificar VISTOS
    patrones = [
        r'VISTOS[:\s]+(.+?)(?=CONSIDERANDO|POR TANTO|DECRETA|RESUELVE|\Z)',
        r'VISTO[:\s]+(.+?)(?=CONSIDERANDO|POR TANTO|DECRETA|RESUELVE|\Z)',
    ]

    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        if match:
            contenido = match.group(1).strip()
            logger.debug(f"Sección VISTOS encontrada: {len(contenido)} caracteres")
            return contenido

    logger.debug("Sección VISTOS no encontrada")
    return None


def extraer_seccion_considerando(texto):
    """
    Extrae la sección CONSIDERANDO del documento.

    Args:
        texto (str): Texto completo

    Returns:
        list: Lista de considerandos o lista vacía
    """
    # Buscar el bloque completo de CONSIDERANDO
    patron_bloque = r'CONSIDERANDO[:\s]+(.+?)(?=POR TANTO|DECRETA|RESUELVE|ARTÍCULO|\Z)'
    match = re.search(patron_bloque, texto, re.IGNORECASE | re.DOTALL)

    if not match:
        logger.debug("Sección CONSIDERANDO no encontrada")
        return []

    bloque = match.group(1).strip()

    # Dividir en considerandos individuales
    # Patrón: "Que..." al inicio de cada considerando
    considerandos = re.split(r'\n\s*Que\s+', bloque, flags=re.IGNORECASE)

    # Limpiar y filtrar considerandos vacíos
    considerandos = [c.strip() for c in considerandos if c.strip()]

    # Agregar "Que" de nuevo al inicio (excepto si ya lo tiene)
    considerandos_formateados = []
    for c in considerandos:
        if not c.lower().startswith('que '):
            c = 'Que ' + c
        considerandos_formateados.append(c)

    logger.debug(f"Encontrados {len(considerandos_formateados)} considerandos")
    return considerandos_formateados


def extraer_seccion_por_tanto(texto):
    """
    Extrae la sección POR TANTO del documento.

    Args:
        texto (str): Texto completo

    Returns:
        str: Contenido de la sección POR TANTO o None
    """
    patrones = [
        r'POR TANTO[:\s,]+(.+?)(?=DECRETA|RESUELVE|ARTÍCULO|SE DECRETA|SE RESUELVE|\Z)',
    ]

    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        if match:
            contenido = match.group(1).strip()
            logger.debug(f"Sección POR TANTO encontrada: {len(contenido)} caracteres")
            return contenido

    logger.debug("Sección POR TANTO no encontrada")
    return None


def extraer_seccion_decreta_resuelve(texto):
    """
    Extrae la sección DECRETA o RESUELVE del documento.

    Args:
        texto (str): Texto completo

    Returns:
        str: Contenido de la sección o None
    """
    patrones = [
        r'(?:SE\s+)?DECRETA[:\s]+(.+?)(?=ARTÍCULO|DISPOSICIONES|\Z)',
        r'(?:SE\s+)?RESUELVE[:\s]+(.+?)(?=ARTÍCULO|DISPOSICIONES|\Z)',
    ]

    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        if match:
            contenido = match.group(1).strip()
            logger.debug(f"Sección DECRETA/RESUELVE encontrada: {len(contenido)} caracteres")
            return contenido

    logger.debug("Sección DECRETA/RESUELVE no encontrada")
    return None


def extraer_articulos(texto):
    """
    Extrae todos los artículos del documento.

    Args:
        texto (str): Texto completo

    Returns:
        list: Lista de diccionarios con número y contenido de cada artículo
    """
    articulos = []

    # Patrones para identificar artículos
    # Ejemplos: "ARTÍCULO 1.-", "Artículo 1º.-", "Art. 1.-", "ARTÍCULO PRIMERO.-"
    patrones = [
        # Artículo con número
        r'ART[IÍ]CULOS?\s+(\d+)[°º]?[.\-:\s]+(.+?)(?=ART[IÍ]CULOS?\s+\d+|DISPOSICI[OÓ]N|REGÍSTRESE|\Z)',
        # Artículo con número romano en palabras (PRIMERO, SEGUNDO, etc.)
        r'ART[IÍ]CULOS?\s+(PRIMER[O]?|SEGUND[O]?|TERCER[O]?|CUART[O]?|QUINT[O]?|SEXT[O]?|S[EÉ]PTIM[O]?|OCTAV[O]?|NOVEN[O]?|D[EÉ]CIM[O]?)[.\-:\s]+(.+?)(?=ART[IÍ]CULOS?|DISPOSICI[OÓ]N|REGÍSTRESE|\Z)',
    ]

    for patron in patrones:
        matches = re.finditer(patron, texto, re.IGNORECASE | re.DOTALL)
        for match in matches:
            numero = match.group(1)
            contenido = match.group(2).strip()

            # Convertir números escritos a dígitos si es necesario
            numero = convertir_numero_escrito(numero)

            articulos.append({
                'numero': numero,
                'contenido': contenido
            })

    # Si no se encontraron artículos con el patrón anterior, intentar otro enfoque
    if not articulos:
        # Buscar simplemente "Artículo" seguido de número
        patron_simple = r'Art[íi]culo\s+(\d+)[°º]?[.\-:\s]*([^\n]+(?:\n(?!Art[íi]culo)[^\n]+)*)'
        matches = re.finditer(patron_simple, texto, re.IGNORECASE)
        for match in matches:
            numero = match.group(1)
            contenido = match.group(2).strip()
            articulos.append({
                'numero': numero,
                'contenido': contenido
            })

    # Eliminar duplicados manteniendo el orden
    articulos_unicos = []
    numeros_vistos = set()
    for art in articulos:
        if art['numero'] not in numeros_vistos:
            articulos_unicos.append(art)
            numeros_vistos.add(art['numero'])

    logger.debug(f"Encontrados {len(articulos_unicos)} artículos")
    return articulos_unicos


def extraer_disposiciones(texto, tipo):
    """
    Extrae disposiciones (finales, transitorias, adicionales, abrogatorias).

    Args:
        texto (str): Texto completo
        tipo (str): Tipo de disposición (FINALES, TRANSITORIAS, etc.)

    Returns:
        list: Lista de disposiciones o lista vacía
    """
    # Normalizar tipo
    tipo = tipo.upper()

    # Patrones para el encabezado
    patrones_encabezado = [
        rf'DISPOSICIONES?\s+{tipo}[:\s]+(.+?)(?=DISPOSICIONES?\s+(?!{tipo})|REGÍSTRESE|COMUNÍQUESE|\Z)',
        rf'DISPOSICI[OÓ]N\s+{tipo}[:\s]+(.+?)(?=DISPOSICIONES?|REGÍSTRESE|COMUNÍQUESE|\Z)',
    ]

    bloque = None
    for patron in patrones_encabezado:
        match = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        if match:
            bloque = match.group(1).strip()
            break

    if not bloque:
        logger.debug(f"Disposiciones {tipo} no encontradas")
        return []

    # Dividir en disposiciones individuales
    # Pueden estar numeradas: "PRIMERA.-", "1.-", etc.
    disposiciones = []

    # Patrón para disposiciones numeradas
    patron_nums = r'(?:PRIMER[A]?|SEGUND[A]?|TERCER[A]?|CUART[A]?|QUINT[A]?|\d+)[°º]?[.\-:\s]+'
    partes = re.split(patron_nums, bloque, flags=re.IGNORECASE)

    # Filtrar partes vacías
    disposiciones = [p.strip() for p in partes if p.strip()]

    logger.debug(f"Encontradas {len(disposiciones)} disposiciones {tipo}")
    return disposiciones


def convertir_numero_escrito(numero_str):
    """
    Convierte números escritos en palabras a dígitos.

    Args:
        numero_str (str): Número en palabras o dígitos

    Returns:
        str: Número en dígitos
    """
    # Si ya es un número, retornar
    if numero_str.isdigit():
        return numero_str

    # Mapeo de palabras a números
    mapeo = {
        'PRIMER': '1', 'PRIMERO': '1', 'PRIMERA': '1',
        'SEGUND': '2', 'SEGUNDO': '2', 'SEGUNDA': '2',
        'TERCER': '3', 'TERCERO': '3', 'TERCERA': '3',
        'CUART': '4', 'CUARTO': '4', 'CUARTA': '4',
        'QUINT': '5', 'QUINTO': '5', 'QUINTA': '5',
        'SEXT': '6', 'SEXTO': '6', 'SEXTA': '6',
        'SÉPTIM': '7', 'SEPTIM': '7', 'SÉPTIMO': '7', 'SEPTIMO': '7', 'SÉPTIMA': '7', 'SEPTIMA': '7',
        'OCTAV': '8', 'OCTAVO': '8', 'OCTAVA': '8',
        'NOVEN': '9', 'NOVENO': '9', 'NOVENA': '9',
        'DÉCIM': '10', 'DECIM': '10', 'DÉCIMO': '10', 'DECIMO': '10', 'DÉCIMA': '10', 'DECIMA': '10',
    }

    numero_upper = numero_str.upper().strip()

    for palabra, digito in mapeo.items():
        if numero_upper.startswith(palabra):
            return digito

    # Si no se encuentra en el mapeo, retornar el original
    return numero_str


def extraer_firmantes(texto):
    """
    Extrae información de los firmantes del documento.

    Args:
        texto (str): Texto completo

    Returns:
        list: Lista de firmantes o lista vacía
    """
    firmantes = []

    # Buscar después de "Regístrese" o al final del documento
    patron_zona_firmas = r'(?:REG[IÍ]STRESE|REGÍSTRESE|COMUNÍQUESE)(.+)\Z'
    match = re.search(patron_zona_firmas, texto, re.IGNORECASE | re.DOTALL)

    if match:
        zona_firmas = match.group(1)

        # Buscar nombres en mayúsculas (típico de firmas)
        # Patrón: 2 o más palabras en mayúsculas
        patron_nombres = r'\b[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{10,}\b'
        nombres = re.findall(patron_nombres, zona_firmas)

        firmantes = [n.strip() for n in nombres if len(n.strip()) > 10]

    logger.debug(f"Encontrados {len(firmantes)} firmantes")
    return firmantes


def limpiar_texto(texto):
    """
    Limpia el texto eliminando caracteres extraños y normalizando espacios.

    Args:
        texto (str): Texto a limpiar

    Returns:
        str: Texto limpio
    """
    if not texto:
        return ""

    # Normalizar saltos de línea
    texto = re.sub(r'\r\n', '\n', texto)

    # Eliminar líneas excesivamente largas de guiones o caracteres especiales
    texto = re.sub(r'[-_=]{10,}', '', texto)

    # Normalizar espacios múltiples
    texto = re.sub(r' +', ' ', texto)

    # Normalizar saltos de línea múltiples
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    return texto.strip()


def obtener_resumen_estructura(secciones):
    """
    Genera un resumen de la estructura del documento parseado.

    Args:
        secciones (dict): Diccionario de secciones parseadas

    Returns:
        dict: Resumen de la estructura
    """
    resumen = {
        'tiene_vistos': secciones.get('vistos') is not None,
        'num_considerandos': len(secciones.get('considerando', [])),
        'tiene_por_tanto': secciones.get('por_tanto') is not None,
        'tiene_decreta_resuelve': secciones.get('decreta_resuelve') is not None,
        'num_articulos': len(secciones.get('articulos', [])),
        'num_disp_finales': len(secciones.get('disposiciones_finales', [])),
        'num_disp_transitorias': len(secciones.get('disposiciones_transitorias', [])),
        'num_disp_adicionales': len(secciones.get('disposiciones_adicionales', [])),
        'num_disp_abrogatorias': len(secciones.get('disposiciones_abrogatorias', [])),
    }

    return resumen
