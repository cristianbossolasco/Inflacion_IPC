from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from .config import CACHE_DIR, INDEC_EXCEL_TEMPLATE, INDEC_URLS


@dataclass(frozen=True)
class InformeExcel:
    url: str
    informe: str
    ultimo_periodo_datos: str


def _parse_number(value):
    if pd.isna(value):
        return float("nan")
    if isinstance(value, (int, float)):
        return value
    return float(str(value).replace(".", "").replace(",", "."))


def download_csv(nombre: str, force: bool = False, cache_dir: Path = CACHE_DIR) -> Path:
    """Descarga una fuente oficial de INDEC y la guarda en cache local."""
    if nombre not in INDEC_URLS:
        raise ValueError(f"Fuente desconocida: {nombre}")

    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{nombre}.csv"

    if force or not path.exists():
        df = pd.read_csv(INDEC_URLS[nombre], sep=";", encoding="latin1")
        df.to_csv(path, index=False, sep=";", encoding="utf-8")

    return path


def _normalizar(df: pd.DataFrame, fuente: str) -> pd.DataFrame:
    categoria_col = "Descripcion_aperturas" if "Descripcion_aperturas" in df.columns else "Descripcion"
    categoria = df[categoria_col].astype("string").str.strip()
    codigo = df["Codigo"].astype(str).str.strip()
    categoria = categoria.fillna(codigo)
    categoria = categoria.mask(categoria.eq(""), codigo)
    categoria = categoria.replace(
        {
            "NIVEL GENERAL": "Nivel general",
            "B": "Bienes",
            "S": "Servicios",
        }
    )

    out = pd.DataFrame(
        {
            "fuente": fuente,
            "codigo": codigo,
            "categoria": categoria.astype(str),
            "clasificador": df["Clasificador"].astype(str).str.strip(),
            "periodo": df["Periodo"].astype(int),
            "indice": df["Indice_IPC"].map(_parse_number).astype(float),
            "var_mensual_oficial": df["v_m_IPC"].map(_parse_number).astype("Float64"),
            "var_interanual_oficial": df["v_i_a_IPC"].map(_parse_number).astype("Float64"),
            "region": df["Region"].astype(str).str.strip(),
        }
    )
    out = out.dropna(subset=["indice"])
    out["fecha"] = pd.to_datetime(out["periodo"].astype(str) + "01", format="%Y%m%d")
    out["periodo_label"] = out["fecha"].dt.strftime("%Y-%m")
    out["serie"] = out["region"] + " - " + out["categoria"]
    return out.sort_values(["fuente", "region", "categoria", "periodo"]).reset_index(drop=True)


def cargar_divisiones(force: bool = False) -> pd.DataFrame:
    path = download_csv("divisiones", force=force)
    raw = pd.read_csv(path, sep=";", encoding="utf-8")
    return _normalizar(raw, "Divisiones")


def cargar_aperturas(force: bool = False) -> pd.DataFrame:
    path = download_csv("aperturas", force=force)
    raw = pd.read_csv(path, sep=";", encoding="utf-8")
    return _normalizar(raw, "Aperturas")


def cargar_todo(force: bool = False, incluir_aperturas: bool = True) -> pd.DataFrame:
    frames = [cargar_divisiones(force=force)]
    if incluir_aperturas:
        frames.append(cargar_aperturas(force=force))
    return pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["fuente", "codigo", "categoria", "periodo", "region"], keep="first"
    )


def ultimo_periodo_disponible(df: pd.DataFrame) -> str:
    return str(df.loc[df["periodo"].idxmax(), "periodo_label"])


def _periodos_informe_excel(url: str) -> list[str]:
    excel = pd.ExcelFile(url, engine="xlrd")
    data = excel.parse("Índices IPC Cobertura Nacional", skiprows=5, nrows=1)
    periodos = []
    for col in data.columns[1:]:
        fecha = pd.to_datetime(col, errors="coerce")
        if pd.notna(fecha):
            periodos.append(fecha.strftime("%Y-%m"))
    return sorted(set(periodos))


def _informe_cache_path() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / "informe_excel.json"


def _leer_informe_cache(max_age_hours: int = 12) -> InformeExcel | None:
    path = _informe_cache_path()
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    checked_at = datetime.fromisoformat(payload["checked_at"])
    if datetime.now() - checked_at > timedelta(hours=max_age_hours):
        return None
    return InformeExcel(
        url=payload["url"],
        informe=payload["informe"],
        ultimo_periodo_datos=payload["ultimo_periodo_datos"],
    )


def _guardar_informe_cache(informe: InformeExcel) -> None:
    payload = {
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "url": informe.url,
        "informe": informe.informe,
        "ultimo_periodo_datos": informe.ultimo_periodo_datos,
    }
    _informe_cache_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")


def buscar_ultimo_informe_excel(
    hoy: date | None = None,
    meses_hacia_atras: int = 18,
    force: bool = False,
) -> InformeExcel | None:
    """Busca el ultimo archivo mensual sh_ipc_MM_AA.xls publicado por INDEC."""
    if not force:
        cached = _leer_informe_cache()
        if cached:
            return cached

    actual = hoy or date.today()
    cursor = pd.Period(actual, freq="M")

    for offset in range(meses_hacia_atras):
        periodo = cursor - offset
        url = INDEC_EXCEL_TEMPLATE.format(month=periodo.month, year=periodo.year % 100)
        try:
            periodos = _periodos_informe_excel(url)
        except Exception:
            continue
        if periodos:
            informe = InformeExcel(
                url=url,
                informe=f"{periodo.year}-{periodo.month:02d}",
                ultimo_periodo_datos=periodos[-1],
            )
            _guardar_informe_cache(informe)
            return informe

    return None
