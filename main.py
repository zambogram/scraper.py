#!/usr/bin/env python3
"""
Punto de entrada principal para el scraper de la Gaceta Oficial de Bolivia

Soporta dos modos:
1. requests + BeautifulSoup (modo rápido, puede fallar si el sitio bloquea)
2. Selenium + Chrome (modo robusto, simula navegador real)
"""
import sys
import os
import argparse
import logging
from datetime import datetime

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from scripts.run_full import main as run_full_main, procesar_documento, exportar_a_json, exportar_a_csv

# Configurar logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(f'gaceta_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main_selenium(args):
    """
    Modo Selenium: usa navegador real

    Args:
        args: ArgumentParser namespace
    """
    logger.info("="*60)
    logger.info("MODO SELENIUM - Navegador Real")
    logger.info("="*60)

    try:
        from selenium_scraper import crear_scraper_selenium
    except ImportError:
        logger.error("Selenium no está instalado. Ejecuta: pip install -r requirements.txt")
        logger.error("También necesitas instalar ChromeDriver:")
        logger.error("  - Ubuntu/Debian: sudo apt-get install chromium-chromedriver")
        logger.error("  - MacOS: brew install chromedriver")
        logger.error("  - Windows: descarga desde https://chromedriver.chromium.org/")
        sys.exit(1)

    inicio = datetime.now()

    # Crear scraper
    scraper = crear_scraper_selenium(
        headless=args.headless,
        chromedriver_path=args.chromedriver_path
    )

    try:
        # 1. Listar documentos
        logger.info(f"\n1. Listando documentos (máximo {args.paginas} páginas)...")

        max_pag = None if args.paginas == 9999 else args.paginas

        documentos = scraper.listar_documentos_desde_gaceta(
            url_base=args.url,
            max_paginas=max_pag
        )

        if not documentos:
            logger.error("No se encontraron documentos.")
            logger.info("\nSe ha guardado un archivo HTML para debug en data/raw/")
            logger.info("Revísalo para identificar los selectores correctos.")
            return

        logger.info(f"Encontrados {len(documentos)} documentos")

        # Aplicar límite
        if args.limite and args.limite > 0:
            documentos = documentos[:args.limite]
            logger.info(f"Limitando a {len(documentos)} documentos")

        # 2. Procesar documentos
        logger.info(f"\n2. Procesando {len(documentos)} documentos...")
        registros = []

        for i, doc in enumerate(documentos, 1):
            logger.info(f"\n--- Documento {i}/{len(documentos)} ---")

            # Descargar PDF con Selenium si es necesario
            if doc.get('url_pdf') and args.download_pdfs:
                ruta_pdf = scraper.descargar_pdf(doc['url_pdf'], doc['id'])
                if ruta_pdf:
                    doc['ruta_pdf_local'] = ruta_pdf

            # Procesar documento
            registro = procesar_documento(doc)
            if registro:
                registros.append(registro)

        logger.info(f"\nProcesados: {len(registros)}/{len(documentos)} documentos")

        if not registros:
            logger.error("No se pudo procesar ningún documento")
            return

        # 3. Exportar
        logger.info("\n3. Exportando resultados...")
        ruta_json = exportar_a_json(registros)
        ruta_csv = exportar_a_csv(registros)

        # 4. Resumen
        fin = datetime.now()
        duracion = fin - inicio

        logger.info("\n" + "="*60)
        logger.info("RESUMEN DE EJECUCIÓN")
        logger.info("="*60)
        logger.info(f"Modo: SELENIUM")
        logger.info(f"Documentos encontrados: {len(documentos)}")
        logger.info(f"Documentos procesados: {len(registros)}")
        logger.info(f"Tasa de éxito: {len(registros)/len(documentos)*100:.1f}%")
        logger.info(f"Duración: {duracion}")
        logger.info(f"\nArchivos generados:")
        logger.info(f"  - JSON: {ruta_json}")
        logger.info(f"  - CSV:  {ruta_csv}")
        logger.info("="*60)

        # Muestra
        logger.info("\nMUESTRA DE RESULTADOS:")
        for i, reg in enumerate(registros[:3], 1):
            logger.info(f"\n{i}. {reg.get('titulo', 'Sin título')[:80]}")
            logger.info(f"   Tipo: {reg.get('tipo_norma', 'N/A')}")
            logger.info(f"   Número: {reg.get('numero_norma', 'N/A')}")
            logger.info(f"   Fecha: {reg.get('fecha', 'N/A')}")
            logger.info(f"   Artículos: {reg.get('num_articulos', 0)}")

    finally:
        # Cerrar navegador
        scraper.cerrar()

    logger.info("\n¡Scraping completado!")


def main_requests(args):
    """
    Modo requests: usa HTTP directo (rápido pero puede fallar)

    Args:
        args: ArgumentParser namespace
    """
    logger.info("="*60)
    logger.info("MODO REQUESTS - HTTP Directo")
    logger.info("="*60)
    logger.warning("ADVERTENCIA: Este modo puede fallar si el sitio bloquea requests.")
    logger.warning("Si falla, usa --modo selenium")
    logger.info("="*60)

    # Usar run_full.py original
    run_full_main(
        paginas=args.paginas,
        limite_documentos=args.limite if args.limite > 0 else None,
        url_base=args.url
    )


def main():
    """Punto de entrada principal con argumentos CLI"""
    parser = argparse.ArgumentParser(
        description='Scraper de la Gaceta Oficial de Bolivia',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Modo Selenium (recomendado) - scrapear 5 páginas
  python main.py --modo selenium --paginas 5

  # Modo Selenium - scrapear TODO (cuidado, puede tardar horas)
  python main.py --modo selenium --paginas 9999

  # Modo Selenium - limitar a 10 documentos para prueba
  python main.py --modo selenium --limite 10

  # Modo Selenium - sin interfaz gráfica (headless)
  python main.py --modo selenium --headless

  # Modo requests (rápido pero puede fallar)
  python main.py --modo requests --paginas 5

  # URL personalizada
  python main.py --modo selenium --url "http://www.gacetaoficialdebolivia.gob.bo/normas/listadonor/10"

  # ChromeDriver personalizado
  python main.py --modo selenium --chromedriver /usr/local/bin/chromedriver
        """
    )

    # Modo de operación
    parser.add_argument(
        '--modo',
        choices=['selenium', 'requests'],
        default='selenium',
        help='Modo de scraping (default: selenium)'
    )

    # Opciones de scraping
    parser.add_argument(
        '--paginas',
        type=int,
        default=1,
        help='Número de páginas a scrapear (9999 = todas, default: 1)'
    )

    parser.add_argument(
        '--limite',
        type=int,
        default=0,
        help='Límite de documentos a procesar (0 = todos, default: 0)'
    )

    parser.add_argument(
        '--url',
        type=str,
        default=None,
        help='URL base personalizada (default: usar config.LISTADO_URL)'
    )

    # Opciones de Selenium
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='Ejecutar Chrome sin interfaz gráfica (default: True)'
    )

    parser.add_argument(
        '--no-headless',
        action='store_false',
        dest='headless',
        help='Mostrar interfaz gráfica de Chrome'
    )

    parser.add_argument(
        '--chromedriver-path',
        type=str,
        default=None,
        help='Ruta al ejecutable de ChromeDriver (default: auto-detectar)'
    )

    parser.add_argument(
        '--download-pdfs',
        action='store_true',
        default=True,
        help='Descargar PDFs (default: True)'
    )

    parser.add_argument(
        '--no-download-pdfs',
        action='store_false',
        dest='download_pdfs',
        help='No descargar PDFs (solo metadatos)'
    )

    # Shortcuts para comandos comunes
    parser.add_argument(
        '--test',
        action='store_true',
        help='Modo prueba: scrapea 10 documentos con Selenium (equivale a --modo selenium --limite 10)'
    )

    parser.add_argument(
        '--full',
        action='store_true',
        help='Modo completo: scrapea TODO con Selenium (equivale a --modo selenium --paginas 9999)'
    )

    args = parser.parse_args()

    # Aplicar shortcuts
    if args.test:
        args.modo = 'selenium'
        args.limite = 10
        logger.info("MODO PRUEBA: 10 documentos con Selenium")

    if args.full:
        args.modo = 'selenium'
        args.paginas = 9999
        args.limite = 0
        logger.info("MODO COMPLETO: Scrapear TODO")

    # Ejecutar modo correspondiente
    try:
        if args.modo == 'selenium':
            main_selenium(args)
        else:
            main_requests(args)

    except KeyboardInterrupt:
        logger.info("\n\nProceso interrumpido por el usuario")
        sys.exit(1)

    except Exception as e:
        logger.error(f"\n\nError fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
