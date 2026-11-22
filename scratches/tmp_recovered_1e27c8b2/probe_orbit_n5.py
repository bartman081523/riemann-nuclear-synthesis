import sys
sys.path.insert(0, "/run/media/julian/ML4/riemann/scratches")
sys.path.insert(0, "/run/media/julian/ML4/riemann")
import h9_atom_n5 as m
import pt_s4_closure_theorem as s4
for n, expect in ((3, (3,)), (4, (3, 12)), (5, (15, 30))):
    pats = m.make_patterns(n)
    groups = {}
    for p in pats:
        groups.setdefault(m.orbit_rep(p, n), []).append(p)
    sizes = tuple(sorted(len(v) for v in groups.values()))
    adj_split = []
    for rep, members in groups.items():
        flags = {s4.is_adjacent(p) for p in members}
        assert len(flags) == 1, (n, flags)
        adj_split.append((flags.pop(), len(members)))
    adj_split.sort(reverse=True, key=lambda t: (t[0], t[1]))
    print(f"n={n}: {len(pats)} Muster, Bahnen {sizes}, adj/disj {adj_split}")
    assert sizes == expect, (sizes, expect)
print("orbit_probe OK")
