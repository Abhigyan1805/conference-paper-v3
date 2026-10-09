"""Fig. 5: projected wall-clock time for 1000 sweeps per method.

Reads per-sweep times (201 points, N=120) from Data/time comparison.xlsx and
projects 1000 sweeps as 1000 x measured sweep time. Bar = mean over G1-G4,
whisker = min-max over G1-G4. No hardcoded timings.
"""
import re
import sys
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(sys.argv[1])
OUT = Path(sys.argv[2])
N_SWEEPS = 1000


def read_xlsx(path):
    z = zipfile.ZipFile(path)
    shared = re.findall(r"<t[^>]*>([^<]*)</t>", z.read("xl/sharedStrings.xml").decode())
    sheet = z.read("xl/worksheets/sheet1.xml").decode()
    rows = []
    for row in re.findall(r"<row[^>]*>(.*?)</row>", sheet):
        vals = []
        for attrs, v in re.findall(r"<c([^>]*)><v>([^<]*)</v></c>", row):
            vals.append(shared[int(v)] if 't="s"' in attrs else float(v))
        rows.append(vals)
    return rows[0], rows[1:]


header, rows = read_xlsx(ROOT / "Data" / "time comparison.xlsx")
cols = {name: i for i, name in enumerate(header)}
methods = [("CST (s)", "CST (FEM)", "0.45", ""),
           ("CPU (s)", "CPU FFT-MoM", "#1f77b4", "//"),
           ("HPC (s)", "HPC A100", "#ff7f0e", "..")]


def fmt(sec):
    if sec >= 3600:
        return f"{sec / 3600:.1f} h"
    return f"{sec / 60:.0f} min"


plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans",
                     "hatch.linewidth": 0.6, "pdf.fonttype": 42})
fig, ax = plt.subplots(figsize=(3.07, 1.49))
x = np.arange(len(methods))
print(f"{'method':14s} {'mean h':>8s} {'min h':>8s} {'max h':>8s}")
for i, (key, label, color, hatch) in enumerate(methods):
    t = np.array([r[cols[key]] for r in rows]) * N_SWEEPS / 3600.0  # hours
    mean, lo, hi = t.mean(), t.min(), t.max()
    print(f"{label:14s} {mean:8.3f} {lo:8.3f} {hi:8.3f}")
    ax.bar(i, mean, width=0.55, color=color, hatch=hatch, edgecolor="white",
           linewidth=0, zorder=2)
    ax.errorbar(i, mean, yerr=[[mean - lo], [hi - mean]], fmt="none",
                ecolor="black", elinewidth=0.8, capsize=3, zorder=3)
    ax.text(i, hi * 1.35, fmt(mean * 3600), ha="center", va="bottom", fontsize=8)

ax.set_yscale("log")
ax.set_ylim(0.1, 400)
ax.set_xticks(x, [m[1] for m in methods])
ax.set_ylabel(f"{N_SWEEPS}-sweep time (h)")
ax.grid(axis="y", which="major", color="0.85", linewidth=0.5, zorder=0)
ax.tick_params(axis="x", length=0)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout(pad=0.2)
fig.savefig(OUT.with_suffix(".pdf"), metadata={"Creator": None, "Producer": None,
                                               "CreationDate": None})
fig.savefig(OUT.with_suffix(".png"), dpi=300)
