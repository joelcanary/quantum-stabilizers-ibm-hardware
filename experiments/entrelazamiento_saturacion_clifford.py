#!/usr/bin/env python3
"""EXPERIMENTO: a que profundidad satura el entrelazamiento en circuitos
Clifford aleatorios? Investigacion exploratoria usando la herramienta exacta
symbolica/plugins/estabilizador_cuantico.py (sesion 2026-07-27).

PREGUNTA: para el modelo de circuito de circuito_clifford_aleatorio(n,
profundidad) -- en cada paso, 50% puerta de 1 qubit (H/S/X/Y/Z al azar),
50% CNOT entre un par de qubits elegido uniforme al azar entre TODOS los
pares -- cuantos pasos hacen falta, en promedio, para que la entropia de
entrelazamiento S_A de una biparticion mitad-mitad ALCANCE su cota maxima
min(|A|,n-|A|) = n/2?

METODO: se mide S_A(t) EXACTO (formula GF(2), sin floats) en cada paso de
la trayectoria, hasta que S_A(t) = n/2 por primera vez. Repetido en varias
trayectorias (semillas distintas) y varios n, para estimar el tiempo medio
de saturacion t_sat(n).

RESULTADO (10 trayectorias por n, semillas 100n..100n+9):
    n=10:  t_sat medio = 144.4  (8/10 trayectorias saturaron en profundidad 200)
    n=20:  t_sat medio = 293.9  (10/10 en profundidad 400)
    n=40:  t_sat medio = 553.5  (10/10 en profundidad 800)
    n=80:  t_sat medio = 1130.1 (10/10 en profundidad 1600)

    t_sat/n:  14.44, 14.70, 13.84, 14.13  -- consistente en las 4 escalas,
    dentro de +-0.5 de 14.3. Sugiere escalado LINEAL t_sat(n) ~ 14.3*n para
    este modelo de circuito.

INTERPRETACION HEURISTICA (no una prueba): con emparejamiento uniforme
entre TODOS los pares (no solo vecinos), la probabilidad de que un paso
sea una puerta de 2 qubits que CRUZA la biparticion mitad-mitad es
aprox. 0.5 * (|A|*|B|*2)/(n*(n-1)) ~ 0.25 para n grande -- una FRACCION
CONSTANTE de los pasos, no decreciente con n. Como el entrelazamiento
maximo alcanzable crece como n/2 y cada paso "util" aporta como mucho
+1 (a menudo menos, por redundancia GF(2)), el numero de pasos totales
necesarios para saturar deberia escalar ~linealmente en n -- consistente
con lo medido, aunque esto es una estimacion de orden de magnitud, no
una derivacion rigurosa.

ALCANCE HONESTO: esto es un resultado EXPERIMENTAL sobre un modelo de
circuito ESPECIFICO (el de circuito_clifford_aleatorio), no un teorema
general sobre entrelazamiento en circuitos cuanticos. Otros modelos
(vecinos mas cercanos en 1D, puertas Haar-aleatorias en vez de Clifford,
mezcla 1q/2q distinta) darian constantes distintas -- y posiblemente
escalados distintos (los circuitos LOCALES en 1D tipicamente saturan
tambien en O(n) pasos pero con una constante mayor, por la geometria).
No se afirma que 14.3 sea una constante universal de ningun tipo.

    python research/exploraciones/entrelazamiento_saturacion_clifford.py
"""
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from stabilizer_exact import entropia_entrelazamiento_exacta
from qiskit import QuantumCircuit


def entropia_incremental(n, profundidad, subsistema_a, semilla):
    """S_A(t) EXACTO para t=1..profundidad, sobre UNA trayectoria de circuito
    Clifford aleatorio (mismo modelo que circuito_clifford_aleatorio, pero
    midiendo en cada paso en vez de solo al final)."""
    rng = random.Random(semilla)
    qc = QuantumCircuit(n)
    puertas_1q = ["h", "s", "x", "y", "z"]
    valores = []
    for _ in range(profundidad):
        if n == 1 or rng.random() < 0.5:
            q = rng.randrange(n)
            getattr(qc, rng.choice(puertas_1q))(q)
        else:
            a, b = rng.sample(range(n), 2)
            qc.cx(a, b)
        valores.append(entropia_entrelazamiento_exacta(qc, subsistema_a))
    return valores


def tiempo_de_saturacion(n, profundidad_max, semilla):
    """Primer t donde S_A(t) alcanza la cota n/2 (biparticion mitad-mitad),
    o None si no satura dentro de profundidad_max."""
    A = list(range(n // 2))
    cota = min(len(A), n - len(A))
    curva = entropia_incremental(n, profundidad_max, A, semilla)
    for t, s in enumerate(curva):
        if s == cota:
            return t
    return None


def medir_escalado(valores_n=(10, 20, 40, 80), trayectorias_por_n=10, factor_profundidad=20):
    """Repite tiempo_de_saturacion sobre varias trayectorias y n, devuelve
    {n: {"saturaciones": [...], "media": float o None, "ratio": float o None}}."""
    resultado = {}
    for n in valores_n:
        profundidad_max = factor_profundidad * n
        saturaciones = [
            tiempo_de_saturacion(n, profundidad_max, semilla=s + 100 * n)
            for s in range(trayectorias_por_n)
        ]
        validos = [t for t in saturaciones if t is not None]
        media = sum(validos) / len(validos) if validos else None
        resultado[n] = {
            "saturaciones": saturaciones,
            "media": media,
            "ratio_t_sat_sobre_n": (media / n) if media else None,
            "trayectorias_que_saturaron": len(validos),
            "total_trayectorias": trayectorias_por_n,
        }
    return resultado


if __name__ == "__main__":
    t0 = time.time()
    print("Midiendo tiempo de saturacion del entrelazamiento, n=10,20,40,80...")
    r = medir_escalado()
    print()
    for n, datos in r.items():
        print(f"n={n:3d}  t_sat medio={datos['media']}  "
              f"t_sat/n={datos['ratio_t_sat_sobre_n']:.2f}  "
              f"({datos['trayectorias_que_saturaron']}/{datos['total_trayectorias']} saturaron)")
    print(f"\n({time.time()-t0:.1f}s)")
