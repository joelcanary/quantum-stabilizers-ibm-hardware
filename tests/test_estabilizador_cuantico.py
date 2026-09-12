import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from stabilizer_exact import (
    entropia_entrelazamiento_exacta, ghz_state, cluster_state_1d,
    circuito_clifford_aleatorio, verificar_cota_area_law, _rango_gf2,
    distancia_codigo_estabilizador, codigo_steane, codigo_5_qubits, codigo_shor,
    TRINITY_PROVIDE,
)
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, partial_trace, entropy


class TestRangoGF2(unittest.TestCase):
    def test_filas_independientes(self):
        self.assertEqual(_rango_gf2([[1, 0], [0, 1]]), 2)

    def test_filas_dependientes(self):
        self.assertEqual(_rango_gf2([[1, 1], [1, 1]]), 1)

    def test_fila_de_ceros_no_cuenta(self):
        self.assertEqual(_rango_gf2([[1, 0], [0, 0], [0, 1]]), 2)


class TestCasosDeLibro(unittest.TestCase):
    # Valores estandar de teoria de informacion cuantica (Nielsen-Chuang,
    # cap. entrelazamiento); recalculados independientemente con la
    # entropia de von Neumann de Qiskit (Statevector+partial_trace) antes
    # de fijarlos aqui.
    def test_producto_sin_entrelazamiento(self):
        qc = QuantumCircuit(2)
        self.assertEqual(entropia_entrelazamiento_exacta(qc, [0]), 0)

    def test_bell_maximamente_entrelazado(self):
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        self.assertEqual(entropia_entrelazamiento_exacta(qc, [0]), 1)

    def test_ghz_corte_de_un_qubit(self):
        for n in (2, 3, 5, 8):
            self.assertEqual(entropia_entrelazamiento_exacta(ghz_state(n), [0]), 1, f"n={n}")

    def test_cluster_1d_area_law(self):
        # entropia constante = 1 en TODO corte del bulk, independiente de n
        for n in (4, 6, 8):
            qc = cluster_state_1d(n)
            for k in range(1, n):
                e = entropia_entrelazamiento_exacta(qc, list(range(k)))
                self.assertEqual(e, 1, f"n={n}, corte en {k}")


class TestCoincideConVonNeumannFloat(unittest.TestCase):
    """La formula GF(2) exacta debe coincidir con la entropia de von Neumann
    de Qiskit (ruta independiente, floats) en circuitos Clifford aleatorios."""

    def test_20_circuitos_aleatorios(self):
        for semilla in range(20):
            qc = circuito_clifford_aleatorio(5, 20, semilla=semilla)
            import random
            rng = random.Random(semilla + 1000)
            A = rng.sample(range(5), rng.randint(1, 4))
            exacto = entropia_entrelazamiento_exacta(qc, A)
            sv = Statevector.from_instruction(qc)
            rho = partial_trace(sv, [q for q in range(5) if q not in A])
            flotante = entropy(rho, base=2)
            self.assertAlmostEqual(exacto, flotante, places=6, msg=f"semilla={semilla}, A={A}")


class TestCotaAreaLaw(unittest.TestCase):
    def test_verificacion_rapida_sin_excepciones(self):
        r = verificar_cota_area_law(n_max=6, profundidad=15, circuitos_por_n=10, semilla=1)
        self.assertTrue(r["resiste"])
        self.assertEqual(r["excepciones"], [])


class TestDistanciaCodigoEstabilizador(unittest.TestCase):
    # Distancias estandar de la literatura de codigos cuanticos
    # (Nielsen-Chuang cap. 10; Gottesman 1997). Recalculadas aqui por
    # busqueda exhaustiva GF(2), no copiadas sin verificar.
    def test_steane_distancia_3(self):
        generadores, n = codigo_steane()
        self.assertEqual(distancia_codigo_estabilizador(generadores, n), 3)

    def test_5_qubits_distancia_3(self):
        generadores, n = codigo_5_qubits()
        self.assertEqual(distancia_codigo_estabilizador(generadores, n), 3)

    def test_shor_distancia_3(self):
        generadores, n = codigo_shor()
        self.assertEqual(distancia_codigo_estabilizador(generadores, n, peso_maximo=4), 3)

    def test_generadores_que_no_conmutan_se_rechazan(self):
        # X en el qubit 0 y Z en el qubit 0 anticonmutan: no es un
        # estabilizador valido, debe rechazarse explicito, no dar un
        # resultado silencioso.
        generadores = [((1, 0), (0, 0)), ((0, 0), (1, 0))]
        with self.assertRaises(ValueError):
            distancia_codigo_estabilizador(generadores, 2)


class TestTrinityProvide(unittest.TestCase):
    def test_declara_dominio_y_funciones(self):
        self.assertEqual(TRINITY_PROVIDE["dominio"], "estabilizador_cuantico")  # nombre historico del dominio
        self.assertIn("entropia_entrelazamiento_exacta", TRINITY_PROVIDE["funciones"])


if __name__ == "__main__":
    unittest.main()
