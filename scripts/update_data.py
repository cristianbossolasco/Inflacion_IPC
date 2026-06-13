from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.indec_loader import buscar_ultimo_informe_excel, cargar_todo, ultimo_periodo_disponible
from src.config import OUTPUT_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Actualiza datos oficiales de IPC INDEC.")
    parser.add_argument("--force", action="store_true", help="Descarga nuevamente los CSV oficiales.")
    parser.add_argument("--export", action="store_true", help="Exporta la base normalizada a outputs/ipc_normalizado.csv.")
    args = parser.parse_args()

    df = cargar_todo(force=args.force, incluir_aperturas=True)
    ultimo = ultimo_periodo_disponible(df)

    print(f"Filas cargadas: {len(df):,}".replace(",", "."))
    print(f"Ultimo periodo disponible: {ultimo}")
    informe = buscar_ultimo_informe_excel(force=args.force)
    if informe:
        print(f"Ultimo informe Excel disponible: {informe.informe}")
        print(f"Datos del informe Excel hasta: {informe.ultimo_periodo_datos}")
        print(f"URL informe Excel: {informe.url}")
    print()
    print("Series por fuente y region:")
    print(df.groupby(["fuente", "region"])["categoria"].nunique().to_string())

    if args.export:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output = OUTPUT_DIR / "ipc_normalizado.csv"
        df.to_csv(output, index=False, encoding="utf-8")
        print()
        print(f"Archivo exportado: {output}")


if __name__ == "__main__":
    main()
