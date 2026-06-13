from __future__ import annotations

import streamlit as st


UI_HELP = {
    "actualizar_datos": "Fuerza una nueva descarga de los CSV oficiales de INDEC y vuelve a calcular la vista.",
    "nivel_detalle": "General y divisiones muestra agregados principales. Aperturas detalladas habilita rubros mas especificos cuando INDEC los publica para la region.",
    "nivel_detalle_dashboard": "Define si el ranking usa agregados principales o rubros mas detallados. Los KPIs siguen usando Nivel general.",
    "region": "Region estadistica oficial publicada por INDEC. Nacional esta disponible en General y divisiones.",
    "region_dash": "Region usada para la foto mensual, los KPIs y el ranking de categorias.",
    "provincia": "La provincia se usa solo para elegir su region INDEC aproximada; no es IPC provincial oficial.",
    "categoria": "Nivel general mide el IPC agregado. Las otras categorias dependen del nivel de detalle elegido.",
    "monto": "Opcional: la app multiplica este monto por el factor entre el indice final y el inicial.",
    "periodo_inicial": "Mes base del calculo. La variacion arranca desde el indice de este periodo.",
    "periodo_final": "Mes de cierre. Debe ser posterior al periodo inicial.",
    "geo_comparador": "Regiones compara datos oficiales. Provincias aproximadas asigna cada provincia a su region INDEC.",
    "comparar": "Selecciona una o varias geografias. Cada una se combinara con las categorias elegidas.",
    "categorias_comparador": "Puedes elegir una o varias categorias; cada combinacion aparece como una serie separada.",
    "mi_ipc_ubicacion": "Elige una region oficial o una provincia aproximada a su region INDEC.",
    "mi_ipc_peso": "Carga la importancia relativa de cada rubro. No hace falta que los pesos sumen 100.",
    "explorador": "Filtra una serie especifica para revisar su historial completo y descargarla.",
    "metric_variacion": "Inflacion acumulada entre el periodo inicial y el final.",
    "metric_factor": "Multiplicador aplicado al monto: indice final dividido por indice inicial.",
    "metric_tasa_mensual": "Tasa mensual constante que produciria la misma variacion acumulada.",
    "metric_monto": "Monto original actualizado por el factor IPC seleccionado.",
    "metric_ultimo": "Ultimo periodo disponible para el nivel de detalle y region seleccionados.",
    "metric_mensual": "Variacion del nivel general entre el ultimo mes y el mes anterior.",
    "metric_interanual": "Variacion del nivel general contra el mismo mes del anio anterior.",
    "metric_mi_ipc": "Variacion estimada de tu canasta personalizada segun los pesos cargados.",
}


EXPANDERS = {
    "calculadora": (
        "Como se calcula",
        """
El calculo usa la relacion entre indices: `IPC acumulado = (indice final / indice inicial - 1) * 100`.

El factor es `indice final / indice inicial`; si cargas un monto, se actualiza como `monto * factor`.
La tasa mensual equivalente reparte esa variacion acumulada como si todos los meses hubieran subido al mismo ritmo.
""",
    ),
    "grafico_calculadora": (
        "Como leer el grafico",
        """
La linea siempre empieza en 0% en el periodo inicial. Cada punto muestra cuanto acumulo la serie desde ese mes base.

Si cambias region, categoria o nivel de detalle, el grafico recalcula el tramo con la serie seleccionada.
""",
    ),
    "tabla_variaciones": (
        "Que significa cada columna",
        """
`Var. mensual oficial` e `interanual oficial` vienen de INDEC. Las demas columnas se calculan con los indices:

- `desde inicio del anio`: acumulado contra diciembre del anio anterior.
- `trimestre calendario`: acumulado dentro del trimestre en curso.
- `ultimos 2` a `ultimos 11 meses`: variacion movil contra el indice de esa cantidad de meses antes.
""",
    ),
    "dashboard": (
        "Como interpretar el dashboard",
        """
La foto mensual resume el ultimo periodo disponible para el nivel de detalle y region elegidos.

Los KPIs usan el nivel general. El ranking cambia segun el nivel de detalle elegido.

El grafico regional usa escala recortada en el eje Y para que las diferencias entre regiones se vean mejor cuando los valores estan muy cerca.
""",
    ),
    "comparador": (
        "Como leer el comparador",
        """
Cada combinacion de geografia y categoria se dibuja como una serie independiente. La linea arranca en 0% para que puedas comparar ritmos, aunque los indices base sean distintos.

Para evitar saturacion visual, el grafico comparativo no muestra etiquetas fijas en cada punto. Usa el cursor sobre la linea y la tabla resumen para leer valores exactos.

Cuando eliges provincias aproximadas, la app usa la region INDEC correspondiente y lo muestra en la tabla resumen.
""",
    ),
    "mi_ipc": (
        "Como interpretar Mi IPC",
        """
Los pesos representan la importancia relativa de cada rubro en tu canasta. La app normaliza automaticamente la suma, por eso pueden sumar 100, 1.000 o cualquier total positivo.

El resultado es una estimacion basada en divisiones IPC oficiales; no reemplaza una medicion exacta de tu gasto personal.
""",
    ),
    "explorador": (
        "Para que sirve el explorador",
        """
Esta vista muestra una unica serie sin recortes. Sirve para auditar datos, descargar CSV y revisar meses especificos antes de usar una serie en calculos o comparaciones.
""",
    ),
    "datos": (
        "Como leer el estado de datos",
        """
La tabla muestra cobertura por region y fuente interna: primer periodo, ultimo periodo y cantidad de series disponibles.

El informe Excel mensual indica el archivo `sh_ipc_MM_AA.xls` detectado y hasta que periodo llegan sus datos.
""",
    ),
}


def h(key: str) -> str:
    return UI_HELP[key]


def help_expander(key: str) -> None:
    title, body = EXPANDERS[key]
    with st.expander(title, expanded=False):
        st.markdown(body.strip())
