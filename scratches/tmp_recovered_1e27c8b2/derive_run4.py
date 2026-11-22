import json, sys
sys.path.insert(0, "/run/media/julian/ML4/riemann")
import pt_ram_q_hardware as hw, pt_ram_q_hardware3 as h3
import pt_ram_q6_kingston as k6

UNION4 = set(hw.Q3_POINTS) | set(hw.Q5_POINTS) \
    | set(h3.CAL_Q3_POINTS) | set(h3.CAL_Q5_POINTS) \
    | set(h3.NEW_Q3_POINTS) | set(h3.NEW_Q5_POINTS)
print("run1 q3:", hw.Q3_POINTS); print("run1 q5:", hw.Q5_POINTS)
print("union4 size:", len(UNION4), "sorted:", sorted(UNION4))
cal3_4 = list(h3.NEW_Q3_POINTS); cal5_4 = list(h3.NEW_Q5_POINTS)
new3_4 = h3.new_points_run3(cal3_4, UNION4)
new5_4 = h3.new_points_run3(cal5_4, UNION4)
print("run4 CAL_Q3:", cal3_4)
print("run4 NEW_Q3:", new3_4)
print("run4 CAL_Q5:", cal5_4)
print("run4 NEW_Q5:", new5_4)
# disjunct check
assert not (set(new3_4) & set(cal3_4)) and not (set(new5_4) & set(cal5_4))
assert not (set(new3_4) & UNION4), set(new3_4) & UNION4
assert not (set(new5_4) & UNION4), set(new5_4) & UNION4
# records + d-invariance + cP for the 13 fresh verdict P
for P in new3_4 + new5_4:
    q, d = (3, h3.D3_MIN) if P in set(new3_4) else (5, h3.D5_MIN)
    pt = h3.arm_point(P, d, q)
    fam = (h3.D3_WIDE, 27) if q == 3 else (h3.D5_WIDE, 125)
    okfam = all(abs(h3.arm_point(P, dd, q)["ratio_true"] - pt["ratio_true"]) < 1e-12 for dd in fam)
    cP = json.loads(json.dumps(h3.coh_sens(pt))) if False else h3.coh_sens(pt)
    print(f"P={P} q={q} m={pt['m']} ratio_true={pt['ratio_true']:.6f} "
          f"L_q={pt['L_q']:.3e} d-invariance_family={okfam} "
          f"cP={float(cP):.6f}")
# 1-NN sanity: distances to old same-arm pools
pools = {"q3_d3": sorted(set(cal3_4) | set(h3.CAL_Q3_POINTS)),
         "q5_d5": sorted(set(cal5_4) | set(h3.CAL_Q5_POINTS))}
for arm, fresh in (("q3_d3", new3_4), ("q5_d5", new5_4)):
    for Pf in fresh:
        dists = sorted(((abs(Pf - Po), Po) for Po in pools[arm]))[:2]
        print(f"1NN {arm} P={Pf}: nn={dists[0][1]} d={dists[0][0]} | second={dists[1][1]} d={dists[1][0]}")
