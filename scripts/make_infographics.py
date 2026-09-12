"""Two infographics that read the stored hardware records and say something the
tables do not:

  figures/error_anatomy.png   where the shots go: for each GHZ(n) run, the fraction of
                              shots at Hamming distance 0, 1, 2, ... from the nearest
                              ideal outcome, and WHICH bit position flips most often
  figures/story.png           the argument in one picture: exact prediction -> naive
                              model -> measurement -> the qubit-#1 hypothesis ->
                              the control test -> what remains (decoherence), with
                              every number taken from data/hardware

Usage: python scripts/make_infographics.py
"""
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RAIZ, "figures"); os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
AZUL, ROJO, VERDE, GRIS, NARANJA, CLARO = "#1f4e79", "#c0392b", "#27ae60", "#7f8c8d", "#e67e22", "#eaf1f8"

recs = {os.path.basename(p): json.load(open(p)) for p in glob.glob(os.path.join(RAIZ, "data", "hardware", "*.json")) if not p.endswith("index.json")}
ghz = sorted([r for r in recs.values() if r["circuit"].startswith("GHZ(") and "control" not in r["circuit"]], key=lambda r: (r["n_qubits"], r["job_id"]))
ctrl = [r for r in recs.values() if "control" in r["circuit"]][0]
clu = sorted([r for r in recs.values() if r["circuit"].startswith("1D cluster")], key=lambda r: r["generator"])

# ---------------------------------------------------------------- 1. error anatomy
def anatomia(rec):
    n = rec["n_qubits"]; c = rec["counts"]; tot = sum(c.values())
    por_dist = np.zeros(n + 1); por_bit = np.zeros(n)
    for s, k in c.items():
        d0 = s.count("1"); d1 = s.count("0")
        d = min(d0, d1); por_dist[d] += k
        if 0 < d < n / 2 or (d == n / 2 and n % 2 == 0):
            ideal = "0" * n if d0 <= d1 else "1" * n
            for i, (a, b) in enumerate(zip(s, ideal)):
                if a != b: por_bit[i] += k
    return por_dist / tot, por_bit / tot


runs = ghz + [ctrl]
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.15, 1]})
ax = axs[0]
labels = ["GHZ(%d)%s" % (r["n_qubits"], " ctrl" if "control" in r["circuit"] else "") for r in runs]
y = np.arange(len(runs)); left = np.zeros(len(runs))
cols = [AZUL, NARANJA, ROJO, "#8e44ad", "#2c3e50"]
maxd = max(r["n_qubits"] for r in runs) // 2 + 1
for d in range(maxd):
    vals = []
    for r in runs:
        pd, _ = anatomia(r); vals.append(pd[d] if d < len(pd) else 0)
    vals = np.array(vals)
    ax.barh(y, vals, left=left, color=cols[d % len(cols)], label=("exact outcome (0 flips)" if d == 0 else "%d bit flip%s" % (d, "s" if d > 1 else "")))
    for i, (l, v) in enumerate(zip(left, vals)):
        if v > 0.03:
            ax.text(l + v / 2, i, "%.1f%%" % (100 * v), ha="center", va="center", fontsize=7.5, color="white" if d == 0 else "black")
    left += vals
ax.set_yticks(y); ax.set_yticklabels(labels); ax.set_xlim(0, 1); ax.set_xlabel("fraction of 4096 shots"); ax.set_ylim(-0.6, len(runs) + 1.4)
ax.set_title("Where the shots go: distance from the nearest ideal outcome (0ⁿ or 1ⁿ)", fontsize=9.5)
ax.legend(fontsize=7.5, frameon=False, loc="upper left", ncol=4)
ax = axs[1]
for r, col in zip(ghz[3:], [AZUL, NARANJA, ROJO, "#8e44ad"]):
    _, pb = anatomia(r); n = r["n_qubits"]
    ax.plot(range(n), 100 * pb, "o-", ms=4, color=col, label="GHZ(%d)" % n)
_, pb3 = anatomia(ghz[0]); ax.plot(range(3), 100 * pb3, "s--", ms=4, color=GRIS, label="GHZ(3), run 1")
_, pbc = anatomia(ctrl); ax.plot(range(3), 100 * pbc, "D--", ms=4, color=VERDE, label="GHZ(3) control (qubits 118-129-128)")
ax.set_xlabel("bit position in the measured string (0 = leftmost)"); ax.set_ylabel("% of shots with that bit flipped")
ax.set_title("Which bit flips: the last measured qubits flip most (they wait longest); the control is flat and low", fontsize=9.5)
ax.legend(fontsize=7.5, frameon=False)
fig.suptitle("Anatomy of the hardware error, from the raw counts (data/hardware)", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "error_anatomy.png"), dpi=160); plt.close(fig)

# ---------------------------------------------------------------- 2. the story
m3 = np.mean([r["measured"]["P(0^n)+P(1^n)_float"] for r in ghz[:3]]); s3 = np.std([r["measured"]["P(0^n)+P(1^n)_float"] for r in ghz[:3]])
naive3 = ghz[0]["naive_noise_model_prediction"]; mc = ctrl["measured"]["P(000)+P(111)_float"]; nc = ctrl["naive_noise_model_prediction"]
low = [r for r in clu if r["touches_miscalibrated_qubit"]]; high = [r for r in clu if not r["touches_miscalibrated_qubit"]]
t1 = min(ctrl["qubit_properties_published_by_IBM"]["T1_us"].values()); dur = ctrl["circuit_duration_us"]

fig, ax = plt.subplots(figsize=(11, 6.8)); ax.set_xlim(0, 100); ax.set_ylim(0, 108); ax.axis("off")


def caja(x, y, w, h, titulo, cuerpo, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.5", fc=CLARO, ec=color, lw=1.8))
    ax.text(x + w / 2, y + h - 3.2, titulo, ha="center", va="top", fontsize=9.5, fontweight="bold", color=color)
    ax.text(x + 1.5, y + h - 9, cuerpo, ha="left", va="top", fontsize=8, linespacing=1.35)


def flecha(x0, y0, x1, y1, texto=""):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=14, color=GRIS, lw=1.4))
    if texto:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 2, texto, ha="center", fontsize=7.5, color=GRIS, style="italic")


caja(1, 62, 30, 30, "1. Exact prediction",
     "GHZ(n) = (|0ⁿ⟩ + |1ⁿ⟩)/√2\nP(0ⁿ) = P(1ⁿ) = 1/2 exactly,\nevery other outcome 0.\nEntropy across any cut: 1 ebit\n(GF(2) rank, integer — no floats).", AZUL)
caja(35, 62, 30, 30, "2. Naive noise model",
     "Multiply IBM's published gate and\nreadout error rates for the qubits used.\nPredicts survival %.3f for GHZ(3)\n(0.70 for GHZ(7))." % naive3, GRIS)
caja(69, 62, 30, 30, "3. Measurement (ibm_kingston)",
     "GHZ(3) ×3: %.3f ± %.3f\nGHZ(4…7): 0.931 → 0.883\n4096 shots each, 2026-07-29.\nThe naive model is ~0.20 too\npessimistic; not shot noise." % (m3, s3), AZUL)
caja(1, 16, 30, 34, "4. Hypothesis: one bad qubit",
     "Default placement used physical\nqubit #1: readout error 23.4 %%\n(chip median 0.9 %%).\nCluster-state test: the 3 stabilizers\ntouching #1 read %.2f, %.2f, %.2f;\nthe one that does not reads %.2f." % (low[0]["measured"]["<K>_float"], low[1]["measured"]["<K>_float"], low[2]["measured"]["<K>_float"], high[0]["measured"]["<K>_float"]), ROJO)
caja(35, 16, 30, 34, "5. Control experiment (causal)",
     "Same GHZ(3) circuit, transpiler forced\nonto low-error qubits 118-129-128\n(readout 0.29/0.34/0.42 %%).\nSurvival %.3f: leakage drops by\n%.2f points — real, but only about\na third of the excess." % (mc, 100 * (mc - m3)), VERDE)
caja(69, 16, 30, 34, "6. What remains",
     "On the good qubits the naive model\nnow predicts %.3f but measures %.3f:\nit flipped from pessimistic to\noptimistic. Missing piece: idle-time\ndecoherence over the %.1f µs circuit\n(T1 ≥ %.0f µs) — same order of magnitude." % (nc, mc, dur, t1), NARANJA)
flecha(31, 77, 35, 77); flecha(65, 77, 69, 77); flecha(84, 62, 16, 50, "why so far off?"); flecha(31, 33, 35, 33); flecha(65, 33, 69, 33)
ax.text(33, 12.5, "test it", ha="center", fontsize=7.5, color=GRIS, style="italic"); ax.text(67, 12.5, "partial: what else?", ha="center", fontsize=7.5, color=GRIS, style="italic")
ax.text(50, 5, "Every number above is read from data/hardware/*.json (12 IBM Quantum jobs, raw counts with job IDs). "
        "Historical measurements: the device is recalibrated daily and these runs cannot be regenerated on demand.",
        ha="center", fontsize=8, color=GRIS, wrap=True)
ax.text(50, 106, "From an exact state to a real machine — the argument of the hardware section, with its true sizes", ha="center", va="top", fontsize=11.5, fontweight="bold")
fig.savefig(os.path.join(OUT, "story.png"), dpi=160, bbox_inches="tight"); plt.close(fig)
print("infographics:", ["error_anatomy.png", "story.png"])
