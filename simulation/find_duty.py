"""Trouve par bissection le duty cycle donnant Vout_cible a Vin/Rload fixes
(Vout(D) monotone croissant, confirme par le balayage complet precedent)."""
import sys

sys.path.insert(0, ".")
from run_point import run


def find_duty(vin, vout_target, rload, d_lo=0.02, d_hi=0.6, tol=0.015,
              max_iter=10, settle_periods=1500):
    r = None
    for i in range(max_iter):
        d = (d_lo + d_hi) / 2
        r = run(vin, vout_target, d, rload, out="_find_tmp.asc",
                settle_periods=settle_periods)
        vout = r.get("vout_avg")
        if vout is None:
            print(f"  iter {i}: D={d:.4f} -> ECHEC")
            d_hi = d
            continue
        print(f"  iter {i}: D={d:.4f} -> Vout={vout:.4f}V (cible {vout_target}V)")
        if abs(vout - vout_target) / vout_target < tol:
            return d, r
        if vout < vout_target:
            d_lo = d
        else:
            d_hi = d
    return d, r


if __name__ == "__main__":
    vin = float(sys.argv[1])
    vout_t = float(sys.argv[2])
    rload = float(sys.argv[3])
    d_lo = float(sys.argv[4]) if len(sys.argv) > 4 else 0.02
    d_hi = float(sys.argv[5]) if len(sys.argv) > 5 else 0.6
    d, r = find_duty(vin, vout_t, rload, d_lo=d_lo, d_hi=d_hi)
    print(f"FINAL: D={d:.4f} Vout={r.get('vout_avg'):.4f}V Pout={r.get('pout_avg'):.4f}W "
          f"eta={100*r.get('pout_avg')/r.get('pin_avg'):.1f}%")
