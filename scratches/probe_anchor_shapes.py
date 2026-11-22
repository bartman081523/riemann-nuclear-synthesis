"""Schema-Zensus, zweiter Lauf: alle Feld-/Key-Namen für die Anchor-Tests.

Fixt den Absturz von Lauf 1: kalibriere_dokument nimmt einen Pfad (calibrations.py
ruft lies_rohdokument(pfad)), nicht die Counts-Liste. Ausserdem: H-Mapping per
Name+P (Lauf-1-Mapping war falsch), q5-punkt-Zensus (sigma2-Name), Struktur-
Familien-Zensus (111/37), readout_cal-Namen auf allen drei Rohs, dir(ch)-Sweep,
Guard-Texte für punkt/quote/ring_dft/norm/ramanujan.
"""
import json
import sys
from fractions import Fraction as F

sys.path.insert(0, "src")
import numpy as np

import primequant as pq
import primequant.channels as ch
from primequant import observables as obs

RAW = ("pt_ram_q_prio48_sv_raw.json",
       "pt_ram_q_hardware3_raw.json",
       "pt_ram_q6_kingston_raw.json")

dokumente = {}
for name in RAW:
    dokumente[name] = pq.lies_rohdokument(name)
reihen = dokumente["pt_ram_q_prio48_sv_raw.json"]["counts"]
hw3 = dokumente["pt_ram_q_hardware3_raw.json"]["counts"]

print("== A hasattr sweep (obs/bands) ==")
for name in ("punkt_konstanten", "quote_exakt", "ring_dft", "quad_magnitude",
             "norm_galois", "galois_konjugiert", "ramanujan_summe",
             "binom_cdf_exakt", "binom_tail_exakt", "p_wert_zweiseitig",
             "alpha_bonferroni", "band_quantile", "chebyshev_schranke",
             "cantelli_schranke", "modell_fuer_art", "tv_exakt",
             "exakter_probvektor", "fuele_modell", "delta_vektor",
             "residue_counts", "sieve_primes"):
    print("  ", name, hasattr(pq, name))

print("== B raw top-level + counts_sha256 (live) ==")
for name in RAW:
    dok = dokumente[name]
    print(name, "| backend:", dok.get("backend"), "| fetched:",
          dok.get("fetched_at_utc"))
    print("   counts_sha256:",
          pq.payload_sha256(pq.counts_payload(dok["counts"])))

print("== C key-union je kind (sv raw) ==")
for art in sorted({r["kind"] for r in reihen}):
    k_union = set()
    for r in reihen:
        if r["kind"] == art:
            k_union |= set(r.keys())
    print("  ", art, sorted(k_union))
erste = reihen[0]
print("first row minus counts:", json.dumps(
    {k: v for k, v in erste.items() if k != "counts"}, sort_keys=True)[:900])
print("== D kinds tally (sv) ==")
tally = {}
for r in reihen:
    tally[r["kind"]] = tally.get(r["kind"], 0) + 1
print("tally:", tally, "| sum:", sum(tally.values()))

print("== E Struktur-Familie census (111/37?) ==")
familie = [r for r in reihen if r["kind"] in pq.STRUKTUR_REIHENARTEN]
paar_z = {}
for r in familie:
    schluessel = (r.get("arm"), r.get("P"))
    paar_z[schluessel] = paar_z.get(schluessel, 0) + 1
print("familie rows:", len(familie), "| distinct (arm,P):", len(paar_z))
print("je-punkt-Zahlen:", sorted(set(paar_z.values())))
print("paare:", sorted(paar_z))

print("== G delta TV census (45 == 0?) ==")
delta_reihe = [r for r in reihen if r["kind"] in pq.DELTA_REIHENARTEN]
null_n = 0
for r in delta_reihe:
    nq = max(len(label) for label in r["counts"].keys())
    tv = pq.tv_exakt(r["counts"], pq.modell_fuer_art(r["kind"], nq))
    if tv == 0:
        null_n += 1
    else:
        print("   NICHT 0:", r["kind"], str(tv))
print("delta rows:", len(delta_reihe), "| TV==0:", null_n)

print("== H Kontrolle-TV mapping (per Name+P) ==")
neg = [r for r in reihen if r["kind"] == "negative_control"]
for r in neg:
    name = r["name"]
    breite = 1 << max(len(x) for x in r["counts"])
    if "composite" in name:
        p_nummer = 181 if "P181" in name else 467
        n_d, m_norm = {181: ([19, 13, 10], 42),
                       467: ([23, 18, 17, 15, 18], 91)}[p_nummer]
        modell = pq.fuele_modell(pq.exakter_probvektor(n_d, m_norm), breite)
        art = "composite P%d" % p_nummer
    else:
        nq = max(len(x) for x in r["counts"])
        q_wert = 3 if name.endswith("_q3") else 5
        modell = pq.modell_fuer_art("negative_control", nq, q=q_wert)
        art = "uniform q%d" % q_wert
    tv = pq.tv_exakt(r["counts"], modell)
    print("  ", name, "->", art, "breite:", breite, "TV:", str(tv), "=",
          repr(float(tv)))

print("== I first-struct quote (sv row 0) ==")
z = reihen[0]
kc = obs.punkt_konstanten(181, 3, 3)
res = obs.quote_exakt(z["counts"], kc)
for k in sorted(res.keys()):
    print("  ", k, "=", str(res[k]))

print("== I5 punkt-Konstanten alle 10 Zeilen (shots=8192) ==")
for args in ((181, 3, 3), (181, 5, 5), (269, 3, 3), (269, 5, 5),
             (467, 3, 3), (467, 5, 5), (673, 3, 3), (673, 5, 5),
             (2005, 3, 3), (2005, 5, 5)):
    kc = obs.punkt_konstanten(args[0], args[1], args[2], shots=8192)
    print(" ", args, sorted(kc.keys()))
    for k in sorted(kc.keys()):
        print("     ", k, "=", str(kc[k]))

print("== I6 mini punkt (13/3/3 s12, 31/7/7 s56) ==")
for args in ((13, 3, 3, 12), (31, 7, 7, 56)):
    kc = obs.punkt_konstanten(args[0], args[1], args[2], shots=args[3])
    print(" ", args)
    for k in sorted(kc.keys()):
        print("     ", k, "=", str(kc[k]))

print("== I7 default == shots 8192? ==")
kc_def = obs.punkt_konstanten(181, 3, 3)
kc_8192 = obs.punkt_konstanten(181, 3, 3, shots=8192)
print("gleich:", all(str(kc_def[k]) == str(kc_8192[k]) for k in kc_def))

print("== J kalibriere hw3 (PFAD) ==")
try:
    kal = pq.kalibriere_dokument("pt_ram_q_hardware3_raw.json")
    print("ret type:", type(kal).__name__)
    if isinstance(kal, dict):
        print("ret keys:", sorted(kal.keys()))
        for k, v in kal.items():
            print("  ", k, "=", str(v)[:500])
    else:
        print("ret:", repr(kal)[:500])
except Exception as exc:  # noqa: BLE001
    print("EXC:", type(exc).__name__, "|", exc)

print("== K kalibriere kingston (PFAD) ==")
try:
    kal_k = pq.kalibriere_dokument("pt_ram_q6_kingston_raw.json")
    print("ret type:", type(kal_k).__name__)
    if isinstance(kal_k, dict):
        print("ret keys:", sorted(kal_k.keys()))
        for k, v in kal_k.items():
            print("  ", k, "=", str(v)[:500])
    else:
        print("ret:", repr(kal_k)[:500])
except Exception as exc:  # noqa: BLE001
    print("EXC:", type(exc).__name__, "|", exc)

print("== L kalibriere sv (fetched None) ==")
try:
    pq.kalibriere_dokument("pt_ram_q_prio48_sv_raw.json")
    print("KEINE Ausnahme!")
except Exception as exc:  # noqa: BLE001
    print("EXC:", type(exc).__name__, "|", exc)

print("== M modell_fuer_art Laengen-Census ==")
for label, aufruf in (
        ("structure arg=2", lambda: pq.modell_fuer_art(
            "structure", 2, n_d=[19, 13, 10], m=42)),
        ("neg uniform arg=3 q=3", lambda: pq.modell_fuer_art(
            "negative_control", 3, q=3)),
        ("neg composite arg=2", lambda: pq.modell_fuer_art(
            "negative_control", 2, n_d=[19, 13, 10], m=42)),
        ("struktur arg=3", lambda: pq.modell_fuer_art(
            "structure", 3, n_d=[19, 13, 10], m=42))):
    try:
        erg = aufruf()
        print("  ", label, "len:", len(erg), "->", [str(x) for x in erg][:4])
    except Exception as exc:  # noqa: BLE001
        print("  ", label, "EXC:", type(exc).__name__, "|", exc)

print("== N kohärenz/dir(ch) ==")
print("dir(ch):", sorted(n for n in dir(ch) if not n.startswith("_")))
if hasattr(ch, "kohärenz_max"):
    probe = np.diag([1.0, 0.0, 0.0, 0.0])
    print("koh. delta:", repr(ch.kohärenz_max(probe)))
    print("koh. gemischt:", repr(ch.kohärenz_max(np.diag([0.5, 0.5]) if
                                                  True else probe)))

print("== O ro_intervall synth ==")
for zeile in ({"name": "synth_7938", "shots_actual": 8192,
               "counts": {"00": 7938, "01": 254}},
              {"name": "synth_voll", "shots_actual": 8192,
               "counts": {"00": 8192}}):
    try:
        resultat = pq.ro_intervall(zeile)
        print("  ", zeile["name"], "->", {k: str(v) if isinstance(v, F)
                                          else v for k, v in resultat.items()})
    except Exception as exc:  # noqa: BLE001
        print("  ", zeile["name"], "EXC:", type(exc).__name__, "|", exc)

print("== P readout_cal-Reihen auf allen drei Rohs ==")
for dok_name, rk in (("sv", reihen), ("hw3", hw3),
                     ("kingston", dokumente["pt_ram_q6_kingston_raw.json"]
                      ["counts"])):
    cal_reihe = [r for r in rk if r.get("kind") == "readout_cal"]
    print("  ", dok_name, "readout_cal-Anzahl:", len(cal_reihe))
    for r in cal_reihe:
        print("    ", r["name"], "| row-keys:", sorted(set(r) - {"counts"}))
        print("       counts:", r["counts"])
        try:
            iv = pq.ro_intervall(r)
            print("       ro_intervall:", {k: str(v) if isinstance(v, F)
                                           else v for k, v in iv.items()})
        except Exception as exc:  # noqa: BLE001
            print("       ro_intervall EXC:", type(exc).__name__, "|", exc)
        try:
            rf = pq.rand_flip_anteile(r)
            print("       rand_flip:", {k: str(v) for k, v in rf.items()})
        except Exception as exc:  # noqa: BLE001
            print("       rand_flip EXC:", type(exc).__name__, "|", exc)
try:
    echte = pq.lese_readout_cal_reihen(dokumente["pt_ram_q_hardware3_raw.json"])
    print("  hw3 lese_readout_cal_reihen:", type(echte).__name__,
          "[len %d]" % len(echte) if hasattr(echte, "__len__") else "")
    if isinstance(echte, list) and echte:
        print("    erstes ret:", str(echte[0])[:400])
except Exception as exc:  # noqa: BLE001
    print("  lese EXC:", type(exc).__name__, "|", exc)

print("== Q ganzzahl_wurzel ==")
for x, n in ((0, 5), (1, 3), (8, 3), (9, 3), (8064 ** 2, 2),
             (8064 ** 2 + 1, 2)):
    print("  ", (x, n), "->", pq.ganzzahl_wurzel(x, n))

print("== R payload/versichere/lies_committed ==")
print("payload1:", pq.counts_payload([{"0": 1}]))
print("payload2:", pq.counts_payload([{"1": 2}, {"0": 1}]))
print("payload3 (sorted keys):", pq.counts_payload([{"01": 2, "00": 1}]))
print("sha_abc:", pq.payload_sha256(b"abc"))
try:
    pq.payload_sha256("abc")
except Exception as exc:  # noqa: BLE001
    print("EXC payload_sha256(str):", type(exc).__name__, "|", exc)
try:
    pq.datei_sha256("scratches/kein_dokument_lala.json")
except Exception as exc:  # noqa: BLE001
    print("EXC datei:", type(exc).__name__, "|", exc)
try:
    pq.lies_rohdokument("scratches/kein_dokument_lala.json")
except Exception as exc:  # noqa: BLE001
    print("EXC roh:", type(exc).__name__, "|", exc)
dok_ok = dokumente["pt_ram_q_prio48_sv_raw.json"]
try:
    print("versichere ok:", str(pq.versichere_counts_md5(dok_ok))[:120])
except Exception as exc:  # noqa: BLE001
    print("versichere ok EXC:", type(exc).__name__, "|", exc)
falsch = dict(dok_ok)
falsch["counts_md5"] = "0" * 32
try:
    pq.versichere_counts_md5(falsch)
    print("falsch KEINE Ausnahme!")
except Exception as exc:  # noqa: BLE001
    print("falsch ->", type(exc).__name__, "|", exc)
ohne = {k: v for k, v in falsch.items() if False}
try:
    pq.versichere_counts_md5({k: v for k, v in dok_ok.items()
                              if k != "counts_md5"})
    print("ohne KEINE Ausnahme!")
except Exception as exc:  # noqa: BLE001
    print("ohne ->", type(exc).__name__, "|", exc)
ret = pq.lies_committed_counts("pt_ram_q_prio48_sv_raw.json")
print("lies_committed_counts ret type:", type(ret).__name__)
if isinstance(ret, dict):
    print("  keys:", sorted(ret.keys())[:12])
else:
    print("  len:", len(ret), "| erstes:", str(ret[0])[:120])

print("== S punkt/quote guards ==")
for args in ((11, 5, 5), (7, 7, 3), (1, 3, 3)):
    try:
        obs.punkt_konstanten(*args)
        print("  punkt", args, "-> KEINE Ausnahme!")
    except Exception as exc:  # noqa: BLE001
        print("  punkt", args, "->", type(exc).__name__, "|", exc)

konst13 = obs.punkt_konstanten(13, 3, 3, shots=12)
uni = obs.quote_exakt({"00": 4, "01": 4, "10": 4}, konst13, shots=12)
print("uniform quote:", {k: str(v) for k, v in uni.items()})
delta_q = obs.quote_exakt({"00": 12}, konst13, shots=12)
print("delta0   quote:", {k: str(v) for k, v in delta_q.items()})
verschi = obs.quote_exakt({"01": 12}, konst13, shots=12)
print("delta1   quote:", {k: str(v) for k, v in verschi.items()})
for label, aufruf in (
        ("synth d", lambda: obs.quote_exakt(
            {"00": 2, "01": 2},
            {"P": 10, "d": 5, "q": 3, "m": 4, "model_share_reg": F(1)})),
        ("shots0", lambda: obs.quote_exakt({"00": 12}, konst13, shots=0)),
        ("summe", lambda: obs.quote_exakt({"00": 10}, konst13, shots=12)),
        ("label", lambda: obs.quote_exakt({"0000": 12}, konst13, shots=12))):
    try:
        aufruf()
        print("  quote", label, "-> KEINE Ausnahme!")
    except Exception as exc:  # noqa: BLE001
        print("  quote", label, "->", type(exc).__name__, "|", exc)

print("== S2 lese guards synth ==")
for dok in ({"x": 1}, {"counts": []}, {"counts": [{"kind": "structure",
                                                   "counts": {"00": 1}}]}):
    try:
        pq.lese_readout_cal_reihen(dok)
        print("  ", list(dok.keys()), "-> KEINE Ausnahme!")
    except Exception as exc:  # noqa: BLE001
        print("  ", list(dok.keys()), "->", type(exc).__name__, "|", exc)
for label, reihen_synth in (
        ("sum7", [{"kind": "readout_cal", "name": "g", "counts": {"00": 7},
                   "shots": 8}]),
        ("laengen", [{"kind": "readout_cal", "name": "g",
                      "counts": {"0": 4, "00": 4}, "shots": 8}]),
        ("shots0", [{"kind": "readout_cal", "name": "g",
                     "counts": {"00": 8}, "shots": 0}]),
        ("masse4.5", [{"kind": "readout_cal", "name": "g",
                       "counts": {"01": 4.5}, "shots": 8}])):
    try:
        pq.lese_readout_cal_reihen({"counts": reihen_synth})
        print("  ", label, "-> KEINE Ausnahme!")
    except Exception as exc:  # noqa: BLE001
        print("  ", label, "->", type(exc).__name__, "|", exc)