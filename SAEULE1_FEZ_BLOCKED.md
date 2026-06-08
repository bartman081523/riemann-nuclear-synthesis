# Säule 1 Fez Submission — Blockiert durch Account-Kontingent

**Datum:** 2026-06-08
**Skript:** `pt_potential_vqe.py`
**Backend:** `ibm_fez` (156 Qubits, operational)
**Test-Stand:** 55/55 grün

## Befund

Nach drei Versuchen, `pt_potential_vqe.py` auf Fez zu submitten, scheiterten
alle drei Runs. Ursachen und Lösungen:

### Versuch 1 (`bzmtvyu13`): ValueError
```
ValueError: Length of ('θ[0]', ..., 'θ[5]') inconsistent with last dimension of [0.523, 1.21, -0.45, 0.88]
```
- **Ursache:** TwoLocal(2, ry, cx, linear, reps=2) hat 6 Parameter, `INITIAL_PARAMS` nur 4.
- **Fix:** Auto-Detection aus `isa_ansatz.num_parameters`, zyklische Erweiterung wenn zu kurz.

### Versuch 2 (`b0pekypf3`): UnboundLocalError
```
UnboundLocalError: cannot access local variable 'INITIAL_PARAMS' where it is not associated with a value
```
- **Ursache:** Re-Assignment von `INITIAL_PARAMS` im `main()`-Scope macht Python-Lookup zu lokal, Lese-Zugriff vor Zuweisung schlägt fehl.
- **Fix:** Lokale Variable `initial_params = list(INITIAL_PARAMS)` zu Beginn von `main()`, alle Re-Assignments/Lese-Zugriffe verwenden diese.

### Versuch 3 (`bf3yqz8tt`): Account-Kontingent erschöpft
```
UserWarning: This instance has met its usage limit. Workloads will not run until time ismade available.
```
- **Diagnose:** IBM Open-Plan (Free Tier) hat monatliches Minuten-Limit erreicht.
- **Bestätigt durch:** Sanity-Test mit minimalem 1-Pub-Job (`d8ji5crnn5bs738plgj0`) wurde von Fez akzeptiert (QUEUED), läuft aber nicht — Limit blockiert Workloads.
- **Backend-Status:** Fez ist operational, 0 pending jobs — die Blockade liegt am **Account**, nicht am Backend.

## Aktionen

- Code-Bugs (1+2) sind behoben, alle 55 Tests grün.
- Sanity-Test-Job `d8ji5crnn5bs738plgj0` wurde gecancelt, keine wartenden Credits.
- `pt_potential_vqe.py` ist **QPU-ready** und wird ausgeführt, sobald das Kontingent zurückgesetzt ist (Anfang Juli 2026, monatlicher Reset).

## Alternative Vorgehensweise

Da Hardware blockiert ist, können wir in der Zwischenzeit:
1. **Aer-Simulation mit Fez-Rauschprofil** statt echter Hardware
   (`pt_aer_stress_test.py` als Vorlage).
2. **Säule 2 (G-Apparat)** auf Fez submitten — gleiche Kontingent-Blockade,
   aber Pre-Registrierung + offline-Resultate sind schon im Repo.
3. **Säule 3 (Prime States)** mit Grover-Oracle in Qiskit lokal simulieren.
4. **Säule 4 (GF(5))** läuft komplett offline, keine Hardware nötig.

## Strategic Vector Update

**Säule 1 Status:** QPU-ready, wartet auf Kontingent-Reset.
**Nächster Schritt (offline):** Aer-Stress-Test mit Fez-Rauschprofil als
Hardware-Validierung-Surrogat, um die relative-Spektrum-Hypothese (H1/H3)
auch ohne echte QPU zu testen.
