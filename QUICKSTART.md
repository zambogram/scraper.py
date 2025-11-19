# QUICKSTART - Scraper Gaceta Oficial Bolivia

Guía ultra-rápida para empezar en 5 minutos.

## ⚡ Instalación Express (3 pasos)

```bash
# 1. Instalar dependencias Python
pip install -r requirements.txt

# 2. Instalar ChromeDriver
# Ubuntu/Debian:
sudo apt-get install chromium-chromedriver

# MacOS:
brew install chromedriver

# Windows: Descarga desde https://chromedriver.chromium.org/

# 3. Verificar
chromedriver --version
```

## 🚀 Comandos Esenciales

### Modo Prueba (Recomendado para empezar)
```bash
python main.py --test
```
✅ Scrapea **10 documentos** para verificar que todo funciona

### Scrapear 5 páginas
```bash
python main.py --modo selenium --paginas 5
```

### Ver Chrome en acción (debugging)
```bash
python main.py --no-headless --limite 5
```

### Scrapear TODO (⚠️ Puede tardar HORAS)
```bash
python main.py --full
```

### Solo metadatos (sin descargar PDFs)
```bash
python main.py --modo selenium --paginas 5 --no-download-pdfs
```

## 📂 Dónde están los resultados

```
exports/json/documentos_gaceta_TIMESTAMP.json  # JSON completo
exports/csv/documentos_gaceta_TIMESTAMP.csv    # CSV con metadatos
data/pdfs/                                     # PDFs descargados
```

## 🔧 Problemas Comunes

### "chromedriver executable needs to be in PATH"
```bash
# Especificar ruta manualmente:
python main.py --chromedriver-path /usr/local/bin/chromedriver
```

### "No se encontraron documentos"
1. Verifica que el sitio funcione: http://www.gacetaoficialdebolivia.gob.bo/
2. Revisa `data/raw/debug_html_*.html` para ver la estructura HTML
3. Ajusta selectores en `selenium_scraper.py`

### Error de versión de ChromeDriver
```bash
# Ver versión de Chrome:
google-chrome --version

# Descarga ChromeDriver compatible:
# https://chromedriver.chromium.org/downloads
```

## 📊 Qué hace cada comando

| Comando | Documentos | Tiempo estimado |
|---------|-----------|----------------|
| `--test` | 10 | 1-2 min |
| `--paginas 5` | 50-100 | 5-10 min |
| `--paginas 20` | 200-400 | 20-40 min |
| `--full` | TODOS | Horas |

## 🎯 Flujo de Trabajo Recomendado

```bash
# 1. Verificar instalación
python main.py --test

# 2. Probar con pocas páginas
python main.py --modo selenium --paginas 3

# 3. Revisar resultados en exports/

# 4. Si todo funciona, scrapear más
python main.py --modo selenium --paginas 20

# 5. Para scraping completo (ejecutar de noche)
python main.py --full
```

## ⚙️ Todas las opciones

```
python main.py --help
```

---

**¿Necesitas más detalles?** Lee `README.md`

**¿Algo no funciona?** Revisa la sección "Solución de Problemas" en `README.md`
