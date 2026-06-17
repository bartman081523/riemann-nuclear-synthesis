> **STATUS: SUPERSEDED 2026-06-17** (quota resolved, H_Im_h1 genuinely QPU-confirmed).
>
> This file documents the Fez quota blockade (6/8–6/16/2026) and the associated code bug fixes (Qiskit version incompatibility, TOKEN1 quarantine blockade, statevector-first architecture). The content remains **historically and technically valuable** (especially the code bug fixes), but is **no longer the source of truth** for the current status.
>
> Successor for current Pillar-1 status: [`QUANTUM_ARCHITECTURE_IMPLEMENTATION.md`](QUANTUM_ARCHITECTURE_IMPLEMENTATION.md) §"Update 2026-06-17 17:25 UTC".
>
> Current theory status: [`RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md`](RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md) §10 (Operational Findings Log).

# Pillar 1 Fez Submission — Blocked by Account Quota

**Date:** 2026-06-08
**Script:** `pt_potential_vqe.py`
**Backend:** `ibm_fez` (156 Qubits, operational)
**Test status:** 55/55 green

## Finding

After three attempts to submit `pt_potential_vqe.py` to Fez, all three runs
failed. Causes and fixes:

### Attempt 1 (`bzmtvyu13`): ValueError
```
ValueError: Length of ('θ[0]', ..., 'θ[5]') inconsistent with last dimension of [0.523, 1.21, -0.45, 0.88]
```
- **Cause:** TwoLocal(2, ry, cx, linear, reps=2) has 6 parameters, `INITIAL_PARAMS` only 4.
- **Fix:** Auto-detection from `isa_ansatz.num_parameters`, cyclic extension if too short.

### Attempt 2 (`b0pekypf3`): UnboundLocalError
```
UnboundLocalError: cannot access local variable 'INITIAL_PARAMS' where it is not associated with a value
```
- **Cause:** Reassignment of `INITIAL_PARAMS` in the `main()` scope makes Python lookup local, read access before assignment fails.
- **Fix:** Local variable `initial_params = list(INITIAL_PARAMS)` at the start of `main()`, all reassignments/read accesses use this.

### Attempt 3 (`bf3yqz8tt`): Account quota exhausted
```
UserWarning: This instance has met its usage limit. Workloads will not run until time ismade available.
```
- **Diagnosis:** IBM Open Plan (Free Tier) has reached its monthly minutes limit.
- **Confirmed by:** Sanity test with minimal 1-Pub job (`d8ji5crnn5bs738plgj0`) was accepted by Fez (QUEUED), but does not run — the limit blocks workloads.
- **Backend status:** Fez is operational, 0 pending jobs — the blockade is at the **account** level, not the backend.

## Actions

- Code bugs (1+2) are fixed, all 55 tests green.
- Sanity test job `d8ji5crnn5bs738plgj0` was canceled, no waiting credits.
- `pt_potential_vqe.py` is **QPU-ready** and will run as soon as the quota is reset (early July 2026, monthly reset).

## Alternative Procedure

Since hardware is blocked, we can in the meantime:
1. **Aer simulation with Fez noise profile** instead of real hardware
   (`pt_aer_stress_test.py` as a template).
2. **Pillar 2 (G-Apparatus)** submit to Fez — same quota blockade,
   but pre-registration + offline results are already in the repo.
3. **Pillar 3 (Prime States)** simulate locally in Qiskit with Grover oracle.
4. **Pillar 4 (GF(5))** runs completely offline, no hardware needed.

## Strategic Vector Update

**Pillar 1 status:** QPU-ready, waiting for quota reset.
**Next step (offline):** Aer stress test with Fez noise profile as
hardware validation surrogate, to test the relative spectrum hypothesis (H1/H3)
even without a real QPU.
