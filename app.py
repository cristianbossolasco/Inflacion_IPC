from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.indec_loader import buscar_ultimo_informe_excel, cargar_todo, ultimo_periodo_disponible
from src.ipc_calculator import (
    calcular_mi_ipc,
    calcular_ranking,
    calcular_variacion,
    serie_para_grafico,
)
from src.regions import PROVINCIA_A_REGION, REGIONES_INDEC
from src.ui_help import h, help_expander


st.set_page_config(page_title="Calculadora IPC Argentina", layout="wide")

DETALLE_A_FUENTE = {
    "General y divisiones": "Divisiones",
    "Aperturas detalladas": "Aperturas",
}


@st.cache_data(ttl=60 * 60 * 12)
def load_data(force: bool = False) -> pd.DataFrame:
    return cargar_todo(force=force, incluir_aperturas=True)


@st.cache_data(ttl=60 * 60 * 12)
def load_excel_report_status():
    return buscar_ultimo_informe_excel(force=False)


def money(value: float) -> str:
    return f"$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(value: float) -> str:
    return f"{value:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def rango_eje_con_margen(values: pd.Series, padding_ratio: float = 0.18, min_span: float = 1.0) -> list[float] | None:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return None
    minimum = float(clean.min())
    maximum = float(clean.max())
    span = max(maximum - minimum, min_span)
    padding = span * padding_ratio
    return [minimum - padding, maximum + padding]


def agregar_labels_barras(fig, orientation: str = "v"):
    axis_value = "x" if orientation == "h" else "y"
    fig.update_traces(
        texttemplate=f"%{{{axis_value}:.1f}}%",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{label}<br>Variacion: %{value:.2f}%<extra></extra>",
    )
    fig.update_layout(uniformtext_minsize=10, uniformtext_mode="hide")
    return fig


def agregar_labels_linea(fig):
    fig.update_traces(
        mode="lines+markers+text",
        texttemplate="%{y:.1f}%",
        textposition="top center",
        cliponaxis=False,
        hovertemplate="%{x|%Y-%m}<br>Variacion acumulada: %{y:.2f}%<extra></extra>",
    )
    fig.update_layout(uniformtext_minsize=9, uniformtext_mode="hide")
    return fig


def aplicar_rango_linea(fig, values: pd.Series):
    axis_range = rango_eje_con_margen(values, padding_ratio=0.12, min_span=5.0)
    if axis_range:
        fig.update_yaxes(range=axis_range)
    return fig


def normalizar_linea_comparador(fig):
    fig.update_traces(
        mode="lines+markers",
        hovertemplate="%{x|%Y-%m}<br>Variacion acumulada: %{y:.2f}%<extra></extra>",
    )
    return fig


def fuente_desde_detalle(detalle: str) -> str:
    return DETALLE_A_FUENTE[detalle]


def regiones_disponibles(data: pd.DataFrame, fuente: str) -> list[str]:
    disponibles = set(data[data["fuente"] == fuente]["region"].unique())
    return [region for region in REGIONES_INDEC if region in disponibles]


def categorias_disponibles(data: pd.DataFrame, fuente: str, region: str) -> list[str]:
    return sorted(data[(data["fuente"] == fuente) & (data["region"] == region)]["categoria"].unique())


def categorias_para_regiones(data: pd.DataFrame, fuente: str, regiones: list[str]) -> list[str]:
    if not regiones:
        return []
    return sorted(data[(data["fuente"] == fuente) & (data["region"].isin(regiones))]["categoria"].unique())


def tabla_variaciones(serie: pd.DataFrame) -> pd.DataFrame:
    ventanas_moviles = [f"var_ultimos_{meses}_meses" for meses in range(2, 12)]
    cols = [
        "periodo_label",
        "indice",
        "var_mensual_oficial",
        "var_interanual_oficial",
        "var_desde_inicio_anio",
        "var_trimestre_calendario",
    ] + ventanas_moviles
    tabla = serie[cols].rename(
        columns={
            "periodo_label": "Periodo",
            "indice": "Indice",
            "var_mensual_oficial": "Var. mensual oficial",
            "var_interanual_oficial": "Var. interanual oficial",
            "var_desde_inicio_anio": "Var. desde inicio del anio",
            "var_trimestre_calendario": "Var. trimestre calendario",
            **{f"var_ultimos_{meses}_meses": f"Var. ultimos {meses} meses" for meses in range(2, 12)},
        }
    )
    numeric_cols = [col for col in tabla.columns if col != "Periodo"]
    tabla[numeric_cols] = tabla[numeric_cols].astype(float).round(2)
    return tabla


def opciones_geo(modo: str, regiones_base: list[str]) -> list[str]:
    if modo == "Provincias aproximadas":
        return sorted(PROVINCIA_A_REGION)
    return regiones_base


def resolver_geo(modo: str, item: str) -> tuple[str, str]:
    if modo == "Provincias aproximadas":
        return PROVINCIA_A_REGION[item], f"{item} ({PROVINCIA_A_REGION[item]})"
    return item, item


with st.sidebar:
    st.title("IPC Argentina")
    force_refresh = st.button("Actualizar datos INDEC", help=h("actualizar_datos"))
    df = load_data(force_refresh)
    informe_excel = load_excel_report_status()
    ultimo = ultimo_periodo_disponible(df)
    st.caption(f"Ultimo periodo disponible: {ultimo}")
    if informe_excel:
        st.caption(f"Informe Excel disponible: {informe_excel.informe}; datos hasta {informe_excel.ultimo_periodo_datos}.")
    st.caption("Fuente: CSV oficiales de INDEC y chequeo del informe Excel mensual.")

periodos = sorted(df["periodo_label"].unique())

st.title("Calculadora y dashboard de IPC")

tab_calc, tab_dash, tab_comp, tab_mi_ipc, tab_exp, tab_datos = st.tabs(
    ["Calculadora", "Dashboard mensual", "Comparador", "Mi IPC", "Explorador", "Datos"]
)

with tab_calc:
    st.subheader("Inflacion entre dos periodos")
    c1, c2, c3, c4 = st.columns(4)
    detalle = c1.selectbox("Nivel de detalle", list(DETALLE_A_FUENTE), key="calc_detalle", help=h("nivel_detalle"))
    fuente = fuente_desde_detalle(detalle)
    region = c2.selectbox("Region", regiones_disponibles(df, fuente), key="calc_region", help=h("region"))
    categorias = categorias_disponibles(df, fuente, region)
    default_categoria = "Nivel general" if "Nivel general" in categorias else categorias[0]
    categoria = c3.selectbox(
        "Categoria",
        categorias,
        index=categorias.index(default_categoria),
        key="calc_categoria",
        help=h("categoria"),
    )
    monto = c4.number_input("Monto a actualizar", min_value=0.0, value=100000.0, step=1000.0, help=h("monto"))

    p1, p2 = st.columns(2)
    periodo_inicial = p1.selectbox(
        "Periodo inicial",
        periodos,
        index=max(0, len(periodos) - 13),
        help=h("periodo_inicial"),
    )
    periodo_final = p2.selectbox("Periodo final", periodos, index=len(periodos) - 1, help=h("periodo_final"))

    try:
        result = calcular_variacion(df, fuente, region, categoria, periodo_inicial, periodo_final, monto)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Variacion acumulada", pct(result.variacion_pct), help=h("metric_variacion"))
        k2.metric("Factor", f"{result.factor:.6f}", help=h("metric_factor"))
        k3.metric("Tasa mensual equivalente", pct(result.tasa_mensual_equivalente_pct), help=h("metric_tasa_mensual"))
        k4.metric("Monto actualizado", money(result.monto_actualizado or 0), help=h("metric_monto"))
        help_expander("calculadora")

        serie = serie_para_grafico(df, fuente, region, categoria, periodo_inicial, periodo_final)
        fig = px.line(
            serie,
            x="fecha",
            y="variacion_acumulada_pct",
            markers=True,
            title=f"{region} - {categoria}: variacion acumulada desde {periodo_inicial}",
            labels={"fecha": "Periodo", "variacion_acumulada_pct": "Variacion acumulada (%)"},
        )
        aplicar_rango_linea(fig, serie["variacion_acumulada_pct"])
        st.plotly_chart(agregar_labels_linea(fig), use_container_width=True)
        help_expander("grafico_calculadora")

        st.dataframe(tabla_variaciones(serie), use_container_width=True, hide_index=True)
        help_expander("tabla_variaciones")
    except ValueError as exc:
        st.error(str(exc))

with tab_dash:
    st.subheader("Foto del ultimo mes disponible")
    detalle_dash = st.selectbox(
        "Nivel de detalle para ranking",
        list(DETALLE_A_FUENTE),
        key="dash_detalle",
        help=h("nivel_detalle_dashboard"),
    )
    fuente_dash = fuente_desde_detalle(detalle_dash)
    region_dash = st.selectbox(
        "Region dashboard",
        regiones_disponibles(df, fuente_dash),
        key="dash_region",
        help=h("region_dash"),
    )
    base = df[(df["fuente"] == fuente_dash) & (df["region"] == region_dash)]
    ultimo_periodo = base["periodo_label"].max()
    anterior = periodos[max(0, periodos.index(ultimo_periodo) - 1)]
    hace_12 = periodos[max(0, periodos.index(ultimo_periodo) - 12)]

    nivel_general = "Nivel general" if "Nivel general" in base["categoria"].unique() else base["categoria"].iloc[0]
    r_mensual = calcular_variacion(df, fuente_dash, region_dash, nivel_general, anterior, ultimo_periodo)
    r_interanual = calcular_variacion(df, fuente_dash, region_dash, nivel_general, hace_12, ultimo_periodo)

    d1, d2, d3 = st.columns(3)
    d1.metric("Ultimo periodo", ultimo_periodo, help=h("metric_ultimo"))
    d2.metric("IPC mensual", pct(r_mensual.variacion_pct), help=h("metric_mensual"))
    d3.metric("IPC interanual", pct(r_interanual.variacion_pct), help=h("metric_interanual"))

    c1, c2 = st.columns(2)
    ranking_12 = calcular_ranking(df, fuente_dash, region_dash, hace_12, ultimo_periodo, top=12)
    ranking_fig = px.bar(
        ranking_12,
        x="variacion_pct",
        y="categoria",
        orientation="h",
        title=f"Mayores subas interanuales - {region_dash}",
        labels={"variacion_pct": "Variacion (%)", "categoria": "Categoria"},
    )
    ranking_fig.update_layout(yaxis={"categoryorder": "total ascending"})
    ranking_fig.update_xaxes(range=[0, float(ranking_12["variacion_pct"].max()) * 1.18])
    c1.plotly_chart(agregar_labels_barras(ranking_fig, orientation="h"), use_container_width=True)

    regiones_rows = []
    for reg in REGIONES_INDEC:
        try:
            r = calcular_variacion(df, "Divisiones", reg, "Nivel general", hace_12, ultimo_periodo)
            regiones_rows.append({"region": reg, "variacion_pct": r.variacion_pct})
        except ValueError:
            pass
    regiones_df = pd.DataFrame(regiones_rows)
    region_chart_df = regiones_df.sort_values("variacion_pct")
    region_fig = px.bar(
        region_chart_df,
        x="region",
        y="variacion_pct",
        title="Interanual por region - Nivel general",
        labels={"region": "Region", "variacion_pct": "Variacion (%)"},
    )
    region_fig.update_yaxes(range=rango_eje_con_margen(region_chart_df["variacion_pct"]), zeroline=False)
    c2.plotly_chart(agregar_labels_barras(region_fig), use_container_width=True)
    help_expander("dashboard")

with tab_comp:
    st.subheader("Comparar regiones, provincias aproximadas y categorias")
    c1, c2, c3 = st.columns(3)
    detalle_comp = c1.selectbox("Nivel de detalle", list(DETALLE_A_FUENTE), key="comp_detalle", help=h("nivel_detalle"))
    fuente_comp = fuente_desde_detalle(detalle_comp)
    regiones_comp = regiones_disponibles(df, fuente_comp)
    modo_geo_comp = c2.radio(
        "Geografia",
        ["Regiones", "Provincias aproximadas"],
        horizontal=True,
        help=h("geo_comparador"),
    )
    geos = opciones_geo(modo_geo_comp, regiones_comp)
    seleccion_geo = c3.multiselect("Comparar", geos, default=geos[:3], help=h("comparar"))

    regiones_seleccionadas = [resolver_geo(modo_geo_comp, geo)[0] for geo in seleccion_geo]
    categorias_comp = categorias_para_regiones(df, fuente_comp, regiones_seleccionadas or regiones_comp)
    default_cats = ["Nivel general"] if "Nivel general" in categorias_comp else categorias_comp[:1]
    categorias_sel = st.multiselect("Categorias", categorias_comp, default=default_cats, help=h("categorias_comparador"))
    p1, p2 = st.columns(2)
    comp_inicio = p1.selectbox(
        "Desde",
        periodos,
        index=max(0, len(periodos) - 13),
        key="comp_inicio",
        help=h("periodo_inicial"),
    )
    comp_fin = p2.selectbox("Hasta", periodos, index=len(periodos) - 1, key="comp_fin", help=h("periodo_final"))

    series = []
    resumen_rows = []
    for geo in seleccion_geo:
        region_real, geo_label = resolver_geo(modo_geo_comp, geo)
        if region_real not in regiones_comp:
            continue
        for categoria_comp in categorias_sel:
            try:
                result = calcular_variacion(df, fuente_comp, region_real, categoria_comp, comp_inicio, comp_fin)
                etiqueta = f"{geo_label} - {categoria_comp}"
                serie = serie_para_grafico(df, fuente_comp, region_real, categoria_comp, comp_inicio, comp_fin)
                series.append(serie.assign(etiqueta=etiqueta, geo=geo_label))
                resumen_rows.append(
                    {
                        "Serie": etiqueta,
                        "Geografia": geo_label,
                        "Region INDEC": region_real,
                        "Categoria": categoria_comp,
                        "Indice inicial": result.indice_inicial,
                        "Indice final": result.indice_final,
                        "Variacion acumulada (%)": result.variacion_pct,
                        "Factor": result.factor,
                        "Tasa mensual equivalente (%)": result.tasa_mensual_equivalente_pct,
                    }
                )
            except ValueError:
                continue
    if series:
        comp_df = pd.concat(series)
        resumen_df = pd.DataFrame(resumen_rows)
        comp_fig = px.line(
            comp_df,
            x="fecha",
            y="variacion_acumulada_pct",
            color="etiqueta",
            markers=True,
            title="Variacion acumulada comparada",
            labels={"fecha": "Periodo", "variacion_acumulada_pct": "Variacion acumulada (%)", "etiqueta": "Serie"},
        )
        aplicar_rango_linea(comp_fig, comp_df["variacion_acumulada_pct"])
        st.plotly_chart(normalizar_linea_comparador(comp_fig), use_container_width=True)
        st.dataframe(resumen_df.round(4), use_container_width=True, hide_index=True)
    else:
        st.info("Selecciona al menos una geografia y una categoria con datos disponibles.")
    help_expander("comparador")

with tab_mi_ipc:
    st.subheader("Canasta personalizada")
    st.caption("Carga ponderaciones propias por division. La app normaliza la suma automaticamente.")
    c1, c2, c3 = st.columns(3)
    modo_geo = c1.radio(
        "Ubicacion",
        ["Region", "Provincia aproximada"],
        horizontal=True,
        help=h("mi_ipc_ubicacion"),
    )
    if modo_geo == "Region":
        region_mi = c2.selectbox("Region", REGIONES_INDEC, key="mi_region", help=h("region"))
    else:
        provincia = c2.selectbox("Provincia", sorted(PROVINCIA_A_REGION), key="mi_provincia", help=h("provincia"))
        region_mi = PROVINCIA_A_REGION[provincia]
        c3.info(f"Se usa la region INDEC: {region_mi}")

    div_cats = sorted(df[(df["fuente"] == "Divisiones") & (df["region"] == region_mi)]["categoria"].unique())
    div_cats = [cat for cat in div_cats if cat != "Nivel general"]
    pesos = {}
    cols = st.columns(3)
    defaults = {"Alimentos y bebidas no alcohólicas": 30.0, "Vivienda, agua, electricidad, gas y otros combustibles": 20.0, "Transporte": 10.0}
    for idx, cat in enumerate(div_cats):
        pesos[cat] = cols[idx % 3].number_input(
            cat,
            min_value=0.0,
            value=defaults.get(cat, 0.0),
            step=1.0,
            key=f"peso_{cat}",
            help=h("mi_ipc_peso"),
        )

    p1, p2 = st.columns(2)
    mi_inicio = p1.selectbox(
        "Desde",
        periodos,
        index=max(0, len(periodos) - 13),
        key="mi_inicio",
        help=h("periodo_inicial"),
    )
    mi_fin = p2.selectbox("Hasta", periodos, index=len(periodos) - 1, key="mi_fin", help=h("periodo_final"))
    try:
        mi_pct, detalle = calcular_mi_ipc(df, region_mi, pesos, mi_inicio, mi_fin)
        st.metric("Mi IPC estimado", pct(mi_pct), help=h("metric_mi_ipc"))
        st.dataframe(
            detalle.rename(
                columns={
                    "categoria": "Categoria",
                    "peso": "Peso cargado",
                    "peso_normalizado": "Peso normalizado",
                    "variacion_pct": "Variacion categoria (%)",
                    "aporte_pp": "Aporte al IPC propio (p.p.)",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    except ValueError as exc:
        st.warning(str(exc))
    help_expander("mi_ipc")

with tab_exp:
    st.subheader("Explorador de series")
    c1, c2, c3 = st.columns(3)
    detalle_exp = c1.selectbox("Nivel de detalle", list(DETALLE_A_FUENTE), key="exp_detalle", help=h("nivel_detalle"))
    fuente_exp = fuente_desde_detalle(detalle_exp)
    region_exp = c2.selectbox("Region", regiones_disponibles(df, fuente_exp), key="exp_region", help=h("region"))
    cats_exp = categorias_disponibles(df, fuente_exp, region_exp)
    cat_exp = c3.selectbox("Categoria", cats_exp, key="exp_cat", help=h("explorador"))
    serie_exp = serie_para_grafico(df, fuente_exp, region_exp, cat_exp)
    st.dataframe(serie_exp, use_container_width=True, hide_index=True)
    st.download_button(
        "Descargar CSV",
        serie_exp.to_csv(index=False).encode("utf-8"),
        file_name=f"ipc_{detalle_exp}_{region_exp}_{cat_exp}.csv".replace(" ", "_"),
        mime="text/csv",
    )
    help_expander("explorador")

with tab_datos:
    st.subheader("Estado de datos")
    resumen = (
        df.groupby("region")
        .agg(
            periodo_min=("periodo_label", "min"),
            periodo_max=("periodo_label", "max"),
            series=("categoria", "nunique"),
            fuentes=("fuente", lambda values: ", ".join(sorted(set(values)))),
        )
        .reset_index()
    )
    st.dataframe(resumen, use_container_width=True, hide_index=True)
    if informe_excel:
        st.markdown(
            f"Ultimo informe Excel detectado: [{informe_excel.informe}]({informe_excel.url}). "
            f"El archivo trae datos hasta {informe_excel.ultimo_periodo_datos}."
        )
    st.info(
        "Provincia aproximada no significa IPC provincial oficial. "
        "La app asigna cada provincia a su region estadistica INDEC."
    )
    help_expander("datos")
