"""Figure clamp secondaire (doc/sim-vs-mesure.md Sec.7bis) a partir de
results/sec_clamp_candidates.csv -- SMCJ43A vs SMCJ54A, dissipation et
Vds_Q2 clampe. Meme style que make_plots_compare.py."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("results/sec_clamp_candidates.csv", encoding="utf-8")))
a = {r["label"]: r for r in rows if r["candidate"] == "smcj43a"}
b = {r["label"]: r for r in rows if r["candidate"] == "smcj54a"}

labels = ["11V_6V3", "11V_12V6", "20V_6V3", "20V_12V6", "25V_6V3", "25V_12V6"]
x = range(len(labels))

fig, axs = plt.subplots(1, 2, figsize=(13, 5))

diss_a = [float(a[l]["ploss_d2sec"]) for l in labels]
diss_b = [float(b[l]["ploss_d2sec"]) for l in labels]
axs[0].bar([i - 0.2 for i in x], diss_a, width=0.4, label="SMCJ43A (47,8V, meme ref. que D1)", color="C0")
axs[0].bar([i + 0.2 for i in x], diss_b, width=0.4, label="SMCJ54A (60V, retenu)", color="C1")
axs[0].set_xticks(list(x))
axs[0].set_xticklabels(labels, rotation=40, ha="right", fontsize=8)
axs[0].set_ylabel("Dissipation clamp D4 (W)")
axs[0].set_title("Dissipation clamp -- P_av datasheet = 5W (marge x3,9 / x6,6)")
axs[0].legend(fontsize=9)
axs[0].grid(alpha=0.3, axis="y")

vds_a = [float(a[l]["vds_q2_max"]) for l in labels]
vds_b = [float(b[l]["vds_q2_max"]) for l in labels]
axs[1].bar([i - 0.2 for i in x], vds_a, width=0.4, color="C0")
axs[1].bar([i + 0.2 for i in x], vds_b, width=0.4, color="C1")
axs[1].axhline(100, color="red", ls="--", lw=1.5, label="Vds max Q2 (100V)")
axs[1].set_xticks(list(x))
axs[1].set_xticklabels(labels, rotation=40, ha="right", fontsize=8)
axs[1].set_ylabel("Vds Q2 max clampe (V)")
axs[1].set_title("Tenue en tension avec clamp -- marge x1,9 / x1,5")
axs[1].legend(fontsize=9)
axs[1].grid(alpha=0.3, axis="y")

fig.tight_layout()
fig.savefig("plots/clamp_comparison_18w9.png", dpi=140)
print("Ecrit plots/clamp_comparison_18w9.png")
