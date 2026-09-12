#!/usr/bin/env python3
"""TRINITY: HERRAMIENTA ESTABILIZADORES CUANTICOS -- entropia de entrelazamiento
exacta, sin floats, via el formalismo estabilizador (teorema de Gottesman-Knill).

POR QUE ESTO Y NO "QISKIT EN GENERAL": la simulacion cuantica general (Qiskit,
amplitudes complejas, Statevector) usa numpy complex128 -- viola la Regla R1
de TRINITY (nunca floats) exactamente igual que lattice QCD viola el metodo
para Yang-Mills (ver usecases/dominios.py, entrada 'yang_mills': "estocastico
y aproximado, lo contrario exacto de la metodologia de TRINITY"). Verificado
directamente esta sesion: incluso un Hadamard de 1 qubit da 0.70710678...
(aproximacion de 1/sqrt(2)), nunca exacto.

PERO los circuitos Clifford (H, S, CNOT, mediciones en base computacional)
son un caso especial genuinamente exacto: el estado se representa por un
tableau binario (GF(2)) de generadores estabilizadores, sin amplitudes
continuas. Este es el contenido real del teorema de Gottesman-Knill.

OBSERVABLE EXACTO: la entropia de entrelazamiento de un estado estabilizador
sobre una biparticion A|B es SIEMPRE un entero (en unidades de log 2) --
nunca irracional, nunca aproximado. Formula (Fattal, Cubitt, Kitaev, Mor,
Vishwanath, "Entanglement in the stabilizer formalism", 2004):

    S_A = rango_GF(2)(M_A) - |A|

donde M_A es la submatriz del tableau (n generadores x 2|A| columnas, las
componentes X y Z de cada qubit en A), rango sobre GF(2). Implementado aqui
con eliminacion Gaussiana binaria pura (XOR), sin numpy ni floats.

VERIFICADO (no solo afirmado): la formula se contrasto contra la entropia de
von Neumann de Qiskit (Statevector + partial_trace, ruta EXACTA en el sentido
de que S=0,1 sale limpio para estos casos, aunque internamente use floats)
en 4 casos de libro (producto, Bell, GHZ) y 30 circuitos Clifford aleatorios
(n=5, 20 puertas cada uno): 30/30 coinciden exacto. Ver tests/test_estabilizador_cuantico.py.
"""
import random
import sys
from itertools import combinations, product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Clifford
    QISKIT_DISPONIBLE = True
    _ERROR_IMPORTACION = None
except ImportError as _e:  # pragma: no cover (segun entorno)
    QISKIT_DISPONIBLE = False
    _ERROR_IMPORTACION = str(_e)


def _requiere_qiskit():
    if not QISKIT_DISPONIBLE:
        raise RuntimeError(
            f"qiskit no esta instalado o no se pudo importar ({_ERROR_IMPORTACION}). "
            "Instalalo con 'pip install qiskit' para habilitar el formalismo "
            "estabilizador. Sin el, este observable no puede medirse: no se "
            "inventa un valor.")


def _rango_gf2_con_base(filas):
    """Rango de una matriz booleana sobre GF(2) (eliminacion Gaussiana pura,
    XOR bit a bit, sin numpy ni floats), y la base reducida por filas (para
    pruebas de pertenencia al espacio generado)."""
    filas = [list(fila) for fila in filas]
    n_col = len(filas[0]) if filas else 0
    pivote = 0
    for col in range(n_col):
        fila_pivote = next((r for r in range(pivote, len(filas)) if filas[r][col]), None)
        if fila_pivote is None:
            continue
        filas[pivote], filas[fila_pivote] = filas[fila_pivote], filas[pivote]
        for r in range(len(filas)):
            if r != pivote and filas[r][col]:
                filas[r] = [a ^ b for a, b in zip(filas[r], filas[pivote])]
        pivote += 1
    return pivote, filas[:pivote]


def _rango_gf2(filas):
    """Solo el rango (ver _rango_gf2_con_base)."""
    return _rango_gf2_con_base(filas)[0]


def entropia_entrelazamiento_exacta(qc, subsistema_a):
    """Entropia de entrelazamiento EXACTA (entero, en bits/ebits) del estado
    estabilizador producido por qc, para la biparticion subsistema_a | resto.

    qc: QuantumCircuit compuesto SOLO de puertas Clifford (H, S, X, Y, Z, CX,
        CZ, CY, SWAP...). Si qc contiene una puerta no-Clifford (p.ej. T),
        Clifford(qc) lanzara un error -- correctamente, porque para esos
        circuitos el estado YA NO es un estado estabilizador y esta formula
        no aplica (dejaria de ser exacta).
    subsistema_a: lista de indices de qubit en la region A.

    Devuelve un entero >= 0. Nunca un float.
    """
    _requiere_qiskit()
    cliff = Clifford(qc)
    x, z = cliff.stab_x, cliff.stab_z
    n = qc.num_qubits
    filas = [
        [v for q in subsistema_a for v in (bool(x[i][q]), bool(z[i][q]))]
        for i in range(n)
    ]
    return _rango_gf2(filas) - len(subsistema_a)


def ghz_state(n):
    """Circuito Clifford que prepara el estado GHZ de n qubits."""
    _requiere_qiskit()
    qc = QuantumCircuit(n)
    qc.h(0)
    for q in range(n - 1):
        qc.cx(q, q + 1)
    return qc


def cluster_state_1d(n):
    """Circuito Clifford que prepara el estado cluster (grafo lineal) de n qubits."""
    _requiere_qiskit()
    qc = QuantumCircuit(n)
    for q in range(n):
        qc.h(q)
    for q in range(n - 1):
        qc.cz(q, q + 1)
    return qc


def circuito_clifford_aleatorio(n, profundidad, semilla=None):
    """Circuito Clifford aleatorio de n qubits y 'profundidad' puertas.
    Reproducible si se da 'semilla' (random.Random propio, no afecta el
    estado global de random)."""
    _requiere_qiskit()
    rng = random.Random(semilla)
    qc = QuantumCircuit(n)
    puertas_1q = ["h", "s", "x", "y", "z"]
    for _ in range(profundidad):
        if n == 1 or rng.random() < 0.5:
            q = rng.randrange(n)
            getattr(qc, rng.choice(puertas_1q))(q)
        else:
            a, b = rng.sample(range(n), 2)
            qc.cx(a, b)
    return qc


def verificar_cota_area_law(n_max, profundidad=20, circuitos_por_n=20, semilla=0):
    """Verifica la cota EXACTA S_A <= min(|A|, n-|A|) (teorema conocido para
    estados estabilizadores) sobre circuitos Clifford aleatorios, para n
    creciente. 0 excepciones esperado -- es un teorema, no una conjetura:
    esto es una verificacion de que la implementacion es correcta a escala,
    no una busqueda de contraejemplos a algo abierto.

    Devuelve dict con el conteo y las excepciones (vacio si todo cumple).
    """
    _requiere_qiskit()
    rng = random.Random(semilla)
    excepciones = []
    verificados = 0
    for n in range(2, n_max + 1):
        for _ in range(circuitos_por_n):
            s = rng.randrange(10**9)
            qc = circuito_clifford_aleatorio(n, profundidad, semilla=s)
            tam_a = rng.randint(1, n - 1)
            A = rng.sample(range(n), tam_a)
            entropia = entropia_entrelazamiento_exacta(qc, A)
            cota = min(len(A), n - len(A))
            verificados += 1
            if entropia > cota or entropia < 0:
                excepciones.append({"n": n, "A": A, "entropia": entropia, "cota": cota})
    return {"n_max": n_max, "verificados": verificados, "excepciones": excepciones,
            "resiste": len(excepciones) == 0}


# ─────────────────────────────────────────────────────────────────────────
# DISTANCIA DE CODIGOS ESTABILIZADORES -- segunda cantidad exacta, sin Qiskit
# (Clifford de Qiskit representa un UNITARIO n->n, apropiado para estados;
# un codigo [[n,k,d]] con k>0 logico necesita generadores explicitos y sus
# OPERADORES LOGICOS, que es geometria simplectica GF(2) directa).
#
# d = peso minimo de un operador de Pauli que CONMUTA con todos los
# generadores del estabilizador pero NO es un producto de generadores (es
# decir, un operador logico no trivial). Formalismo estandar de codigos
# cuanticos (Gottesman 1997, Nielsen-Chuang cap. 10).
# ─────────────────────────────────────────────────────────────────────────

_PAULIS_NO_IDENTIDAD = [(0, 1), (1, 0), (1, 1)]  # (x,z) para Z, X, Y


def _producto_simplectico(p1, p2):
    """<p1,p2> sobre GF(2): 0 si conmutan como operadores de Pauli, 1 si anticonmutan."""
    x1, z1 = p1
    x2, z2 = p2
    return sum((x1[i] & z2[i]) ^ (z1[i] & x2[i]) for i in range(len(x1))) % 2


def _vector_binario(p):
    x, z = p
    return tuple(x) + tuple(z)


def _en_span_gf2(vector, base_reducida):
    """vector esta en el espacio generado por base_reducida (ya reducida por filas)?"""
    v = list(vector)
    for fila in base_reducida:
        piv_col = next(i for i, b in enumerate(fila) if b)
        if v[piv_col]:
            v = [a ^ b for a, b in zip(v, fila)]
    return all(x == 0 for x in v)


def distancia_codigo_estabilizador(generadores, n, peso_maximo=None):
    """Distancia EXACTA d de un codigo estabilizador [[n, k, d]].

    generadores: lista de (x, z) -- cada uno una tupla de n bits (0/1),
        n-k generadores INDEPENDIENTES y que conmutan entre si (se verifica).
    n: numero de qubits fisicos.
    peso_maximo: corta la busqueda (por defecto n). Para codigos con
        distancia grande y n alto, esto puede ser lento (crece como
        C(n,d)*3^d) -- es busqueda exhaustiva, no un atajo aproximado.

    Devuelve el entero d, o None si no se encontro operador logico hasta
    peso_maximo (K=0, codigo trivial sin qubits logicos, o el limite era
    demasiado bajo).
    """
    for i in range(len(generadores)):
        for j in range(i + 1, len(generadores)):
            if _producto_simplectico(generadores[i], generadores[j]) != 0:
                raise ValueError(
                    f"generadores {i} y {j} no conmutan -- no son un "
                    "estabilizador valido (todo par debe conmutar)")

    _, base = _rango_gf2_con_base([_vector_binario(g) for g in generadores])
    peso_maximo = peso_maximo if peso_maximo is not None else n

    for peso in range(1, peso_maximo + 1):
        for soporte in combinations(range(n), peso):
            for combo in product(_PAULIS_NO_IDENTIDAD, repeat=peso):
                x = [0] * n
                z = [0] * n
                for idx, q in enumerate(soporte):
                    x[q], z[q] = combo[idx]
                candidato = (tuple(x), tuple(z))
                if all(_producto_simplectico(candidato, g) == 0 for g in generadores):
                    if not _en_span_gf2(_vector_binario(candidato), base):
                        return peso
    return None


def _pauli_str_a_generador(s):
    """Convierte una cadena como 'XZZXI' a (x, z)."""
    x, z = [], []
    for c in s:
        x.append(1 if c in "XY" else 0)
        z.append(1 if c in "ZY" else 0)
    return (tuple(x), tuple(z))


def codigo_steane():
    """Generadores del codigo de Steane [[7,1,3]] (CSS sobre Hamming [7,4,3])."""
    n = 7
    H = [(0, 0, 0, 1, 1, 1, 1), (0, 1, 1, 0, 0, 1, 1), (1, 0, 1, 0, 1, 0, 1)]
    generadores = [(fila, tuple([0] * n)) for fila in H]      # tipo X
    generadores += [(tuple([0] * n), fila) for fila in H]      # tipo Z
    return generadores, n


def codigo_5_qubits():
    """Generadores del codigo perfecto de 5 qubits [[5,1,3]] (rotaciones ciclicas de XZZXI)."""
    n = 5
    base = "XZZXI"
    generadores = []
    s = base
    for _ in range(4):
        generadores.append(_pauli_str_a_generador(s))
        s = s[-1] + s[:-1]
    return generadores, n


def codigo_shor():
    """Generadores del codigo de Shor [[9,1,3]]."""
    n = 9

    def zz(a, b):
        x, z = [0] * n, [0] * n
        z[a] = z[b] = 1
        return (tuple(x), tuple(z))

    def xn(qs):
        x, z = [0] * n, [0] * n
        for q in qs:
            x[q] = 1
        return (tuple(x), tuple(z))

    generadores = [zz(0, 1), zz(1, 2), zz(3, 4), zz(4, 5), zz(6, 7), zz(7, 8),
                   xn([0, 1, 2, 3, 4, 5]), xn([3, 4, 5, 6, 7, 8])]
    return generadores, n


TRINITY_PROVIDE = {
    "dominio": "estabilizador_cuantico",
    "funciones": {
        "entropia_entrelazamiento_exacta": entropia_entrelazamiento_exacta,
        "ghz_state": ghz_state,
        "cluster_state_1d": cluster_state_1d,
        "circuito_clifford_aleatorio": circuito_clifford_aleatorio,
        "verificar_cota_area_law": verificar_cota_area_law,
        "distancia_codigo_estabilizador": distancia_codigo_estabilizador,
        "codigo_steane": codigo_steane,
        "codigo_5_qubits": codigo_5_qubits,
        "codigo_shor": codigo_shor,
    },
    "descripcion": "Entropia de entrelazamiento y distancia de codigo EXACTAS "
                   "(GF(2), sin floats) para estados y codigos estabilizadores",
}


if __name__ == "__main__":
    if not QISKIT_DISPONIBLE:
        print(f"qiskit no disponible: {_ERROR_IMPORTACION}")
    else:
        print("=" * 70)
        print("TRINITY: ESTABILIZADORES CUANTICOS - ENTROPIA EXACTA")
        print("=" * 70)
        print()
        print("GHZ_n, corte en el primer qubit (esperado: 1 para todo n>=2):")
        for n in (2, 3, 5, 8):
            e = entropia_entrelazamiento_exacta(ghz_state(n), [0])
            print(f"  n={n}: S = {e}")
        print()
        print("Cluster 1D, cortes en el 'bulk' (esperado: 1, area-law):")
        for n in (4, 6, 8):
            qc = cluster_state_1d(n)
            valores = [entropia_entrelazamiento_exacta(qc, list(range(k))) for k in range(1, n)]
            print(f"  n={n}: S por corte = {valores}")
        print()
        print("Verificando cota S_A <= min(|A|,n-|A|) en circuitos Clifford "
              "aleatorios, n=2..15...")
        r = verificar_cota_area_law(15)
        print(f"  verificados: {r['verificados']}, excepciones: {len(r['excepciones'])}")
        print(f"  resiste: {r['resiste']}")
        print()
        print("Distancia de codigos estabilizadores conocidos (contra la literatura):")
        for nombre, constructor, esperado in (
            ("Steane [[7,1,3]]", codigo_steane, 3),
            ("5 qubits [[5,1,3]]", codigo_5_qubits, 3),
            ("Shor [[9,1,3]]", codigo_shor, 3),
        ):
            generadores, n = constructor()
            d = distancia_codigo_estabilizador(generadores, n)
            ok = "OK" if d == esperado else "MISMATCH"
            print(f"  {nombre}: d = {d} (esperado {esperado}) [{ok}]")
