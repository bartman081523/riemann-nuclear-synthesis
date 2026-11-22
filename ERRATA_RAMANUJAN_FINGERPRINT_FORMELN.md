# Errata: Formel-Typos in „Srinivasa Ramanujans göttliche Mathematik.md"

Bezugsdokument (NICHT editiert, Import-Log bleibt byte-identisch):
`Srinivasa Ramanujans göttliche Mathematik.md` (Repo-Root, untracked).

Code-Referenz (maßgeblich, gefroren):
`pt_ram_q_zyklizitaet.py:35-36` (Baustein B1),
`pt_ram_q_asymptotik.py:37` (Baustein B2),
`src/primequant/observables.py:120-126` (exakte Fraction-Spiegel).

## Befund 1 — Fehlender Bruchstrich (Zeilen 52, 58, 120, 148, 152)

Gedruckt (sinngemäß): `share = (q−1)·d·m·(m−q·n0)²`
bzw. `Share(m) = 4·d·m·(m−5)²`.

Richtig:

    share*_model(P, d=q^k) = (m − q·n0)² / ((q−1)·d·m)

Spezialfälle: q=5, n0=1: `(m−5)²/(4·d·m)`; q=3, n0=1: `(m−3)²/(2·d·m)`.

Ursache: Darstellungs-Artefakt des Markdown-Exports (Zähler/Nenner
kollabiert). Inhaltlich belegt B1 die Bruchform; alle 056/057-Pins
rechnen damit (z. B. P=625,d=625,q=5: share 1522/35625, Modell
11881/285000, ratio 12176/11881).

## Befund 2 — B2-Zeile 208 verdreht

Gedruckt (sinngemäß): `share = (q−1)·d·m·(m−q·n0)² + d·m·q·σ²`.

Richtig (`pt_ram_q_asymptotik.py:37`):

    share*_q = (m − q·n0)²/((q−1)·d·m) + q·σ²/(d·m)
    ratio   = 1 + q·(q−1)·σ²/(m − q·n0)²  ≥ 1  (n0=1, m>q)

## Verifikation (0 QPU, seed-frei)

    ./venv/bin/python scratches/pt_ququint_ramanujan_symcomp_056.py
      # H-SYMCOMP_CONFIRMED (Prereg-md5 a7922c99…), E4-Fraction-Identität exakt
    ./venv/bin/python scratches/pt_mocs_hp_target_057.py
      # H-MOCS-HP_CONFIRMED
    ./venv/bin/python scratches/pt_mocs_ext_repin_058.py
      # H-REPIN-EXT_CONFIRMED (023-EXT-Repin, T1–T4 grün)

Status: beide Befunde rein typografisch; keine Re-Decide-, kein
Umdeutungs-Bedarf an den gefrorenen Preregs/Results.
