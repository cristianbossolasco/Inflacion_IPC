import unittest

import pandas as pd

from src.ipc_calculator import calcular_mi_ipc, calcular_variacion, enriquecer_variaciones, meses_entre


class IpcCalculatorTest(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame(
            [
                {"fuente": "Divisiones", "region": "Nacional", "categoria": "Nivel general", "periodo_label": "2024-01", "indice": 100.0},
                {"fuente": "Divisiones", "region": "Nacional", "categoria": "Nivel general", "periodo_label": "2024-02", "indice": 110.0},
                {"fuente": "Divisiones", "region": "Nacional", "categoria": "Nivel general", "periodo_label": "2024-03", "indice": 121.0},
                {"fuente": "Divisiones", "region": "Nacional", "categoria": "Alimentos", "periodo_label": "2024-01", "indice": 200.0},
                {"fuente": "Divisiones", "region": "Nacional", "categoria": "Alimentos", "periodo_label": "2024-03", "indice": 220.0},
                {"fuente": "Divisiones", "region": "Nacional", "categoria": "Transporte", "periodo_label": "2024-01", "indice": 100.0},
                {"fuente": "Divisiones", "region": "Nacional", "categoria": "Transporte", "periodo_label": "2024-03", "indice": 130.0},
            ]
        )

    def test_meses_entre(self):
        self.assertEqual(meses_entre("2024-01", "2024-03"), 2)

    def test_calcular_variacion(self):
        result = calcular_variacion(self.df, "Divisiones", "Nacional", "Nivel general", "2024-01", "2024-03", 1000)
        self.assertAlmostEqual(result.variacion_pct, 21.0)
        self.assertAlmostEqual(result.factor, 1.21)
        self.assertAlmostEqual(result.monto_actualizado, 1210.0)

    def test_mi_ipc(self):
        variacion, detalle = calcular_mi_ipc(
            self.df,
            "Nacional",
            {"Alimentos": 70, "Transporte": 30},
            "2024-01",
            "2024-03",
        )
        self.assertAlmostEqual(variacion, 16.0)
        self.assertEqual(len(detalle), 2)

    def test_enriquecer_variaciones(self):
        serie = pd.DataFrame(
            [
                {"periodo_label": "2023-12", "indice": 100.0},
                {"periodo_label": "2024-01", "indice": 110.0},
                {"periodo_label": "2024-02", "indice": 121.0},
                {"periodo_label": "2024-03", "indice": 133.1},
                {"periodo_label": "2024-04", "indice": 146.41},
                {"periodo_label": "2024-05", "indice": 161.051},
                {"periodo_label": "2024-06", "indice": 177.1561},
                {"periodo_label": "2024-07", "indice": 194.87171},
                {"periodo_label": "2024-08", "indice": 214.358881},
                {"periodo_label": "2024-09", "indice": 235.7947691},
                {"periodo_label": "2024-10", "indice": 259.37424601},
                {"periodo_label": "2024-11", "indice": 285.311670611},
            ]
        )
        out = enriquecer_variaciones(serie)
        abril = out[out["periodo_label"] == "2024-04"].iloc[0]
        self.assertAlmostEqual(abril["var_ultimos_2_meses"], 21.0)
        self.assertAlmostEqual(abril["var_ultimos_3_meses"], 33.1)
        self.assertAlmostEqual(abril["var_desde_inicio_anio"], 46.41)
        self.assertAlmostEqual(abril["var_trimestre_calendario"], 10.0)
        noviembre = out[out["periodo_label"] == "2024-11"].iloc[0]
        for meses in range(2, 12):
            self.assertIn(f"var_ultimos_{meses}_meses", out.columns)
        self.assertAlmostEqual(noviembre["var_ultimos_11_meses"], 185.311670611)


if __name__ == "__main__":
    unittest.main()
