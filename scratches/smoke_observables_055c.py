# -*- coding: utf-8 -*-
"""Smoke-Test src/primequant/observables.py gegen das gefrorene Gesetz (0 QPU).

Anker:
* Galois-Summe: N(1 - omega) = q fuer q in {2,3,5,7,11}; N(omega^k) = 1.
* punkt_konstanten == hw.arm_point feldweise (ein-Rundung-Felder bit-exakt).
* quote_exakt == hwa.ratio_from_counts auf den committeten 055b-struct-
  Reihen: Faltform bit-exakt (Delta == 0.0), FFT-Pfad <= 2 ULP.
"""
import json
import sys

sys.path.insert(0, ".")

import pt_ram_q_hardware as hw
import pt_ram_q_hardware_aer as hwa
from primequant import _cyc
from primequant import observables as obs

failures = []


def check(label, ok, detail=""):
    status = "OK  " if ok else "FAIL"
    print(f"[{status}] {label} {detail}")
    if not ok:
        failures.append(label)


# ---- 1) Galois-Norm-Pins -------------------------------------------------
for q in (2, 3, 5, 7, 11):
    if q == 2:
        element = (2,)                       # 1 - omega mit omega = -1
    else:
        element = tuple([1, -1] + [0] * (q - 3))
    wert = obs.norm_galois(element, q)
    check(f"N(1-omega)=q, q={q}", wert == q, f"erhalten {wert}")

for q in (3, 5, 7):
    potenz = tuple(_cyc.cyc_omega(q, 2))
    e2 = obs.norm_galois(potenz, q)
    check(f"N(omega^2)=1, q={q}", e2 == 1, f"erhalten {e2}")

# ---- 2) punkt_konstanten == arm_point ------------------------------------
punkte = [(181, 3, 3), (181, 5, 5), (269, 3, 3), (269, 5, 5),
          (673, 3, 3), (673, 5, 5), (2005, 3, 3), (2005, 5, 5)]
for (P, d, q) in punkte:
    ap = hw.arm_point(P, d, q)
    kc = obs.punkt_konstanten(P, d, q)
    for k in ("m", "n_d", "N", "n0", "q_sum_N_sq_minus_m2"):
        check(f"arm_point/{k} P={P} d={d} q={q}", ap[k] == kc[k])
    for k in ("ratio_true", "share_true_reg", "model_share_reg", "L_q"):
        hw_f, ex = ap[k], float(kc[k])
        check(f"arm_point/{k} bit-exakt P={P} d={d} q={q}", hw_f == ex,
              f"hw={hw_f!r} exakt->float={ex!r}")
    for k in ("closed_form", "sigma2", "delta", "delta_sq"):
        if k in ap and k in kc:
            hw_f, ex = ap[k], float(kc[k])
            rel = abs(hw_f - ex) / max(2.0 ** -40, abs(hw_f))
            check(f"arm_point/{k} Float-Kette P={P} d={d} q={q}",
                  hw_f == ex or rel < 1e-6,
                  f"hw={hw_f!r} exakt->float={ex!r}")

# ---- 3) quote_exakt gegen ratio_from_counts (committete 055b-Reihen) -----
with open("pt_ram_q_prio48_sv_raw.json", encoding="utf-8") as fh:
    raw = json.load(fh)
rows = raw["counts"]
struct_rows = [r for r in rows
               if r["kind"] in ("structure", "kalibrier_structure")]
check("111 struct-Reihen erwartet", len(struct_rows) == 111,
      f"erhalten {len(struct_rows)}")

for r in struct_rows:
    q_arm = 3 if r["arm"] == "q3" else 5
    P, d, q = r["P"], q_arm, q_arm
    ap = hw.arm_point(P, d, q)
    nq = hwa.nq_of(ap)
    gesetz = hwa.ratio_from_counts(r["counts"], ap, nq)
    kc = obs.punkt_konstanten(P, d, q)
    res = obs.quote_exakt(r["counts"], kc)
    check(f"m_hat==m ({r['name']})",
          res["m_hat"] == ap["m"] == gesetz["m_hat"],
          f"exakt={res['m_hat']} hw={gesetz['m_hat']}")
    # Faltform bit-exakt: EINE Rundung auf beiden Seiten (Theorem-Satz).
    nf = [0] * (2 ** nq)
    for bits, c in r["counts"].items():
        nf[int(bits.replace(" ", ""), 2)] += c
    n_hat_flt = (ap["m"] * hwa.fold_d(nf, d) / hw.SHOTS).tolist()
    gefalt = hwa.share_hw_folded(n_hat_flt, q, d, float(sum(n_hat_flt)))
    check(f"Faltform bit-exakt ({r['name']})",
          gefalt == res["anteil_flt_falt"],
          f"falt={gefalt!r} exakt->float={res['anteil_flt_falt']!r}")
    # FFT-Pfad (committete Quote-Kette): <= 2 ULP
    dif = abs(gesetz["ratio"] - res["quote_flt"])
    ulp = abs(res["quote_flt"]) * 2.220446049250313e-16
    check(f"FFT-Quote <= 2 ULP ({r['name']})", dif <= 2.0 * ulp or dif == 0.0,
          f"|delta|={dif:.3e} quote={res['quote_flt']!r}")

# ---- 4) distributions: TV-Konvention + Delta-Saettigung ------------------
import math
from fractions import Fraction

import primequant.distributions as dist

kontrolle_pins = {
    "ctrl_composite_P181_d3": (
        dist.modell_kontrolle_composite([19, 13, 10], 42),
        Fraction(551, 86016),
    ),
    "ctrl_uniform_q3": (
        dist.modell_kontrolle_uniform(3),
        Fraction(79, 24576),
    ),
    "ctrl_composite_P467_d5": (
        dist.modell_kontrolle_composite([23, 18, 17, 15, 18], 91),
        Fraction(835, 106496),
    ),
    "ctrl_uniform_q5": (
        dist.modell_kontrolle_uniform(5),
        Fraction(31, 2560),
    ),
}
for r in [x for x in rows if x["kind"] == "negative_control"]:
    modell, pin = kontrolle_pins[r["name"]]
    tv = dist.tv_exakt(r["counts"], modell)
    check(f"TV-Pin exakt ({r['name']})", tv == pin, f"{tv} vs Pin {pin}")

delta_reihen = [x for x in rows if x["kind"] in dist.DELTA_REIHENARTEN]
check("45 Delta-Reihen erwartet", len(delta_reihen) == 45,
      f"erhalten {len(delta_reihen)}")
for r in delta_reihen:
    nq = len(next(iter(r["counts"].keys())))
    modell, pin = kontrolle_pins.get(
        r["name"], (dist.modell_fuer_art(r["kind"], nq), None)
    )
    tv = dist.tv_exakt(r["counts"], dist.modell_fuer_art(r["kind"], nq))
    check(f"Delta-TV==0 ({r['name']})", tv == 0, f"erhalten {tv}")

struktur_modell = dist.modell_fuer_art("structure", 2, [19, 13, 10], 42)
check("struktur-Modell Laenge 2^nq", len(struktur_modell) == 4,
      f"erhalten {len(struktur_modell)}")
check("struktur-Modell Summe 1", sum(struktur_modell) == 1)
uniform_modell = dist.modell_fuer_art("negative_control", 3, q=5)
check("uniform-Modell Laenge 8 / 1/5", len(uniform_modell) == 8 and
      uniform_modell[0] == Fraction(1, 5) and uniform_modell[7] == 0)

try:
    dist.tv_exakt({"00": 10}, [Fraction(1, 3), Fraction(1, 3)])
    tv_guard_ok = False
    tv_guard_detail = "kein Fehler geworfen"
except ValueError as exc:
    tv_guard_ok = True
    tv_guard_detail = str(exc)
check("tv_exakt verweigert Modell-Summe != 1", tv_guard_ok and
      "Modell-Summe" in tv_guard_detail, tv_guard_detail)

try:
    dist.modell_fuer_art("negative_control", 2)
    ctrl_guard_ok = False
    ctrl_guard_detail = "kein Fehler geworfen"
except ValueError as exc:
    ctrl_guard_ok = True
    ctrl_guard_detail = str(exc)
check("negative_control ohne n_d/q verweigert", ctrl_guard_ok and
      "Klassen-Ebene" in ctrl_guard_detail, ctrl_guard_detail)

# ---- 5) bands: exakte CDF + Band-Kanten + Schranken ----------------------
from scipy.stats import binom as scipy_binom

import primequant.bands as bnd

# (a) Kleine-S-Kreuzchecks gegen scipy (ABGELEITET-Kreuzcheck, nie Quelle):
for (p_frac, S_klein, k_probe) in [
    (Fraction(1, 5), 60, 8), (Fraction(1, 3), 60, 17),
    (Fraction(1, 2), 61, 37), (Fraction(19, 42), 60, 30),
    (Fraction(23, 91), 60, 11),
]:
    exakt = bnd.binom_cdf_exakt(k_probe, S_klein, p_frac)
    float_cdf = float(exakt)
    dif = abs(float_cdf - scipy_binom.cdf(k_probe, S_klein, float(p_frac)))
    check(f"CDF scipy-Kreuz p={p_frac} S={S_klein} k={k_probe}",
          dif <= 1e-12, f"|diff|={dif:.3e}")

# (b) Exakte Identitaeten: Entartung, Spiegel, Vollstaendigkeit, Einzelterm.
for p_frac in (Fraction(1, 5), Fraction(1, 3), Fraction(19, 42)):
    num_i, den_i = Fraction(p_frac).numerator, Fraction(p_frac).denominator
    check(f"cdf(S)==1 p={p_frac}", bnd.binom_cdf_exakt(60, 60, p_frac) == 1)
    check(f"cdf(k<0)==0 p={p_frac}",
          bnd.binom_cdf_exakt(-1, 60, p_frac) == 0)
    check(f"tail(0)==1 p={p_frac}", bnd.binom_tail_exakt(0, 60, p_frac) == 1)
    total = sum(math.comb(60, k) * num_i ** k * (den_i - num_i) ** (60 - k)
                for k in range(61))
    check(f"Walk-Gesamtsumme==den^S p={p_frac}", total == den_i ** 60)
    term13 = math.comb(60, 13) * num_i ** 13 * (den_i - num_i) ** 47
    cdf13 = (bnd.binom_cdf_exakt(13, 60, p_frac)
             - bnd.binom_cdf_exakt(12, 60, p_frac))
    check(f"Einzelterm==CDF-Diffe p={p_frac} k=13",
          cdf13 == Fraction(term13, den_i ** 60))

# (c) Band-Kanten synthetisch (p=1/5, S=60, alpha=1/20, Bonferroni 5):
p_syn = Fraction(1, 5)
k_lo_s, k_hi_s = bnd.band_quantile(p_syn, 60, Fraction(1, 20), 5)
check("Kante-unten Definition (S=60)",
      bnd.binom_cdf_exakt(k_lo_s, 60, p_syn) <= Fraction(1, 200)
      and bnd.binom_cdf_exakt(k_lo_s + 1, 60, p_syn) > Fraction(1, 200),
      f"k_lo={k_lo_s}")
check("Kante-oben Definition (S=60)",
      bnd.binom_tail_exakt(k_hi_s, 60, p_syn) <= Fraction(1, 200)
      and bnd.binom_tail_exakt(k_hi_s - 1, 60, p_syn) > Fraction(1, 200),
      f"k_hi={k_hi_s}")

# (d) Chebyshev/Cantelli exakt-oben + Ordnung:
cheb = bnd.chebyshev_schranke(Fraction(12), 60, p_syn)
cant = bnd.cantelli_schranke(Fraction(12), 60, p_syn)
echter_tail = bnd.binom_tail_exakt(24, 60, p_syn)  # P(X - 12 >= 12)
check("Cantelli >= echtem einseitigen Tail", cant >= echter_tail)
check("Chebyshev >= zweiseitigem Umschluss", cheb >= echter_tail)
check("Cantelli <= Chebyshev (d > 0)", cant <= cheb,
      f"cant={cant} cheb={cheb}")

# (e) COMMITTED ANCHOR — uniform_q5 V11 exakt (alle 5 Labels simultan):
label_of = {"000": 0, "001": 1, "010": 2, "011": 3, "100": 4}
for r_ctrl in [x for x in rows if x["kind"] == "negative_control"]:
    if r_ctrl["name"] == "ctrl_uniform_q5":
        modell_ctrl = dist.modell_kontrolle_uniform(5)
        for bits, c_wert in sorted(r_ctrl["counts"].items()):
            label = label_of[bits]
            p_wert_lb = bnd.p_wert_zweiseitig(c_wert, 8192, Fraction(1, 5))
            im_band = p_wert_lb > Fraction(1, 200)
            check(f"V11 Label {bits} ({c_wert}) p_wert>1/200",
                  im_band, f"p_wert~{float(p_wert_lb):.6f}")
    if r_ctrl["name"] == "ctrl_uniform_q3":
        p_wert_q3 = bnd.p_wert_zweiseitig(r_ctrl["counts"]["01"], 8192,
                                          Fraction(1, 3))
        check("uniform_q3 max-dev Label (01) im Band",
              p_wert_q3 > Fraction(1, 200),
              f"p_wert~{float(p_wert_q3):.6f}")
    if r_ctrl["name"] == "ctrl_composite_P181_d3":
        p_wert_c3 = bnd.p_wert_zweiseitig(r_ctrl["counts"]["10"], 8192,
                                          Fraction(10, 42))
        check("composite_q3 max-dev Label (10) im Band",
              p_wert_c3 > Fraction(1, 200),
              f"p_wert~{float(p_wert_c3):.6f}")
    if r_ctrl["name"] == "ctrl_composite_P467_d5":
        p_wert_c5 = bnd.p_wert_zweiseitig(r_ctrl["counts"]["100"], 8192,
                                          Fraction(18, 91))
        check("composite_q5 max-dev Label (100) im Band",
              p_wert_c5 > Fraction(1, 200),
              f"p_wert~{float(p_wert_c5):.6f}")

# (e2) Band-Kanten auf committeten Parametern (uniform_q5 Bonferroni-5):
k_lo_c, k_hi_c = bnd.band_quantile(Fraction(1, 5), 8192,
                                   Fraction(1, 20), 5)
ctrl_q5_counts = next(x for x in rows
                      if x["name"] == "ctrl_uniform_q5")["counts"]
min_count = min(int(ctrl_q5_counts[b])
                for b in ("000", "001", "010", "011", "100"))
max_count = max(int(ctrl_q5_counts[b])
                for b in ("000", "001", "010", "011", "100"))
check("alle 5 uniform_q5 Counts im Kanten-Band",
      k_lo_c < min_count and max_count < k_hi_c,
      f"k_lo={k_lo_c}, k_hi={k_hi_c}, min={min_count}, max={max_count}")
check("Kante-unten Definition (committet)",
      bnd.binom_cdf_exakt(k_lo_c, 8192, Fraction(1, 5)) <= Fraction(1, 200)
      and bnd.binom_cdf_exakt(k_lo_c + 1, 8192, Fraction(1, 5))
      > Fraction(1, 200))
check("Kante-oben Definition (committet)",
      bnd.binom_tail_exakt(k_hi_c, 8192, Fraction(1, 5)) <= Fraction(1, 200)
      and bnd.binom_tail_exakt(k_hi_c - 1, 8192, Fraction(1, 5))
      > Fraction(1, 200))

# (f) Bonferroni-Exaktheit:
check("alpha_bonferroni 1/20/5 == 1/100",
      bnd.alpha_bonferroni(Fraction(1, 20), 5) == Fraction(1, 100))

# ---- 6) channels: exakter Diagonal-Zweig + Kraus-Float-Schicht ------------
import numpy as np

import primequant.channels as chan
from primequant._guarantees import (
    AnchorViolation,
    Guarantee,
    pruefe_verkettung,
)

ULLP = 2.220446049250313e-16  # float-ULP-Skala (Anker-Konvention der Suite)

# (a) Depolarisieren: ganzes Register + 1q-Bein (Hand-Pins, exakt):
res_a = chan.depolarisiert_probs(
    P4 := [Fraction(1), Fraction(0), Fraction(0), Fraction(0)],
    Fraction(1, 5), 4)
check("depolarisiert voll [17/20,1/20,1/20,1/20]",
      res_a == [Fraction(17, 20), Fraction(1, 20), Fraction(1, 20),
                Fraction(1, 20)],
      f"erhalten {res_a}")
res_b = chan.depolarisiert_probs(P4, Fraction(1, 5), 4, qubits=(0,))
check("depolarisiert 1q [9/10,1/10,0,0]",
      res_b == [Fraction(9, 10), Fraction(1, 10), Fraction(0), Fraction(0)],
      f"erhalten {res_b}")

# (b) Abklingen: 1q + 2q-Kreuz-Terme (Hand-Pins):
res_c = chan.abklingen_probs([Fraction(1, 4), Fraction(3, 4)],
                             Fraction(1, 3), 2)
check("abklingen [1/4,3/4] γ=1/3 -> [1/2,1/2]",
      res_c == [Fraction(1, 2), Fraction(1, 2)], f"erhalten {res_c}")
p_zwei_eins = [Fraction(1, 2), Fraction(0), Fraction(0), Fraction(1, 2)]
res_c2 = chan.abklingen_probs(p_zwei_eins, Fraction(1, 2), 4, qubits=(0, 1))
check("abklingen 2q γ=1/2 -> [5/8,1/8,1/8,1/8]",
      res_c2 == [Fraction(5, 8), Fraction(1, 8), Fraction(1, 8),
                 Fraction(1, 8)], f"erhalten {res_c2}")

# (c) Auslese exakt + Dephasieren-Identitaet:
# Hand-Pin: new[b] = ro^h (1-ro)^(nq-h) mit h = Hamming(b, 0); new[0] =
# (1-ro)^2 = 9/16 (BEIDE Qubits korrekt gelesen), Summe 16/16 = 1:
res_d = chan.auslese_probs(P4, Fraction(1, 4), 4)
check("auslese ro=1/4 -> [9/16,3/16,3/16,1/16]",
      res_d == [Fraction(9, 16), Fraction(3, 16), Fraction(3, 16),
                Fraction(1, 16)], f"erhalten {res_d}")
res_e = chan.dephasieren_probs([Fraction(1, 3), Fraction(2, 3)],
                              Fraction(2, 5))
check("dephasieren == Identitaet auf Wahrscheinlichkeiten",
      res_e == [Fraction(1, 3), Fraction(2, 3)], f"erhalten {res_e}")

# (d) Dispatcher: apply_to_probs_diag == direkter Kanal-Aufruf:
k_dep = chan.Kanal("depolarisiert",
                   chan.Param("p_dep", Fraction(1, 5), "geschätzt:Hypothese"))
check("Dispatcher==direkt (depolarisiert)",
      chan.apply_to_probs_diag(P4, k_dep, 4) == res_a)
k_ab = chan.Kanal("abklingen",
                  chan.Param("g", Fraction(1, 2), "geschätzt:Hypothese"),
                  qubits=(0, 1))
check("Dispatcher==direkt (abklingen)",
      chan.apply_to_probs_diag(p_zwei_eins, k_ab, 4) == res_c2)
k_dph = chan.Kanal(
    "dephasieren",
    chan.Param("gphi", Fraction(2, 5), "kalibriert+2026-10-06T00:00:00Z"))
check("Dispatcher==direkt (dephasieren)",
      chan.apply_to_probs_diag(P4, k_dph, 4) == [Fraction(1), Fraction(0),
                                                 Fraction(0), Fraction(0)])
param_ro = chan.Param("ro", float(1 - 0.6 ** 0.5), "kalibriert+2026-10-02")
check("Param float -> Garantie ABGELEITET + grenze gesetzt",
      param_ro.garantie().klasse == "ABGELEITET"
      and param_ro.garantie().grenze is not None)

# (e) DIAGONAL-ABSCHLUSS-THEOREM im Float-Pfad — bitweise (Kohaerenz 0.0):
rho0 = chan.rho_diag([0.5, 0.0, 0.0, 0.5])
theo_proben = [
    ("depolarisiert2q", chan.kraus_depolarisiert(0.3, 2), (0, 1)),
    ("abklingen-q0", chan.kraus_abklingen(0.4), (0,)),
    ("dephasieren-q1", chan.kraus_dephasieren(0.6), (1,)),
    ("depolarisiert1q", chan.kraus_depolarisiert(0.3, 1), (1,)),
]
for (name, ops_t, q_sel) in theo_proben:
    rho_neu = chan.apply_kraus(rho0, ops_t, q_sel)
    check(f"Theorem Kohaerenz==0.0 bitweise ({name})",
          chan.kohärenz_max(rho_neu) == 0.0)
    check(f"Theorem Spur==1 ({name})",
          abs(np.trace(rho_neu).real - 1.0) < 1e-12)

# (f) Kraus-Float-Schicht == exakter Zweig (<= 2 ULP): Abklingen Kreuz:
rho_ab = chan.apply_kraus(chan.rho_diag([0.5, 0.5]),
                          chan.kraus_abklingen(1 / 3), (0,))
ex_c = chan.abklingen_probs([Fraction(1, 2), Fraction(1, 2)],
                            Fraction(1, 3), 2)
dif_ab = max(abs(float(v) - rho_ab[i, i].real) for i, v in enumerate(ex_c))
check("abklingen Float==exakt <= 2 ULP",
      dif_ab <= 2 * ULLP * max(abs(float(v)) for v in ex_c),
      f"|delta|={dif_ab:.3e}")
M_klass = chan.auslese_verwirrung(0.25, 2)
p_out = M_klass @ np.array([0.5, 0.0, 0.0, 0.5])
ex_l = chan.auslese_probs(p_zwei_eins, Fraction(1, 4), 4)
dif_l = max(abs(float(v) - p_out[i]) for i, v in enumerate(ex_l))
check("auslese klassisch==exakt <= 2 ULP",
      dif_l <= 2 * ULLP * max(abs(float(v)) for v in ex_l),
      f"|delta|={dif_l:.3e}")

# (g) ChannelModel: ISA-Op-Counts-Komposition (V12) + Garantie-Etikett:
ops_p = {"sx": 6, "rz": 5, "measure": 2, "cz": 1, "x": 1}
modell = chan.ChannelModel.aus_op_counts(ops_p, {
    "p_1q": chan.Param("p_1q", Fraction(1, 64), "geschätzt:Hypothese"),
    "p_2q": chan.Param("p_2q", Fraction(1, 16), "geschätzt:Hypothese"),
})
pin_p1 = Fraction(64 ** 7 - 63 ** 7, 64 ** 7)
check("p_1q_eff Integer-Walk Pin", modell.p_1q_eff == pin_p1,
      f"erhalten {modell.p_1q_eff}")
check("p_2q_eff == 1/16", modell.p_2q_eff == Fraction(1, 16))
check("fam_zuehler virtuell/1q/auslese/2q",
      modell.fam_zuehler == {"virtuell": 5, "1q": 7, "auslese": 2, "2q": 1},
      f"erhalten {modell.fam_zuehler}")
check("Modell-Klasse GESAMPFELT bei geschätzt-Params",
      modell.garantie().klasse == "GESAMPFELT"
      and modell.garantie().herkunft == "abgeleitet")

# ratio-Pfad: p_2q = p_1q * ratio_2q EXAKT; Klassen erben die SCHWAECHESTE:
modell_r = chan.ChannelModel.aus_op_counts(ops_p, {
    "p_1q": chan.Param("p_1q", Fraction(1, 64), "geschätzt:Hypothese"),
    "ratio_2q": chan.Param("ratio_2q", Fraction(4), "geschätzt:Hypothese"),
})
check("ratio-Pfad p_2q_eff == 1/16", modell_r.p_2q_eff == Fraction(1, 16))
check("ratio-Pfad p_2q == p_1q*ratio exakt",
      modell_r.params["p_2q"].wert == Fraction(1, 16))
check("ratio-Pfad p_2q erbt geschätzt (GESAMPFELT)",
      modell_r.params["p_2q"].garantie().klasse == "GESAMPFELT"
      and modell_r.params["p_2q"].herkunft.startswith("geschätzt:"),
      f"herkunft={modell_r.params['p_2q'].herkunft!r}")
check("ratio-Pfad Modell-Klasse GESAMPFELT",
      modell_r.garantie().klasse == "GESAMPFELT")

# kalibriert-Eingaben -> abgeleitet -> ABGELEITET (keine Aufwaerts-Wanderung):
modell_k = chan.ChannelModel.aus_op_counts(ops_p, {
    "p_1q": chan.Param("p_1q", Fraction(1, 64),
                       "kalibriert+2026-10-02T00:00:00Z"),
    "ratio_2q": chan.Param("ratio_2q", Fraction(4),
                           "kalibriert+2026-10-02T00:00:00Z"),
})
check("kalibriert-Ratio -> ABGELEITET",
      modell_k.params["p_2q"].garantie().klasse == "ABGELEITET"
      and modell_k.garantie().klasse == "ABGELEITET")

# alle-EXAKT -> EXAKT + "exakt-definiert" (Op-Counts = registrierte Struktur):
modell_e = chan.ChannelModel.aus_op_counts(ops_p, {
    "p_1q": chan.Param("p_1q", Fraction(1, 64), "exakt-definiert"),
    "p_2q": chan.Param("p_2q", Fraction(1, 16), "exakt-definiert"),
})
check("Modell-Klasse EXAKT bei exakt-definiert-Params",
      modell_e.garantie().klasse == "EXAKT"
      and modell_e.garantie().herkunft == "exakt-definiert")
check("EXAKT-Modell json-Schema",
      modell_e.als_json()["garantie"]["klasse"] == "EXAKT")

# (h) Waechter: unbekannte Op, float-Param, float-Vektor, auslese-qubits,
#     Aufwaerts-Wanderung (AnchorViolation — Laundering-Verbot):
try:
    chan.ChannelModel.aus_op_counts({**ops_p, "banana": 3}, {})
    banana_ok = False
    banana_dt = "kein Fehler geworfen"
except ValueError as exc:
    banana_ok = True
    banana_dt = str(exc)
check("unbekannte Op verweigert", banana_ok and
      "banana" in banana_dt, banana_dt)

try:
    f_modell = chan.ChannelModel.aus_op_counts(ops_p, {
        "p_1q": chan.Param("p_1q", 1 / 64, "geschätzt:Hypothese"),
        "p_2q": chan.Param("p_2q", Fraction(1, 16), "geschätzt:Hypothese"),
    })
    f1q_ok = False
    f1q_dt = "kein Fehler geworfen"
except ValueError as exc:
    f1q_ok = True
    f1q_dt = str(exc)
check("float p_1q verweigert (EXAKT-Zweig)", f1q_ok, f1q_dt)

try:
    chan.depolarisiert_probs([0.5, 0.5], Fraction(1, 5), 2)
    fv_ok = False
    fv_dt = "kein Fehler geworfen"
except ValueError as exc:
    fv_ok = True
    fv_dt = str(exc)
check("float-Vektoreintrag verweigert", fv_ok and "EXAKT" in fv_dt, fv_dt)

try:
    chan.Kanal("auslese", chan.Param("ro", Fraction(1, 4),
                "kalibriert+2026-10-02"), qubits=(0,))
    roq_ok = False
    roq_dt = "kein Fehler geworfen"
except ValueError as exc:
    roq_ok = True
    roq_dt = str(exc)
check("auslese mit qubits verweigert", roq_ok and
      "qubits" in roq_dt, roq_dt)

try:
    pruefe_verkettung(
        Guarantee("EXAKT", "exakt-definiert"), [modell.garantie()])
    laun_ok = False
    laun_dt = "kein Fehler geworfen"
except AnchorViolation as exc:
    laun_ok = True
    laun_dt = str(exc)
check("Aufwaerts-Wanderung verweigert (GESAMPFELT !=> EXAKT)", laun_ok,
      laun_dt)

try:
    pruefe_verkettung(
        Guarantee("EXAKT", "exakt-definiert"), [modell_e.params["p_1q"].garantie()])
    laun2_ok = True
    laun2_dt = "Eingabe selbst EXAKT — verkettung erlaubt"
except AnchorViolation as exc:
    laun2_ok = False
    laun2_dt = str(exc)
check("EXAKT->EXAKT verkettung erlaubt", laun2_ok, laun2_dt)

# ---- 7) d%q-Waechter -----------------------------------------------------
try:
    kc9 = obs.punkt_konstanten(181, 9, 3)
    ok = True
except ValueError as exc:
    ok = False
    detail9 = str(exc)
check("punkt_konstanten(181,9,3) erlaubt (d=q^2)", ok)

try:
    kc35 = obs.punkt_konstanten(181, 3, 5)   # Klassen-Ebene konsistent
    res35 = obs.quote_exakt({"00": 8192}, kc35)
    quote9_ok = False
    quote9_detail = "kein Fehler geworfen"
except ValueError as exc:
    quote9_ok = False
    quote9_detail = str(exc)
check("quote_exakt verweigert nicht-vielfaches d", quote9_ok is False and
      "Vielfaches" in quote9_detail, quote9_detail)

print()
if failures:
    print(f"SMOKE: {len(failures)} FAILURES: {failures[:5]}")
    sys.exit(1)
print("SMOKE: ALLES GRUEN")