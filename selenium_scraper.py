"""
Scraper con Selenium para la Gaceta Oficial de Bolivia
Simula un navegador real para evitar bloqueos
"""
import time
import random
import os
import logging
from datetime import datetime
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

import config

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class GacetaSeleniumScraper:
    """Scraper de la Gaceta Oficial usando Selenium"""

    def __init__(self, headless=True, chromedriver_path=None):
        """
        Inicializa el scraper con Selenium.

        Args:
            headless (bool): Si True, ejecuta Chrome sin interfaz gráfica
            chromedriver_path (str): Ruta al ejecutable de ChromeDriver (opcional)
        """
        self.headless = headless
        self.chromedriver_path = chromedriver_path
        self.driver = None
        self.wait_time = 10  # segundos de espera para elementos

    def _init_driver(self):
        """Inicializa el driver de Chrome con opciones optimizadas"""
        logger.info("Inicializando Chrome WebDriver...")

        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless')
            logger.info("Modo headless activado")

        # Opciones para evitar detección
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # User agent realista
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Opciones de descarga
        prefs = {
            'download.default_directory': config.PDFS_DIR,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'plugins.always_open_pdf_externally': True
        }
        chrome_options.add_experimental_option('prefs', prefs)

        try:
            if self.chromedriver_path:
                service = Service(executable_path=self.chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)

            # Eliminar propiedad webdriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            self.driver.set_page_load_timeout(30)
            logger.info("Chrome WebDriver inicializado correctamente")

        except WebDriverException as e:
            logger.error(f"Error inicializando ChromeDriver: {e}")
            logger.error("Asegúrate de tener ChromeDriver instalado y en el PATH")
            logger.error("Descarga desde: https://chromedriver.chromium.org/")
            raise

    def _random_delay(self, min_sec=1, max_sec=3):
        """Delay aleatorio para simular comportamiento humano"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def _scroll_to_bottom(self):
        """Scroll gradual al fondo de la página"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll hacia abajo
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._random_delay(0.5, 1.5)

            # Calcular nueva altura
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break

            last_height = new_height

    def listar_documentos_desde_gaceta(self, url_base=None, max_paginas=None):
        """
        Lista todos los documentos de la Gaceta Oficial.

        Args:
            url_base (str): URL base del listado (default: usar config)
            max_paginas (int): Máximo de páginas a scrapear (None = todas)

        Returns:
            list: Lista de documentos con metadatos
        """
        if not self.driver:
            self._init_driver()

        url = url_base or config.LISTADO_URL
        documentos = []
        pagina_actual = 1

        logger.info(f"Iniciando scraping desde: {url}")

        try:
            while True:
                if max_paginas and pagina_actual > max_paginas:
                    logger.info(f"Alcanzado límite de {max_paginas} páginas")
                    break

                logger.info(f"Procesando página {pagina_actual}...")

                # Navegar a la página
                page_url = self._construir_url_pagina(url, pagina_actual)
                self.driver.get(page_url)
                self._random_delay(2, 4)

                # Scroll para cargar contenido dinámico
                self._scroll_to_bottom()

                # Extraer documentos de la página
                docs_pagina = self._extraer_documentos_de_pagina_actual()

                if not docs_pagina:
                    logger.info("No se encontraron más documentos. Finalizando.")
                    break

                documentos.extend(docs_pagina)
                logger.info(f"Extraídos {len(docs_pagina)} documentos de página {pagina_actual}")

                # Verificar si hay siguiente página
                if not self._hay_siguiente_pagina():
                    logger.info("No hay más páginas. Finalizando.")
                    break

                pagina_actual += 1
                self._random_delay(2, 5)

        except Exception as e:
            logger.error(f"Error durante scraping: {e}", exc_info=True)

        logger.info(f"Total documentos extraídos: {len(documentos)}")
        return documentos

    def _construir_url_pagina(self, url_base, numero_pagina):
        """Construye URL de página según patrón del sitio"""
        # Patrón común: /normas/listadonor/NUMERO
        if 'listadonor' in url_base:
            # Reemplazar el número al final
            base = url_base.rsplit('/', 1)[0]
            return f"{base}/{numero_pagina * 10}"  # Probablemente usa múltiplos de 10
        else:
            # Intentar patrón ?page=N
            separator = '&' if '?' in url_base else '?'
            return f"{url_base}{separator}page={numero_pagina}"

    def _extraer_documentos_de_pagina_actual(self):
        """
        Extrae documentos de la página actual cargada en Selenium.

        IMPORTANTE: Esta función necesita ajustarse según la estructura HTML real.
        Incluye múltiples estrategias de extracción.
        """
        documentos = []

        try:
            # ESTRATEGIA 1: Buscar tabla de documentos
            try:
                tabla = self.driver.find_element(By.TAG_NAME, 'table')
                filas = tabla.find_elements(By.TAG_NAME, 'tr')[1:]  # Saltar encabezado

                for i, fila in enumerate(filas):
                    try:
                        doc = self._extraer_de_fila_tabla(fila, i)
                        if doc:
                            documentos.append(doc)
                    except Exception as e:
                        logger.debug(f"Error extrayendo fila {i}: {e}")

                if documentos:
                    logger.info(f"Estrategia 1 (tabla): {len(documentos)} documentos")
                    return documentos

            except NoSuchElementException:
                pass

            # ESTRATEGIA 2: Buscar divs con clase específica
            selectores_div = [
                '.documento',
                '.norma',
                '.item-norma',
                '.gaceta-item',
                '[class*="documento"]',
                '[class*="norma"]'
            ]

            for selector in selectores_div:
                try:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elementos:
                        for i, elem in enumerate(elementos):
                            doc = self._extraer_de_div(elem, i)
                            if doc:
                                documentos.append(doc)

                        if documentos:
                            logger.info(f"Estrategia 2 (div {selector}): {len(documentos)} docs")
                            return documentos

                except NoSuchElementException:
                    continue

            # ESTRATEGIA 3: Buscar todos los enlaces a PDF
            try:
                enlaces_pdf = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf') or contains(@href, 'descargar')]")

                for i, enlace in enumerate(enlaces_pdf):
                    doc = self._extraer_de_enlace_pdf(enlace, i)
                    if doc:
                        documentos.append(doc)

                if documentos:
                    logger.info(f"Estrategia 3 (enlaces PDF): {len(documentos)} documentos")
                    return documentos

            except NoSuchElementException:
                pass

            # ESTRATEGIA 4: Inspección genérica
            logger.warning("Ninguna estrategia funcionó. Guardando HTML para inspección...")
            self._guardar_html_debug()

        except Exception as e:
            logger.error(f"Error general en extracción: {e}", exc_info=True)

        return documentos

    def _extraer_de_fila_tabla(self, fila, index):
        """Extrae documento de una fila de tabla"""
        try:
            celdas = fila.find_elements(By.TAG_NAME, 'td')
            if len(celdas) < 2:
                return None

            # Buscar enlace en la fila
            enlaces = fila.find_elements(By.TAG_NAME, 'a')
            url_pdf = None
            url_detalle = None
            titulo = fila.text.strip()

            for enlace in enlaces:
                href = enlace.get_attribute('href')
                if href:
                    if '.pdf' in href.lower() or 'descargar' in href.lower():
                        url_pdf = href
                    elif 'view' in href or 'ver' in href or 'detalle' in href:
                        url_detalle = href

                    # Usar texto del enlace como título si es más descriptivo
                    texto_enlace = enlace.text.strip()
                    if len(texto_enlace) > len(titulo):
                        titulo = texto_enlace

            # Extraer fecha del texto de la fila
            from scraper import _extraer_fecha_de_texto, _extraer_seccion_de_texto, _generar_id_documento

            texto_fila = fila.text
            fecha_raw = _extraer_fecha_de_texto(texto_fila)
            seccion_raw = _extraer_seccion_de_texto(texto_fila)

            doc_id = _generar_id_documento(titulo, fecha_raw, index)

            return {
                'id': doc_id,
                'url_pdf': url_pdf,
                'url_detalle': url_detalle,
                'titulo_raw': titulo,
                'fecha_raw': fecha_raw,
                'seccion_raw': seccion_raw,
            }

        except Exception as e:
            logger.debug(f"Error en fila {index}: {e}")
            return None

    def _extraer_de_div(self, elemento, index):
        """Extrae documento de un div"""
        try:
            from scraper import _extraer_fecha_de_texto, _extraer_seccion_de_texto, _generar_id_documento

            texto = elemento.text.strip()

            # Buscar enlaces dentro del div
            enlaces = elemento.find_elements(By.TAG_NAME, 'a')
            url_pdf = None
            url_detalle = None
            titulo = texto[:200]

            for enlace in enlaces:
                href = enlace.get_attribute('href')
                texto_enlace = enlace.text.strip()

                if href:
                    if '.pdf' in href.lower():
                        url_pdf = href
                    else:
                        url_detalle = href

                    if texto_enlace and len(texto_enlace) > 10:
                        titulo = texto_enlace

            fecha_raw = _extraer_fecha_de_texto(texto)
            seccion_raw = _extraer_seccion_de_texto(texto)
            doc_id = _generar_id_documento(titulo, fecha_raw, index)

            if url_pdf or url_detalle:
                return {
                    'id': doc_id,
                    'url_pdf': url_pdf,
                    'url_detalle': url_detalle,
                    'titulo_raw': titulo,
                    'fecha_raw': fecha_raw,
                    'seccion_raw': seccion_raw,
                }

        except Exception as e:
            logger.debug(f"Error en div {index}: {e}")

        return None

    def _extraer_de_enlace_pdf(self, enlace, index):
        """Extrae documento de un enlace a PDF"""
        try:
            from scraper import _extraer_fecha_de_texto, _extraer_seccion_de_texto, _generar_id_documento

            url_pdf = enlace.get_attribute('href')
            titulo = enlace.text.strip()

            # Buscar contexto (elemento padre)
            try:
                padre = enlace.find_element(By.XPATH, '..')
                texto_contexto = padre.text
            except:
                texto_contexto = titulo

            fecha_raw = _extraer_fecha_de_texto(texto_contexto)
            seccion_raw = _extraer_seccion_de_texto(texto_contexto)
            doc_id = _generar_id_documento(titulo, fecha_raw, index)

            return {
                'id': doc_id,
                'url_pdf': url_pdf,
                'url_detalle': None,
                'titulo_raw': titulo,
                'fecha_raw': fecha_raw,
                'seccion_raw': seccion_raw,
            }

        except Exception as e:
            logger.debug(f"Error en enlace {index}: {e}")

        return None

    def _hay_siguiente_pagina(self):
        """Verifica si existe botón de siguiente página"""
        selectores_siguiente = [
            "//a[contains(text(), 'Siguiente')]",
            "//a[contains(text(), 'Next')]",
            "//a[contains(@class, 'next')]",
            "//button[contains(text(), 'Siguiente')]",
            "//a[@rel='next']",
            "//a[contains(@href, 'page=')]",
        ]

        for selector in selectores_siguiente:
            try:
                elemento = self.driver.find_element(By.XPATH, selector)
                if elemento.is_displayed() and elemento.is_enabled():
                    return True
            except NoSuchElementException:
                continue

        return False

    def _guardar_html_debug(self):
        """Guarda HTML de la página actual para debugging"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ruta = os.path.join(config.RAW_DIR, f'debug_html_{timestamp}.html')

            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)

            logger.info(f"HTML guardado para debug: {ruta}")
            logger.info("Revisa este archivo para identificar los selectores correctos")

        except Exception as e:
            logger.error(f"Error guardando HTML debug: {e}")

    def descargar_pdf(self, url_pdf, doc_id):
        """
        Descarga PDF usando Selenium (para manejar autenticación/sesiones).

        Args:
            url_pdf (str): URL del PDF
            doc_id (str): ID del documento

        Returns:
            str: Ruta del archivo descargado
        """
        if not url_pdf:
            return None

        os.makedirs(config.PDFS_DIR, exist_ok=True)
        ruta_destino = os.path.join(config.PDFS_DIR, f"{doc_id}.pdf")

        if os.path.exists(ruta_destino):
            logger.info(f"PDF ya existe: {doc_id}.pdf")
            return ruta_destino

        try:
            logger.info(f"Descargando PDF: {url_pdf}")

            # Navegar al PDF (esto iniciará la descarga automática)
            self.driver.get(url_pdf)

            # Esperar a que se descargue (máximo 30 segundos)
            tiempo_espera = 0
            archivo_temp = None

            while tiempo_espera < 30:
                # Buscar archivo .crdownload (descarga en progreso de Chrome)
                archivos = os.listdir(config.PDFS_DIR)
                descargando = [f for f in archivos if f.endswith('.crdownload')]

                if not descargando:
                    # Buscar PDF recién descargado
                    pdfs = [f for f in archivos if f.endswith('.pdf')]
                    if pdfs:
                        # Renombrar al nombre correcto
                        archivo_temp = os.path.join(config.PDFS_DIR, pdfs[-1])
                        break

                time.sleep(1)
                tiempo_espera += 1

            if archivo_temp and os.path.exists(archivo_temp):
                # Renombrar al nombre correcto
                os.rename(archivo_temp, ruta_destino)
                tamaño = os.path.getsize(ruta_destino)
                logger.info(f"PDF descargado: {doc_id}.pdf ({tamaño} bytes)")
                return ruta_destino
            else:
                logger.warning(f"Timeout descargando PDF: {url_pdf}")
                return None

        except Exception as e:
            logger.error(f"Error descargando PDF {url_pdf}: {e}")
            return None

    def cerrar(self):
        """Cierra el navegador"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Navegador cerrado")
            except Exception as e:
                logger.error(f"Error cerrando navegador: {e}")


def crear_scraper_selenium(headless=True, chromedriver_path=None):
    """
    Factory function para crear scraper con Selenium.

    Args:
        headless (bool): Ejecutar sin interfaz gráfica
        chromedriver_path (str): Ruta a ChromeDriver (opcional)

    Returns:
        GacetaSeleniumScraper: Instancia del scraper
    """
    return GacetaSeleniumScraper(headless=headless, chromedriver_path=chromedriver_path)
