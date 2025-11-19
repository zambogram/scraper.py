# Scraper de la Gaceta Oficial de Bolivia

Scraper completo para la Gaceta Oficial de Bolivia que extrae documentos legales, los parsea y estructura con metadatos completos.

**IMPORTANTE:** El sitio oficial bloquea requests HTTP simples. Este scraper usa **Selenium** para simular un navegador real.

## Características

- **Dos modos de scraping:**
  - **Selenium (recomendado):** Simula navegador real, evita bloqueos
  - **Requests:** HTTP directo, rápido pero puede fallar

- **Scraping robusto:**
  - Navegación automática de páginas
  - Delays aleatorios anti-detección
  - Manejo de errores y reintentos
  - Descarga masiva de PDFs

- **Extracción de texto:**
  - PyPDF2 para PDFs digitales
  - OCR (Tesseract) para PDFs escaneados
  - Fallback automático

- **Parsing de secciones jurídicas:**
  - VISTOS
  - CONSIDERANDO
  - POR TANTO
  - ARTÍCULOS (con números)
  - DISPOSICIONES (FINALES, TRANSITORIAS, ADICIONALES, ABROGATORIAS)

- **Extracción de metadatos:**
  - Tipo de norma (LEY, DECRETO SUPREMO, etc.)
  - Número de norma
  - Fecha (normalizada a ISO)
  - Entidad emisora
  - Temas principales

- **Exportación:**
  - JSON (con texto completo y artículos)
  - CSV (metadatos estructurados)

## Estructura del Proyecto

```
bo-scraper-gaceta/
├── README.md
├── QUICKSTART.md        # Guía rápida
├── requirements.txt
├── main.py              # 🎯 PUNTO DE ENTRADA PRINCIPAL
├── selenium_scraper.py  # Scraper con Selenium (navegador real)
├── scraper.py           # Scraper con requests (HTTP directo)
├── parser.py            # Parsing de documentos legales + OCR
├── metadata.py          # Extracción de metadatos
├── config.py            # Configuración
│
├── data/
│   ├── raw/            # HTML guardado para debug
│   ├── pdfs/           # PDFs descargados
│   └── text/           # Textos extraídos
│
├── exports/
│   ├── json/           # Exportaciones JSON
│   └── csv/            # Exportaciones CSV
│
└── scripts/
    └── run_full.py     # Script legacy (modo requests)
```

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/zambogram/scraper.py.git
cd scraper.py
```

### 2. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### 3. Instalar ChromeDriver (OBLIGATORIO para modo Selenium)

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install chromium-chromedriver

# Verificar instalación
chromedriver --version
```

#### MacOS:
```bash
brew install --cask chromedriver

# O con Homebrew:
brew install chromedriver

# Verificar instalación
chromedriver --version
```

#### Windows:
1. Descarga ChromeDriver desde: https://chromedriver.chromium.org/downloads
2. **IMPORTANTE:** Descarga la versión que coincida con tu Chrome instalado
3. Extrae el archivo `chromedriver.exe`
4. Añádelo al PATH o especifica la ruta con `--chromedriver-path`

Para verificar tu versión de Chrome:
```bash
# En Chrome, ve a: chrome://version/
# O desde terminal:
google-chrome --version  # Linux
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version  # MacOS
```

### 4. (Opcional) Instalar Tesseract para OCR

Si los PDFs están escaneados (imágenes), necesitarás OCR:

#### Ubuntu/Debian:
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

#### MacOS:
```bash
brew install tesseract tesseract-lang
```

#### Windows:
1. Descarga desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Instala e incluye el paquete de idioma español

## Uso

### 🚀 Comando más simple (modo prueba)

```bash
python main.py --test
```

Esto scrapeará **10 documentos** para verificar que todo funciona.

### ⚡ Comandos Principales

```bash
# Modo Selenium (RECOMENDADO) - Scrapear 5 páginas
python main.py --modo selenium --paginas 5

# Scrapear TODO (cuidado: puede tardar HORAS)
python main.py --modo selenium --paginas 9999

# Modo prueba (10 documentos)
python main.py --test

# Scrapear SIN descargar PDFs (solo metadatos)
python main.py --modo selenium --paginas 5 --no-download-pdfs

# Ver el navegador Chrome (útil para debugging)
python main.py --modo selenium --no-headless --limite 5

# URL personalizada
python main.py --modo selenium --url "http://www.gacetaoficialdebolivia.gob.bo/normas/listadonor/10"

# ChromeDriver personalizado
python main.py --modo selenium --chromedriver-path /usr/local/bin/chromedriver
```

### 📋 Opciones Completas

```
main.py [-h] [--modo {selenium,requests}] [--paginas PAGINAS]
        [--limite LIMITE] [--url URL] [--headless] [--no-headless]
        [--chromedriver-path PATH] [--download-pdfs] [--no-download-pdfs]
        [--test] [--full]

Opciones:
  --modo {selenium,requests}  Modo de scraping (default: selenium)
  --paginas PAGINAS          Páginas a scrapear (9999=todas, default: 1)
  --limite LIMITE            Límite de documentos (0=todos, default: 0)
  --url URL                  URL base personalizada
  --headless                 Chrome sin interfaz (default: True)
  --no-headless              Mostrar Chrome (útil para debug)
  --chromedriver-path PATH   Ruta a chromedriver
  --download-pdfs            Descargar PDFs (default: True)
  --no-download-pdfs         Solo metadatos, no descargar PDFs
  --test                     Modo prueba: 10 docs
  --full                     Scrapear TODO
```

## Formato de Salida

### JSON
```json
{
  "id": "ley_1234_20240115",
  "titulo": "Ley de...",
  "tipo_norma": "LEY",
  "numero_norma": "1234",
  "fecha": "2024-01-15",
  "seccion": "LEY",
  "entidad_emisora": "ASAMBLEA LEGISLATIVA",
  "url_pdf": "http://...",
  "resumen": "...",
  "temas": "EDUCACIÓN,SALUD",
  "num_articulos": 25,
  "num_considerandos": 5,
  "texto_completo": "...",
  "articulos_json": "[{\"numero\":\"1\",\"contenido\":\"...\"}]"
}
```

### CSV
Columnas: id, titulo, tipo_norma, numero_norma, fecha, seccion, entidad_emisora, url_pdf, resumen, temas, num_articulos, num_considerandos, tiene_vistos, tiene_disposiciones_finales

## Solución de Problemas

### Error: "chromedriver executable needs to be in PATH"

**Solución:**
```bash
# Opción 1: Especificar ruta manualmente
python main.py --chromedriver-path /ruta/a/chromedriver

# Opción 2: Instalar con gestores de paquetes (ver sección Instalación)

# Opción 3: Agregar al PATH
export PATH=$PATH:/ruta/donde/esta/chromedriver  # Linux/Mac
```

### Error: "This version of ChromeDriver only supports Chrome version XX"

**Solución:**
1. Verifica tu versión de Chrome: `google-chrome --version`
2. Descarga ChromeDriver compatible desde: https://chromedriver.chromium.org/downloads
3. Reemplaza el chromedriver antiguo

### No se encuentran documentos

**Solución:**
1. Verifica que el sitio esté funcionando: http://www.gacetaoficialdebolivia.gob.bo/
2. El scraper guardará un HTML en `data/raw/debug_html_*.html` para que inspecciones la estructura
3. Ajusta los selectores en `selenium_scraper.py` función `_extraer_documentos_de_pagina_actual()`

### PDFs descargados pero sin texto

**Posibles causas:**
- PDF es escaneado (imagen), no digital

**Solución:**
1. Instala Tesseract OCR (ver sección Instalación)
2. El scraper usará automáticamente OCR como fallback

### El sitio me bloquea

**Solución:**
- Ya estás usando Selenium que simula un navegador real
- Aumenta los delays en `selenium_scraper.py`:
  ```python
  self._random_delay(min_sec=3, max_sec=7)  # Más delay
  ```

### Error 503 Service Unavailable

**Causas posibles:**
- El sitio está caído temporalmente
- Demasiadas requests simultáneas

**Solución:**
- Espera unos minutos
- Usa `--limite` bajo para probar: `--limite 5`
- Aumenta delays entre requests

## Configuración Avanzada

Edita `config.py` para ajustar:
- URLs del sitio
- Timeouts y reintentos
- Tipos de normas reconocidas
- Secciones jurídicas esperadas

## Ajuste de Selectores HTML

Si el sitio cambia su estructura o el scraper no encuentra documentos:

1. El scraper guardará HTML en `data/raw/debug_html_*.html`
2. Abre ese archivo e inspecciona la estructura
3. Edita `selenium_scraper.py`, función `_extraer_documentos_de_pagina_actual()` (línea ~170)
4. Ajusta los selectores CSS según la estructura real

El scraper intenta **4 estrategias** automáticamente:
- Estrategia 1: Tablas (`<table>`)
- Estrategia 2: Divs con clases específicas
- Estrategia 3: Enlaces directos a PDF
- Estrategia 4: Inspección genérica

## Ejemplos de Uso Completo

### Caso 1: Prueba Rápida (10 documentos)
```bash
python main.py --test
```

### Caso 2: Scrapear un mes completo (estimado: 50-100 docs)
```bash
python main.py --modo selenium --paginas 10
```

### Caso 3: Scrapear TODO sin descargar PDFs (solo metadatos)
```bash
python main.py --full --no-download-pdfs
```

### Caso 4: Debugging (ver Chrome en acción)
```bash
python main.py --no-headless --limite 5
```

### Caso 5: Servidor sin interfaz gráfica
```bash
python main.py --headless --paginas 20
```

## Dependencias

**Core:**
- requests: HTTP requests (modo requests)
- beautifulsoup4: HTML parsing (modo requests)
- lxml: Parser rápido
- PyPDF2: Extracción de texto de PDF
- python-dateutil: Parsing de fechas

**Selenium (navegador real):**
- selenium: Automatización de navegador
- webdriver-manager: Gestión automática de ChromeDriver (opcional)

**OCR (opcional, para PDFs escaneados):**
- pytesseract: Wrapper de Tesseract
- Pillow: Procesamiento de imágenes
- pdf2image: Conversión PDF a imagen

## Logs

Los logs se guardan automáticamente:
```
gaceta_scraper_20240115_143022.log
```

Nivel de logging: INFO (configurable en `config.py`)

## Limitaciones Conocidas

1. **Velocidad:** Selenium es más lento que requests (pero más robusto)
2. **Dependencia de Chrome:** Requiere Chrome y ChromeDriver instalados
3. **Selectores HTML:** Pueden cambiar si el sitio se actualiza
4. **PDFs escaneados:** OCR es lento y puede tener errores
5. **Memoria:** Procesar miles de PDFs puede consumir mucha RAM

## Rendimiento Estimado

- **Modo Selenium + PyPDF2:** ~10-20 documentos/minuto
- **Modo Selenium + OCR:** ~2-5 documentos/minuto (mucho más lento)
- **Memoria:** ~500MB-2GB dependiendo de PDFs

## Recomendaciones

✅ Usa `--test` primero para verificar funcionamiento
✅ Empieza con `--limite` bajo antes de scrapear todo
✅ Usa `--headless` en servidores
✅ Revisa los logs para detectar problemas
✅ Haz backups de `exports/` regularmente

❌ No uses `--paginas 9999` sin antes probar con límites bajos
❌ No ejecutes múltiples instancias simultáneas (puede causar bloqueos)
❌ No ignores los mensajes de advertencia

## Soporte

- Reporta issues en: [GitHub Issues](https://github.com/zambogram/scraper.py/issues)
- Consulta `QUICKSTART.md` para comandos rápidos

## Licencia

[Especificar licencia]

## Contribuciones

[Instrucciones para contribuir]

---

**Desarrollado para la Gaceta Oficial del Estado Plurinacional de Bolivia**
Sitio oficial: http://www.gacetaoficialdebolivia.gob.bo/
