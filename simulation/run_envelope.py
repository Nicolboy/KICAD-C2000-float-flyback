"""Etape 4 : lance les points de fonctionnement retenus (Vin x Vout_cible,
duty cycle trouve par find_duty.py) avec le reglage detaille (4000
periodes), ecrit results/envelope.csv."""
import csv
import sys

sys.path.insert(0, ".")
from run_point import run

POINTS = [
    # (label, vin, vout_target, d, rload, pout_target)
    ("11V_6V", 11.0, 6.0, 0.3828, 3.6, 10.0),
    ("11V_12V", 11.0, 12.0, 0.5359, 14.4, 10.0),
    ("20V_6V", 20.0, 6.0, 0.2500, 3.6, 10.0),
    ("20V_12V", 20.0, 12.0, 0.3016, 14.4, 10.0),
    ("25V_6V", 25.0, 6.0, 0.2109, 3.6, 10.0),
    ("25V_12V", 25.0, 12.0, 0.2625, 14.4, 10.0),
    ("20V_6V_light", 20.0, 6.0, 0.1134, 36.0, 1.0),
]

FIELDS = ["label", "vin", "vout_target", "d", "rload", "vout_avg", "iout_avg",
          "pout_avg", "pin_avg", "eta_pct", "mode", "ploss_q1", "ploss_q2body",
          "ploss_dcr1", "ploss_dcr2", "ploss_rshunt", "ploss_cout",
          "ploss_sum", "ploss_total_pin_pout", "vds_q1_max", "vds_q2_max",
          "ipk_pri", "irms_pri"]


def main():
    rows = []
    for label, vin, vout_t, d, rload, pout_t in POINTS:
        print(f"=== {label} : Vin={vin}V D={d} Rload={rload} ===")
        out = f"results/point_{label}.asc"
        r = run(vin, vout_t, d, rload, out=out, settle_periods=4000,
                measure_periods=100, pout=pout_t)
        if "vout_avg" not in r:
            print(f"  ECHEC pour {label}, resultats partiels : {r}")
            continue
        il2_end = r.get("il2_end_of_period", 0.0)
        mode = "CCM" if abs(il2_end) > 0.05 * r.get("ipk_pri", 1.0) else "DCM"
        ploss_sum = sum(r.get(k, 0.0) for k in
                         ["ploss_q1", "ploss_q2body", "ploss_dcr1",
                          "ploss_dcr2", "ploss_rshunt", "ploss_cout"])
        ploss_total = r["pin_avg"] - r["pout_avg"]
        row = {
            "label": label, "vin": vin, "vout_target": vout_t, "d": d,
            "rload": rload,
            "vout_avg": r.get("vout_avg"), "iout_avg": r.get("iout_avg"),
            "pout_avg": r.get("pout_avg"), "pin_avg": r.get("pin_avg"),
            "eta_pct": 100 * r["pout_avg"] / r["pin_avg"],
            "mode": mode,
            "ploss_q1": r.get("ploss_q1"), "ploss_q2body": r.get("ploss_q2body"),
            "ploss_dcr1": r.get("ploss_dcr1"), "ploss_dcr2": r.get("ploss_dcr2"),
            "ploss_rshunt": r.get("ploss_rshunt"), "ploss_cout": r.get("ploss_cout"),
            "ploss_sum": ploss_sum, "ploss_total_pin_pout": ploss_total,
            "vds_q1_max": r.get("vds_q1_max"), "vds_q2_max": r.get("vds_q2_max"),
            "ipk_pri": r.get("ipk_pri"), "irms_pri": r.get("irms_pri"),
        }
        rows.append(row)
        print(f"  Vout={row['vout_avg']:.3f}V Pout={row['pout_avg']:.3f}W "
              f"eta={row['eta_pct']:.1f}% mode={mode} "
              f"(somme pertes={ploss_sum:.3f}W vs Pin-Pout={ploss_total:.3f}W)")

    with open("results/envelope.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"\nEcrit results/envelope.csv ({len(rows)} points)")


if __name__ == "__main__":
    main()
