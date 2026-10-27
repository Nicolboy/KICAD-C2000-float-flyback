"""Compare la courbe de transfert HV_BIAS=f(VAR_GATE) : modele IDEAL
(bias_fb_with_q7_r52_39k.csv, U21=UniversalOpAmp2 par defaut, Q6/Q7=NMOS
niveau 1 generique VTO=1/KP=0.05) vs modele REEL (Q6/Q7=BSS127I reel,
U21=MCP6001 parametre datasheet -- rampe .tran resampleee, voir
gen_bias_fb_ramp_real.py pour pourquoi une rampe plutot qu'un .dc)."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ideal_rows = list(csv.DictReader(open("results/bias_fb_with_q7_r52_39k.csv", encoding="utf-8")))
vg_ideal = [float(r["vargate_v"]) for r in ideal_rows]
vb_ideal = [float(r["hv_bias_v"]) for r in ideal_rows]

real_rows = list(csv.DictReader(open("results/bias_fb_ramp_real_timedomain.csv", encoding="utf-8")))
t_real = [float(r["time_s"]) for r in real_rows]
vg_real_t = [float(r["V(vargate)"]) for r in real_rows]
vb_real_t = [float(r["V(hv_bias)"]) for r in real_rows]

grid = [round(0.05 * i, 2) for i in range(61)]  # 0 -> 3.0V pas 0.05V
vb_real_grid = []
j = 0
for vg in grid:
    while j < len(vg_real_t) - 1 and vg_real_t[j + 1] < vg:
        j += 1
    vb_real_grid.append(vb_real_t[j])

fig, axs = plt.subplots(1, 2, figsize=(13, 5.5))

axs[0].plot(vg_ideal, vb_ideal, color="C1", lw=1.8, label="Ideal (opamp/MOSFET generiques)")
axs[0].plot(grid, vb_real_grid, color="C0", lw=1.8, label="Reel (MCP6001 parametre + BSS127I)")
axs[0].set_xlabel("VAR_GATE (V)")
axs[0].set_ylabel("HV_BIAS (V)")
axs[0].set_title("Courbe de transfert complete")
axs[0].legend(fontsize=9)
axs[0].grid(alpha=0.3)

mask = [(g, i, r) for g, i, r in zip(grid,
         [vb_ideal[min(range(len(vg_ideal)), key=lambda k: abs(vg_ideal[k]-g))] for g in grid],
         vb_real_grid) if g <= 3.0]
axs[1].plot([m[0] for m in mask], [m[1] for m in mask], color="C1", lw=1.8, label="Ideal")
axs[1].plot([m[0] for m in mask], [m[2] for m in mask], color="C0", lw=1.8, label="Reel")
axs[1].set_xlabel("VAR_GATE (V)")
axs[1].set_ylabel("HV_BIAS (V)")
axs[1].set_title("Zoom 0-3V (meme grille d'echantillonnage)")
axs[1].legend(fontsize=9)
axs[1].grid(alpha=0.3)

fig.suptitle("HV_BIAS=f(VAR_GATE) -- ideal vs composants reels (MCP6001 parametre + BSS127I)",
             fontsize=12)
fig.tight_layout()
fig.savefig("plots/bias_fb_real_vs_ideal.png", dpi=140)
print("Ecrit plots/bias_fb_real_vs_ideal.png")

for g, vb_i, vb_r in zip(grid, [m[1] for m in mask], [m[2] for m in mask]):
    if g in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
        print(f"VAR_GATE={g:.2f}V : ideal={vb_i:.3f}V reel={vb_r:.3f}V ecart={vb_r-vb_i:+.3f}V")
