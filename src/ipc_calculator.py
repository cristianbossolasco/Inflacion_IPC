from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class IpcResult:
    fuente: str
    region: str
    categoria: str
    periodo_inicial: str
    periodo_final: str
    indice_inicial: float
    indice_final: float
    meses: int
    factor: float
    variacion_pct: float
    tasa_mensual_equivalente_pct: float
    tasa_anualizada_pct: float
    monto_original: float | None = None
    monto_actualizado: float | None = None


def meses_entre(periodo_inicial: str, periodo_final: str) -> int:
    ini = pd.Period(periodo_inicial, freq="M")
    fin = pd.Period(periodo_final, freq="M")
    return int(fin.ordinal - ini.ordinal)


def filtrar_serie(df: pd.DataFrame, fuente: str, region: str, categoria: str) -> pd.DataFrame:
    sort_col = "periodo" if "periodo" in df.columns else "periodo_label"
    serie = df[
        (df["fuente"] == fuente)
        & (df["region"] == region)
        & (df["categoria"] == categoria)
    ].sort_values(sort_col)
    if serie.empty:
        raise ValueError(f"No existe la serie {fuente} / {region} / {categoria}.")
    return serie


def calcular_variacion(
    df: pd.DataFrame,
    fuente: str,
    region: str,
    categoria: str,
    periodo_inicial: str,
    periodo_final: str,
    monto: float | None = None,
) -> IpcResult:
    meses = meses_entre(periodo_inicial, periodo_final)
    if meses <= 0:
        raise ValueError("El periodo final debe ser posterior al periodo inicial.")

    serie = filtrar_serie(df, fuente, region, categoria)
    valores = serie.set_index("periodo_label")["indice"]

    faltantes = [p for p in [periodo_inicial, periodo_final] if p not in valores.index]
    if faltantes:
        raise ValueError(f"No hay indice para: {', '.join(faltantes)}.")

    indice_inicial = float(valores.loc[periodo_inicial])
    indice_final = float(valores.loc[periodo_final])
    factor = indice_final / indice_inicial
    variacion_pct = (factor - 1) * 100
    tasa_mensual = (math.pow(factor, 1 / meses) - 1) * 100
    tasa_anualizada = (math.pow(factor, 12 / meses) - 1) * 100
    monto_actualizado = None if monto is None else monto * factor

    return IpcResult(
        fuente=fuente,
        region=region,
        categoria=categoria,
        periodo_inicial=periodo_inicial,
        periodo_final=periodo_final,
        indice_inicial=indice_inicial,
        indice_final=indice_final,
        meses=meses,
        factor=factor,
        variacion_pct=variacion_pct,
        tasa_mensual_equivalente_pct=tasa_mensual,
        tasa_anualizada_pct=tasa_anualizada,
        monto_original=monto,
        monto_actualizado=monto_actualizado,
    )


def calcular_ranking(
    df: pd.DataFrame,
    fuente: str,
    region: str,
    periodo_inicial: str,
    periodo_final: str,
    top: int = 10,
) -> pd.DataFrame:
    rows = []
    categorias = sorted(df[(df["fuente"] == fuente) & (df["region"] == region)]["categoria"].unique())
    for categoria in categorias:
        try:
            result = calcular_variacion(df, fuente, region, categoria, periodo_inicial, periodo_final)
        except ValueError:
            continue
        rows.append(
            {
                "categoria": categoria,
                "variacion_pct": result.variacion_pct,
                "factor": result.factor,
                "tasa_mensual_equivalente_pct": result.tasa_mensual_equivalente_pct,
            }
        )
    ranking = pd.DataFrame(rows).sort_values("variacion_pct", ascending=False)
    return ranking.head(top)


def serie_para_grafico(
    df: pd.DataFrame,
    fuente: str,
    region: str,
    categoria: str,
    periodo_inicial: str | None = None,
    periodo_final: str | None = None,
) -> pd.DataFrame:
    serie = enriquecer_variaciones(filtrar_serie(df, fuente, region, categoria).copy())
    if periodo_inicial:
        serie = serie[serie["periodo_label"] >= periodo_inicial]
    if periodo_final:
        serie = serie[serie["periodo_label"] <= periodo_final]
    serie["variacion_acumulada_pct"] = (serie["indice"] / serie["indice"].iloc[0] - 1) * 100
    return serie


def enriquecer_variaciones(serie: pd.DataFrame) -> pd.DataFrame:
    """Agrega variaciones calculadas que INDEC no publica en la tabla base."""
    serie = serie.sort_values("periodo_label").copy()
    for meses in range(2, 12):
        serie[f"var_ultimos_{meses}_meses"] = serie["indice"].pct_change(meses) * 100
    serie["var_ultimos_12_meses"] = serie["indice"].pct_change(12) * 100

    valores = serie.set_index("periodo_label")["indice"]
    ytd = []
    trimestre = []
    for _, row in serie.iterrows():
        periodo = pd.Period(row["periodo_label"], freq="M")
        cierre_anio_anterior = f"{periodo.year - 1}-12"
        cierre_trimestre_anterior = pd.Period(year=periodo.year, quarter=periodo.quarter, freq="Q").asfreq("M", "start") - 1

        if cierre_anio_anterior in valores.index:
            ytd.append((row["indice"] / valores.loc[cierre_anio_anterior] - 1) * 100)
        else:
            ytd.append(pd.NA)

        trimestre_label = cierre_trimestre_anterior.strftime("%Y-%m")
        if trimestre_label in valores.index:
            trimestre.append((row["indice"] / valores.loc[trimestre_label] - 1) * 100)
        else:
            trimestre.append(pd.NA)

    serie["var_desde_inicio_anio"] = ytd
    serie["var_trimestre_calendario"] = trimestre
    return serie


def calcular_mi_ipc(
    df: pd.DataFrame,
    region: str,
    ponderaciones: dict[str, float],
    periodo_inicial: str,
    periodo_final: str,
    fuente: str = "Divisiones",
) -> tuple[float, pd.DataFrame]:
    total = sum(v for v in ponderaciones.values() if v > 0)
    if total <= 0:
        raise ValueError("La suma de ponderaciones debe ser mayor a cero.")

    rows = []
    factor_ponderado = 0.0
    for categoria, peso in ponderaciones.items():
        if peso <= 0:
            continue
        result = calcular_variacion(df, fuente, region, categoria, periodo_inicial, periodo_final)
        peso_norm = peso / total
        factor_ponderado += result.factor * peso_norm
        rows.append(
            {
                "categoria": categoria,
                "peso": peso,
                "peso_normalizado": peso_norm,
                "variacion_pct": result.variacion_pct,
                "aporte_pp": (result.factor - 1) * peso_norm * 100,
            }
        )

    return (factor_ponderado - 1) * 100, pd.DataFrame(rows).sort_values("aporte_pp", ascending=False)
