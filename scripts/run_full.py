"""
Script principal para ejecutar el scraper completo de la Gaceta Oficial de Bolivia
"""
import sys
import os
import json
import csv
import logging
from datetime import datetime

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import scraper
import parser
import metadata

# Configurar logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def procesar_documento(documento):
    """
    Procesa un documento completo: descarga, parseo, extracción de metadatos.

    Args:
        documento (dict): Información básica del documento

    Returns:
        dict: Registro completo del documento procesado o None si falla
    """
    doc_id = documento['id']
    logger.info(f"Procesando documento: {doc_id}")

    try:
        # 1. Descargar PDF si existe
        ruta_pdf = None
        if documento.get('url_pdf'):
            ruta_pdf = scraper.descargar_pdf(documento['url_pdf'], doc_id)

        # 2. Obtener texto del documento
        texto = None

        # Intentar extraer de PDF
        if ruta_pdf:
            texto = parser.extraer_texto_de_pdf(ruta_pdf)

        # Si no hay PDF o falla la extracción, intentar desde URL de detalle
        if not texto and documento.get('url_detalle'):
            texto = scraper.obtener_texto_completo_desde_url(documento['url_detalle'])

        # 3. Si no se pudo obtener texto, solo procesar metadatos básicos
        if not texto:
            logger.warning(f"No se pudo obtener texto para {doc_id}")
            metadatos = metadata.extraer_metadatos(documento, None)
            return metadata.construir_registro_completo(documento, {}, metadatos)

        # 4. Guardar texto
        scraper.guardar_texto(texto, doc_id)

        # 5. Parsear documento
        texto_limpio = parser.limpiar_texto(texto)
        secciones = parser.parsear_documento(texto_limpio)

        # 6. Extraer metadatos
        metadatos = metadata.extraer_metadatos(documento, secciones)

        # 7. Validar metadatos
        es_valido, errores = metadata.validar_metadatos(metadatos)
        if not es_valido:
            logger.error(f"Metadatos inválidos para {doc_id}: {errores}")

        # 8. Construir registro completo
        registro = metadata.construir_registro_completo(documento, secciones, metadatos)

        logger.info(f"Documento procesado exitosamente: {doc_id}")
        return registro

    except Exception as e:
        logger.error(f"Error procesando documento {doc_id}: {e}", exc_info=True)
        return None


def exportar_a_json(registros, nombre_archivo='documentos_gaceta'):
    """
    Exporta registros a formato JSON.

    Args:
        registros (list): Lista de registros a exportar
        nombre_archivo (str): Nombre base del archivo (sin extensión)

    Returns:
        str: Ruta del archivo generado
    """
    os.makedirs(config.JSON_DIR, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ruta = os.path.join(config.JSON_DIR, f"{nombre_archivo}_{timestamp}.json")

    # Crear copia sin texto_completo para JSON más ligero
    registros_export = []
    for reg in registros:
        reg_copy = reg.copy()
        # Opcionalmente, remover texto completo para reducir tamaño
        # reg_copy.pop('texto_completo', None)
        registros_export.append(reg_copy)

    with open(ruta, 'w', encoding=config.ENCODING) as f:
        json.dump(registros_export, f, ensure_ascii=False, indent=2)

    logger.info(f"Exportado a JSON: {ruta} ({len(registros)} registros)")
    return ruta


def exportar_a_csv(registros, nombre_archivo='documentos_gaceta'):
    """
    Exporta registros a formato CSV.

    Args:
        registros (list): Lista de registros a exportar
        nombre_archivo (str): Nombre base del archivo (sin extensión)

    Returns:
        str: Ruta del archivo generado
    """
    if not registros:
        logger.warning("No hay registros para exportar a CSV")
        return None

    os.makedirs(config.CSV_DIR, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ruta = os.path.join(config.CSV_DIR, f"{nombre_archivo}_{timestamp}.csv")

    # Definir columnas (excluir texto_completo y articulos_json por tamaño)
    columnas = [
        'id', 'titulo', 'tipo_norma', 'numero_norma', 'fecha', 'seccion',
        'entidad_emisora', 'url_pdf', 'url_detalle', 'resumen', 'temas',
        'num_articulos', 'num_considerandos', 'tiene_vistos',
        'tiene_disposiciones_finales'
    ]

    with open(ruta, 'w', encoding=config.ENCODING, newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=columnas,
            delimiter=config.CSV_DELIMITER,
            quotechar=config.CSV_QUOTECHAR,
            quoting=csv.QUOTE_MINIMAL
        )

        writer.writeheader()

        for registro in registros:
            # Filtrar solo las columnas que queremos
            fila = {col: _sanitizar_valor_csv(registro.get(col, '')) for col in columnas}
            writer.writerow(fila)

    logger.info(f"Exportado a CSV: {ruta} ({len(registros)} registros)")
    return ruta


def _sanitizar_valor_csv(valor):
    """
    Sanitiza un valor para exportación CSV.

    Args:
        valor: Valor a sanitizar

    Returns:
        str: Valor sanitizado
    """
    if valor is None:
        return ''

    if isinstance(valor, bool):
        return 'Sí' if valor else 'No'

    if isinstance(valor, (list, dict)):
        return str(valor)

    # Convertir a string y limpiar
    valor_str = str(valor)

    # Reemplazar saltos de línea por espacios
    valor_str = valor_str.replace('\n', ' ').replace('\r', ' ')

    # Normalizar espacios
    valor_str = ' '.join(valor_str.split())

    # Limitar longitud para CSV
    if len(valor_str) > 1000:
        valor_str = valor_str[:997] + '...'

    return valor_str


def main(paginas=1, limite_documentos=None, url_base=None):
    """
    Función principal del scraper.

    Args:
        paginas (int): Número de páginas a scrapear
        limite_documentos (int): Límite de documentos a procesar (None = todos)
        url_base (str): URL base personalizada (opcional)
    """
    logger.info("="*60)
    logger.info("INICIANDO SCRAPER DE LA GACETA OFICIAL DE BOLIVIA")
    logger.info("="*60)

    inicio = datetime.now()

    # 1. Listar documentos
    logger.info(f"\n1. Listando documentos ({paginas} página(s))...")
    documentos = scraper.listar_documentos_desde_gaceta(paginas=paginas, url_base=url_base)

    if not documentos:
        logger.error("No se encontraron documentos. Verifica la URL y los selectores.")
        logger.info("\nNOTA: Probablemente necesites ajustar los selectores en scraper.py")
        logger.info("      para que coincidan con la estructura real del sitio web.")
        return

    logger.info(f"Encontrados {len(documentos)} documentos")

    # Aplicar límite si se especificó
    if limite_documentos:
        documentos = documentos[:limite_documentos]
        logger.info(f"Limitando a {len(documentos)} documentos")

    # 2. Procesar documentos
    logger.info(f"\n2. Procesando {len(documentos)} documentos...")
    registros = []

    for i, doc in enumerate(documentos, 1):
        logger.info(f"\n--- Documento {i}/{len(documentos)} ---")
        registro = procesar_documento(doc)
        if registro:
            registros.append(registro)
        else:
            logger.warning(f"No se pudo procesar el documento {i}")

    logger.info(f"\nProcesados exitosamente: {len(registros)}/{len(documentos)} documentos")

    if not registros:
        logger.error("No se pudo procesar ningún documento")
        return

    # 3. Exportar resultados
    logger.info("\n3. Exportando resultados...")

    ruta_json = exportar_a_json(registros)
    ruta_csv = exportar_a_csv(registros)

    # 4. Resumen final
    fin = datetime.now()
    duracion = fin - inicio

    logger.info("\n" + "="*60)
    logger.info("RESUMEN DE EJECUCIÓN")
    logger.info("="*60)
    logger.info(f"Documentos encontrados: {len(documentos)}")
    logger.info(f"Documentos procesados: {len(registros)}")
    logger.info(f"Tasa de éxito: {len(registros)/len(documentos)*100:.1f}%")
    logger.info(f"Duración: {duracion}")
    logger.info(f"\nArchivos generados:")
    logger.info(f"  - JSON: {ruta_json}")
    logger.info(f"  - CSV:  {ruta_csv}")
    logger.info("="*60)

    # 5. Mostrar muestra de resultados
    logger.info("\nMUESTRA DE RESULTADOS:")
    for i, reg in enumerate(registros[:3], 1):
        logger.info(f"\n{i}. {reg.get('titulo', 'Sin título')[:80]}")
        logger.info(f"   Tipo: {reg.get('tipo_norma', 'N/A')}")
        logger.info(f"   Número: {reg.get('numero_norma', 'N/A')}")
        logger.info(f"   Fecha: {reg.get('fecha', 'N/A')}")
        logger.info(f"   Artículos: {reg.get('num_articulos', 0)}")

    logger.info("\n¡Scraping completado!")


if __name__ == '__main__':
    import argparse

    parser_args = argparse.ArgumentParser(
        description='Scraper de la Gaceta Oficial de Bolivia'
    )

    parser_args.add_argument(
        '--paginas',
        type=int,
        default=1,
        help='Número de páginas a scrapear (default: 1)'
    )

    parser_args.add_argument(
        '--limite',
        type=int,
        default=None,
        help='Límite de documentos a procesar (default: todos)'
    )

    parser_args.add_argument(
        '--url',
        type=str,
        default=None,
        help='URL base personalizada (default: usar config.LISTADO_URL)'
    )

    args = parser_args.parse_args()

    # Ejecutar scraper
    try:
        main(
            paginas=args.paginas,
            limite_documentos=args.limite,
            url_base=args.url
        )
    except KeyboardInterrupt:
        logger.info("\nProceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)
