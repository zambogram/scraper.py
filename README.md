# Scraper de la Gaceta Oficial de Bolivia

Scraper completo para la Gaceta Oficial de Bolivia que extrae documentos legales, los parsea y estructura con metadatos completos.

## Características

- Scraping automático del sitio de la Gaceta Oficial
- Descarga de PDFs
- Extracción de texto de PDFs
- Parsing de secciones jurídicas:
  - VISTOS
  - CONSIDERANDO
  - POR TANTO
  - ARTÍCULOS (con números)
  - DISPOSICIONES (FINALES, TRANSITORIAS, ADICIONALES, ABROGATORIAS)
- Extracción de metadatos:
  - Tipo de norma
  - Número de norma
  - Fecha
  - Entidad emisora
  - Temas
- Exportación a JSON y CSV

## Estructura del Proyecto

```
bo-scraper-gaceta/
├── README.md
├── requirements.txt
├── scraper.py          # Scraping y descarga
├── parser.py           # Parsing de documentos legales
├── metadata.py         # Extracción de metadatos
├── config.py           # Configuración
│
├── data/
│   ├── raw/           # Datos crudos
│   ├── pdfs/          # PDFs descargados
│   └── text/          # Textos extraídos
│
├── exports/
│   ├── json/          # Exportaciones JSON
│   └── csv/           # Exportaciones CSV
│
└── scripts/
    └── run_full.py    # Script principal
```

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repo>
cd bo-scraper-gaceta
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Uso Básico

Scrapear 1 página (por defecto):
```bash
python scripts/run_full.py
```

### Opciones Avanzadas

Scrapear múltiples páginas:
```bash
python scripts/run_full.py --paginas 5
```

Limitar número de documentos a procesar:
```bash
python scripts/run_full.py --limite 10
```

Usar URL personalizada:
```bash
python scripts/run_full.py --url "https://www.gacetaoficialdebolivia.gob.bo/normas/buscar"
```

Combinar opciones:
```bash
python scripts/run_full.py --paginas 3 --limite 20
```

## Configuración

Editar `config.py` para ajustar:

- URLs del sitio web
- Directorios de datos
- Headers HTTP
- Timeouts y reintentos
- Tipos de normas reconocidas
- Secciones jurídicas esperadas

## Ajuste de Selectores

**IMPORTANTE**: Antes de usar el scraper por primera vez, debes ajustar los selectores CSS/XPath en `scraper.py` para que coincidan con la estructura real del sitio web de la Gaceta Oficial.

Revisa la función `_extraer_documentos_de_pagina()` en `scraper.py` (línea 75) y ajusta los patrones de búsqueda según la estructura HTML real.

## Formato de Salida

### JSON
```json
{
  "id": "ley_1234_2024",
  "titulo": "Ley de...",
  "tipo_norma": "LEY",
  "numero_norma": "1234",
  "fecha": "2024-01-15",
  "seccion": "LEY",
  "entidad_emisora": "ASAMBLEA LEGISLATIVA",
  "url_pdf": "...",
  "url_detalle": "...",
  "resumen": "...",
  "temas": "EDUCACIÓN,SALUD",
  "num_articulos": 25,
  "num_considerandos": 5,
  "tiene_vistos": true,
  "tiene_disposiciones_finales": true,
  "texto_completo": "...",
  "articulos_json": "[...]"
}
```

### CSV
Columnas principales:
- id
- titulo
- tipo_norma
- numero_norma
- fecha
- seccion
- entidad_emisora
- url_pdf
- url_detalle
- resumen
- temas
- num_articulos
- num_considerandos
- tiene_vistos
- tiene_disposiciones_finales

## Logs

Los logs se guardan automáticamente en archivos con timestamp:
```
scraper_20240115_143022.log
```

## Solución de Problemas

### No se encuentran documentos

Si el scraper no encuentra documentos, probablemente necesites ajustar los selectores:

1. Abre el sitio web de la Gaceta Oficial en tu navegador
2. Inspecciona la estructura HTML del listado de documentos
3. Ajusta los selectores en `scraper.py` función `_extraer_documentos_de_pagina()`

### Error al extraer texto de PDF

Algunos PDFs pueden estar escaneados (imágenes). Para esto necesitarías OCR:
- Considera usar `pytesseract` para OCR (no incluido por defecto)
- O descarga solo los metadatos sin procesar el PDF

### Error de conexión

- Verifica que el sitio esté disponible
- Ajusta `TIMEOUT` y `MAX_RETRIES` en `config.py`
- Agrega delay entre requests con `DELAY_BETWEEN_REQUESTS`

## Funciones Principales

### scraper.py
- `listar_documentos_desde_gaceta(paginas)`: Lista documentos del sitio
- `descargar_pdf(url_pdf, doc_id)`: Descarga un PDF
- `obtener_texto_completo_desde_url(url)`: Extrae texto de URL

### parser.py
- `extraer_texto_de_pdf(ruta_pdf)`: Extrae texto de PDF
- `parsear_documento(texto)`: Parsea secciones jurídicas
- `extraer_articulos(texto)`: Extrae artículos numerados
- `extraer_disposiciones(texto, tipo)`: Extrae disposiciones

### metadata.py
- `extraer_metadatos(documento, secciones)`: Extrae metadatos completos
- `extraer_tipo_norma(titulo, texto)`: Identifica tipo de norma
- `extraer_numero_norma(titulo, texto)`: Extrae número de norma
- `extraer_y_normalizar_fecha(fecha_raw, texto)`: Normaliza fecha a ISO

## Desarrollo

Para agregar nuevos tipos de normas, edita:
- `config.py`: Agrega a `TIPOS_NORMAS`
- `metadata.py`: Ajusta patrones en `extraer_tipo_norma()`

Para agregar nuevas secciones jurídicas:
- `config.py`: Agrega a `SECCIONES_JURIDICAS`
- `parser.py`: Crea nueva función `extraer_seccion_X()`

## Dependencias

- `requests`: HTTP requests
- `beautifulsoup4`: Parsing HTML
- `lxml`: Parser XML/HTML rápido
- `PyPDF2`: Extracción de texto de PDFs
- `python-dateutil`: Parsing de fechas

## Notas Importantes

- Este scraper está diseñado SOLO para la Gaceta Oficial de Bolivia
- Respeta los términos de servicio del sitio web
- Usa delays apropiados entre requests
- No sobrecargues el servidor con muchas requests simultáneas
- Los selectores pueden cambiar si el sitio web se actualiza

## Licencia

[Especificar licencia]

## Contribuciones

[Instrucciones para contribuir]
