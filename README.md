# Calculadora IPC Argentina

App para calcular variaciones del IPC argentino entre cualquier par de meses usando series oficiales de INDEC.

Permite calcular IPC acumulado mensual, trimestral, interanual o entre cualquier periodo elegido, comparar regiones/categorias, actualizar montos, explorar series historicas y estimar una canasta personalizada.

## Fuentes usadas

La app descarga y cachea estos CSV oficiales:

- `https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv`
- `https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_aperturas.csv`

Tambien verifica el ultimo informe Excel mensual publicado con el patron:

```text
https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_MM_AA.xls
```

Ejemplo: `sh_ipc_05_26.xls` es el informe publicado en mayo de 2026, pero sus datos llegan hasta abril de 2026. Esto es normal: el archivo de publicacion de un mes suele contener el IPC del mes anterior.

La fuente oficial publica regiones estadisticas, no IPC provincial puro. Cuando elegis una provincia, la app la asigna a su region INDEC correspondiente. Por ejemplo, Mendoza usa Cuyo; Cordoba usa Pampeana.

## Instalacion inicial

Abrir PowerShell en la carpeta del proyecto:

```powershell
cd "C:\Users\corebi\Documents\Calculadora Inflacion"
```

Crear un entorno virtual:

```powershell
python -m venv .venv
```

Activarlo:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

## Como abrir el dashboard

Con el entorno virtual activado:

```powershell
streamlit run app.py
```

Streamlit va a mostrar una URL local parecida a:

```text
http://localhost:8501
```

Abrila en el navegador. Si el puerto `8501` esta ocupado, Streamlit usa otro y lo informa en la consola.

## Uso mensual recomendado

INDEC suele actualizar cerca del dia 15. Ese dia, o unos dias despues:

1. Abrir PowerShell en el proyecto.
2. Activar el entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Forzar descarga de datos oficiales:

```powershell
python scripts/update_data.py --force
```

4. Mirar la linea:

```text
Ultimo periodo disponible: AAAA-MM
```

Si esperabas mayo 2026 y todavia dice `2026-04`, INDEC aun no actualizo los CSV o la publicacion disponible todavia corresponde a abril.

5. Abrir la app:

```powershell
streamlit run app.py
```

Tambien podes actualizar desde el boton `Actualizar datos INDEC` en la barra lateral del dashboard.

## Pestaña Calculadora

Sirve para calcular IPC entre dos meses.

Campos:

- `Nivel de detalle`: `General y divisiones` para nivel general, bienes, servicios y divisiones principales. `Aperturas detalladas` para rubros mas especificos.
- `Region`: Nacional, GBA, Pampeana, Noreste, Noroeste, Cuyo o Patagonia.
- `Categoria`: nivel general o categoria IPC.
- `Monto a actualizar`: opcional. Si pones 100.000, la app calcula cuanto equivale al periodo final.
- `Periodo inicial`: mes base.
- `Periodo final`: mes limite.

La app devuelve:

- variacion acumulada;
- factor de actualizacion;
- tasa mensual equivalente;
- monto actualizado;
- grafico del tramo;
- tabla con indice, variacion mensual oficial e interanual oficial.
- variacion desde inicio del anio;
- variacion del trimestre calendario;
- variaciones moviles de los ultimos 2 a 11 meses.

Formula usada:

```text
IPC acumulado = (Indice final / Indice inicial - 1) * 100
Monto actualizado = Monto original * (Indice final / Indice inicial)
```

Ejemplo: si elegis `2024-01` a `2024-04`, calcula la inflacion acumulada entre esos dos indices, aunque INDEC no la publique como "trimestral" en una tabla separada.

## Pestaña Dashboard mensual

Muestra la foto del ultimo periodo disponible:

- ultimo mes cargado;
- IPC mensual del nivel general;
- IPC interanual;
- ranking de categorias que mas subieron;
- comparacion interanual por region.

Es la primera pantalla a mirar cuando sale un nuevo dato.

## Pestaña Comparador

Sirve para comparar regiones, provincias aproximadas y categorias.

Ejemplos utiles:

- Nacional vs GBA vs Cuyo para `Nivel general`;
- Mendoza, Cordoba y Chaco usando sus regiones INDEC aproximadas;
- Nacional vs Patagonia para `Transporte`;
- `Alimentos`, `Transporte` y `Salud` dentro de la misma region;
- varias regiones contra varias categorias al mismo tiempo.

La linea arranca en 0% en el periodo inicial y muestra la variacion acumulada de cada serie. Debajo del grafico hay una tabla resumen con indice inicial, indice final, variacion acumulada, factor y tasa mensual equivalente.

## Pestaña Mi IPC

Permite armar una canasta propia.

1. Elegir region o provincia aproximada.
2. Cargar pesos por division. No hace falta que sumen 100; la app normaliza.
3. Elegir periodo inicial y final.
4. Ver `Mi IPC estimado`.

Ejemplo:

- alimentos: 35;
- vivienda: 30;
- transporte: 15;
- salud: 10;
- educacion: 10.

La app pondera la variacion de cada categoria segun esos pesos.

Importante: esto es una estimacion por divisiones IPC, no reemplaza una medicion exacta de consumo individual.

## Pestaña Explorador

Muestra la serie completa para un nivel de detalle, region y categoria.

Desde ahi podes:

- revisar indices historicos;
- ver variacion mensual e interanual oficial;
- descargar la serie filtrada como CSV.

## Pestaña Datos

Muestra control de cobertura:

- fuente interna usada por INDEC;
- region;
- primer periodo disponible;
- ultimo periodo disponible;
- cantidad de series.

Usala para verificar rapidamente si una region o nivel de detalle esta cargado.

## Comandos utiles

Actualizar cache local:

```powershell
python scripts/update_data.py --force
```

Ese comando tambien informa cual es el ultimo Excel mensual detectado y hasta que periodo llegan sus datos.

Actualizar y exportar base normalizada:

```powershell
python scripts/update_data.py --force --export
```

Correr tests:

```powershell
python -m unittest discover -s tests -v
```

## Estructura del proyecto

```text
app.py                    Dashboard Streamlit
src/indec_loader.py       Descarga y normaliza datos oficiales
src/ipc_calculator.py     Motor de calculo IPC
src/regions.py            Regiones INDEC y provincia -> region
scripts/update_data.py    Actualizacion mensual por consola
tests/                    Tests unitarios del motor
data/cache/               Cache local de CSV oficiales
outputs/                  Exportaciones generadas
```

## Limitaciones conocidas

- INDEC publica IPC nacional y regional, no provincial puro en estas fuentes.
- La asignacion por provincia es aproximada y usa la region estadistica INDEC.
- Si INDEC cambia nombres de columnas o formato de CSV, hay que ajustar `src/indec_loader.py`.
- `Aperturas` puede tener menos cobertura que `Divisiones` para algunas combinaciones.
