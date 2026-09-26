# -*- coding: utf-8 -*-
"""Tests fuer pt_ram_q_hardware_eval.py — die gefrorene verdict_map, SYNTHETISCH.

KEIN QPU, KEIN Netzwerk: alle Verdict-Zweige der gefrorenen Map werden auf
synthetischen Raw-Dokumenten durchgespielt, deren Counts die gefrorene
Estimator-Kette (n_hat = m*c/S -> fold -> ABSOLUT-FFT) GESETZTREU durchlaufen:

  Klassen-Profil N (q Werte, Summe m): Ziel-Ratio r  <=>
      q*sum N^2 - m^2 = d*m*r*model_share_reg          (041-Identitaet)
  Bisektion ueber N_0 = x in [m/q, m] (f monotone steigend), Entfaltung
  n_hat[a] = N[a%q]/(d/q), groesste-Reste-Rounding auf EXAKT S Shots
  (=> t6: sum n_hat = m exakt).  kappa-Synth: p0-Skalierung der
  Loschmidt-Cal-Paare (kappa_hat = k +- 1/(S*0.98)).

Getestet: alle 8 Zweige (CONFIRMED/COARSE/REFUTED/AMPL/VOID/DEGENERAT/
INVALID x3-Mechanismen/UNMATCHED), die Praezedenz-Ordnung, die
alternative Lesarten (w_A-Falsifikation, Exklusion) und das committete
Raw (struktur-only — der Verdict-Wert selbst wird erst NACH dem
Auswertungs-Lauf gepinnt, Phase-3c-Disziplin).
"""
import json
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pt_ram_q_hardware as hw
import pt_ram_q_hardware_aer as aer
import pt_ram_q_hardware_qpu as qpu
import pt_ram_q_hardware_eval as ev

W_B = ev.load_w_b()
W_A = aer.W_A
LAW_KAPPA = 0.95
S = hw.SHOTS


# === Synth-Werkzeuge =====================================================

def _lr(fracs, total):
    """Groesste-Reste-Rounding: exakte Summe total."""
    floors = [int(math.floor(x)) for x in fracs]
    rem = int(total) - sum(floors)
    order = sorted(range(len(fracs)),
                   key=lambda i: -(fracs[i] - math.floor(fracs[i])))
    for i in order[:rem]:
        floors[i] += 1
    return floors


def _class_counts(pt, ratio):
    """Counts (dict bitstring -> int, Summe S), deren gefrorene Estimator-
    Kette ratio == `ratio` liefert (up to O(m/S)-Rounding).

    Weg: Klassen-Profil N_0 = x, N_j = (m-x)/(q-1) per Bisektion auf
    q*sum N^2 - m^2 = d*m*r*model_share_reg + m^2 (041-Identitaet); dann
    Klassen-TOTALS groesste-Reste auf S runden (Summe exakt S -> t6) und
    je Klasse ganzzahlig-stetig auf die d/q Labels verteilen.
    """
    d, q, m = pt["d"], pt["q"], pt["m"]
    model = pt["model_share_reg"]
    per_class = d // q
    assert d % q == 0 and per_class >= 1

    def f(x):
        return x * x + (m - x) ** 2 / (q - 1)

    target = (d * m * ratio * model + m * m) / q
    lo, hi = m / q, float(m)
    assert f(lo) - 1e-9 <= target <= f(hi) + 1e-9, \
        f"Ziel-Ratio {ratio} ausserhalb des Shares-Spektrums [{lo},{hi}]"
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) < target:
            lo = mid
        else:
            hi = mid
    x = 0.5 * (lo + hi)
    N = [x] + [(m - x) / (q - 1)] * (q - 1)
    # Klassen-Totals: exakte Summe S, Fehler je Klasse <= (m/S)/2
    class_tot = _lr([S * N[j] / m for j in range(q)], S)
    out = {}
    for j in range(q):
        base, rem = divmod(class_tot[j], per_class)
        for i in range(per_class):
            a = j + i * q
            c = base + (1 if i < rem else 0)
            if c:
                out[format(a, f"0{aer.NQ_BY_ARM[f'q{q}_d{d}']}b")] = c
    return out


def _p0_counts(nq, p0):
    """Counts mit P(0^n) = p0 (Cal/Loschmidt-Paar-Synth)."""
    n0 = int(round(S * p0))
    return {"0" * nq: n0,
            "0" * (nq - 1) + "1": S - n0}


def _uniform_counts(nq):
    """Struktur-freie Kontrolle: uniform ueber alle 2^nq Labels."""
    n_labels = 2 ** nq
    counts = _lr([S / n_labels] * n_labels, S)
    return {format(a, f"0{nq}b"): c for a, c in enumerate(counts) if c}


def _point_cfg_default(arm, P):
    # gesetzestreu: ratio = Zentrum c(kappa); kappa 0.95 (>= 0.81)
    return {"kappa": LAW_KAPPA, "res": 0.0}


def _synth_raw(point_cfg=None, control_cfg=None, *, md5_override=None,
               transpile_override=None, corrupt_counts=None):
    """Vollstaendiges 58-Circuit-Raw-Dokument (Struktur == aer.build_...)."""
    point_cfg = point_cfg or {}
    control_cfg = control_cfg or {}
    pts = aer._point_pts()
    entries = []
    for c in aer.build_hardware_circuit_set():
        kind, name = c["kind"], c["name"]
        if kind == "structure":
            arm, P, rep = c["arm"], c["P"], c["rep"]
            cfg = point_cfg.get((arm, P), _point_cfg_default(arm, P))
            pt = pts[(arm, P)]
            kappa = cfg["kappa"]
            center = aer.center_v1(kappa, pt)
            ratio = center + cfg.get("res", 0.0)
            counts = _class_counts(pt, ratio)
        elif kind == "loschmidt":
            arm, P = c["arm"], c["P"]
            cfg = point_cfg.get((arm, P), _point_cfg_default(arm, P))
            counts = _p0_counts(aer.NQ_BY_ARM[arm],
                                cfg["kappa"] * 0.98)
        elif kind == "readout_cal":
            nq = int(c["name"].split("_")[1].rstrip("q"))
            counts = _p0_counts(nq, 0.98)
        elif kind == "negative_control":
            counts = _uniform_counts(aer.NQ_BY_ARM[c["arm"]])
            if control_cfg.get("degenerat") == name:
                pt_ref = pts[(c["arm"], c["P"])]
                counts = _class_counts(pt_ref, pt_ref["ratio_true"])
        else:
            raise AssertionError(kind)
        if corrupt_counts == name:
            counts = dict(counts)
            counts["0" * aer.NQ_BY_ARM[c["arm"]]] = \
                counts.get("0" * aer.NQ_BY_ARM[c["arm"]], 0) - 192
        entries.append({
            "name": name, "kind": kind, "arm": c.get("arm"), "P": c.get("P"),
            "rep": c.get("rep"), "shots_actual": S, "counts": counts,
        })
    doc = {
        "status": "QPU_RAW_FETCHED",
        "experiment": hw.EXPERIMENT, "hypothesis": hw.HYPOTHESIS,
        "backend": "ibm_fez",
        "job_meta": {"job_id": "SYNTH_RAMQ_EVAL", "backend": "ibm_fez",
                     "shots_per_circuit": S},
        "transpile": transpile_override or {
            "optimization_level": 3, "seed_transpiler": 7,
            "isa_2q_total": 1570, "isa_2q_max": 76},
        "registered_run_config":
            hw.load_frozen_prereg()["hardware_parameters"]["run_config"],
        "n_circuits": len(entries), "shots_per_circuit": S,
        "counts": entries,
    }
    doc["counts_md5"] = (md5_override if md5_override is not None
                         else qpu.counts_md5([e["counts"] for e in entries]))
    return doc


def _eval_synth(tmp_path, **kw):
    doc = _synth_raw(**kw)
    raw_path = tmp_path / "raw_synth.json"
    raw_path.write_text(json.dumps(doc), encoding="utf-8")
    return ev.evaluate(raw_path=str(raw_path))


# === Synth-Selbstcheck ===================================================

class TestSynthSelfCheck:
    def test_law_following_synth_lands_in_sharp_band(self, tmp_path):
        doc = _eval_synth(tmp_path)
        assert doc["counts_md5_verified"] is True
        k = doc["kontrollen"]
        assert k["t3_identity_two_ways"]["ok"] is True
        assert k["t4_negative_must_not_fire"]["ok"] is True
        assert k["t5_gate_set_frozen"]["ok"] is True
        assert k["t6_mass_conservation"]["ok"] is True

    def test_synth_ratio_hits_target(self, tmp_path):
        # Spotcheck: ein Punkt, Ziel = Zentrum c(0.95) — gemessenes ratio
        # trifft das Ziel auf < 0.01 (1/S-Rounding auf dem Klassen-Profil).
        pts = aer._point_pts()
        pt = pts[("q3_d9", 109)]
        kappa = LAW_KAPPA
        center = aer.center_v1(kappa, pt)
        counts = _class_counts(pt, center)
        rc = aer.ratio_from_counts(counts, pt, 4)
        assert abs(rc["ratio"] - center) < 0.01

    def test_class_profile_share_identity(self, tmp_path):
        # 041-Identitaet auch auf dem Synth: FFT-Share == gefaltete Formel.
        pts = aer._point_pts()
        pt = pts[("q5_d25", 625)]
        counts = _class_counts(pt, 1.1)
        rc = aer.ratio_from_counts(counts, pt, 5)
        assert rc["share"] >= 0.0
        assert abs(rc["ratio"] - 1.1) < 0.01


# === Die 8 Verdict-Zweige ================================================

class TestVerdictBranches:
    def test_confirmed_all_law_following(self, tmp_path):
        doc = _eval_synth(tmp_path)
        assert doc["verdict"] == ev.V_CONFIRMED
        vi = doc["verdict_inputs"]
        assert vi["n_in_sharp"] == 13 and vi["n_kappa_low"] == 0
        assert doc["verdict_map_text"] == \
            hw.load_frozen_prereg()["verdict_map"][ev.V_CONFIRMED]

    def test_coarse_hold_sharp_miss(self, tmp_path):
        pts = aer._point_pts()
        cfg = {}
        # 12 Punkte gesetzestreu; 1 Punkt knapp unter der scharfen Kante,
        # aber im groben Band: res = -(w_B + 0.01) > -w_A
        first = ("q3_d9", 109)
        cfg[first] = {"kappa": LAW_KAPPA, "res": -(W_B + 0.01)}
        doc = _eval_synth(tmp_path, point_cfg=cfg)
        assert doc["verdict"] == ev.V_COARSE
        vi = doc["verdict_inputs"]
        assert vi["n_in_sharp"] == 12
        assert vi["all_in_coarse_w_a"] is True
        assert vi["n_below_sharp"] == 1  # < 2 -> kein REFUTED

    def test_refuted_two_below_sharp(self, tmp_path):
        # res = -(w_A + 0.01): unter BEIDEN Kanten -> REFUTED (und unter
        # w_A konsistent: alternative Lesart stimmt hier ueberein).
        cfg = {("q3_d9", 109): {"kappa": LAW_KAPPA, "res": -(W_A + 0.01)},
               ("q3_d9", 163): {"kappa": LAW_KAPPA, "res": -(W_A + 0.01)}}
        doc = _eval_synth(tmp_path, point_cfg=cfg)
        assert doc["verdict"] == ev.V_REFUTED
        assert doc["alternative_lesarten"]["refuted_mit_w_a"][
            "verdict_waere"] == ev.V_REFUTED

    def test_refuted_divergence_under_w_a(self, tmp_path):
        # res = -(w_B + 0.01) an 13 Punkten: unter der SCHARFEN Kante
        # (REFUTED), aber IM groben Band -> w_A-Lesart: kein REFUTED.
        # Das dokumentiert die Band-Weite-Abhaengigkeit des Falsifikators.
        cfg = {k: {"kappa": LAW_KAPPA, "res": -(W_B + 0.01)}
               for k in aer._point_pts()}
        doc = _eval_synth(tmp_path, point_cfg=cfg)
        assert doc["verdict"] == ev.V_REFUTED
        assert doc["verdict_inputs"]["n_below_sharp"] == 13
        assert doc["verdict_inputs"]["n_below_coarse_w_a"] == 0
        alt = doc["alternative_lesarten"]["refuted_mit_w_a"]
        assert alt["n_below_coarse_w_a"] == 0
        assert alt["verdict_waere"] is None

    def test_invalid_amplification(self, tmp_path):
        # Ein Punkt ueber dem Ceiling c(kappa=1) + w: Depolarisierung kann
        # Prime-Harmonische nur daempfen — der einseitige Safeguard feuert.
        pts = aer._point_pts()
        pt = pts[("q3_d9", 109)]
        ceiling = aer.center_v1(1.0, pt) + W_B
        cfg = {("q3_d9", 109): {"kappa": LAW_KAPPA, "res": 0.3}}
        doc = _eval_synth(tmp_path, point_cfg=cfg)
        rec = doc["punkte"]["q3_d9|109"]
        assert rec["ratio_hw"] > ceiling
        assert rec["above_ceiling_w_b"] is True
        assert doc["verdict"] == ev.V_AMPL

    def test_void_calibration_two_low_kappa(self, tmp_path):
        cfg = {k: {"kappa": 0.70, "res": 0.0} for k in aer._point_pts()}
        doc = _eval_synth(tmp_path, point_cfg=cfg)
        assert doc["verdict"] == ev.V_VOID
        assert doc["verdict_inputs"]["n_kappa_low"] == 13

    def test_degenerat_control_fires(self, tmp_path):
        # Eine Negativ-Kontrolle zeigt PRIME-Level-Share (>= registrierte
        # untere Prime-Bandkante) -> T4 verletzt -> DEGENERAT (Praezedenz 1).
        name = "ctrl_shuffle_421_P109_d9"
        doc = _eval_synth(tmp_path, control_cfg={"degenerat": name})
        ctrl = doc["kontrollen"]["t4_negative_must_not_fire"]["controls"][name]
        assert ctrl["ok"] is False
        assert ctrl["measured_share"] >= ctrl["lower_prime_band_edge"]
        assert doc["verdict"] == ev.V_DEGENERAT

    def test_invalid_t6_mass_violation(self, tmp_path):
        # 192 Shots weniger auf einem Struktur-Circuit: Massenerhaltung
        # verletzt (m_hat != m) -> EVALUATION_INVALID.
        doc = _eval_synth(tmp_path, corrupt_counts="struct_q3_d9_109_r0")
        k = doc["kontrollen"]["t6_mass_conservation"]
        assert k["ok"] is False
        assert doc["verdict"] == ev.V_INVALID

    def test_invalid_md5_mismatch(self, tmp_path):
        doc = _eval_synth(tmp_path, md5_override="deadbeef" * 4)
        assert doc["counts_md5_verified"] is False
        assert doc["verdict"] == ev.V_INVALID

    def test_invalid_t5_transpile_record(self, tmp_path):
        doc = _eval_synth(
            tmp_path,
            transpile_override={"optimization_level": 3,
                                "seed_transpiler": 7,
                                "isa_2q_total": 999, "isa_2q_max": 76})
        assert doc["kontrollen"]["t5_gate_set_frozen"]["transpile_ok"] is False
        assert doc["verdict"] == ev.V_INVALID

    def test_unmatched_and_exklusion_divergence(self, tmp_path):
        # 12 gesetzestreu + 1 Punkt mit kappa 0.70, der IN SEINEM eigenen
        # Band liegt: n_kappa_low = 1 (< 2, kein VOID), alle im scharfen
        # Band, aber n_kappa_low != 0 -> kein CONFIRMED -> UNMATCHED
        # (ehrlicher Nicht-Treffer).  Die Exklusions-Lesart des
        # kappa_floor_void-Texts haette stattdessen CONFIRMED ueber 12 —
        # die Divergenz wird als alternative_lesart ausgewiesen.
        one = ("q5_d25", 625)
        cfg = {one: {"kappa": 0.70, "res": 0.0}}
        doc = _eval_synth(tmp_path, point_cfg=cfg)
        assert doc["verdict"] == ev.V_UNMATCHED
        assert doc["verdict_inputs"]["n_kappa_low"] == 1
        assert doc["verdict_inputs"]["n_in_sharp"] == 13
        alt = doc["alternative_lesarten"]["exklusion"]
        assert alt["n_points"] == 12
        assert alt["verdict_waere"] == ev.V_CONFIRMED


# === Praezedenz als reine Funktion =======================================

class TestDecideVerdict:
    def test_t4_beats_everything(self):
        assert ev.decide_verdict(
            t4_violated=True, t_fail_other=True, n_kappa_low=13,
            n_above_ceiling=13, n_below_sharp=13, n_in_sharp=0,
            all_in_coarse=False, n_points=13) == ev.V_DEGENERAT

    def test_invalid_before_void(self):
        assert ev.decide_verdict(
            t4_violated=False, t_fail_other=True, n_kappa_low=13,
            n_above_ceiling=0, n_below_sharp=0, n_in_sharp=0,
            all_in_coarse=False, n_points=13) == ev.V_INVALID

    def test_void_before_amplification_and_refuted(self):
        assert ev.decide_verdict(
            t4_violated=False, t_fail_other=False, n_kappa_low=2,
            n_above_ceiling=1, n_below_sharp=2, n_in_sharp=0,
            all_in_coarse=False, n_points=13) == ev.V_VOID

    def test_amplification_before_refuted(self):
        assert ev.decide_verdict(
            t4_violated=False, t_fail_other=False, n_kappa_low=0,
            n_above_ceiling=1, n_below_sharp=2, n_in_sharp=0,
            all_in_coarse=False, n_points=13) == ev.V_AMPL

    def test_refuted_before_confirmed(self):
        assert ev.decide_verdict(
            t4_violated=False, t_fail_other=False, n_kappa_low=0,
            n_above_ceiling=0, n_below_sharp=2, n_in_sharp=11,
            all_in_coarse=True, n_points=13) == ev.V_REFUTED

    def test_confirmed_needs_all_and_kappa_ok(self):
        assert ev.decide_verdict(
            t4_violated=False, t_fail_other=False, n_kappa_low=0,
            n_above_ceiling=0, n_below_sharp=0, n_in_sharp=13,
            all_in_coarse=True, n_points=13) == ev.V_CONFIRMED
        # 12 im scharfen Band + 1 ausserhalb, grob ok -> COARSE
        assert ev.decide_verdict(
            t4_violated=False, t_fail_other=False, n_kappa_low=0,
            n_above_ceiling=0, n_below_sharp=0, n_in_sharp=12,
            all_in_coarse=True, n_points=13) == ev.V_COARSE

    def test_no_match_is_honest_catch_all(self):
        # alles im scharfen Band, aber ein kappa low (nur 1): weder
        # CONFIRMED (kappa) noch VOID (< 2) -> UNMATCHED
        assert ev.decide_verdict(
            t4_violated=False, t_fail_other=False, n_kappa_low=1,
            n_above_ceiling=0, n_below_sharp=0, n_in_sharp=13,
            all_in_coarse=True, n_points=13) == ev.V_UNMATCHED
        # und: Punkt unter w_B UND Punkt ueber Ceiling gleichzeitig -> AMPL
        # (Praezedenz: einseitiger Safeguard vor Falsifikation)
        assert ev.decide_verdict(
            t4_violated=False, t_fail_other=False, n_kappa_low=0,
            n_above_ceiling=1, n_below_sharp=1, n_in_sharp=0,
            all_in_coarse=False, n_points=13) == ev.V_AMPL


# === Committetes Raw: struktur-only ======================================

RAW_EXISTS = pytest.mark.skipif(
    not os.path.exists(qpu.RAW_PATH), reason="Fez-Raw noch nicht committet")


class TestCommittedRaw:
    """Das ECHTE committete Fez-Raw durch die gefrorene Auswertung.

    STRUCTUR-ONLY: hier wird NICHT der Verdict-Wert gepinnt (der Pin
    folgt erst nach dem ersten Auswertungs-Lauf im Verdict-Commit,
    Phase-3c-Disziplin) — nur der Vertrag der Auswertung.
    """

    @RAW_EXISTS
    def test_eval_contract(self):
        doc = ev.evaluate()
        assert doc["status"] == "EVALUATED"
        assert doc["counts_md5_verified"] is True
        assert len(doc["punkte"]) == 13
        k = doc["kontrollen"]
        assert k["t3_identity_two_ways"]["ok"] is True
        assert k["t5_gate_set_frozen"]["ok"] is True
        assert k["t6_mass_conservation"]["ok"] is True
        assert doc["verdict"] in {
            ev.V_CONFIRMED, ev.V_COARSE, ev.V_REFUTED, ev.V_AMPL,
            ev.V_VOID, ev.V_DEGENERAT, ev.V_INVALID, ev.V_UNMATCHED}
        vi = doc["verdict_inputs"]
        assert vi["n_points"] == 13
        assert vi["n_evaluated"] in (12, 13)

    @RAW_EXISTS
    def test_eval_diagnostisch_v2_not_verdict_bearing(self):
        doc = ev.evaluate()
        for rec in doc["punkte"].values():
            d2 = rec["diagnostisch_v2"]
            assert d2["nicht_verdict_tragend"] is True
            assert "b_p_aer" in d2 and "center_v2" in d2

    @RAW_EXISTS
    def test_eval_alternative_lesarten_present(self):
        doc = ev.evaluate()
        alt = doc["alternative_lesarten"]
        assert "refuted_mit_w_a" in alt
        assert "amplification_mit_w_a" in alt
        assert "exklusion" in alt


class TestVerdictPin:
    """GEFRORENER Verdict-Pin — NACH dem ersten Auswertungs-Lauf gepinnt
    (Phase-3c-Disziplin: erst sehen, dann pinnen).  Raw-md5 d19f4a56
    (Job darq1stvr3kc73ej96ig), w_B aus dem committeten Freeze B."""

    @RAW_EXISTS
    def test_verdict_void_calibration(self):
        doc = ev.evaluate()
        assert doc["verdict"] == ev.V_VOID
        vi = doc["verdict_inputs"]
        assert vi["n_kappa_low"] == 13
        assert vi["n_below_sharp"] == 3
        assert vi["n_in_sharp"] == 7
        assert vi["n_above_ceiling_w_b"] == 0
        assert doc["verdict_map_text"] == \
            hw.load_frozen_prereg()["verdict_map"][ev.V_VOID]
        # Alle Kontrollen gruen: der Void ist KALIBRIER-bedingt (kappa),
        # nicht Pipeline-bedingt; keine Exklusions-Lesart aktivierbar
        # (13 von 13 low, nicht 1).
        assert doc["kontrollen"]["t4_negative_must_not_fire"]["ok"] is True
        assert doc["counts_md5_verified"] is True
        assert doc["alternative_lesarten"]["exklusion"] is None

    @RAW_EXISTS
    def test_kappa_all_below_ceiling_depth_ordered(self):
        doc = ev.evaluate()
        for key, rec in doc["punkte"].items():
            assert rec["kappa_hat"] < hw.KAPPA_CEILING, key
            assert rec["kappa_ok"] is False
        # Register-Tiefe degradiert kappa: 5q-Werte strikt unter den
        # 4q-Werten ((1-eps)^5 < (1-eps)^4) — physikalisch konsistent.
        k4 = [r["kappa_hat"] for k, r in doc["punkte"].items()
              if k.startswith("q3")]
        k5 = [r["kappa_hat"] for k, r in doc["punkte"].items()
              if k.startswith("q5")]
        assert min(k4) > max(k5)