"""
Scraper principal para la Gaceta Oficial de Bolivia
"""
import requests
from bs4 import BeautifulSoup
import time
import os
import logging
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime

import config

# Configurar logging
logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


def listar_documentos_desde_gaceta(paginas=1, url_base=None):
    """
    Lista documentos desde el sitio de la Gaceta Oficial de Bolivia.

    Args:
        paginas (int): Número de páginas a scrapear (default: 1)
        url_base (str): URL base del listado (opcional, usa config si no se provee)

    Returns:
        list: Lista de diccionarios con información de cada documento
    """
    documentos = []
    url_listado = url_base or config.LISTADO_URL

    logger.info(f"Iniciando scraping de {paginas} página(s) desde {url_listado}")

    for pagina in range(1, paginas + 1):
        logger.info(f"Procesando página {pagina}/{paginas}")

        try:
            # Construir URL de la página
            if pagina == 1:
                url = url_listado
            else:
                # Ajustar según la paginación real del sitio
                # Opciones comunes: ?page=N, ?p=N, /page/N
                url = f"{url_listado}?page={pagina}"

            # Realizar request
            response = _hacer_request(url)
            if not response:
                logger.warning(f"No se pudo obtener la página {pagina}")
                continue

            # Parsear HTML
            soup = BeautifulSoup(response.content, 'lxml')

            # Extraer documentos de la página
            docs_pagina = _extraer_documentos_de_pagina(soup, url)
            documentos.extend(docs_pagina)

            logger.info(f"Extraídos {len(docs_pagina)} documentos de la página {pagina}")

            # Delay entre requests
            if pagina < paginas:
                time.sleep(config.DELAY_BETWEEN_REQUESTS)

        except Exception as e:
            logger.error(f"Error procesando página {pagina}: {e}")
            continue

    logger.info(f"Total de documentos extraídos: {len(documentos)}")
    return documentos


def _extraer_documentos_de_pagina(soup, url_pagina):
    """
    Extrae documentos de una página HTML parseada.

    Args:
        soup (BeautifulSoup): Objeto BeautifulSoup de la página
        url_pagina (str): URL de la página (para resolver URLs relativas)

    Returns:
        list: Lista de diccionarios con información de documentos
    """
    documentos = []

    # IMPORTANTE: Estos selectores deben ajustarse según la estructura real del sitio
    # Intentamos varios patrones comunes

    # Patrón 1: Tabla de documentos
    filas = soup.find_all('tr', class_=re.compile(r'documento|norma|item'))
    if not filas:
        # Patrón 2: Divs o artículos con clase específica
        filas = soup.find_all(['div', 'article'], class_=re.compile(r'documento|norma|item|result'))
    if not filas:
        # Patrón 3: Lista de elementos
        filas = soup.find_all('li', class_=re.compile(r'documento|norma|item'))
    if not filas:
        # Patrón 4: Buscar todos los enlaces que parezcan PDFs o detalles de normas
        links_pdf = soup.find_all('a', href=re.compile(r'\.pdf|/norma/|/documento/', re.IGNORECASE))
        if links_pdf:
            logger.info(f"Encontrados {len(links_pdf)} enlaces a documentos/PDFs")
            for link in links_pdf:
                doc = _extraer_info_desde_enlace(link, url_pagina)
                if doc:
                    documentos.append(doc)
            return documentos

    # Procesar filas encontradas
    for i, fila in enumerate(filas):
        try:
            doc = _extraer_info_de_elemento(fila, url_pagina, i)
            if doc:
                documentos.append(doc)
        except Exception as e:
            logger.debug(f"Error extrayendo documento de fila {i}: {e}")
            continue

    return documentos


def _extraer_info_de_elemento(elemento, url_base, index):
    """
    Extrae información de un elemento HTML que representa un documento.

    Args:
        elemento: Elemento BeautifulSoup (tr, div, li, etc.)
        url_base (str): URL base para resolver URLs relativas
        index (int): Índice del elemento

    Returns:
        dict: Información del documento o None si no se pudo extraer
    """
    # Buscar enlace al PDF
    link_pdf = elemento.find('a', href=re.compile(r'\.pdf', re.IGNORECASE))
    url_pdf = urljoin(url_base, link_pdf['href']) if link_pdf else None

    # Buscar enlace a detalle
    link_detalle = elemento.find('a', href=re.compile(r'/norma/|/documento/|/detalle/', re.IGNORECASE))
    if not link_detalle and link_pdf and '.pdf' not in link_pdf.get('href', '').lower():
        link_detalle = link_pdf
    url_detalle = urljoin(url_base, link_detalle['href']) if link_detalle else None

    # Extraer título
    titulo = None
    if link_detalle:
        titulo = link_detalle.get_text(strip=True)
    elif link_pdf:
        titulo = link_pdf.get_text(strip=True)
    else:
        # Buscar en el texto del elemento
        titulo = elemento.get_text(strip=True)[:200]  # Limitar longitud

    # Extraer fecha (buscar patrones comunes)
    fecha_raw = _extraer_fecha_de_texto(elemento.get_text())

    # Extraer sección (buscar patrones)
    seccion_raw = _extraer_seccion_de_texto(elemento.get_text())

    # Generar ID único
    doc_id = _generar_id_documento(titulo, fecha_raw, index)

    # Retornar solo si tenemos al menos URL del PDF o detalle
    if url_pdf or url_detalle:
        return {
            'id': doc_id,
            'url_pdf': url_pdf,
            'url_detalle': url_detalle,
            'titulo_raw': titulo,
            'fecha_raw': fecha_raw,
            'seccion_raw': seccion_raw,
        }

    return None


def _extraer_info_desde_enlace(link, url_base):
    """
    Extrae información desde un enlace directo.

    Args:
        link: Elemento <a> de BeautifulSoup
        url_base (str): URL base

    Returns:
        dict: Información del documento
    """
    href = link.get('href', '')
    url_completa = urljoin(url_base, href)
    titulo = link.get_text(strip=True)

    # Determinar si es PDF o detalle
    es_pdf = href.lower().endswith('.pdf')

    # Buscar fecha en el contexto del enlace (elemento padre)
    parent = link.parent
    fecha_raw = _extraer_fecha_de_texto(parent.get_text() if parent else '')
    seccion_raw = _extraer_seccion_de_texto(parent.get_text() if parent else '')

    doc_id = _generar_id_documento(titulo, fecha_raw, hash(url_completa))

    return {
        'id': doc_id,
        'url_pdf': url_completa if es_pdf else None,
        'url_detalle': url_completa if not es_pdf else None,
        'titulo_raw': titulo,
        'fecha_raw': fecha_raw,
        'seccion_raw': seccion_raw,
    }


def _extraer_fecha_de_texto(texto):
    """
    Extrae fecha del texto usando expresiones regulares.

    Args:
        texto (str): Texto que puede contener una fecha

    Returns:
        str: Fecha encontrada o None
    """
    # Patrones comunes de fecha en español
    patrones = [
        r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}',  # 15 de enero de 2024
        r'\d{1,2}/\d{1,2}/\d{4}',             # 15/01/2024
        r'\d{4}-\d{1,2}-\d{1,2}',             # 2024-01-15
        r'\d{1,2}-\d{1,2}-\d{4}',             # 15-01-2024
    ]

    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            return match.group(0)

    return None


def _extraer_seccion_de_texto(texto):
    """
    Extrae sección/tipo del documento del texto.

    Args:
        texto (str): Texto que puede contener tipo de norma

    Returns:
        str: Sección/tipo encontrado o None
    """
    for tipo in config.TIPOS_NORMAS:
        if tipo.lower() in texto.lower():
            return tipo

    return None


def _generar_id_documento(titulo, fecha, fallback):
    """
    Genera un ID único para el documento.

    Args:
        titulo (str): Título del documento
        fecha (str): Fecha del documento
        fallback: Valor de respaldo para generar ID único

    Returns:
        str: ID único
    """
    # Limpiar título para usarlo en ID
    if titulo:
        titulo_limpio = re.sub(r'[^a-z0-9]+', '_', titulo.lower())[:50]
    else:
        titulo_limpio = f"doc_{fallback}"

    # Agregar fecha si está disponible
    if fecha:
        fecha_limpia = re.sub(r'[^0-9]+', '', fecha)[:8]
        return f"{titulo_limpio}_{fecha_limpia}"

    return titulo_limpio


def descargar_pdf(url_pdf, doc_id):
    """
    Descarga un PDF desde una URL y lo guarda localmente.

    Args:
        url_pdf (str): URL del PDF
        doc_id (str): ID del documento (usado para nombrar el archivo)

    Returns:
        str: Ruta del archivo descargado o None si falla
    """
    if not url_pdf:
        logger.warning(f"No hay URL de PDF para {doc_id}")
        return None

    # Asegurar que el directorio existe
    os.makedirs(config.PDFS_DIR, exist_ok=True)

    # Determinar nombre del archivo
    nombre_archivo = f"{doc_id}.pdf"
    ruta_destino = os.path.join(config.PDFS_DIR, nombre_archivo)

    # Si ya existe, no descargar de nuevo
    if os.path.exists(ruta_destino):
        logger.info(f"PDF ya existe: {nombre_archivo}")
        return ruta_destino

    logger.info(f"Descargando PDF: {url_pdf}")

    try:
        # Descargar con reintentos
        response = _hacer_request(url_pdf, stream=True)
        if not response:
            return None

        # Verificar que es un PDF
        content_type = response.headers.get('Content-Type', '')
        if 'pdf' not in content_type.lower() and not url_pdf.lower().endswith('.pdf'):
            logger.warning(f"La URL no parece ser un PDF: {content_type}")
            # Continuar de todas formas por si es un falso negativo

        # Guardar archivo
        with open(ruta_destino, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Verificar tamaño
        tamaño = os.path.getsize(ruta_destino)
        logger.info(f"PDF descargado: {nombre_archivo} ({tamaño} bytes)")

        if tamaño < 100:  # Muy pequeño, probablemente error
            logger.warning(f"Archivo muy pequeño ({tamaño} bytes), puede estar corrupto")
            os.remove(ruta_destino)
            return None

        return ruta_destino

    except Exception as e:
        logger.error(f"Error descargando PDF {url_pdf}: {e}")
        # Limpiar archivo parcial si existe
        if os.path.exists(ruta_destino):
            os.remove(ruta_destino)
        return None


def _hacer_request(url, stream=False):
    """
    Realiza una petición HTTP con reintentos.

    Args:
        url (str): URL a solicitar
        stream (bool): Si se debe hacer streaming (para archivos grandes)

    Returns:
        Response: Objeto Response de requests o None si falla
    """
    for intento in range(config.MAX_RETRIES):
        try:
            response = requests.get(
                url,
                headers=config.HEADERS,
                timeout=config.TIMEOUT,
                stream=stream,
                allow_redirects=True
            )
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            logger.warning(f"Intento {intento + 1}/{config.MAX_RETRIES} falló para {url}: {e}")
            if intento < config.MAX_RETRIES - 1:
                time.sleep(2 ** intento)  # Backoff exponencial
            else:
                logger.error(f"Todos los intentos fallaron para {url}")
                return None


def obtener_texto_completo_desde_url(url_detalle):
    """
    Obtiene el texto completo desde una URL de detalle.

    Args:
        url_detalle (str): URL de la página de detalle

    Returns:
        str: Texto completo o None si falla
    """
    if not url_detalle:
        return None

    logger.info(f"Obteniendo texto desde: {url_detalle}")

    try:
        response = _hacer_request(url_detalle)
        if not response:
            return None

        soup = BeautifulSoup(response.content, 'lxml')

        # Intentar diferentes selectores para el contenido
        contenido = None

        # Patrón 1: Div con clase específica
        contenido_elem = soup.find(['div', 'article'], class_=re.compile(r'contenido|content|texto|body', re.IGNORECASE))
        if contenido_elem:
            contenido = contenido_elem.get_text(separator='\n', strip=True)

        # Patrón 2: Main content
        if not contenido:
            contenido_elem = soup.find('main') or soup.find('article')
            if contenido_elem:
                contenido = contenido_elem.get_text(separator='\n', strip=True)

        # Patrón 3: Todo el body (menos nav, footer, header)
        if not contenido:
            # Remover elementos de navegación
            for elem in soup.find_all(['nav', 'footer', 'header', 'aside']):
                elem.decompose()
            contenido = soup.get_text(separator='\n', strip=True)

        return contenido

    except Exception as e:
        logger.error(f"Error obteniendo texto de {url_detalle}: {e}")
        return None


def guardar_texto(texto, doc_id):
    """
    Guarda texto en un archivo.

    Args:
        texto (str): Texto a guardar
        doc_id (str): ID del documento

    Returns:
        str: Ruta del archivo guardado
    """
    os.makedirs(config.TEXT_DIR, exist_ok=True)

    ruta = os.path.join(config.TEXT_DIR, f"{doc_id}.txt")

    with open(ruta, 'w', encoding=config.ENCODING) as f:
        f.write(texto)

    logger.info(f"Texto guardado: {ruta}")
    return ruta
