"""Export every real-hardware record embedded in the experiment scripts to
data/hardware/*.json, one file per IBM Quantum job, with the raw counts exactly
as returned by the backend and the exact prediction next to them.

These are HISTORICAL data: runs on ibm_kingston (156-qubit Heron r2), 2026-07-29,
4096 shots each, via Qiskit Runtime SamplerV2. They cannot be regenerated -- the
hardware drifts and is recalibrated daily -- which is why the counts are stored
verbatim rather than recomputed.  Usage: python scripts/export_hardware_data.py
"""
import json
import os
import sys
from fractions import Fraction

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "experiments"))
import ghz_hardware_real as G          # noqa: E402
import cluster_state_hardware_real as C  # noqa: E402

OUT = os.path.join(RAIZ, "data", "hardware")
os.makedirs(OUT, exist_ok=True)
index = []


def escribe(nombre, doc):
    ruta = os.path.join(OUT, nombre + ".json")
    json.dump(doc, open(ruta, "w", encoding="utf-8"), indent=1, sort_keys=True)
    index.append({"file": nombre + ".json", "job_id": doc["job_id"], "circuit": doc["circuit"], "shots": doc["shots"]})


comun = {"backend": "ibm_kingston", "date": "2026-07-29", "runtime": "Qiskit Runtime SamplerV2", "shots": 4096,
         "note": "raw counts as returned by the backend; historical, not reproducible on demand"}

for e in G.EXPERIMENTOS_REALES:
    n = e["n"]; c = e["counts"]; tot = sum(c.values()); assert tot == e["shots"]
    p_ideal = Fraction(c.get("0" * n, 0) + c.get("1" * n, 0), tot)
    escribe("ghz%d_%s" % (n, e["job_id"]), dict(comun, job_id=e["job_id"], circuit="GHZ(%d)" % n, n_qubits=n, counts=c,
        exact_prediction={"P(0^n)": "1/2", "P(1^n)": "1/2", "P(other)": "0"},
        measured={"P(0^n)+P(1^n)": str(p_ideal), "P(0^n)+P(1^n)_float": float(p_ideal), "leak": float(1 - p_ideal)},
        naive_noise_model_prediction=G.PREDICCION_MODELO_INGENUO.get(e["job_id"])))

e = G.EXPERIMENTO_CONTROL; c = e["counts"]; tot = sum(c.values()); assert tot == e["shots"]
p_ideal = Fraction(c.get("000", 0) + c.get("111", 0), tot)
escribe("ghz3_control_%s" % e["job_id"], dict(comun, job_id=e["job_id"], circuit="GHZ(3) control on low-error qubits", n_qubits=3,
    physical_qubits=e["physical_qubits"], counts=c,
    exact_prediction={"P(000)": "1/2", "P(111)": "1/2", "P(other)": "0"},
    measured={"P(000)+P(111)": str(p_ideal), "P(000)+P(111)_float": float(p_ideal), "leak": float(1 - p_ideal)},
    naive_noise_model_prediction=G.PREDICCION_INGENUA_CONTROL,
    qubit_properties_published_by_IBM={"T1_us": G.T1_MICROSEGUNDOS_CONTROL, "T2_us": G.T2_MICROSEGUNDOS_CONTROL},
    circuit_duration_us=G.DURACION_CIRCUITO_MICROSEGUNDOS_CONTROL))

for e in C.EXPERIMENTOS_REALES:
    c = e["counts"]; tot = sum(c.values()); assert tot == e["shots"]
    ev = C.expval_medido(e)
    escribe("cluster4_K%d_%s" % (e["generator"], e["job_id"]), dict(comun, job_id=e["job_id"],
        circuit="1D cluster state, n=4, stabilizer generator K_%d measured" % e["generator"], n_qubits=C.N,
        generator=e["generator"], generator_support=C.generador_soporte(e["generator"], C.N), counts=c,
        exact_prediction={"<K_%d>" % e["generator"]: 1},
        measured={"<K>": str(ev) if isinstance(ev, Fraction) else ev, "<K>_float": float(ev)},
        touches_miscalibrated_qubit=C.involucra_qubit(e["generator"], C.N, C.QUBIT_FISICO_MALO)))

json.dump({"backend": "ibm_kingston", "date": "2026-07-29", "jobs": index}, open(os.path.join(OUT, "index.json"), "w"), indent=1)
print("exported %d job records to %s" % (len(index), OUT))
