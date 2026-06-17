"""
pt_spectral_scaling_statevector.py - Statevector baseline for spectral-scaling test.

Prereg: pt_spectral_scaling_prereg.json
Decision: H_BlockDiag_Invariance_Statevector: max(|Im_E_i(H_PT_n) - Im_E_i(H_PT_2)|) < 1e-6

Berechnet:
  - H_PT_2x2, H_PT_3x3, H_PT_4x4 mit derselben E_DIAG[:n] truncation
  - Imaginärteile der Eigenwerte (sortiert nach Realteil)
  - Vergleich: Im_E_0..1(H_PT_n) ≈ Im_E_0..1(H_PT_2)?
"""
import json
import numpy as np
from pt_structural import jacobi_A, E_DIAG

GAMMA = 0.02


def build_H_PT_n(n, gamma=GAMMA, y=1.0):
    """Build H_PT on E_DIAG[:n] mit jacobi_A Kopplung."""
    x_levels = E_DIAG[:n]
    A = jacobi_A(x_levels, y=y)
    H_diag = np.diag(x_levels).astype(complex)
    return H_diag + 1j * gamma * A, A, H_diag


def main():
    print("=" * 70)
    print("SPECTRAL-SCALING STATEVECTOR BASELINE")
    print("=" * 70)

    # === Compute spectra for n=2, 3, 4 ===
    spectra = {}
    matrices = {}
    for n in [2, 3, 4]:
        H_PT, A, H_diag = build_H_PT_n(n)
        eigs = sorted(np.linalg.eigvals(H_PT), key=lambda z: z.real)
        spectra[n] = [{"re": float(e.real), "im": float(e.imag)} for e in eigs]
        matrices[n] = {
            "A": A.tolist(),
            "E_diag": np.diag(H_diag).real.tolist(),
        }
        print(f"\nH_PT_{n}x{n} (gamma={GAMMA}):")
        for i, e in enumerate(spectra[n]):
            print(f"  E_{i} = {e['re']:.8f} + {e['im']:.8f}j")

    # === Test H_BlockDiag_Invariance_Statevector ===
    # Im_E_i(H_PT_n) for i in {0,1} should match Im_E_i(H_PT_2) for n in {3, 4}
    ref_im = [spectra[2][i]["im"] for i in range(2)]
    print(f"\nReference Im_E_0..1 (H_PT_2x2): {[f'{x:+.8f}' for x in ref_im]}")

    all_pass = True
    block_diffs = []
    for n in [3, 4]:
        im_n = [spectra[n][i]["im"] for i in range(2)]
        diffs = [abs(im_n[i] - ref_im[i]) for i in range(2)]
        max_diff = max(diffs)
        block_diffs.append({"n": n, "diffs": diffs, "max": max_diff})
        passed = max_diff < 1e-6
        all_pass = all_pass and passed
        print(f"  n={n}: Im_E_0..1 = {[f'{x:+.8f}' for x in im_n]}")
        print(f"         max |diff| = {max_diff:.2e} -> {'PASS' if passed else 'FAIL'}")

    # === Save baseline ===
    baseline = {
        "prereg_file": "pt_spectral_scaling_prereg.json",
        "prereg_md5": "984886c53e47fa82aa0ce2009daefbed",
        "method": "pt_spectral_scaling_statevector.py - H_PT on E_DIAG[:n] for n in {2,3,4}",
        "gamma": GAMMA,
        "E_DIAG_full": E_DIAG.tolist(),
        "spectra": {str(n): spectra[n] for n in [2, 3, 4]},
        "H_BlockDiag_Invariance_Statevector": {
            "test": "max(|Im_E_i(H_PT_n) - Im_E_i(H_PT_2)|) < 1e-6",
            "diffs": block_diffs,
            "PASS": bool(all_pass),
        },
        "decision_rule": (
            "PASS H_BlockDiag_Invariance_Statevector if all max_diffs < 1e-6. "
            "Algebraic identity: the 2x2 Jacobi block is preserved under block extension."
        ),
    }
    with open("pt_spectral_scaling_statevector_results.json", "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"\n{'='*70}")
    print(f"H_BlockDiag_Invariance_Statevector: {'PASS' if all_pass else 'FAIL'}")
    print(f"Baseline saved: pt_spectral_scaling_statevector_results.json")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
