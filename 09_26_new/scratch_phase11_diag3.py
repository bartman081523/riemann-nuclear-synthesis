# -*- coding: utf-8 -*-
"""Phase 11a, Teil 3: Details + Run-3-P-Regel (0 QPU)."""
import json
import numpy as np
import pt_ram_q_hardware_aer as aer
import pt_ram_q_hardware2_aer as s2b
from scratch_phase11_diag import load_all, coh_sens
from scratch_phase11_diag2 import bp_old_all


def is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def next_prime_above(n):
    p = n + 1
    while not is_prime(p):
        p += 1
    return p


def main():
    rows = load_all()
    bp_old = bp_old_all()
    s2b_res = json.load(open("pt_ram_q_stage2b_results.json"))
    print(f"{'key':12s} {'delta':>7s} {'bP':>7s} {'kdef':>7s} {'bP_kdef':>8s} "
          f"{'dcal':>7s} {'cP':>7s} {'gamma':>7s}")
    for arm in ("q3_d3", "q5_d5"):
        old = [r for r in rows if r["arm"] == arm and r["set"] == "old"]
        new = [r for r in rows if r["arm"] == arm and r["set"] == "new"]
        nq = s2b.NQ_BY_ARM[arm]
        for tag, sel in (("old", old), ("new", new)):
            for r in sel:
                bp = bp_old[r["key"]]["b_p"] if tag == "old" else s2b_res["b_p"][r["key"]]
                r["cP"] = coh_sens(r["pt"], nq, "worst")
                r["dcal"] = r["r_ro"] + bp * (r["kappa"] - 1.0) - r["ratio"]
            cp = np.array([r["cP"] for r in sel])
            dc = np.array([r["dcal"] for r in sel])
            g = float(cp @ dc / (cp @ cp))
            print(f"-- {arm} {tag}: gamma_LSQ {g:.5f}")
            for r in sel:
                print(f"{r['key']:12s} {r['delta']:7.4f} {bp:7.4f} {1-r['kappa']:7.4f} "
                      f"{bp*(1-r['kappa']):8.4f} {r['dcal']:7.4f} {r['cP']:7.4f} "
                      f"{r['dcal']/r['cP']:7.4f}")
    # Run-3 P-Regel
    print("\n=== Run-3 P-Regel: kleinste Primzahl > P_alt+30, nicht in gemessener Vereinigung ===")
    used = {"q3_d3": sorted(set(hw_q3() ) | set(s2b_pts("q3_d3"))),
            "q5_d5": sorted(set(hw_q5()) | set(s2b_pts("q5_d5")))}
    alt = {"q3_d3": [149, 197, 251, 347, 433, 577, 659, 761],
           "q5_d5": [433, 499, 577, 631, 659]}
    for arm, alt_pts in alt.items():
        out = []
        for P in alt_pts:
            cand = next_prime_above(P + 30)
            skipped = []
            while cand in used[arm]:
                skipped.append(cand)
                cand = next_prime_above(cand)
            out.append((P, cand, skipped))
        print(f"{arm}: used {used[arm]}")
        for P, cand, sk in out:
            print(f"  {P} -> {cand}" + (f"  (uebersprungen: {sk})" if sk else ""))
        assert all(is_prime(c) for _, c, _ in out)
        assert all(c not in used[arm] for _, c, _ in out)


def hw_q3():
    import pt_ram_q_hardware as hw
    return hw.Q3_POINTS


def hw_q5():
    import pt_ram_q_hardware as hw
    return hw.Q5_POINTS


def s2b_pts(arm):
    return [k[1] for k in (s2b._point_pts() | s2b._diagnostik_pts()) if k[0] == arm]


if __name__ == "__main__":
    main()
