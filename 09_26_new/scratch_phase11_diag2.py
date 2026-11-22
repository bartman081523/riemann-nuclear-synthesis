# -*- coding: utf-8 -*-
"""Phase 11a, Teil 2: v3b-Transfer-Test auf committeten Run-2-Daten (0 QPU).

v3b-Gesetz: center_v3 = (1-1/S)*(ratio_ro_exact(pt, ro_hat) + b_P*(kappa-1)
             - gamma_arm*cP) + L_q
  b_P  = Aer-exakt-Steigung pro Punkt (fuer die 13 NEUEN P: committet im
         Stage-2b-Resultat; fuer die 13 ALTEN P: hier offline nachgerechnet)
  cP   = klassisch exakte worst-case kohärente Empfindlichkeit (scratch1)
  gamma_arm = in-job LSQ-durch-Null auf dem Kalibrier-Bein (13 alte P)
Transfer-Test: gamma aus ALTEN Punkten fitten -> Residuen der NEUEN Punkte.
"""
import json
import numpy as np
import pt_ram_q_hardware_aer as aer
import pt_ram_q_hardware2_aer as s2b
from scratch_phase11_diag import load_all, coh_sens, share_grad

BP_OLD_CACHE = "scratch_bp_old.json"


def bp_old_all():
    try:
        return json.load(open(BP_OLD_CACHE))
    except FileNotFoundError:
        pass
    out = {}
    for key, pt in sorted(s2b._diagnostik_pts().items()):
        nq = s2b.NQ_BY_ARM[key[0]]
        curve = [aer.exact_point_level(pt, nq, p1) for p1 in s2b.STRESS_GRID_P1]
        fit = aer.fit_b_p([c["kappa"] for c in curve], [c["ratio"] for c in curve])
        out[f"{key[0]}|{key[1]}"] = {"b_p": fit["b_p"],
                                     "intercept": fit["intercept"],
                                     "max_res": fit["max_res"],
                                     "n_nodes": fit["n_nodes"],
                                     "ratio_ro": aer.ratio_ro_exact(pt, aer.RO_STRESS, nq)}
        print(f"bp_old {key[0]}|{key[1]}: b_p {fit['b_p']:.4f} "
              f"max_res {fit['max_res']:.2e} n_nodes {fit['n_nodes']}")
    json.dump(out, open(BP_OLD_CACHE, "w"), indent=1)
    return out


def main():
    rows = load_all()
    bp_old = bp_old_all()
    print()
    print("=== v3b-Transfer (gamma LSQ-durch-Null auf 13 alten P) ===")
    w_transfer = {}
    for arm in ("q3_d3", "q5_d5"):
        old = [r for r in rows if r["arm"] == arm and r["set"] == "old"]
        new = [r for r in rows if r["arm"] == arm and r["set"] == "new"]
        nq = s2b.NQ_BY_ARM[arm]
        # delta_cal = ratio_ro + bP*(kappa-1) - ratio  (kohärenter Floor-Anteil)
        for r in old:
            bp = bp_old[f"{r['key']}"]["b_p"]
            r["cP"] = coh_sens(r["pt"], nq, "worst")
            r["delta_cal"] = (r["r_ro"] + bp * (r["kappa"] - 1.0) - r["ratio"])
        for r in new:
            v = json.load(open("pt_ram_q_stage2b_results.json"))["b_p"][r["key"]]
            r["cP"] = coh_sens(r["pt"], nq, "worst")
            r["delta_cal"] = (r["r_ro"] + v * (r["kappa"] - 1.0) - r["ratio"])
        cp = np.array([r["cP"] for r in old])
        dc = np.array([r["delta_cal"] for r in old])
        g_lsq = float(cp @ dc / (cp @ cp))
        g_mean = float(np.mean(dc / cp))
        print(f"\n{arm}: gamma_LSQ {g_lsq:.4f}  gamma_mean {g_mean:.4f}")
        for tag, g in (("LSQ", g_lsq), ("mean", g_mean)):
            res_old = [r["delta_cal"] - g * r["cP"] for r in old]
            res_new = [r["delta_cal"] - g * r["cP"] for r in new]
            mo = max(abs(x) for x in res_old)
            mn = max(abs(x) for x in res_new)
            print(f"  {tag}: in-cal max|res| {mo:.4f} -> transfer max|res| {mn:.4f}")
            print(f"      transfer res: {['%+.4f' % x for x in res_new]}")
            w_transfer[(arm, tag)] = mn
    print()
    print("w_B''-Kandidaten (max ueber Arme):",
          {k: round(v, 4) for k, v in w_transfer.items()})
    # 541-Konsistenz: res_v1 run1 vs run2 (d-Inv-Bein)
    print("\n=== 541-Querkonsistenz (run1 d=25 vs run2 d=5) ===")
    e = json.load(open("pt_ram_q_hardware2_eval.json"))
    for key, v in e["d_invarianz_bein"]["punkte"].items():
        if v["P"] in (401, 463, 541, 599, 625):
            print(f"{key}: res_v1_run1 {v['res_v1_run1']:+.4f}  "
                  f"res_v1_run2 {v['res_v1_run2']:+.4f}  delta {v['res_v1_run2']-v['res_v1_run1']:+.4f}")


if __name__ == "__main__":
    main()
