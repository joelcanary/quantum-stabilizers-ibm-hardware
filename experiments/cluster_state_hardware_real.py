#!/usr/bin/env python3
"""EXPERIMENTO: los generadores estabilizadores del estado cluster 1D
(symbolica.plugins.estabilizador_cuantico.cluster_state_1d), medidos en
hardware cuantico real, para n=4.

Esta NO es una entrada del registro de hallazgos (P-Lean/P/V/H/X) por la
misma razon que research/exploraciones/ghz_hardware_real.py: es una
medicion fisica con ruido real, no una demostracion matematica.

DEFINICION: el estado cluster sobre un grafo lineal 0-1-2-...-(n-1) esta
estabilizado por n generadores, uno por qubit:
    K_0     = X_0 Z_1
    K_i     = Z_{i-1} X_i Z_{i+1}   para 0 < i < n-1
    K_{n-1} = Z_{n-2} X_{n-1}

Por definicion de estado estabilizador, K_i|psi> = |psi> para cada i, asi
que <K_i> = 1 EXACTAMENTE para el estado ideal. Esta es la propiedad
elemental sobre la que se apoya toda la maquinaria del Teorema de
Gottesman-Knill usada en el resto de symbolica/plugins/estabilizador_cuantico.py
y verificada en tests/test_estabilizador_cuantico.py; aqui no se prueba
de nuevo -- se comprueba cuanto la respeta el hardware real.

METODO: para medir <K_i>, se rota el qubit "X" del generador a la base Z
(puerta H antes de medir) y se mide todo el mundo en base computacional.
Por cada shot, el signo es el producto de (-1)^bit sobre los qubits que
aparecen en el soporte del generador; <K_i> es el promedio de esos signos.
Verificado ANTES de usar hardware real: la logica de signo y de orden de
bits reproduce exacto 1.0000 contra una simulacion perfecta (Statevector,
tanto valor esperado analitico como muestreo sin ruido) para los 4
generadores de n=4 -- ver el historial de este archivo / la sesion del
2026-07-29.

EXPERIMENTO REAL (registrado, no reproducible a voluntad -- el hardware
cambia con el tiempo):
    Backend:  ibm_kingston (156 qubits, IBM Quantum Platform)
    Shots:    4096 por generador
    Fecha:    2026-07-29
    Los 4 circuitos se transpilaron al MISMO mapeo fisico (logico i ->
    fisico i, para i=0,1,2,3) -- el mismo mapeo que se uso en las
    corridas de GHZ(3) de ghz_hardware_real.py, incluyendo el mismo qubit
    fisico #1 con error de lectura publicado del 23.4% (vs mediana 0.9%
    en todo el chip).

RESULTADO Y EL PATRON QUE EXPLICA (esto es el hallazgo, no un detalle):
    K_0  soporte {0:X, 1:Z}        <K> = 0.8374  (exacto: 1.0000)
    K_1  soporte {0:Z, 1:X, 2:Z}   <K> = 0.8965  (exacto: 1.0000)
    K_2  soporte {1:Z, 2:X, 3:Z}   <K> = 0.9136  (exacto: 1.0000)
    K_3  soporte {2:Z, 3:X}        <K> = 0.9697  (exacto: 1.0000)

    K_0, K_1 y K_2 involucran el qubit fisico #1 (el de 23.4% de error de
    lectura). K_3 es el UNICO generador que NO lo toca -- y es, con
    diferencia, el mas cercano al valor exacto. Esto corrobora, con un
    experimento distinto (valores esperados de estabilizadores, no solo
    conteo de bitstrings de GHZ), la misma conclusion de
    ghz_hardware_real.py: un qubit fisico especifico con mal calibrado
    domina el error observado, mas que el numero de qubits o puertas
    involucradas en el generador.

Reproducir la conexion (requiere qiskit-ibm-runtime y credenciales propias,
NO incluidas aqui):

    python research/exploraciones/cluster_state_hardware_real.py
"""
from fractions import Fraction


def generador_soporte(i, n):
    """Soporte exacto {qubit: 'X'|'Z'} del generador estabilizador K_i del
    estado cluster lineal de n qubits (grafo 0-1-2-...-(n-1))."""
    soporte = {i: "X"}
    if i - 1 >= 0:
        soporte[i - 1] = "Z"
    if i + 1 <= n - 1:
        soporte[i + 1] = "Z"
    return soporte


def involucra_qubit(i, n, qubit_fisico):
    """Si el generador K_i (n qubits, mapeo logico=fisico identidad) toca
    un qubit fisico dado."""
    return qubit_fisico in generador_soporte(i, n)


# --- Registro del experimento real (dato historico, no recalculable) -------

N = 4

EXPERIMENTOS_REALES = [
    {
        "generator": 0, "job_id": "d9kveiibr2fc73e7v8k0", "shots": 4096,
        "counts": {"0111": 472, "1000": 436, "1011": 419, "1111": 412,
                   "0011": 529, "0000": 559, "0100": 469, "1100": 467,
                   "0101": 66, "1001": 56, "1010": 22, "1101": 55,
                   "0010": 29, "0001": 60, "0110": 25, "1110": 20},
    },
    {
        "generator": 1, "job_id": "d9kvfcibr2fc73e7vacg", "shots": 4096,
        "counts": {"0011": 513, "1000": 477, "1011": 476, "0110": 450,
                   "0000": 535, "0101": 526, "1110": 447, "1101": 460,
                   "0111": 23, "0010": 10, "1111": 27, "1100": 16,
                   "0001": 57, "0100": 24, "1001": 50, "1010": 5},
    },
    {
        "generator": 2, "job_id": "d9kvgr0ii2cc73egprug", "shots": 4096,
        "counts": {"0111": 487, "1100": 483, "0000": 500, "0001": 546,
                   "1010": 431, "1101": 523, "0110": 484, "1011": 465,
                   "0100": 28, "1110": 5, "0101": 50, "1001": 31,
                   "1000": 28, "0010": 9, "0011": 22, "1111": 4},
    },
    {
        "generator": 3, "job_id": "d9kvhg0ii2cc73egpsvg", "shots": 4096,
        "counts": {"0001": 586, "1110": 460, "0000": 506, "0011": 530,
                   "1100": 478, "1111": 483, "0010": 463, "1101": 528,
                   "0100": 7, "1000": 10, "0111": 8, "0101": 13,
                   "0110": 6, "1011": 7, "1010": 7, "1001": 4},
    },
]

QUBIT_FISICO_MALO = 1  # error de lectura publicado 23.4% ese dia


def expval_medido(experimento):
    """<K_i> medido, exacto como Fraction, a partir de las cuentas
    registradas. Qiskit ordena el bitstring impreso como q_{n-1}...q_0
    (MSB primero), por eso se invierte antes de indexar por qubit."""
    i = experimento["generator"]
    soporte = generador_soporte(i, N)
    total = experimento["shots"]
    suma = 0
    for bitstring, n_shots in experimento["counts"].items():
        bits = bitstring[::-1]
        signo = 1
        for q in soporte:
            b = int(bits[q])
            signo *= (1 - 2 * b)
        suma += signo * n_shots
    return Fraction(suma, total)


def resumen():
    print("Estado cluster (n=4): <K_i> exacto vs hardware real "
          "(ibm_kingston, 2026-07-29)\n")
    for e in EXPERIMENTOS_REALES:
        i = e["generator"]
        ev = expval_medido(e)
        toca_malo = involucra_qubit(i, N, QUBIT_FISICO_MALO)
        print(f"  K_{i}  soporte={generador_soporte(i, N)}  "
              f"<K>={float(ev):.4f} ({ev})  exacto=1  "
              f"toca qubit#{QUBIT_FISICO_MALO} (mal calibrado): {toca_malo}")


if __name__ == "__main__":
    resumen()
