import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "experiments")); sys.path.insert(0, str(RAIZ / "src"))
from entrelazamiento_saturacion_clifford import entropia_incremental, tiempo_de_saturacion


class TestEntropiaIncremental(unittest.TestCase):
    def test_no_decrece_localmente_mas_de_lo_posible(self):
        # S_A(t) es un entero >= 0, y nunca puede subir en mas de 1 por
        # puerta (una sola puerta Clifford cambia la entropia en como
        # mucho +-1 -- hecho estandar del formalismo estabilizador).
        valores = entropia_incremental(6, 30, [0, 1, 2], semilla=1)
        self.assertTrue(all(v >= 0 for v in valores))
        anteriores = [0] + valores[:-1]
        for previo, actual in zip(anteriores, valores):
            self.assertLessEqual(abs(actual - previo), 1)

    def test_nunca_excede_la_cota(self):
        n, tam_a = 8, 4
        cota = min(tam_a, n - tam_a)
        valores = entropia_incremental(n, 100, list(range(tam_a)), semilla=2)
        self.assertTrue(all(v <= cota for v in valores))

    def test_reproducible_con_la_misma_semilla(self):
        v1 = entropia_incremental(6, 20, [0, 1, 2], semilla=42)
        v2 = entropia_incremental(6, 20, [0, 1, 2], semilla=42)
        self.assertEqual(v1, v2)


class TestTiempoDeSaturacion(unittest.TestCase):
    def test_satura_dentro_de_profundidad_generosa(self):
        # n pequeno, profundidad generosa: debe saturar casi siempre
        t = tiempo_de_saturacion(4, profundidad_max=200, semilla=7)
        self.assertIsNotNone(t)

    def test_devuelve_none_si_profundidad_es_cero(self):
        self.assertIsNone(tiempo_de_saturacion(4, profundidad_max=0, semilla=1))


if __name__ == "__main__":
    unittest.main()
