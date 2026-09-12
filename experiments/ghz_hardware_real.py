#!/usr/bin/env python3
"""EXPERIMENTO: el estado GHZ(n) exacto, medido en hardware cuantico real,
para n=3 (x3 repeticiones), 4, 5, 6, 7 -- mas una comparacion cuantitativa
contra un modelo de ruido construido con las tasas de error que IBM
publica para el chip usado.

Esta NO es una entrada del registro de hallazgos (P-Lean/P/V/H/X). Esa
jerarquia es sobre certeza MATEMATICA (que tan bien esta demostrado un
enunciado). Una medicion en hardware real tiene ruido fisico genuino
(decoherencia, error de puerta, error de lectura) -- no es "verificado
exacto" en ningun sentido, por muy bonito que salga el numero. Es evidencia
de un tipo distinto: cuanto se aleja una maquina real de lo que la
matematica exacta predice, y cuanto se acerca (o no) un modelo de ruido
construido con los datos publicos del fabricante.

CIRCUITO: symbolica.plugins.estabilizador_cuantico.ghz_state(n) -- el mismo
circuito, sin modificar, que ya esta verificado en tests/test_estabilizador_cuantico.py
contra la formula GF(2) de entropia de entrelazamiento.

PREDICCION EXACTA (definicion del estado GHZ, no un calculo ni un ajuste):
    |GHZ(n)> = (|0^n> + |1^n>) / sqrt(2)
    P(0^n) = 1/2, P(1^n) = 1/2, P(cualquier otro resultado) = 0, exacto.

EXPERIMENTOS REALES (registrados, no reproducibles a voluntad -- el
hardware cambia con el tiempo; esto es un dato historico de ejecuciones
concretas):
    Backend:  ibm_kingston (156 qubits, IBM Quantum Platform)
    Shots:    4096 por circuito
    Fecha:    2026-07-29
    Cuenta:   instancia de pago por uso

    n=3 (run 1)  job d9kuc78ii2cc73egnv4g  leak=5.59%
    n=3 (run 2)  job d9kukujhdfks73ck7g0g  leak=5.88%
    n=3 (run 3)  job d9kul9bjf64c739iolog  leak=5.98%
    n=4          job d9kumsqbr2fc73e7tsvg  leak=6.93%
    n=5          job d9kuolabr2fc73e7tvf0  leak=8.33%
    n=6          job d9kv0tibr2fc73e7udjg  leak=11.04%
    n=7          job d9kv4ojjf64c739ipdgg  leak=11.72%

    Fuga monotona creciente con n (5.8% -> 6.9% -> 8.3% -> 11.0% -> 11.7%),
    consistente con mas puertas CNOT/CZ y mas qubits medidos acumulando
    mas error.

MODELO DE RUIDO INGENUO Y POR QUE FALLA (esto es el hallazgo interesante,
no un detalle secundario): para cada circuito transpilado realmente
enviado, se tomaron las tasas de error QUE IBM PUBLICA para cada puerta y
medicion, en los qubits fisicos exactos usados (via backend.target,
snapshot de calibracion de 2026-07-29), y se multiplicaron como si cada
error fuera independiente y siempre volteara el bit medido:

    n=3   predicho=0.7337   medido~0.94    diferencia ~+0.21
    n=4   predicho=0.7286   medido=0.9307  diferencia ~+0.20
    n=5   predicho=0.7187   medido=0.9167  diferencia ~+0.20
    n=6   predicho=0.7104   medido=0.8896  diferencia ~+0.18
    n=7   predicho=0.7025   medido=0.8828  diferencia ~+0.18

    El modelo ingenuo predice SIEMPRE peor supervivencia de la que se
    observo -- una brecha sistematica de ~18-21 puntos, estable en las 7
    corridas, no ruido aleatorio. Se descarto la explicacion facil
    (mitigacion de errores aplicada por el servicio Runtime): las
    opciones del job se mandaron vacias (sin twirling ni dynamical
    decoupling activados). La explicacion mas probable, consistente con
    fisica conocida: las tasas de error de "randomized benchmarking" que
    publica IBM miden la infidelidad TOTAL de una puerta frente al ideal
    (promediada sobre todos los tipos de error, incluyendo errores de
    fase), no la probabilidad de que ESE error en particular voltee el
    bit que se termina midiendo. El modelo ingenuo es, por tanto, un
    limite pesimista, no un predictor realista.

    Dato adicional: el qubit fisico #1, usado en las 3 corridas de n=3,
    tiene un error de lectura publicado del 23.4% -- frente a una mediana
    del 0.9% en los 156 qubits del chip (8 qubits del chip completo
    superan el 10%). Aun con ese qubit "malo" en el circuito, la fuga
    real observada fue solo 5.6-6.0%, otra confirmacion de que el error
    de lectura publicado no se traduce 1:1 en bit volteado.

EXPERIMENTO DE CONTROL (causal, no solo correlacional): si el qubit #1
malo explica la diferencia, evitarlo a proposito deberia mejorar la
fidelidad medida. Se forzo el transpilador (initial_layout explicito) a
usar una cadena distinta de qubits fisicos verificados de bajo error
(118-129-128: lectura 0.29%/0.34%/0.42%, muy por debajo de la mediana del
chip) para el mismo circuito GHZ(3), y se repitio la medicion:

    control (sin qubit malo)  job d9l04c8ii2cc73egqna0  leak=3.98%
    baseline (con qubit malo) 3 corridas                leak medio=5.82%

    Mejora real de ~1.84 puntos (la desviacion estandar del baseline es
    solo 0.20%, asi que esta diferencia no es ruido). PERO no es la caida
    dramatica hacia ~0% que se veria si el qubit malo explicara TODA la
    fuga: sigue habiendo ~4.0% de fuga incluso con los mejores qubits
    disponibles. Conclusion honesta: el qubit malo es UNA causa real y
    verificada (no solo correlacion), responsable de aproximadamente un
    tercio de la fuga observada en las corridas originales -- el resto
    (~4%, el "piso" que persiste incluso en el mejor caso) es ruido base
    del circuito que no depende de un unico qubit defectuoso.

DE DONDE SALE EL PISO DEL ~4%: aplicando el MISMO modelo de ruido ingenuo
de arriba (producto de tasas de error publicadas) al circuito de control
(qubits 118,129,128), la prediccion es 0.9853 (fuga 1.47%) -- pero lo
medido fue 0.9602 (fuga 3.98%). El modelo ingenuo aqui es DEMASIADO
OPTIMISTA (al reves que con el qubit malo, donde era demasiado
pesimista): el sesgo del modelo cambia de signo segun la calidad del
qubit. Explicacion mas probable: el modelo ingenuo solo multiplica
errores POR OPERACION (puerta, medicion); nunca modela la decoherencia
acumulada mientras el qubit permanece "vivo" durante todo el circuito.
Estimacion aproximada: sumando las duraciones publicadas de cada
puerta/medicion del circuito real enviado (~6.84 microsegundos en serie)
y dividiendo por el T1 mas corto de los tres qubits (qubit 128, T1=230us),
sale una probabilidad de decoherencia de ~2.97% -- muy cercana al ~2.51%
que separaba la prediccion ingenua (1.47%) de lo medido (3.98%). Esto es
una ESTIMACION GRUESA (trata las duraciones como si fueran completamente
en serie, cuando en la practica hay paralelismo real; usa T1 como proxy
simple, no un modelo de canal cuantico riguroso), no una derivacion
formal -- pero encaja lo bastante bien como para senalar la explicacion
mas probable: el hueco que deja el modelo ingenuo optimista es,
aproximadamente, la decoherencia que ese modelo nunca contempla.

Reproducir la conexion (requiere qiskit-ibm-runtime y credenciales propias,
NO incluidas aqui):

    python research/exploraciones/ghz_hardware_real.py
"""
from fractions import Fraction

# --- Prediccion exacta (no depende de ningun hardware) ---------------------


def prediccion_exacta(n):
    """Distribucion exacta de GHZ(n) en la base computacional: {"0"*n:
    1/2, "1"*n: 1/2}. Fracciones exactas, no aproximaciones."""
    return {"0" * n: Fraction(1, 2), "1" * n: Fraction(1, 2)}


def prediccion_exacta_suma_uno(n):
    """Verifica que la prediccion exacta es una distribucion de probabilidad
    valida: las fracciones dadas suman exactamente 1, para cualquier n."""
    return sum(prediccion_exacta(n).values()) == Fraction(1, 1)


# --- Registro de los experimentos reales (dato historico, no recalculable) -

EXPERIMENTOS_REALES = [
    {
        "n": 3, "job_id": "d9kuc78ii2cc73egnv4g", "shots": 4096,
        "counts": {"000": 1975, "111": 1892, "001": 87, "101": 75,
                   "011": 34, "100": 18, "110": 15},
    },
    {
        "n": 3, "job_id": "d9kukujhdfks73ck7g0g", "shots": 4096,
        "counts": {"000": 1985, "111": 1870, "110": 13, "101": 83,
                   "001": 98, "011": 27, "010": 4, "100": 16},
    },
    {
        "n": 3, "job_id": "d9kul9bjf64c739iolog", "shots": 4096,
        "counts": {"000": 1941, "110": 16, "111": 1910, "101": 79,
                   "001": 103, "100": 18, "011": 29},
    },
    {
        "n": 4, "job_id": "d9kumsqbr2fc73e7tsvg", "shots": 4096,
        "counts": {"0000": 1901, "1111": 1911, "0111": 35, "1101": 93,
                   "0100": 3, "0001": 92, "1011": 11, "0011": 8,
                   "1100": 8, "1110": 19, "1000": 9, "0010": 2,
                   "1001": 3, "0101": 1},
    },
    {
        "n": 5, "job_id": "d9kuolabr2fc73e7tvf0", "shots": 4096,
        "counts": {"00000": 1970, "11111": 1785, "00001": 80,
                   "10111": 32, "01111": 37, "11011": 19, "11101": 77,
                   "11110": 19, "11100": 13, "11000": 6, "10000": 21,
                   "01110": 1, "01000": 3, "00011": 14, "00101": 1,
                   "00010": 2, "00111": 12, "10001": 1, "00100": 1,
                   "10101": 1, "10100": 1},
    },
    {
        "n": 6, "job_id": "d9kv0tibr2fc73e7udjg", "shots": 4096,
        "counts": {"000000": 1881, "111111": 1763, "000001": 83,
                   "111101": 97, "101111": 69, "001000": 3,
                   "110111": 14, "000011": 14, "111001": 2,
                   "000111": 9, "111110": 16, "111000": 10,
                   "100000": 31, "111100": 12, "001111": 9,
                   "110000": 18, "111011": 14, "011111": 20,
                   "010000": 12, "011110": 1, "101100": 1,
                   "001001": 2, "111010": 1, "100111": 1,
                   "000101": 1, "101000": 1, "000010": 2,
                   "100001": 1, "000100": 3, "101101": 3,
                   "010111": 1, "110101": 1},
    },
    {
        "n": 7, "job_id": "d9kv4ojjf64c739ipdgg", "shots": 4096,
        "counts": {"1111111": 1702, "0000000": 1914, "0011111": 13,
                   "0010000": 10, "1111101": 117, "0000001": 76,
                   "1101111": 77, "1111000": 10, "1110000": 13,
                   "1111100": 9, "1110111": 12, "0111111": 18,
                   "0001101": 3, "1000000": 14, "1100000": 10,
                   "1111110": 12, "0001111": 9, "1111011": 12,
                   "1100111": 1, "1011111": 14, "0000110": 1,
                   "1110100": 1, "0011101": 1, "0000111": 10,
                   "0000011": 8, "0110111": 1, "0100000": 8,
                   "0000101": 2, "0111101": 1, "1011101": 2,
                   "1001111": 1, "0101111": 1, "0111011": 1,
                   "0010001": 2, "1000001": 1, "0000100": 1,
                   "1101101": 3, "1101100": 1, "1110001": 1,
                   "1111010": 1, "1101011": 1, "0010111": 1},
    },
]

# Experimento de control: mismo circuito GHZ(3), pero forzando el
# transpilador a una cadena de qubits fisicos de bajo error (118-129-128),
# evitando a proposito el qubit #1 usado en EXPERIMENTOS_REALES. Separado
# de la lista anterior porque usa fisicamente otros qubits -- no es parte
# de la serie n=3..7, es la prueba causal de la hipotesis que esa serie
# sugirio.
EXPERIMENTO_CONTROL = {
    "n": 3, "job_id": "d9l04c8ii2cc73egqna0", "shots": 4096,
    "physical_qubits": [118, 129, 128],
    "counts": {"111": 1915, "000": 2018, "100": 32, "110": 47,
               "010": 6, "001": 12, "011": 38, "101": 28},
}


def mejora_del_control_vs_baseline():
    """(fuga_media_baseline, fuga_control, mejora) como floats. La mejora
    es real (mayor que la desviacion estandar del baseline) pero parcial:
    el qubit malo no explica toda la fuga, ver docstring del modulo."""
    fugas_base = [float(f) for f in leaks_por_n(3)]
    media_base = sum(fugas_base) / len(fugas_base)
    _, fuga_control = desviacion_de_la_prediccion_exacta(EXPERIMENTO_CONTROL)
    return media_base, float(fuga_control), media_base - float(fuga_control)


# Prediccion del modelo ingenuo para el circuito de control (mismo metodo
# que PREDICCION_MODELO_INGENUO, tasas publicadas por IBM el 2026-07-29
# para los qubits fisicos 118,129,128).
PREDICCION_INGENUA_CONTROL = 0.9853

# Datos de coherencia de los tres qubits del control, publicados por IBM
# el 2026-07-29 (backend.qubit_properties), y la duracion total (en serie)
# de las puertas/medicion del circuito realmente enviado (backend.target
# duration de cada instruccion del job d9l04c8ii2cc73egqna0).
T1_MICROSEGUNDOS_CONTROL = {118: 287.6, 129: 247.7, 128: 230.0}
T2_MICROSEGUNDOS_CONTROL = {118: 153.0, 129: 137.2, 128: 63.3}
DURACION_CIRCUITO_MICROSEGUNDOS_CONTROL = 6.836


def estimacion_gruesa_decoherencia():
    """Probabilidad de decoherencia estimada como
    duracion_circuito / min(T1), usando el T1 mas corto de los tres
    qubits del control. Estimacion GRUESA (no un modelo de canal
    riguroso): trata la duracion como si fuera completamente en serie
    (en la practica hay paralelismo), y usa T1 como proxy simple. Sirve
    para comparar orden de magnitud contra el hueco que deja el modelo
    ingenuo, no como una prediccion precisa."""
    t1_min = min(T1_MICROSEGUNDOS_CONTROL.values())
    return DURACION_CIRCUITO_MICROSEGUNDOS_CONTROL / t1_min


def hueco_del_modelo_ingenuo_en_el_control():
    """(fuga_predicha_ingenua, fuga_medida, hueco) para el circuito de
    control. El signo del hueco aqui es OPUESTO al de la serie n=3..7:
    ahi el modelo ingenuo subestimaba la supervivencia (era pesimista);
    aqui la sobreestima (es optimista)."""
    _, fuga_medida = desviacion_de_la_prediccion_exacta(EXPERIMENTO_CONTROL)
    fuga_ingenua = 1 - PREDICCION_INGENUA_CONTROL
    return fuga_ingenua, float(fuga_medida), float(fuga_medida) - fuga_ingenua


# Prediccion del modelo de ruido ingenuo (producto de 1-error sobre cada
# puerta/medicion, con las tasas publicadas por IBM el 2026-07-29 para los
# qubits fisicos exactos usados en cada job -- ver docstring del modulo
# para la explicacion de por que este modelo subestima la supervivencia
# real de forma sistematica).
PREDICCION_MODELO_INGENUO = {
    "d9kuc78ii2cc73egnv4g": 0.7337,
    "d9kukujhdfks73ck7g0g": 0.7337,
    "d9kul9bjf64c739iolog": 0.7337,
    "d9kumsqbr2fc73e7tsvg": 0.7286,
    "d9kuolabr2fc73e7tvf0": 0.7187,
    "d9kv0tibr2fc73e7udjg": 0.7104,
    "d9kv4ojjf64c739ipdgg": 0.7025,
}


def desviacion_de_la_prediccion_exacta(experimento):
    """Compara un experimento registrado contra su prediccion exacta.
    Devuelve (p_ideal, fuga) como Fraction exactos sobre 'shots'."""
    n = experimento["n"]
    lo, hi = "0" * n, "1" * n
    counts = experimento["counts"]
    shots = experimento["shots"]
    p_ideal = Fraction(counts.get(lo, 0) + counts.get(hi, 0), shots)
    fuga = Fraction(1, 1) - p_ideal
    return p_ideal, fuga


def diferencia_vs_modelo_ingenuo(experimento):
    """medido - predicho_por_el_modelo_ingenuo, como float (el modelo
    ingenuo no es exacto, asi que no tiene sentido forzarlo a Fraction)."""
    p_ideal, _ = desviacion_de_la_prediccion_exacta(experimento)
    predicho = PREDICCION_MODELO_INGENUO[experimento["job_id"]]
    return float(p_ideal) - predicho


def leaks_por_n(n, experimentos=EXPERIMENTOS_REALES):
    """Lista de fugas (Fraction) para todas las corridas registradas de un n dado."""
    return [desviacion_de_la_prediccion_exacta(e)[1]
            for e in experimentos if e["n"] == n]


def resumen():
    print("GHZ(n): prediccion exacta vs hardware real (ibm_kingston, 2026-07-29)\n")
    for e in EXPERIMENTOS_REALES:
        p_ideal, fuga = desviacion_de_la_prediccion_exacta(e)
        diff = diferencia_vs_modelo_ingenuo(e)
        print(f"  n={e['n']}  job={e['job_id'][:16]}...  "
              f"P(ideal)={float(p_ideal):.4f}  fuga={float(fuga):.4f}  "
              f"vs modelo ingenuo: {diff:+.4f}")

    fugas_n3 = leaks_por_n(3)
    media = sum(float(f) for f in fugas_n3) / len(fugas_n3)
    var = sum((float(f) - media) ** 2 for f in fugas_n3) / (len(fugas_n3) - 1)
    print(f"\nn=3 repetido {len(fugas_n3)}x: fuga media={media:.4f}, "
          f"desviacion estandar={var**0.5:.4f}")


if __name__ == "__main__":
    resumen()
