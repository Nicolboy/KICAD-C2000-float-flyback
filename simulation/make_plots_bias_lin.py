"""Figure de la linearisation HV_BIAS a partir de results/bias_lin.csv
(donnees reelles issues de LTspice, pas de valeurs inventees). Modeles
generiques/ideaux (U20, Q5) -- voir docstring de gen_bias_lin.py."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("results/bias_lin.csv", encoding="utf-8")))
vg = [float(r["vargate_v"]) for r in rows]
vb = [float(r["hv_bias_v"]) for r in rows]

fig, ax = plt.subplots(figsize=(7, 5))
ax.plot(vg, vb, color="C0", lw=2, label="V(HV_BIAS) simule (LTspice, modeles generiques)")
ax.axvline(0.80, color="gray", ls="--", lw=1, alpha=0.7)
ax.annotate("D3 entre en conduction directe\n(plafonne ~0,8V)",
            (0.80, 40), xytext=(1.1, 45), fontsize=9,
            arrowprops=dict(arrowstyle="->", alpha=0.6))
ax.set_xlabel("VAR_GATE (V)")
ax.set_ylabel("HV_BIAS (V)")
ax.set_title("Linearisation HV_BIAS -- U20 (MCP6001 ideal) + Q5 (BSS127I generique)\n"
             "HV80_IN=80V, R26=100k, R45=1k -- 1ere passe, modeles non constructeur")
ax.set_xlim(0, 3.0)
ax.set_ylim(-2, 85)
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig("plots/bias_lin_transfer.png", dpi=140)
print("Ecrit plots/bias_lin_transfer.png")
