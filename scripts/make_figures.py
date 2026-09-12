"""Figures for the README, from the exact library and the stored hardware data.

  figures/ghz_hardware.png       GHZ(n) on ibm_kingston: measured P(0^n)+P(1^n) vs exact 1,
                                 the naive noise model, and the control run on low-error qubits
  figures/cluster_hardware.png   the four stabilizer expectation values <K_i> of the n=4 cluster state
  figures/entropy_exact.png      exact entanglement entropy of GHZ and cluster states vs cut (integers)
  figures/code_distance.png      logical-operator search: minimum weight found for Steane / 5-qubit / Shor
  figures/overview.png           summary panel

Each computed quantity is asserted before drawing (entropies against the closed
forms, distances against the published d = 3). The hardware panels only READ the
JSON records in data/hardware. Usage: python scripts/make_figures.py
"""
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
from stabilizer_exact import (entropia_entrelazamiento_exacta, ghz_state, cluster_state_1d,   # noqa: E402
                              distancia_codigo_estabilizador, codigo_steane, codigo_5_qubits, codigo_shor)

OUT = os.path.join(RAIZ, "figures"); os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.titlesize": 9.5, "axes.spines.top": False, "axes.spines.right": False})
AZUL, ROJO, VERDE, GRIS, NARANJA = "#1f4e79", "#c0392b", "#27ae60", "#7f8c8d", "#e67e22"


def carga_hw():
    recs = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(RAIZ, "data", "hardware", "*.json"))) if not p.endswith("index.json")]
    ghz = sorted([r for r in recs if r["circuit"].startswith("GHZ(") and "control" not in r["circuit"]], key=lambda r: (r["n_qubits"], r["job_id"]))
    ctrl = [r for r in recs if "control" in r["circuit"]][0]
    clu = sorted([r for r in recs if r["circuit"].startswith("1D cluster")], key=lambda r: r["generator"])
    return ghz, ctrl, clu


ghz, ctrl, clu = carga_hw()

# 1. GHZ on hardware -----------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.6, 3.8))
ns = [r["n_qubits"] for r in ghz]; meas = [r["measured"]["P(0^n)+P(1^n)_float"] for r in ghz]; naive = [r["naive_noise_model_prediction"] for r in ghz]
ax.axhline(1.0, color="black", lw=0.8, label="exact: P(0^n)+P(1^n) = 1")
ax.plot(ns, meas, "o", color=AZUL, ms=6, label="measured on ibm_kingston, 4096 shots (2026-07-29)")
ax.plot(ns, naive, "s", color=GRIS, ms=5, label="naive noise model from IBM's published error rates")
ax.plot([3], [ctrl["measured"]["P(000)+P(111)_float"]], "D", color=VERDE, ms=7, label="control: GHZ(3) on low-error qubits %s" % ctrl["physical_qubits"])
ax.plot([3], [ctrl["naive_noise_model_prediction"]], "s", color=VERDE, ms=5, alpha=0.6)
for n, m in zip(ns, meas):
    if n > 3:
        ax.annotate("%.3f" % m, (n, m), textcoords="offset points", xytext=(6, 4), fontsize=7, color=AZUL)
ax.annotate("3 runs: 0.944, 0.941, 0.940", (3, 0.94), textcoords="offset points", xytext=(10, -12), fontsize=7, color=AZUL)
ax.set_xticks(ns); ax.set_ylim(0.65, 1.02); ax.set_xlabel("n qubits"); ax.set_ylabel("survival of the GHZ support")
ax.set_title("GHZ(n) on real hardware: the exact state predicts 1; the naive product-of-error-rates model is far too pessimistic")
ax.legend(fontsize=7.5, frameon=False, loc="center right")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "ghz_hardware.png"), dpi=160); plt.close(fig)

# 2. Cluster-state stabilizers on hardware ---------------------------------------
fig, ax = plt.subplots(figsize=(8.6, 3.4))
ks = [r["generator"] for r in clu]; ev = [r["measured"]["<K>_float"] for r in clu]; bad = [r["touches_miscalibrated_qubit"] for r in clu]
ax.bar(ks, ev, color=[ROJO if b else AZUL for b in bad], width=0.6)
ax.axhline(1.0, color="black", lw=0.8)
for k, v, b in zip(ks, ev, bad):
    ax.text(k, v + 0.01, "%.3f%s" % (v, "  (touches qubit #1)" if b else ""), ha="center", fontsize=8)
ax.set_ylim(0.7, 1.05); ax.set_xticks(ks); ax.set_xticklabels(["K_%d" % k for k in ks]); ax.set_ylabel("measured <K_i>")
ax.set_title("1D cluster state (n=4): each stabilizer generator has <K_i> = 1 exactly; on hardware the three touching the miscalibrated qubit #1 (readout error 23.4%) are the low ones")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "cluster_hardware.png"), dpi=160); plt.close(fig)

# 3. Exact entanglement entropies ---------------------------------------------
fig, ax = plt.subplots(figsize=(8.6, 3.4))
N = 10
ghz_S = [entropia_entrelazamiento_exacta(ghz_state(N), list(range(k))) for k in range(1, N)]
clu_S = [entropia_entrelazamiento_exacta(cluster_state_1d(N), list(range(k))) for k in range(1, N)]
assert ghz_S == [1] * (N - 1), ghz_S                       # GHZ: one ebit across any cut
assert clu_S == [1] * (N - 1), clu_S                       # 1D cluster: area law, one ebit per cut
rnd_S = [entropia_entrelazamiento_exacta(__import__("stabilizer_exact").circuito_clifford_aleatorio(N, 400, semilla=7), list(range(k))) for k in range(1, N)]
assert all(s <= min(k, N - k) for k, s in zip(range(1, N), rnd_S))   # Page bound for stabilizer states
ax.plot(range(1, N), ghz_S, "o-", color=AZUL, label="GHZ(10): S = 1 for every cut")
ax.plot(range(1, N), clu_S, "s--", color=VERDE, label="1D cluster(10): S = 1 for every contiguous cut (area law)")
ax.plot(range(1, N), rnd_S, "^-", color=ROJO, label="random Clifford(10), depth 400: S <= min(k, 10-k)")
ax.plot(range(1, N), [min(k, N - k) for k in range(1, N)], ":", color=GRIS, label="bound min(k, n-k)")
ax.set_xlabel("cut: first k qubits"); ax.set_ylabel("entanglement entropy (integer ebits)")
ax.set_title("Exact entanglement entropy of stabilizer states via GF(2) rank of the tableau -- always an integer, no floating point")
ax.legend(fontsize=7.5, frameon=False)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "entropy_exact.png"), dpi=160); plt.close(fig)

# 4. Code distance ----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.6, 2.8))
codigos = [("Steane [[7,1,3]]",) + codigo_steane(), ("5-qubit [[5,1,3]]",) + codigo_5_qubits(), ("Shor [[9,1,3]]",) + codigo_shor()]
ds = []
for nombre, gens, n in codigos:
    d = distancia_codigo_estabilizador(gens, n, peso_maximo=4)
    assert d == 3, (nombre, d)
    ds.append(d)
ax.bar(range(3), ds, color=AZUL, width=0.5)
ax.set_xticks(range(3)); ax.set_xticklabels([c[0] for c in codigos]); ax.set_ylabel("distance d found"); ax.set_ylim(0, 4)
for i, d in enumerate(ds):
    ax.text(i, d + 0.1, "d = %d (published: 3)" % d, ha="center", fontsize=8)
ax.set_title("Exact code distance by exhaustive search over logical operators (symplectic GF(2) test): three canonical codes recovered")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "code_distance.png"), dpi=160); plt.close(fig)

# 5. Overview -----------------------------------------------------------------
fig, axs = plt.subplots(2, 2, figsize=(10, 6.4))
axs[0, 0].plot(range(1, N), ghz_S, "o-", color=AZUL); axs[0, 0].plot(range(1, N), rnd_S, "^-", color=ROJO); axs[0, 0].plot(range(1, N), [min(k, N - k) for k in range(1, N)], ":", color=GRIS)
axs[0, 0].set_title("exact entropies: GHZ (1 ebit), random Clifford, bound")
axs[0, 1].bar(range(3), ds, color=AZUL, width=0.5); axs[0, 1].set_xticks(range(3)); axs[0, 1].set_xticklabels(["Steane", "5-qubit", "Shor"]); axs[0, 1].set_ylim(0, 4)
axs[0, 1].set_title("exact code distance: d = 3, 3, 3")
axs[1, 0].axhline(1, color="black", lw=0.8); axs[1, 0].plot(ns, meas, "o", color=AZUL); axs[1, 0].plot(ns, naive, "s", color=GRIS); axs[1, 0].plot([3], [ctrl["measured"]["P(000)+P(111)_float"]], "D", color=VERDE)
axs[1, 0].set_ylim(0.65, 1.02); axs[1, 0].set_title("GHZ on ibm_kingston: measured (blue), naive model (grey), control (green)")
axs[1, 1].bar(ks, ev, color=[ROJO if b else AZUL for b in bad], width=0.6); axs[1, 1].axhline(1, color="black", lw=0.8); axs[1, 1].set_ylim(0.7, 1.05)
axs[1, 1].set_title("cluster-state stabilizers on hardware: red = touches qubit #1")
fig.suptitle("Exact stabilizer toolkit (GF(2), no floats) + 12 real IBM Quantum jobs, stored verbatim", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "overview.png"), dpi=160); plt.close(fig)
print("figures:", sorted(os.listdir(OUT)))
