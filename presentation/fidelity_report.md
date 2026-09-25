# Fidelity report — presentation claims

Every claim recomputed from its committed source at build time.

**Gate:** PASS — 0 mismatches

| id | label | grade | scenes | value (expected) | source |
|---|---|---|---|---|---|
| alpha_1e6 | measured | A− | act3_anomaly | `0.22275345050922138` | JSON pt_asymptotic_N1e6_results.json |
| alpha_curve | measured | A− | act3_anomaly | `((31, 0.33305202609341633), (63, 0.2597306718152198), (12…` | JSON pt_asymptotic_N1e6_results.json |
| alpha_at_31 | measured | A− | act3_anomaly | `0.33305202609341633` | JSON pt_asymptotic_N1e6_results.json |
| alpha_verdict | doc-frozen | — | act3_anomaly | `'H_C (anderes Power-Law)'` | JSON pt_asymptotic_N1e6_results.json |
| alpha_qpu | measured | A− | act3_anomaly, act4_qpu_timeline | `0.3478584070739363` | JSON pt_prime_state_qpu_singleshot_results.json |
| alpha_aer | measured | A− | act3_anomaly, act4_qpu_timeline | `0.271875107307134` | JSON pt_prime_state_qpu_singleshot_results.json |
| alpha_latorre | doc-frozen | — | act3_anomaly | `1.0` | JSON pt_prime_state_qpu_singleshot_results.json |
| alpha_qpu_verdict | doc-frozen | — | act3_anomaly | `'QPU bestaetigt Aer (DISSENS zu Latorre-Sierra)'` | JSON pt_prime_state_qpu_singleshot_results.json |
| deriv_sign_global | measured | A− | act3_anomaly | `'negative'` | JSON pt_alpha_derivative_results.json |
| bias_points | measured | A+ | act2_pillar1 | `(-0.0018453229255750575, 0.0022208938718740537, -0.002687…` | JSON pt_im_bias_token2_results.json |
| bias_mean | measured | A+ | act2_pillar1 | `-0.00011882903909564077` | JSON pt_im_bias_token2_results.json |
| bias_std | measured | A+ | act2_pillar1 | `0.0018895941511433932` | JSON pt_im_bias_token2_results.json |
| bias_max_abs | measured | A+ | act2_pillar1 | `0.0026877576040748585` | JSON pt_im_bias_token2_results.json |
| bias_job_ids | doc-frozen | — | act2_pillar1 | `('d8pbl2201fac73d1gdag', 'd8pbl2eab0ds73dos8a0', 'd8pbl2m…` | JSON pt_im_bias_token2_results.json |
| vqd_e0 | measured | A | act4_qpu_timeline | `2.1398203106629032` | JSON pt_vqe_vqd_results.json |
| vqd_bias | measured | A | act4_qpu_timeline | `-0.011922308405310833` | JSON pt_vqe_vqd_results.json |
| vqd_job | doc-frozen | — | act4_qpu_timeline | `'d9fidihhtsac739fg3n0'` | JSON pt_vqe_vqd_results.json |
| fez_phi | measured | A− | act4_qpu_timeline | `0.625244140625` | JSON pt_ququint_fez_results.json |
| fez_sep | measured | A− | act4_qpu_timeline | `0.16611328125` | JSON pt_ququint_fez_results.json |
| fez_job | doc-frozen | — | act4_qpu_timeline | `'dakjk9hhvn6c73cvr1cg'` | JSON pt_ququint_fez_results.json |
| fez_bands_hold | measured | A− | act4_qpu_timeline | `{'phi_margin': True, 'sep_margin': True, 'confound_max_di…` | JSON pt_ququint_fez_results.json |
| kingston_bias | measured | A− | act4_qpu_timeline | `0.007403730279381016` | JSON pt_v5_kingston_results.json |
| kingston_bands | measured | A− | act4_qpu_timeline | `True` | JSON pt_v5_kingston_results.json |
| kingston_job | doc-frozen | — | act4_qpu_timeline | `'daqaeteekp0c73aqetdg'` | JSON pt_v5_kingston_results.json |
| kingston_md5 | doc-frozen | — | act4_qpu_timeline | `'d019d587c0d8ca28cfa0559057d590c8'` | JSON pt_v5_kingston_results.json |
| margin_curve | measured | A− | act5_kappa | `((0.0, 0.7271340355472928), (0.0001, 0.6773878666169415),…` | JSON pt_crossover_v4_results.json |
| margin_primary | measured | A− | act5_kappa | `0.5840264877973111` | JSON pt_crossover_v4_results.json |
| margin_sign_interval | measured | A− | act5_kappa | `(0.003, 0.01)` | JSON pt_crossover_v4_results.json |
| kappa_star | measured | A− | act5_kappa | `62.26124150876291` | JSON pt_crossover_v4_results.json |
| kappa_bracket | measured | A− | act5_kappa | `(62.09289060367421, 62.43004885946025)` | JSON pt_crossover_v4_results.json |
| kappa_per_p1 | measured | A− | act5_kappa | `((0.0001, 85.23579048290256), (0.0003, 62.26124150876291)…` | JSON pt_crossover_v4_results.json |
| kappa_rough | doc-frozen | — | act5_kappa | `62.31` | doc RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md:1326 |
| crossover_md5 | doc-frozen | — | act5_kappa | `'7abb5e60100bd666e8bf93730e33f458'` | JSON pt_crossover_v4_results.json |
| crossover_verdict | measured | A− | act5_kappa | `'H-STAR-4_CONFIRMED_CROSSOVER'` | JSON pt_crossover_v4_results.json |
| ram_gated | measured | B+ | act6_ramanujan | `((401, 0.029448101265823555), (463, 0.03271111111111206),…` | JSON pt_ramanujan_results.json |
| ram_overlap_limit | measured | B+ | act6_ramanujan | `0.02218126582278481` | JSON pt_ramanujan_results.json |
| ram_verdict | measured | B+ | act6_ramanujan | `'H-RAM-2_REPLICATED_FINGERPRINT'` | JSON pt_ramanujan_results.json |
| ram_md5 | doc-frozen | — | act6_ramanujan | `'a2fc4875e10dd198e95d4996b1692759'` | JSON pt_ramanujan_results.json |
| hshor_verdict | measured | B | act7_qpe_peaks, act8_fermat_grid, act10_verdict_ladder | `'CONFIRMED'` | live pt_hshor1.run_evaluation() |
| hshor_o1 | measured | B | act8_fermat_grid | `{'7': 0.0, '9': 0.8, '11': 0.0, '13': 0.0, '15': 0.571428…` | live pt_hshor1.run_evaluation() |
| hshor_prime_rate_max | measured | B | act8_fermat_grid | `0.0` | live pt_hshor1.run_evaluation() |
| hshor_comp_rate_min | measured | B | act8_fermat_grid | `0.5714285714285714` | live pt_hshor1.run_evaluation() |
| hshor_bridge_min | measured | B | act7_qpe_peaks | `1.0` | live pt_hshor1.run_evaluation() |
| hshor_crt_dev | measured | B | act8_fermat_grid | `0.0` | live pt_hshor1.run_evaluation() |
| hshor_trace_dev | measured | B | act8_fermat_grid | `0.0` | live pt_hshor1.run_evaluation() |
| hshor_shuffle_p | measured | B | act8_fermat_grid | `0.0` | live pt_hshor1.run_evaluation() |
| hshor_561_order | measured | B | act8_fermat_grid, act9_failure_board | `80` | live pt_hshor1.run_evaluation() |
| hshor_shor | measured | B | act8_fermat_grid | `{'15': (3, 5), '21': (3, 7)}` | live pt_hshor1.run_evaluation() |
| hshor_md5 | doc-frozen | — | act7_qpe_peaks, act8_fermat_grid | `'73bc664ae3475a79a692cd7735b2b387'` | live pt_hshor1.run_evaluation() |
| korselt_561 | measured | B | act8_fermat_grid | `True` | live pt_hshor1.korselt_criterion_check() |
| im_band | doc-frozen | — | act2_pillar1 | `0.005` | JSON pt_im_bias_prereg.json |
| ququint_bound | doc-frozen | — | act4_qpu_timeline | `0.2` | JSON pt_crossover_v4_results.json |
| ram_band | doc-frozen | — | act6_ramanujan | `(0.8, 1.25)` | JSON pt_ramanujan_prereg.json |
| ram_gate_pi | doc-frozen | — | act6_ramanujan | `79` | JSON pt_ramanujan_prereg.json |
| ram_model | doc-frozen | — | act6_ramanujan | `((401, 0.027726582278481012), (463, 0.03211111111111111),…` | JSON pt_ramanujan_results.json |
| qpe_15 | measured | B | act7_qpe_peaks | `{'Q': 625, 'XD': 25, 'r': 4, 'N': 15, 'a': 7, 'peak_ks': …` | live pt_shor_ququint.qpe_order() |
| leakage_r0 | doc-frozen | C | act9_failure_board | `'0.3553'` | doc RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md:1326 |
| chi2_v1 | doc-frozen | C | act9_failure_board | `'1311'` | doc RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md:1326 |
| v3_rmean | doc-frozen | C | act9_failure_board | `'0.2059'` | doc RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md:1326 |
| gue_correction | doc-frozen | C | act9_failure_board | `'0.5996'` | doc RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md:1326 |
| vector_ladder | doc-frozen | — | act10_verdict_ladder | `'10.19 Strategic Vectors'` | doc RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md:1350 |
| hstar5_score | doc-frozen | — | act10_verdict_ladder | `'Score 7/10'` | doc RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md:1375 |
| hstar5_md5 | doc-frozen | — | act10_verdict_ladder | `'837dae2c'` | doc RIEMANN_HYPOTHESIS_AND_NUCLEAR_STRUCTURE.md:1408 |
| date_fez_singleshot | doc-frozen | — | act4_qpu_timeline | `'2026-06-10'` | doc README.md:64 |
| date_vqd | doc-frozen | — | act4_qpu_timeline | `'2026-07-21'` | doc README.md:64 |
| date_fez_phi | doc-frozen | — | act4_qpu_timeline | `'2026-09-15'` | doc README.md:61 |
| date_kingston | doc-frozen | — | act4_qpu_timeline | `'2026-09-24'` | doc README.md:62 |
| test_count | measured | — | act1_title, act10_verdict_ladder | `671` | live test collection |

## Criteria shown before results (explanation_scaffold)

- **alpha_1e6** — Latorre–Sierra predicts α → 1; frozen band excludes α ≥ 1
- **bias_points** — frozen: all |bias| < 0.005 (pt_im_bias_prereg.json, H_Im_h1)
- **vqd_e0** — frozen: |bias_PT_re| < 0.05 → H1/H3 confirmed
- **fez_phi** — frozen: phi margin > 0, sep margin < 0, confound ≤ 0.05 (md5 18fb1e62)
- **kingston_bias** — frozen: bias < 0.05, all observables inside bands (md5 d019d587)
- **margin_curve** — margin = measured V minus the frozen 1/5 bound, per noise level p1
- **kappa_star** — frozen: κ* ≥ 10 → CONFIRMED (md5 7abb5e60…)
- **ram_gated** — frozen: 5/5 gated points in band, no control overlap (md5 a2fc4875)
- **hshor_verdict** — frozen: composite rate > 0.05, prime rate = 0 (md5 73bc664a)
- **hshor_bridge_min** — frozen: bridge match = 1.0 (md5 73bc664a)

## Glosses (audience_calibration, ≤ 12 words)

- **alpha_1e6** — α = entropy growth per factor of ten in N
- **bias_points** — VQE = a quantum routine tuning a circuit toward lowest energy
- **vqd_e0** — VQD = VQE plus the second-lowest energy level
- **fez_phi** — phi V = how strongly prime positions carry the signal
- **margin_curve** — margin = how far the measured value stays above the frozen bound
- **kappa_star** — κ* = noise strength where the quantum advantage margin closes
- **ram_gated** — mod-5 fingerprint = a residue pattern that only primes show
- **hshor_verdict** — Carmichael numbers: rare composites that pass every Fermat test
- **hshor_bridge_min** — QPE reads a frequency; here the frequency is the cycle length
- **hshor_crt_dev** — CRT = split a number into coprime parts, exactly
- **hshor_561_order** — Korselt: the theorem that names the Carmichael exceptions
- **ram_gate_pi** — π(P) = how many primes sit below P
