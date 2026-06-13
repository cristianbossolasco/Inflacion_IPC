from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = BASE_DIR / "data" / "cache"
OUTPUT_DIR = BASE_DIR / "outputs"

INDEC_URLS = {
    "divisiones": "https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv",
    "aperturas": "https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_aperturas.csv",
    "metadatos": "https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_metadatos.txt",
}

INDEC_EXCEL_TEMPLATE = "https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_{month:02d}_{year:02d}.xls"
