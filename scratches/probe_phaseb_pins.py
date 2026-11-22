"""Probe: restliche Phase-B-Pins für die Test-Tabellen (C-Reihe)."""
import json
import sys
from fractions import Fraction as F

sys.path.insert(0, "src")
import primequant as pq
import primequant.channels as ch
from primequant import observables as obs, distributions as dt, bands as bnd, _anchors as an

print("== C1 struct row fields ==")
dok = an.lies_rohdokument("pt_ram_q_prio48_sv_raw.json")
reihen = dok["counts"]
struct = [z for z in reihen if z["kind"] == "structure"]
print("first struct row keys =", sorted(struct[0].keys()))
print(json.dumps({k: v for k, v in struct[0].items() if k != "counts"}, sort_keys=True)[:600])

print("== C2 struct quote tie (first row) ==")
z = struct[0]
kc = obs.punkt_konstanten(181, 3, 3)
res = obs.quote_exakt(z["counts"], kc)
print("name =", z["name"])
print("m_hat =", res["m_hat"], "num =", res["q_sum_N_sq_nd_sum_N2"] if False else res["q_sum_N_sq_minus_m2"],
      "anteil_falt =", str(res["anteil_falt"]), "quote =", str(res["quote"]))
print("quote_flt repr =", repr(float(res["quote_flt"])))

print("== C3 ratio-path params ==")
ops = {"sx": 6, "rz": 5, "measure": 2, "cz": 1, "x": 1}
m_ratio = ch.ChannelModel.aus_op_counts(ops, {
    "p_1q": ch.Param("p_1q", F(1, 64), "geschätzt:Hypothese", "kein on-disk Datum"),
    "ratio_2q": ch.Param("ratio_2q", 4, "geschätzt:Hypothese", "kein on-disk Datum")})
print("params keys =", sorted(m_ratio.params.keys()))
for name, prm in m_ratio.params.items():
    print("  ", name, "|", prm.herkunft, "|", str(prm.wert))
jj = m_ratio.als_json()
print("json params keys =", sorted(jj["params"].keys()))
print("json p_2q_eff =", jj["p_2q_eff"], "| json p_1q_eff =", jj["p_1q_eff"])
print("json herkunft p_2q =", jj["params"]["p_2q"]["herkunft"])
m_ex = ch.ChannelModel.aus_op_counts(ops, {
    "p_1q": ch.Param("p_1q", F(1, 64), "exakt-definiert", "Definition des Pilot-Modells"),
    "p_2q": ch.Param("p_2q", F(1, 16), "exakt-definiert", "Definition des Pilot-Modells")})
gr3 = m_ex.garantie()
print("EXAKT-Variante:", gr3.klasse, "|", gr3.herkunft, "|", gr3.grenze, "|", str(gr3.quelle)[:80])

print("== C4 norm(ω−1) = q — Identität ==")
for q in (2, 3, 5, 7, 11):
    el = (-1,) if q == 2 else tuple([-1, 1] + [0]*(q-3))
    print("q =", q, "norm =", str(obs.norm_galois(el, q)))

print("== C5 rest synth pins ==")
print("abklingen d3 γ=1/2 alle Qubits:", [str(f) for f in ch.abklingen_probs(pq.delta_vektor(2, 3), F(1,2), 4)])
print("abklingen label2 γ=1/2 alle:", [str(f) for f in ch.abklingen_probs(pq.delta_vektor(2, 2), F(1,2), 4)])
print("depolarisiert qubits=[0] δ0:", [str(f) for f in ch.depolarisiert_probs(pq.delta_vektor(2), F(1,2), 4, qubits=[0])])
print("auslese δ0 ro=1/4:", [str(f) for f in ch.auslese_probs(pq.delta_vektor(1), F(1,4), 2)])
print("auslese δ3 ro=1/4 breite4:", [str(f) for f in ch.auslese_probs(pq.delta_vektor(2, 3), F(1,4), 4)])
print("norm q=2 über (2,):", str(obs.norm_galois((2,), 2)))
print("tv über-Modell:", dt.tv_exakt({"1": 3}, [F(1)]))
print("exakte_masse gemischt:", dt.exakte_masse_am_label({"1": 2, "01": 3}, 1))
print("zaehlung Fusion:", dt.zaehlung_auf_labels({"1": 2, "01": 3}, 4))

print("== C6 bandedge ==")
kc_lo, kc_hi = bnd.band_quantile(F(1,5), 8192, F(1,20), 5)
print("Kanten:", (kc_lo, kc_hi))
print("cdf(k_lo) <= 1/200 < cdf(k_lo+1):",
      bnd.binom_cdf_exakt(kc_lo, 8192, F(1,5)) <= F(1,200) < bnd.binom_cdf_exakt(kc_lo + 1, 8192, F(1,5)))
print("tail(k_hi) <= 1/200 < tail(k_hi-1):",
      bnd.binom_tail_exakt(kc_hi, 8192, F(1,5)) <= F(1,200) < bnd.binom_tail_exakt(kc_hi - 1, 8192, F(1,5)))