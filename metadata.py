"""
Extractor de metadatos de documentos legales de la Gaceta Oficial de Bolivia
"""
import re
import logging
from datetime import datetime
from dateutil import parser as date_parser

import config

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


def extraer_metadatos(documento, secciones=None):
    """
    Extrae metadatos completos de un documento.

    Args:
        documento (dict): Diccionario con información básica del documento
        secciones (dict): Secciones parseadas del documento (opcional)

    Returns:
        dict: Metadatos estructurados
    """
    logger.info(f"Extrayendo metadatos de {documento.get('id')}")

    titulo = documento.get('titulo_raw', '')
    texto_completo = ''

    if secciones:
        texto_completo = secciones.get('texto_completo', '')

    metadatos = {
        'id': documento.get('id'),
        'titulo': titulo,
        'tipo_norma': extraer_tipo_norma(titulo, texto_completo),
        'numero_norma': extraer_numero_norma(titulo, texto_completo),
        'fecha': extraer_y_normalizar_fecha(documento.get('fecha_raw'), texto_completo),
        'fecha_raw': documento.get('fecha_raw'),
        'seccion': documento.get('seccion_raw') or extraer_tipo_norma(titulo, texto_completo),
        'url_pdf': documento.get('url_pdf'),
        'url_detalle': documento.get('url_detalle'),
        'resumen': generar_resumen(titulo, secciones),
        'temas': extraer_temas(titulo, texto_completo),
        'entidad_emisora': extraer_entidad_emisora(titulo, texto_completo),
    }

    # Agregar información de secciones si está disponible
    if secciones:
        from parser import obtener_resumen_estructura
        metadatos['estructura'] = obtener_resumen_estructura(secciones)

    return metadatos


def extraer_tipo_norma(titulo, texto=''):
    """
    Identifica el tipo de norma legal.

    Args:
        titulo (str): Título del documento
        texto (str): Texto completo (opcional)

    Returns:
        str: Tipo de norma o 'DESCONOCIDO'
    """
    texto_busqueda = f"{titulo} {texto[:500]}"

    # Buscar en orden de especificidad
    for tipo in config.TIPOS_NORMAS:
        # Usar word boundaries para evitar coincidencias parciales
        patron = rf'\b{re.escape(tipo)}\b'
        if re.search(patron, texto_busqueda, re.IGNORECASE):
            logger.debug(f"Tipo de norma identificado: {tipo}")
            return tipo

    # Tipos adicionales no en config
    tipos_extra = {
        'DECRETO LEY': r'\bDECRETO\s+LEY\b',
        'LEY MUNICIPAL': r'\bLEY\s+MUNICIPAL\b',
        'RESOLUCIÓN SUPREMA': r'\bRESOLUCI[OÓ]N\s+SUPREMA\b',
        'RESOLUCIÓN MINISTERIAL': r'\bRESOLUCI[OÓ]N\s+MINISTERIAL\b',
    }

    for tipo, patron in tipos_extra.items():
        if re.search(patron, texto_busqueda, re.IGNORECASE):
            logger.debug(f"Tipo de norma identificado: {tipo}")
            return tipo

    logger.debug("Tipo de norma no identificado")
    return 'DESCONOCIDO'


def extraer_numero_norma(titulo, texto=''):
    """
    Extrae el número de la norma legal.

    Args:
        titulo (str): Título del documento
        texto (str): Texto completo (opcional)

    Returns:
        str: Número de la norma o None
    """
    texto_busqueda = f"{titulo} {texto[:500]}"

    # Patrones comunes para números de normas
    patrones = [
        # Ley Nº 1234
        r'(?:LEY|DECRETO|RESOLUCIÓN|RESOLUCION)\s+(?:N[°º]?|NRO\.?|No\.?)\s*(\d+)',
        # D.S. 1234
        r'D\.S\.\s*(?:N[°º]?|NRO\.?|No\.?)?\s*(\d+)',
        # Número seguido de tipo
        r'(\d+)\s*[-/]\s*\d{4}',  # Formato 1234/2024
    ]

    for patron in patrones:
        match = re.search(patron, texto_busqueda, re.IGNORECASE)
        if match:
            numero = match.group(1)
            logger.debug(f"Número de norma identificado: {numero}")
            return numero

    logger.debug("Número de norma no identificado")
    return None


def extraer_y_normalizar_fecha(fecha_raw, texto=''):
    """
    Extrae y normaliza la fecha del documento.

    Args:
        fecha_raw (str): Fecha en formato crudo
        texto (str): Texto completo para búsqueda adicional

    Returns:
        str: Fecha normalizada en formato ISO (YYYY-MM-DD) o None
    """
    if not fecha_raw and texto:
        # Intentar extraer fecha del texto
        from scraper import _extraer_fecha_de_texto
        fecha_raw = _extraer_fecha_de_texto(texto[:1000])

    if not fecha_raw:
        logger.debug("No se pudo encontrar fecha")
        return None

    try:
        # Intentar parsear con dateutil (maneja múltiples formatos)
        fecha_obj = date_parser.parse(fecha_raw, dayfirst=True, fuzzy=True)
        fecha_iso = fecha_obj.strftime('%Y-%m-%d')
        logger.debug(f"Fecha normalizada: {fecha_iso}")
        return fecha_iso

    except Exception as e:
        logger.debug(f"No se pudo parsear fecha '{fecha_raw}': {e}")

        # Intentar extracción manual
        # Formato: dd de mes de yyyy
        patron = r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})'
        match = re.search(patron, fecha_raw, re.IGNORECASE)

        if match:
            dia = match.group(1).zfill(2)
            mes_texto = match.group(2).lower()
            año = match.group(3)

            meses = {
                'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
                'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
                'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
            }

            mes = meses.get(mes_texto)
            if mes:
                fecha_iso = f"{año}-{mes}-{dia}"
                logger.debug(f"Fecha normalizada manualmente: {fecha_iso}")
                return fecha_iso

        return fecha_raw  # Retornar sin normalizar si no se puede parsear


def generar_resumen(titulo, secciones=None):
    """
    Genera un resumen del documento.

    Args:
        titulo (str): Título del documento
        secciones (dict): Secciones parseadas (opcional)

    Returns:
        str: Resumen del documento
    """
    partes_resumen = []

    # Agregar título
    if titulo:
        partes_resumen.append(titulo[:200])

    # Agregar información de artículos si existe
    if secciones:
        num_articulos = len(secciones.get('articulos', []))
        if num_articulos > 0:
            partes_resumen.append(f"Contiene {num_articulos} artículo(s)")

        # Agregar primer considerando si existe
        considerandos = secciones.get('considerando', [])
        if considerandos:
            primer_considerando = considerandos[0][:150]
            partes_resumen.append(f"Considerando: {primer_considerando}...")

    resumen = '. '.join(partes_resumen)
    return resumen


def extraer_temas(titulo, texto=''):
    """
    Identifica temas principales del documento.

    Args:
        titulo (str): Título del documento
        texto (str): Texto completo (opcional)

    Returns:
        list: Lista de temas identificados
    """
    temas = []
    texto_busqueda = f"{titulo} {texto[:1000]}".lower()

    # Diccionario de temas y palabras clave
    palabras_clave_temas = {
        'EDUCACIÓN': ['educación', 'educativo', 'escuela', 'universidad', 'estudiante', 'maestro'],
        'SALUD': ['salud', 'medicina', 'hospital', 'médico', 'sanitario', 'enfermedad'],
        'ECONOMÍA': ['económico', 'economía', 'comercio', 'impuesto', 'tributario', 'financiero'],
        'MEDIO AMBIENTE': ['medio ambiente', 'ambiental', 'ecológico', 'contaminación', 'recursos naturales'],
        'JUSTICIA': ['justicia', 'judicial', 'penal', 'delito', 'tribunal', 'sentencia'],
        'TRABAJO': ['laboral', 'trabajo', 'empleado', 'sindicato', 'salario'],
        'MINERÍA': ['minería', 'minero', 'explotación minera', 'cooperativa minera'],
        'HIDROCARBUROS': ['hidrocarburos', 'petróleo', 'gas', 'ypfb'],
        'DEFENSA': ['defensa', 'militar', 'fuerzas armadas'],
        'SEGURIDAD': ['seguridad', 'policía', 'orden público'],
        'AGRICULTURA': ['agricultura', 'agrícola', 'agropecuario', 'rural', 'campesino'],
        'VIVIENDA': ['vivienda', 'construcción', 'urbanismo'],
        'TRANSPORTE': ['transporte', 'vial', 'tránsito', 'carretera'],
        'TELECOMUNICACIONES': ['telecomunicaciones', 'comunicación', 'internet', 'telefonía'],
        'TURISMO': ['turismo', 'turístico', 'patrimonio'],
    }

    for tema, palabras in palabras_clave_temas.items():
        for palabra in palabras:
            if palabra in texto_busqueda:
                if tema not in temas:
                    temas.append(tema)
                break

    logger.debug(f"Temas identificados: {temas}")
    return temas


def extraer_entidad_emisora(titulo, texto=''):
    """
    Identifica la entidad que emitió el documento.

    Args:
        titulo (str): Título del documento
        texto (str): Texto completo (opcional)

    Returns:
        str: Entidad emisora o None
    """
    texto_busqueda = f"{titulo} {texto[:1000]}"

    entidades = {
        'PRESIDENCIA': r'\bPRESIDEN(?:CIA|TE)\b',
        'ASAMBLEA LEGISLATIVA': r'\bASAMBLEA\s+LEGISLATIVA\b',
        'CONGRESO': r'\bCONGRESO\b',
        'MINISTERIO DE ECONOMÍA': r'\bMINISTERIO\s+DE\s+ECONOM[IÍ]A\b',
        'MINISTERIO DE SALUD': r'\bMINISTERIO\s+DE\s+SALUD\b',
        'MINISTERIO DE EDUCACIÓN': r'\bMINISTERIO\s+DE\s+EDUCACI[OÓ]N\b',
        'MINISTERIO DE JUSTICIA': r'\bMINISTERIO\s+DE\s+JUSTICIA\b',
        'MINISTERIO DE TRABAJO': r'\bMINISTERIO\s+DE\s+TRABAJO\b',
        'MINISTERIO': r'\bMINISTERIO\s+DE\s+[A-ZÁÉÍÓÚÑ\s]+',
        'TRIBUNAL CONSTITUCIONAL': r'\bTRIBUNAL\s+CONSTITUCIONAL\b',
        'CORTE SUPREMA': r'\bCORTE\s+SUPREMA\b',
    }

    for entidad, patron in entidades.items():
        match = re.search(patron, texto_busqueda, re.IGNORECASE)
        if match:
            if entidad == 'MINISTERIO':
                # Capturar el nombre completo del ministerio
                entidad_encontrada = match.group(0)
            else:
                entidad_encontrada = entidad
            logger.debug(f"Entidad emisora identificada: {entidad_encontrada}")
            return entidad_encontrada

    logger.debug("Entidad emisora no identificada")
    return None


def construir_registro_completo(documento, secciones, metadatos):
    """
    Construye un registro completo del documento para exportación.

    Args:
        documento (dict): Información básica del documento
        secciones (dict): Secciones parseadas
        metadatos (dict): Metadatos extraídos

    Returns:
        dict: Registro completo del documento
    """
    registro = {
        # Información básica
        'id': metadatos.get('id'),
        'titulo': metadatos.get('titulo'),
        'tipo_norma': metadatos.get('tipo_norma'),
        'numero_norma': metadatos.get('numero_norma'),
        'fecha': metadatos.get('fecha'),
        'seccion': metadatos.get('seccion'),
        'entidad_emisora': metadatos.get('entidad_emisora'),

        # URLs
        'url_pdf': metadatos.get('url_pdf'),
        'url_detalle': metadatos.get('url_detalle'),

        # Contenido
        'resumen': metadatos.get('resumen'),
        'temas': ','.join(metadatos.get('temas', [])),

        # Estructura del documento
        'num_articulos': len(secciones.get('articulos', [])) if secciones else 0,
        'num_considerandos': len(secciones.get('considerando', [])) if secciones else 0,
        'tiene_vistos': bool(secciones.get('vistos')) if secciones else False,
        'tiene_disposiciones_finales': bool(secciones.get('disposiciones_finales')) if secciones else False,

        # Texto completo (opcional, puede ser muy grande)
        'texto_completo': secciones.get('texto_completo', '') if secciones else '',
    }

    # Agregar artículos como JSON string si existen
    if secciones and secciones.get('articulos'):
        import json
        registro['articulos_json'] = json.dumps(secciones['articulos'], ensure_ascii=False)

    return registro


def validar_metadatos(metadatos):
    """
    Valida que los metadatos sean completos y correctos.

    Args:
        metadatos (dict): Metadatos a validar

    Returns:
        tuple: (es_valido, lista_de_errores)
    """
    errores = []

    # Campos requeridos
    if not metadatos.get('id'):
        errores.append("Falta ID del documento")

    if not metadatos.get('titulo'):
        errores.append("Falta título del documento")

    # Advertencias (no errores críticos)
    if metadatos.get('tipo_norma') == 'DESCONOCIDO':
        logger.warning(f"Tipo de norma desconocido para {metadatos.get('id')}")

    if not metadatos.get('fecha'):
        logger.warning(f"Fecha no identificada para {metadatos.get('id')}")

    es_valido = len(errores) == 0

    return es_valido, errores
