"""Single source of truth for every number shown in the presentation.

SciComPresentationMind v1.0_20260923 — claim_extraction module.

Rule: every on-screen number flows through ``claims.display(id)`` /
``claims.raw(id)``; scenes and deck never carry numbers of their own.
``recompute(id)`` re-derives each value live from its committed source
(JSON / module / cmd / doc anchor). ``check_gate()`` compares the
recomputation against the frozen expectation below — any mismatch is a
publish-stop (exit 2) before anything is rendered or written.

This module must never import manim or pyslides.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
PRESENTATION_DIR = REPO_ROOT / "presentation"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Absolute prereg path for the live H-SHOR-1 recompute (module resolves its
# prereg relative to the process cwd; pin it so any entry point works).
PREREG_ABS = str(REPO_ROOT / "pt_hshor1_prereg.json")


class Kind(str, Enum):
    """How a claim's value is (re-)derived."""

    RECOMPUTE_JSON = "recompute-json"      # committed result JSON
    RECOMPUTE_MODULE = "recompute-module"  # live module call
    RECOMPUTE_CMD = "recompute-cmd"        # shell command (CLI gate only)
    DOC_FROZEN = "doc-frozen"              # pinned by anchor in committed doc


class Label(str, Enum):
    """Wording ladder (audience_calibration)."""

    MEASURED = "measured"      # wording: "shows"
    DOC_FROZEN = "doc-frozen"  # registered in a committed doc
    POINTS_TO = "points-to"    # wording: "points to"
    HYPOTHESIS = "hypothesis"  # wording: "speculates", grey


@dataclass(frozen=True)
class Source:
    """Where a claim's value comes from.

    path: JSON walk — str = key, int = list index, -1 = last element.
    convention: optional post-processing (registered in _CONVENTIONS).
    line/anchor: DOC_FROZEN pinning (anchor must appear near line).
    """

    kind: Kind
    file: str = ""
    path: tuple = ()
    convention: str | None = None
    module: str | None = None
    call: str | None = None
    args: tuple = ()
    extract: tuple = ()   # walk into the module-call result
    line: int | None = None
    anchor: str | None = None
    cmd: tuple = ()
    regex: str | None = None


@dataclass(frozen=True)
class Claim:
    id: str
    value: object                 # EXPECTED — read by the gate/tests only
    display: str                  # format template, {} = recomputed value
    label: Label
    source: Source
    tol: float = 1e-9
    grade: str | None = None
    criterion: str | None = None  # frozen criterion, shown BEFORE the result
    gloss: str | None = None      # <= 12 words, first use of a technical term
    scenes: tuple = ()
    fmt: Callable | None = None   # custom formatter (structured values)


# --------------------------------------------------------------------------
# Conventions: registered post-processing over raw source values.
# --------------------------------------------------------------------------

def _pairs_p1_margin(curve):
    """encoded.curve -> [(p1, phi margin)] in file order."""
    return tuple((c["p1"], c["phi"]["margin"]) for c in curve)


def _pairs_alpha(entries):
    """incremental_alpha_vN -> [(N_max, alpha_vN)] in file order."""
    return tuple((e["N_max"], e["alpha_vN"]) for e in entries)


def _margin_at_3e4(curve):
    """encoded.curve -> phi margin at the frozen primary p1 = 3e-4."""
    for c in curve:
        if abs(c["p1"] - 3e-4) < 1e-12:
            return c["phi"]["margin"]
    raise ValueError("no curve entry at p1 = 3e-4")


def _sign_interval(curve):
    """Derived claim: bracket where the encoded margin crosses zero."""
    pts = sorted((c["p1"], c["phi"]["margin"]) for c in curve)
    for (pa, ma), (pb, mb) in zip(pts, pts[1:]):
        if ma > 0 and mb < 0:
            return (pa, pb)
    return None


def _ram_gated(rows):
    """Ramanujan gated points -> [(P, share_prime)] for d == 625."""
    return tuple((r["P"], r["share_prime"]) for r in rows if r.get("gated"))


def _kappa_per_p1(d):
    """kappa_star_per_p1_descriptive -> [(p1, kappa)] sorted, no None slot."""
    return tuple(sorted((float(k), v) for k, v in d.items() if v is not None))


def _bands_all(bands):
    """bands_hold dict -> True iff every prereg band held."""
    return all(bool(v) for v in bands.values())


def _kingston_bands(detail):
    """detail.flags -> True iff every observable landed inside its band."""
    return all(bool(v["in_band"]) for v in detail["flags"].values())


def _max_of(seq):
    """abs_biases (or similar) -> max element."""
    return max(seq)


def _o1_grid(d):
    """o1_grid_classical -> {str(window): rate} (key-type normalized)."""
    return {str(k): float(v) for k, v in d.items()}


def _o1p_composites(o1p):
    """o1p_shor -> only the composite entries (factors as tuples)."""
    return {k: tuple(v) if v is not None else None
            for k, v in o1p.items() if k in {"15", "21"}}


def _qpe_summary(res):
    """qpe_order(...) -> gate-sized summary (no 625-length arrays)."""
    return {"Q": int(res["Q"]), "XD": int(res["XD"]), "r": res["r"],
            "N": int(res["N"]), "a": int(res["a"]),
            "peak_ks": tuple(int(k) for k, _ in res["peaks"])}


def _im_band_parse(pred):
    """H_Im_h1 prediction text -> the frozen |bias| band bound."""
    m = re.search(r"\|Im_bias\| < (0\.\d+)", pred)
    if m is None:
        raise ValueError("band bound not found in H_Im_h1 prediction")
    return float(m.group(1))


def _first_bound(curve):
    """encoded.curve -> the frozen 1/5 bound carried by the first entry."""
    return curve[0]["phi"]["bound"]


def _ram_model(rows):
    """Ramanujan gated points -> [(P, model share_star)] for d == 625."""
    return tuple((r["P"], r["model"]) for r in rows if r.get("gated"))


_CONVENTIONS = {
    "pairs-p1-margin": _pairs_p1_margin,
    "pairs-alpha": _pairs_alpha,
    "margin-at-3e4": _margin_at_3e4,
    "sign-interval": _sign_interval,
    "ram-gated": _ram_gated,
    "ram-model": _ram_model,
    "kappa-per-p1": _kappa_per_p1,
    "bands-all": _bands_all,
    "kingston-bands": _kingston_bands,
    "max-of": _max_of,
    "o1-grid": _o1_grid,
    "o1p-composites": _o1p_composites,
    "im-band-parse": _im_band_parse,
    "first-bound": _first_bound,
    "qpe-summary": _qpe_summary,
}


# --------------------------------------------------------------------------
# Claim table (claim_extraction — VOR Gestaltung).
# --------------------------------------------------------------------------

_CL = []

_CL.append(Claim(
    id="alpha_1e6", value=0.22275345050922138,
    display="α(10⁶) = {:.3f}", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_asymptotic_N1e6_results.json",
                  path=("alpha_vN_full_fit",)),
    criterion="Latorre–Sierra predicts α → 1; frozen band excludes α ≥ 1",
    gloss="α = entropy growth per factor of ten in N",
    scenes=("act3_anomaly",)))

_CL.append(Claim(
    id="alpha_curve",
    value=((31, 0.33305202609341633), (63, 0.2597306718152198),
           (127, 0.2718751073071342), (255, 0.34335334422993624),
           (511, 0.34660441634713357), (1023, 0.34749400912938905),
           (10000, 0.3058497886833033), (100000, 0.2575878229816306),
           (1000000, 0.22275345050922138)),
    display="9 measured points, 31 → 10⁶", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_asymptotic_N1e6_results.json",
                  path=("incremental_alpha_vN",),
                  convention="pairs-alpha"),
    scenes=("act3_anomaly",)))

_CL.append(Claim(
    id="alpha_at_31", value=0.33305202609341633,
    display="α(31) = {:.3f}", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_asymptotic_N1e6_results.json",
                  path=("incremental_alpha_vN", 0, "alpha_vN")),
    scenes=("act3_anomaly",)))

_CL.append(Claim(
    id="alpha_verdict", value="H_C (anderes Power-Law)",
    display="verdict: {}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_asymptotic_N1e6_results.json",
                  path=("verdict",)),
    scenes=("act3_anomaly",)))

_CL.append(Claim(
    id="alpha_qpu", value=0.3478584070739363,
    display="α_QPU = {:.3f}", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_prime_state_qpu_singleshot_results.json",
                  path=("alpha_qpu",)),
    scenes=("act3_anomaly", "act4_qpu_timeline")))

_CL.append(Claim(
    id="alpha_aer", value=0.271875107307134,
    display="α_Aer = {:.3f}", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_prime_state_qpu_singleshot_results.json",
                  path=("alpha_aer",)),
    scenes=("act3_anomaly", "act4_qpu_timeline")))

_CL.append(Claim(
    id="alpha_latorre", value=1.0,
    display="α_Latorre–Sierra = {:.1f} (excluded)", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_prime_state_qpu_singleshot_results.json",
                  path=("alpha_latorre_sierra",)),
    scenes=("act3_anomaly",)))

_CL.append(Claim(
    id="alpha_qpu_verdict", value="QPU bestaetigt Aer (DISSENS zu Latorre-Sierra)",
    display="verdict: {}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_prime_state_qpu_singleshot_results.json",
                  path=("verdict",)),
    scenes=("act3_anomaly",)))

_CL.append(Claim(
    id="deriv_sign_global", value="negative",
    display="global trend dα: {}", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_alpha_derivative_results.json",
                  path=("h_dalpha", "sign_at_N_1e6_global")),
    scenes=("act3_anomaly",)))

_CL.append(Claim(
    id="bias_points",
    value=(-0.0018453229255750575, 0.0022208938718740537,
           -0.0026877576040748585, 0.0015245924859990465,
           0.00019344897629861198),
    display="5 Im-channel bias points", label=Label.MEASURED, grade="A+",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_im_bias_token2_results.json",
                  path=("Im_bias_qpu_minus_statevector",)),
    criterion="frozen: all |bias| < 0.005 (pt_im_bias_prereg.json, H_Im_h1)",
    gloss="VQE = a quantum routine tuning a circuit toward lowest energy",
    scenes=("act2_pillar1",)))

_CL.append(Claim(
    id="bias_mean", value=-0.00011882903909564077,
    display="mean = {:+.4f}", label=Label.MEASURED, grade="A+",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_im_bias_token2_results.json",
                  path=("mean_bias",)),
    scenes=("act2_pillar1",)))

_CL.append(Claim(
    id="bias_std", value=0.0018895941511433932,
    display="std = {:.4f}", label=Label.MEASURED, grade="A+",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_im_bias_token2_results.json",
                  path=("std_bias",)),
    scenes=("act2_pillar1",)))

_CL.append(Claim(
    id="bias_max_abs", value=0.0026877576040748585,
    display="max |bias| = {:.4f}", label=Label.MEASURED, grade="A+",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_im_bias_token2_results.json",
                  path=("abs_biases",),
                  convention="max-of"),
    scenes=("act2_pillar1",)))

_CL.append(Claim(
    id="bias_job_ids",
    value=("d8pbl2201fac73d1gdag", "d8pbl2eab0ds73dos8a0",
           "d8pbl2mab0ds73dos8ag", "d8pbl2q01fac73d1gdcg",
           "d8pbl3ekodhs7381kec0"),
    display="5 sequential Fez jobs", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_im_bias_token2_results.json",
                  path=("job_ids",)),
    scenes=("act2_pillar1",)))

_CL.append(Claim(
    id="vqd_e0", value=2.1398203106629032,
    display="E₀ = {:.4f}", label=Label.MEASURED, grade="A",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_vqe_vqd_results.json",
                  path=("vqe_result", "E0_meas")),
    criterion="frozen: |bias_PT_re| < 0.05 → H1/H3 confirmed",
    gloss="VQD = VQE plus the second-lowest energy level",
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="vqd_bias", value=-0.011922308405310833,
    display="bias_PT_re = {:+.4f}", label=Label.MEASURED, grade="A",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_vqe_vqd_results.json",
                  path=("bias_analysis", "bias_PT_re_minus_diag")),
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="vqd_job", value="d9fidihhtsac739fg3n0",
    display="job {}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_vqe_vqd_results.json",
                  path=("job_ids", 0)),
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="fez_phi", value=0.625244140625,
    display="φ V = {:.3f} > 1/5", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_ququint_fez_results.json",
                  path=("phi_v_hat",)),
    criterion="frozen: phi margin > 0, sep margin < 0, confound ≤ 0.05 (md5 18fb1e62)",
    gloss="phi V = how strongly prime positions carry the signal",
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="fez_sep", value=0.16611328125,
    display="sep V = {:.3f} < 1/5", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_ququint_fez_results.json",
                  path=("sep_v_hat",)),
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="fez_job", value="dakjk9hhvn6c73cvr1cg",
    display="job {}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_ququint_fez_results.json",
                  path=("job_id",)),
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="fez_bands_hold", value={"phi_margin": True, "sep_margin": True,
                                "confound_max_diff": True},
    display="3/3 prereg bands held", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_ququint_fez_results.json",
                  path=("bands_hold",)),
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="kingston_bias", value=0.007403730279381016,
    display="bias = {:+.4f} < 0.05", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_v5_kingston_results.json",
                  path=("meas", "bias")),
    criterion="frozen: bias < 0.05, all observables inside bands (md5 d019d587)",
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="kingston_bands", value=True,
    display="all observables inside frozen bands", label=Label.MEASURED,
    grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_v5_kingston_results.json",
                  path=("detail",),
                  convention="kingston-bands"),
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="kingston_job", value="daqaeteekp0c73aqetdg",
    display="job {}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_v5_kingston_results.json",
                  path=("job_id",)),
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="kingston_md5", value="d019d587c0d8ca28cfa0559057d590c8",
    display="prereg md5 {}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_v5_kingston_results.json",
                  path=("prereg_md5",)),
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="margin_curve",
    value=((0.0, 0.7271340355472928), (1e-4, 0.6773878666169415),
           (3e-4, 0.5840264877973111), (1e-3, 0.361110060751934),
           (3e-3, 0.031297237332560374), (1e-2, -0.12650149068526279)),
    display="6-point margin curve", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_crossover_v4_results.json",
                  path=("encoded", "curve"), convention="pairs-p1-margin"),
    tol=1e-6,
    criterion="margin = measured V minus the frozen 1/5 bound, per noise level p1",
    gloss="margin = how far the measured value stays above the frozen bound",
    scenes=("act5_kappa",)))

_CL.append(Claim(
    id="margin_primary", value=0.5840264877973111,
    display="margin(p1 = 3e-4) = {:.3f}", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_crossover_v4_results.json",
                  path=("encoded", "curve"),
                  convention="margin-at-3e4"),
    tol=1e-9,
    scenes=("act5_kappa",)))

_CL.append(Claim(
    id="margin_sign_interval", value=(0.003, 0.01),
    display="sign change between p1 = 3e-3 and 1e-2",
    label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_crossover_v4_results.json",
                  path=("encoded", "curve"), convention="sign-interval"),
    scenes=("act5_kappa",)))

_CL.append(Claim(
    id="kappa_star", value=62.26124150876291,
    display="κ* = {:.2f}", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_crossover_v4_results.json",
                  path=("kappa_star", "kappa_star")),
    tol=1e-6,
    criterion="frozen: κ* ≥ 10 → CONFIRMED (md5 7abb5e60…)",
    gloss="κ* = noise strength where the quantum advantage margin closes",
    scenes=("act5_kappa",)))

_CL.append(Claim(
    id="kappa_bracket", value=(62.09289060367421, 62.43004885946025),
    display="bracket", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_crossover_v4_results.json",
                  path=("kappa_star", "bracket")),
    tol=1e-6, fmt=lambda v: "bracket [{:.2f}, {:.2f}]".format(*v),
    scenes=("act5_kappa",)))

_CL.append(Claim(
    id="kappa_per_p1",
    value=((1e-4, 85.23579048290256), (3e-4, 62.26124150876291),
           (1e-3, 43.315904550557775), (3e-3, 30.299034981920034),
           (1e-2, 12.088878631371212)),
    display="κ* vs p1, 5 points", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_crossover_v4_results.json",
                  path=("kappa_star_per_p1_descriptive",),
                  convention="kappa-per-p1"),
    tol=1e-6,
    scenes=("act5_kappa",)))

_CL.append(Claim(
    id="kappa_rough", value=62.31,
    display="Rough model {:.2f}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.DOC_FROZEN,
                  file="RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md",
                  line=1326, anchor="Rough-Modell 62.31"),
    tol=1e-9,
    scenes=("act5_kappa",)))

_CL.append(Claim(
    id="crossover_md5", value="7abb5e60100bd666e8bf93730e33f458",
    display="prereg md5 {}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_crossover_v4_results.json",
                  path=("prereg_md5",)),
    scenes=("act5_kappa",)))

_CL.append(Claim(
    id="crossover_verdict", value="H-STAR-4_CONFIRMED_CROSSOVER",
    display="verdict: {}", label=Label.MEASURED, grade="A−",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_crossover_v4_results.json",
                  path=("verdict",)),
    scenes=("act5_kappa",)))

_CL.append(Claim(
    id="ram_gated",
    value=((401, 0.029448101265823555), (463, 0.03271111111111206),
           (541, 0.0363200000000007), (599, 0.04042568807339458),
           (625, 0.04272280701754398)),
    display="5/5 gated points", label=Label.MEASURED, grade="B+",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_ramanujan_results.json",
                  path=("rows",), convention="ram-gated"),
    criterion="frozen: 5/5 gated points in band, no control overlap (md5 a2fc4875)",
    gloss="mod-5 fingerprint = a residue pattern that only primes show",
    scenes=("act6_ramanujan",)))

_CL.append(Claim(
    id="ram_overlap_limit", value=0.02218126582278481,
    display="control separation {:.4f}", label=Label.MEASURED, grade="B+",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_ramanujan_results.json",
                  path=("composite_overlap_limit",)),
    scenes=("act6_ramanujan",)))

_CL.append(Claim(
    id="ram_verdict", value="H-RAM-2_REPLICATED_FINGERPRINT",
    display="verdict: {}", label=Label.MEASURED, grade="B+",
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_ramanujan_results.json",
                  path=("verdict",)),
    scenes=("act6_ramanujan",)))

_CL.append(Claim(
    id="ram_md5", value="a2fc4875e10dd198e95d4996b1692759",
    display="prereg md5 {}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_ramanujan_results.json",
                  path=("prereg_md5",)),
    scenes=("act6_ramanujan",)))

_CL.append(Claim(
    id="hshor_verdict", value="CONFIRMED",
    display="verdict: {}", label=Label.MEASURED, grade="B",
    source=Source(kind=Kind.RECOMPUTE_MODULE, module="pt_hshor1",
                  call="run_evaluation", args=(PREREG_ABS,),
                  extract=("verdict",)),
    tol=0.0,
    criterion="frozen: composite rate > 0.05, prime rate = 0 (md5 73bc664a)",
    gloss="Carmichael numbers: rare composites that pass every Fermat test",
    scenes=("act7_qpe_peaks", "act8_fermat_grid", "act10_verdict_ladder")))

_CL.append(Claim(
    id="hshor_o1",
    value={"7": 0.0, "9": 0.8, "11": 0.0, "13": 0.0,
           "15": 0.5714285714285714, "17": 0.0, "19": 0.0,
           "21": 0.7272727272727273, "23": 0.0, "25": 0.8421052631578947,
           "33": 0.8421052631578947, "35": 0.8695652173913043,
           "39": 0.8695652173913043, "561": 0.0},
    display="order-grid rates, 14 windows", label=Label.MEASURED, grade="B",
    source=Source(kind=Kind.RECOMPUTE_MODULE, module="pt_hshor1",
                  call="run_evaluation", args=(PREREG_ABS,),
                  extract=("results", "o1_grid_classical"),
                  convention="o1-grid"),
    tol=1e-9,
    scenes=("act8_fermat_grid",)))

_CL.append(Claim(
    id="hshor_prime_rate_max", value=0.0,
    display="prime grid violation = {:.1f}", label=Label.MEASURED, grade="B",
    source=Source(kind=Kind.RECOMPUTE_MODULE, module="pt_hshor1",
                  call="run_evaluation", args=(PREREG_ABS,),
                  extract=("results", "o1_prime_rate_max")),
    tol=0.0,
    scenes=("act8_fermat_grid",)))

_CL.append(Claim(
    id="hshor_comp_rate_min", value=0.5714285714285714,
    display="min composite rate = {:.4f} > 0.05", label=Label.MEASURED,
    grade="B",
    source=Source(kind=Kind.RECOMPUTE_MODULE, module="pt_hshor1",
                  call="run_evaluation", args=(PREREG_ABS,),
                  extract=("results", "o1_composite_rate_min_nonkorselt")),
    tol=1e-9,
    scenes=("act8_fermat_grid",)))

_CL.append(Claim(
    id="hshor_bridge_min", value=1.0,
    display="bridge match = {:.1f}", label=Label.MEASURED, grade="B",
    source=Source(kind=Kind.RECOMPUTE_MODULE, module="pt_hshor1",
                  call="run_evaluation", args=(PREREG_ABS,),
                  extract=("results", "o1b_bridge_match_min")),
    tol=0.0,
    criterion="frozen: bridge match = 1.0 (md5 73bc664a)",
    gloss="QPE reads a frequency; here the frequency is the cycle length",
    scenes=("act7_qpe_peaks",)))

_CL.append(Claim(
    id="hshor_crt_dev", value=0.0,
    display="CRT deviation = {:.1f}", label=Label.MEASURED, grade="B",
    source=Source(kind=Kind.RECOMPUTE_MODULE, module="pt_hshor1",
                  call="run_evaluation", args=(PREREG_ABS,),
                  extract=("results", "o2_crt_max_dev")),
    tol=0.0,
    gloss="CRT = split a number into coprime parts, exactly",
    scenes=("act8_fermat_grid",)))

_CL.append(Claim(
    id="hshor_trace_dev", value=0.0,
    display="trace identity deviation = {:.1f}", label=Label.MEASURED,
    grade="B",
    source=Source(kind=Kind.RECOMPUTE_MODULE, module="pt_hshor1",
                  call="run_evaluation", args=(PREREG_ABS,),
                  extract=("results", "o2_trace_max_dev")),
    tol=0.0,
    scenes=("act8_fermat_grid",)))

_CL.append(Claim(
    id="hshor_shuffle_p", value=0.0,
    display="shuffle p = {:.3f}", label=Label.MEASURED, grade="B",
    source=Source(kind=Kind.RECOMPUTE_MODULE, module="pt_hshor1",
                  call="run_evaluation", args=(PREREG_ABS,),
                  extract=("results", "shuffle", "p")),
    tol=1e-9,
    scenes=("act8_fermat_grid",)))

_CL.append(Claim(
    id="hshor_561_order", value=80,
    display="561 max order = {} ≠ 560", label=Label.MEASURED, grade="B",
    source=Source(kind=Kind.RECOMPUTE_MODULE, module="pt_hshor1",
                  call="run_evaluation", args=(PREREG_ABS,),
                  extract=("results", "o1_max_order_561")),
    tol=0.0,
    gloss="Korselt: the theorem that names the Carmichael exceptions",
    scenes=("act8_fermat_grid", "act9_failure_board")))

_CL.append(Claim(
    id="hshor_shor",
    value={"15": (3, 5), "21": (3, 7)},
    display="15 → (3, 5), 21 → (3, 7)", label=Label.MEASURED, grade="B",
    source=Source(kind=Kind.RECOMPUTE_MODULE, module="pt_hshor1",
                  call="run_evaluation", args=(PREREG_ABS,),
                  extract=("results", "o1p_shor"),
                  convention="o1p-composites"),
    tol=0.0,
    scenes=("act8_fermat_grid",)))

_CL.append(Claim(
    id="hshor_md5", value="73bc664ae3475a79a692cd7735b2b387",
    display="prereg md5 {}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_MODULE, module="pt_hshor1",
                  call="run_evaluation", extract=("prereg_md5",)),
    tol=0.0,
    scenes=("act7_qpe_peaks", "act8_fermat_grid")))

_CL.append(Claim(
    id="korselt_561", value=True,
    display="561 passes Korselt: True", label=Label.MEASURED, grade="B",
    source=Source(kind=Kind.RECOMPUTE_MODULE, module="pt_hshor1",
                  call="korselt_criterion_check", args=(561,)),
    tol=0.0,
    scenes=("act8_fermat_grid",)))

_CL.append(Claim(
    id="im_band", value=0.005,
    display="frozen band |bias| < {:.3f}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_im_bias_prereg.json",
                  path=("hypotheses", "H_Im_h1", "prediction"),
                  convention="im-band-parse"),
    scenes=("act2_pillar1",)))

_CL.append(Claim(
    id="ququint_bound", value=0.2,
    display="frozen bound 1/5 = {:.1f}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_crossover_v4_results.json",
                  path=("encoded", "curve"), convention="first-bound"),
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="ram_band", value=(0.8, 1.25),
    display="prereg band × model", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_ramanujan_prereg.json",
                  path=("thresholds", "band")),
    tol=1e-9,
    fmt=lambda v: f"band {v[0]:.2f}–{v[1]:.2f} × model",
    scenes=("act6_ramanujan",)))

_CL.append(Claim(
    id="ram_gate_pi", value=79,
    display="gate π ≥ {}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_ramanujan_prereg.json",
                  path=("thresholds", "gate_min_pi")),
    gloss="π(P) = how many primes sit below P",
    scenes=("act6_ramanujan",)))

_CL.append(Claim(
    id="ram_model",
    value=((401, 0.027726582278481012), (463, 0.03211111111111111),
           (541, 0.0361), (599, 0.03969174311926606),
           (625, 0.041687719298245614)),
    display="model share* at the gated points", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.RECOMPUTE_JSON, file="pt_ramanujan_results.json",
                  path=("rows",), convention="ram-model"),
    tol=1e-9,
    scenes=("act6_ramanujan",)))

_CL.append(Claim(
    id="qpe_15",
    value={"Q": 625, "XD": 25, "r": 4, "N": 15, "a": 7,
           "peak_ks": (0, 156, 157, 312, 313, 468, 469)},
    display="QPE readout", label=Label.MEASURED, grade="B",
    source=Source(kind=Kind.RECOMPUTE_MODULE, module="pt_shor_ququint",
                  call="qpe_order", args=(7, 15), convention="qpe-summary"),
    tol=1e-9,
    fmt=lambda v: f"r = {v['r']} from the QPE readout (Q = {v['Q']})",
    scenes=("act7_qpe_peaks",)))

_CL.append(Claim(
    id="leakage_r0", value="0.3553",
    display="sieve portal r0 = {}", label=Label.DOC_FROZEN, grade="C",
    source=Source(kind=Kind.DOC_FROZEN,
                  file="RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md",
                  line=1326, anchor="r0 0.3553 < 0.3833"),
    scenes=("act9_failure_board",)))

_CL.append(Claim(
    id="chi2_v1", value="1311",
    display="leakage structure real: χ² = {}", label=Label.DOC_FROZEN,
    grade="C",
    source=Source(kind=Kind.DOC_FROZEN,
                  file="RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md",
                  line=1326, anchor="χ² 1311"),
    scenes=("act9_failure_board",)))

_CL.append(Claim(
    id="v3_rmean", value="0.2059",
    display="⟨r⟩ d25 = {}", label=Label.DOC_FROZEN, grade="C",
    source=Source(kind=Kind.DOC_FROZEN,
                  file="RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md",
                  line=1326, anchor="0.2059"),
    scenes=("act9_failure_board",)))

_CL.append(Claim(
    id="gue_correction", value="0.5996",
    display="GUE constant corrected: 0.5359 → {}",
    label=Label.DOC_FROZEN, grade="C",
    source=Source(kind=Kind.DOC_FROZEN,
                  file="RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md",
                  line=1326, anchor="0.5996"),
    scenes=("act9_failure_board",)))

_CL.append(Claim(
    id="vector_ladder", value="10.19 Strategic Vectors",
    display="§10.19 Strategic Vectors — Gesamtstatus",
    label=Label.DOC_FROZEN,
    source=Source(kind=Kind.DOC_FROZEN,
                  file="RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md",
                  line=1350, anchor="10.19 Strategic Vectors"),
    scenes=("act10_verdict_ladder",)))

_CL.append(Claim(
    # Registrierung: Extraordinaritaet 7/10 (§Z.18). Phase 6a ausgefuehrt
    # 2026-09-25 (§10.21): VERDICT REFUTED (sauber, Kontrollen zuerst).
    id="hstar5_score", value="Score 7/10",
    display="H-STAR-5 (registered at {}): REFUTED (Phase 6a)",
    label=Label.DOC_FROZEN,
    source=Source(kind=Kind.DOC_FROZEN,
                  file="RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md",
                  line=1375, anchor="HYPOTHESE (Score 7/10)"),
    scenes=("act10_verdict_ladder",)))

_CL.append(Claim(
    # Ausfuehrungs-Prereg v2 (S₄-Schluss-Fix), frozen VOR der Messung;
    # Skelett-Anker f915729e unveraendert (§10.21)
    id="hstar5_md5", value="837dae2c",
    display="exec-prereg md5 {} (skeleton f915729e) — REFUTED",
    label=Label.DOC_FROZEN,
    source=Source(kind=Kind.DOC_FROZEN,
                  file="RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md",
                  line=1408, anchor="837dae2c19476eae0e7d13550c1e66f1"),
    scenes=("act10_verdict_ladder",)))

_CL.append(Claim(
    id="date_fez_singleshot", value="2026-06-10",
    display="{}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.DOC_FROZEN, file="README.md", line=64,
                  anchor="Fez/TOKEN2 Singleshot 2026-06-10"),
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="date_vqd", value="2026-07-21",
    display="{}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.DOC_FROZEN, file="README.md", line=64,
                  anchor="2026-07-21"),
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="date_fez_phi", value="2026-09-15",
    display="{}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.DOC_FROZEN, file="README.md", line=61,
                  anchor="2026-09-15"),
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    id="date_kingston", value="2026-09-24",
    display="{}", label=Label.DOC_FROZEN,
    source=Source(kind=Kind.DOC_FROZEN, file="README.md", line=62,
                  anchor="2026-09-24"),
    scenes=("act4_qpu_timeline",)))

_CL.append(Claim(
    # 046c1cc: 642 — auf hstar5-execution: +26 Execution-Tests -> 668;
    # v2 (S₄-Schluss-Fix): +3 Miniatur-Theorem-Tests -> 671;
    # ram-q-zyklizitaet: +26 RAM-Q-Tests (23 + 3 Post-Freeze-Pinning) -> 697;
    # Phase 8 (asymptotik): +19 (15 + 4 Post-Freeze-Pinning) -> 716;
    # Phase 9 (H-RAM-Q-3 Freeze A): +12 -> 728;
    # Stage-2 Aer-Bein (EXPERIMENT 042): +47 -> 776; +12 ISA-Runner-Tests
    # +1 run_stage2-Serialize-Regression -> 789; +2 w_B-Domain-Fix-Pins
    # (Sub-Domain/Exact-Exclusion, unclipped Gate) -> 791
    # (gerenderte Medien zeigen weiterhin den 046c1cc-Snapshot 642)
    id="test_count", value=791,
    display="{} tests collected", label=Label.MEASURED, grade=None,
    source=Source(kind=Kind.RECOMPUTE_CMD,
                  cmd=(sys.executable, "-m", "pytest", "tests/",
                       "--collect-only", "-q"),
                  regex=r"(\d+) tests? collected"),
    tol=0.0,
    scenes=("act1_title", "act10_verdict_ladder")))

CLAIMS: dict = {c.id: c for c in _CL}

# --------------------------------------------------------------------------
# SCENES + DESIGN (visual_encoding / aesthetic_layer).
# --------------------------------------------------------------------------

SCENES: tuple = ("act1_title", "act2_pillar1", "act3_anomaly",
                 "act4_qpu_timeline", "act5_kappa", "act6_ramanujan",
                 "act7_qpe_peaks", "act8_fermat_grid", "act9_failure_board",
                 "act10_verdict_ladder")

# Headline claim per scene — the claim whose frozen criterion is shown
# BEFORE the result (explanation_scaffold). None = no headline (title,
# failure board, ladder).
HEADLINES: dict = {
    "act1_title": None,
    "act2_pillar1": "bias_points",
    "act3_anomaly": "alpha_1e6",
    "act4_qpu_timeline": "fez_phi",
    "act5_kappa": "kappa_star",
    "act6_ramanujan": "ram_gated",
    "act7_qpe_peaks": "hshor_bridge_min",
    "act8_fermat_grid": "hshor_verdict",
    "act9_failure_board": None,
    "act10_verdict_ladder": None,
}

DESIGN: dict = {
    "PRIME": "#FFC933",
    "COMPOSITE": "#3FA9F5",
    "FROZEN": "#7C4DFF",
    "QPU": "#E4572E",
    "HYPOTHESIS": "#8D99AE",
    "TEXT": "#F5F5F5",
    "MUTED": "#9E9E9E",
    "AXIS": "#616161",
    "GRADE_A": "#4CAF50",
    "GRADE_B": "#FFC933",
    "GRADE_C": "#8D99AE",
    "BG": "#0E1117",
}

# Layout geometry / axis labels / CSS that may contain digits (visual
# encoding constants — NOT data). Anything with a digit used in the render
# scripts must be listed here or route through claims.
DECORATIVE: frozenset = frozenset({
    # axis + unit labels (semantic labels, not measured values)
    "log10 N", "x: log10 N", "p1", "margin", "kappa", "κ*", "phi V",
    "sep V", "bias", "10⁶", "10⁵", "10⁴", "10³", "10²", "N = 10⁶",
    "S_vN", "share_prime", "P",
    # scene registry slugs (keys of SLUG_TO_CLASS in render_manim.py)
    "act1_title", "act2_pillar1", "act3_anomaly", "act4_qpu_timeline",
    "act5_kappa", "act6_ramanujan", "act7_qpe_peaks", "act8_fermat_grid",
    "act9_failure_board", "act10_verdict_ladder",
    # end-card identifiers (repo + license)
    "github.com/bartman081523/riemann-nuclear-synthesis", "CC-BY",
    # registered hypothesis names + data-carried window label (act8/act9)
    "V1", "V2", "V3", "H-STAR-5", "561",
    # axis label carrying the p1 symbol (act5 noise axes)
    "noise level (−log10 p1)",
    # codec / container tags used by the ffprobe medium gate + embeds
    # (libx264 is the remux fallback encoder in build_deck)
    "h264", "yuv420p", "aac", "1080p30", "480p15", "video/mp4", "mp4",
    "libx264",
    ".mp4", "media/", "presentation/media", "30",  # --fps final render
    # manim font sizes, run times, geometry are numeric literals —
    # registered in DECORATIVE_NUMS below.
})

DECORATIVE_NUMS: frozenset = frozenset({
    # font sizes
    20, 24, 26, 28, 30, 32, 36, 40, 44, 48, 54, 60,
    # run times / animation timings
    0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.75, 0.8, 1.0, 1.25, 1.5, 2.0,
    2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0,
    # layout offsets / scale factors
    0.06, 0.08, 0.1, 0.12, 0.15, 0.2, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6,
    0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.1, 1.2, 1.25, 1.3, 1.4,
    1.5, 1.6, 1.75, 2.0, 2.2, 2.5, 3.0, 3.2, 3.5, 4.0, 4.5, 5.0, 5.5,
    6.0, 6.5, 7.0, 7.5, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0,
    0.02, 0.04, 0.05, 0.08,
    # axis ranges (layout geometry — scale choices, not data)
    0, 1, 2, 3, 4, 5, 6, 7, -0.15, 0.25, 0.5, 0.75, 1.05,
    -0.006, 0.003, 0.006,  # bias-bar axis padding (band scale)
    0.3, 0.9,  # kappa-panel y bounds
    0.28, 625,  # QPE probability axis bounds
    400, 626,  # ramanujan P axis bounds
    100,  # kappa x-axis upper bracket
})

# HTML/CSS constants for the deck (build_deck.py) — layout only.
DECORATIVE_CSS: frozenset = frozenset({
    "font-size:0.8em", "font-size:0.85em", "font-size:1.1em",
    "font-size:1.2em", "font-size:0.9em", "font-size:1.05em",
    "margin:4px 0", "margin:6px 0", "max-height:62vh",
    "border-radius:8px", "grid-template-columns:repeat(2,1fr)",
    "width:100%", "border-left:4px solid", "padding:8px 12px",
    "opacity:0.85", "monospace", "sans-serif", "reveal",
})

CLAIM_IDS: frozenset = frozenset(CLAIMS)


# --------------------------------------------------------------------------
# Recompute engine.
# --------------------------------------------------------------------------

def _walk(obj, path):
    for step in path:
        if step == -1:
            obj = obj[-1]
        elif isinstance(step, int):
            obj = obj[step]
        else:
            obj = obj[step]
    return obj


@lru_cache(maxsize=None)
def _module_call(module: str, call: str, args: tuple):
    fn = getattr(import_module(module), call)
    return fn(*args)


@lru_cache(maxsize=None)
def recompute(id_: str):
    """Re-derive the claim value live from its committed source."""
    c = CLAIMS[id_]
    src = c.source
    if src.kind is Kind.RECOMPUTE_JSON:
        data = json.loads((REPO_ROOT / src.file).read_text(encoding="utf-8"))
        val = _walk(data, src.path)
    elif src.kind is Kind.RECOMPUTE_MODULE:
        # Cached per (module, call, args) so several claims share one
        # expensive call (H-SHOR-1 run_evaluation takes ~6.6 s).
        val = _module_call(src.module, src.call, src.args)
        if src.extract:
            val = _walk(val, src.extract)
    elif src.kind is Kind.RECOMPUTE_CMD:
        out = subprocess.run(src.cmd, cwd=REPO_ROOT, capture_output=True,
                             text=True, check=True).stdout
        m = re.search(src.regex, out)
        if m is None:
            raise ValueError(f"cmd claim {id_}: pattern not found")
        val = int(m.group(1))
    elif src.kind is Kind.DOC_FROZEN:
        return None  # pinned by anchor; verified by gate + tests
    else:  # pragma: no cover
        raise ValueError(f"unknown kind {src.kind}")
    if src.convention:
        val = _CONVENTIONS[src.convention](val)
    if isinstance(val, list):
        val = tuple(val)
    return val


def display(id_: str) -> str:
    """The on-screen string for a claim — recomputed, never from memory.

    DOC_FROZEN claims format their frozen value: the value itself is
    verified by the anchor gate (and the anchor test), so formatting the
    registered number is the recomputation-equivalent for a doc pin.
    """
    c = CLAIMS[id_]
    v = c.value if c.source.kind is Kind.DOC_FROZEN else recompute(id_)
    if c.fmt is not None:
        return c.fmt(v)
    return c.display.format(v)


def raw(id_: str):
    """Structured recomputed value (for plotting)."""
    return recompute(id_)


@lru_cache(maxsize=None)
def plot_data(id_: str):
    """Unconventioned full recompute for scene plotting (module claims).

    Scenes plot dense arrays (e.g. the QPE probability vector) that no
    claim can gate element-wise; the claim's summary convention freezes
    the gate-sized view of the SAME call, so plot_data stays consistent
    with the gate by construction (identical module/call/args).
    """
    c = CLAIMS[id_]
    src = c.source
    if src.kind is not Kind.RECOMPUTE_MODULE:
        raise ValueError(f"plot_data: {id_} is not module-backed")
    return _module_call(src.module, src.call, src.args)


def frozen_value(id_: str):
    """Numeric value of a DOC_FROZEN claim (anchor-verified by the gate)."""
    c = CLAIMS[id_]
    if c.source.kind is not Kind.DOC_FROZEN:
        raise ValueError(f"frozen_value: {id_} is not doc-frozen")
    return c.value


def criterion(id_: str) -> str:
    return CLAIMS[id_].criterion or ""


def grade(id_: str):
    return CLAIMS[id_].grade


def gloss(id_: str):
    return CLAIMS[id_].gloss or ""


def source_tag(id_: str) -> str:
    """Short provenance line shown under a claim."""
    c = CLAIMS[id_]
    src = c.source
    if src.kind is Kind.RECOMPUTE_JSON:
        return f"JSON {src.file}"
    if src.kind is Kind.RECOMPUTE_MODULE:
        return f"live {src.module}.{src.call}()"
    if src.kind is Kind.RECOMPUTE_CMD:
        return "live test collection"
    return f"doc {src.file}:{src.line}"


# --------------------------------------------------------------------------
# Gate (fidelity_audit — publish-stop).
# --------------------------------------------------------------------------

class FidelityGateError(RuntimeError):
    """Raised by main() entry points when the gate fails."""


def _close(a, b, tol):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if a is None or b is None:
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= tol
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(
            _close(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(
            _close(x, y, tol) for x, y in zip(a, b))
    return a == b


def check_gate(full: bool = True) -> list:
    """Recompute every claim; return a list of mismatch messages ([] = pass).

    full=False skips RECOMPUTE_CMD claims (pytest collection subprocess)
    for the in-test/CI light mode.
    """
    mismatches = []
    for id_, c in CLAIMS.items():
        if not full and c.source.kind is Kind.RECOMPUTE_CMD:
            continue
        try:
            got = recompute(id_)
        except Exception as exc:  # noqa: BLE001 — report, don't crash
            mismatches.append(f"{id_}: recompute raised {type(exc).__name__}: {exc}")
            continue
        if c.source.kind is Kind.DOC_FROZEN:
            if not _doc_anchor_ok(c.source):
                mismatches.append(
                    f"{id_}: doc anchor {c.source.anchor!r} not found near "
                    f"line {c.source.line} in {c.source.file}")
            continue
        if not _close(got, c.value, c.tol):
            mismatches.append(
                f"{id_}: expected {c.value!r}, recomputed {got!r} "
                f"(source: {source_tag(id_)})")
    return mismatches


def _doc_anchor_ok(src: Source) -> bool:
    path = REPO_ROOT / src.file
    if not path.exists():
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    lo = max(0, (src.line or 1) - 41)
    hi = min(len(lines), (src.line or 1) + 40)
    window = "\n".join(lines[lo:hi])
    return src.anchor in window


def raise_if_gate_fails(full: bool = True) -> None:
    """Publish-stop helper for main() of both scripts."""
    mismatches = check_gate(full=full)
    if mismatches:
        raise FidelityGateError(
            "fidelity gate FAILED — publish-stop:\n"
            + "\n".join(f"  - {m}" for m in mismatches))


def write_report(path: Path | None = None) -> Path:
    """Write presentation/fidelity_report.md (committed deliverable)."""
    out = path or (PRESENTATION_DIR / "fidelity_report.md")
    lines = ["# Fidelity report — presentation claims",
             "",
             "Every claim recomputed from its committed source at build time.",
             ""]
    mism = check_gate(full=True)
    lines.append(f"**Gate:** {'PASS — 0 mismatches' if not mism else f'FAILED — {len(mism)} mismatches'}")
    if mism:
        lines += [""] + [f"- {m}" for m in mism]
    lines += ["", "| id | label | grade | scenes | value (expected) | source |",
              "|---|---|---|---|---|---|"]
    for id_, c in CLAIMS.items():
        val = c.value
        shown = repr(val)
        if len(shown) > 60:
            shown = shown[:57] + "…"
        scenes = ", ".join(c.scenes)
        lines.append(f"| {id_} | {c.label.value} | {c.grade or '—'} "
                     f"| {scenes} | `{shown}` | {source_tag(id_)} |")
    lines += ["", "## Criteria shown before results (explanation_scaffold)", ""]
    for id_, c in CLAIMS.items():
        if c.criterion:
            lines.append(f"- **{id_}** — {c.criterion}")
    lines += ["", "## Glosses (audience_calibration, ≤ 12 words)", ""]
    for id_, c in CLAIMS.items():
        if c.gloss:
            lines.append(f"- **{id_}** — {c.gloss}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out