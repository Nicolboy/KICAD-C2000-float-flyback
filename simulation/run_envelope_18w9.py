"""Etape 1+2 du plan 18,9W (doc/sim-vs-mesure.md a completer) : meme
enveloppe Vin x Vout que run_envelope.py/run_envelope_schottky.py, mais a
la cible de puissance REELLE de la spec (00-intention-conception.md §2,
10 filaments, 6,3V/3A ou 12,6V/1,5A -- meme Pout=18,9W dans les deux
cablages), pas les 10W de validation initiale.

D trouve par find_duty.py (modele schottky rapide) a Rload=Vout^2/18.9 ;
Rload=2.1 Ohm (coin 6,3V) / 8.4 Ohm (coin 12,6V).

Deux passes, meme points, meme discipline incrementale que le reste du
dossier (memoire simulation-incremental-methodology) :
  - "schottky" : meme modele ideal rapide deja valide a 10W -- isole
    "puissance plus elevee" comme seule variable changee.
  - "sync_ideal" : Q2 = vrai IPD050N10N5 (gen_asc.py), grille pilotee en
    synchrone ideal (proxy UCC24612, voir docstring de gen_asc.build) --
    seul nouvel ajout par rapport a la passe precedente.
"""
import csv
import sys

sys.path.insert(0, ".")
from run_point import run

POINTS = [
    # (label, vin, vout_target, d, rload)
    ("11V_6V3", 11.0, 6.3, 0.4006, 2.1),
    ("11V_12V6", 11.0, 12.6, 0.5502, 8.4),
    ("20V_6V3", 20.0, 6.3, 0.2602, 2.1),
    ("20V_12V6", 20.0, 12.6, 0.4006, 8.4),
    ("25V_6V3", 25.0, 6.3, 0.2194, 2.1),
    ("25V_12V6", 25.0, 12.6, 0.3462, 8.4),
]
POUT_T = 18.9

FIELDS = ["label", "vin", "vout_target", "d", "rload", "vout_avg", "iout_avg",
          "pout_avg", "pin_avg", "eta_pct", "mode", "ploss_q1", "ploss_rect",
          "ploss_d1", "ploss_dcr1", "ploss_dcr2", "ploss_rshunt", "ploss_cout",
          "ploss_sum", "ploss_total_pin_pout", "vds_q1_max", "vds_q2_max",
          "ipk_pri", "irms_pri", "il2_end_of_period"]


def run_pass(rectifier, csv_name):
    rows = []
    for label, vin, vout_t, d, rload in POINTS:
        print(f"=== {rectifier} {label} : Vin={vin}V D={d} Rload={rload} ===")
        out = f"results/point18w9_{rectifier}_{label}.asc"
        r = run(vin, vout_t, d, rload, out=out, settle_periods=4000,
                measure_periods=100, pout=POUT_T, rectifier=rectifier)
        if "vout_avg" not in r:
            print(f"  ECHEC pour {label}, resultats partiels : {r}")
            continue
        il2_end = r.get("il2_end_of_period", 0.0)
        ipk = r.get("ipk_pri", 1.0)
        mode = "CCM" if abs(il2_end) > 0.05 * ipk else "DCM"
        ploss_sum = sum(r.get(k, 0.0) for k in
                         ["ploss_q1", "ploss_rect", "ploss_d1", "ploss_dcr1",
                          "ploss_dcr2", "ploss_rshunt", "ploss_cout"])
        ploss_total = r["pin_avg"] - r["pout_avg"]
        row = {
            "label": label, "vin": vin, "vout_target": vout_t, "d": d,
            "rload": rload,
            "vout_avg": round(r["vout_avg"], 4),
            "iout_avg": round(r["iout_avg"], 4),
            "pout_avg": round(r["pout_avg"], 4),
            "pin_avg": round(r["pin_avg"], 4),
            "eta_pct": round(100 * r["pout_avg"] / r["pin_avg"], 2),
            "mode": mode,
            "ploss_q1": round(r.get("ploss_q1", 0.0), 4),
            "ploss_rect": round(r.get("ploss_rect", 0.0), 4),
            "ploss_d1": round(r.get("ploss_d1", 0.0), 4),
            "ploss_dcr1": round(r.get("ploss_dcr1", 0.0), 4),
            "ploss_dcr2": round(r.get("ploss_dcr2", 0.0), 4),
            "ploss_rshunt": round(r.get("ploss_rshunt", 0.0), 4),
            "ploss_cout": round(r.get("ploss_cout", 0.0), 4),
            "ploss_sum": round(ploss_sum, 4),
            "ploss_total_pin_pout": round(ploss_total, 4),
            "vds_q1_max": round(r.get("vds_q1_max", 0.0), 3),
            "vds_q2_max": round(r.get("vds_q2_max", 0.0), 3),
            "ipk_pri": round(r.get("ipk_pri", 0.0), 4),
            "irms_pri": round(r.get("irms_pri", 0.0), 4),
            "il2_end_of_period": round(il2_end, 4),
        }
        rows.append(row)
        print(f"  Vout={row['vout_avg']}V Pout={row['pout_avg']}W "
              f"eta={row['eta_pct']}% mode={mode} "
              f"Vds_Q2_max={row['vds_q2_max']}V "
              f"(somme pertes={ploss_sum:.3f}W vs Pin-Pout={ploss_total:.3f}W)")

    with open(f"results/{csv_name}", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"\nEcrit results/{csv_name} ({len(rows)} points)\n")
    return rows


def main():
    run_pass("schottky", "envelope_18w9_schottky.csv")
    run_pass("sync_ideal", "envelope_18w9_sync.csv")


if __name__ == "__main__":
    main()
