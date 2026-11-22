import json, math, itertools
import numpy as np

r = json.load(open('pt_test2_entanglement_comovement_results.json'))
gp = {p['N']: p for p in r['grid_points']}
NS = [15,31,63,127,255,511,1023,10000,100000,1000000]
g  = np.array([gp[N]['K3_q95_001'] for N in NS], float)
gm = np.array([gp[N]['K3_median_001'] for N in NS], float)
g5 = np.array([gp[N]['K3_q95_005'] for N in NS], float)
rv = np.array([float(gp[N]['n_valid_base']) for N in NS], float)
# AXIS_FROZEN aus dem 049-Runner (bits): S-Achse strikt monotone Folge
# aus dem frischen Gate-D — hier aus dem 049b-Ergebnis-File? Nein: 049b-File
# enthaelt S_valid. Aber rekonstruierbar: S_rank = 1..10 (strikt monotone
# Achse, Gate-D bit-exakt). Wir nehmen die committeten 049b-Werte.
rb = json.load(open('pt_test2b_rank_controlled_results.json'))
print('049b konf:', rb['konfund_kit'])
# Arrays in 049b-File?
print('049b keys:', sorted(rb.keys()))
S = None
for k in ('S_valid','verdict_arrays','arrays','rank_arrays'):
    if k in rb: print(k, rb[k])
