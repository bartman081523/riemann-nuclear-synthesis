# MANIFEST — tmp_recovered_1e27c8b2

**Provenienz:** User-Direktive 2026-10-03: "rekonstruiere die dateien mit mcp, und ab jetzt nicht mehr in /tmp arbeiten, scratches in scratches ordner im.workdir. bitte global merken."

Spiegel des Arbeitsverzeichnisses der Session 1e27c8b2
(`/home/julian/.claude/jobs/1e27c8b2/tmp/`), 104 Dateien, 992 K, `cp -a`
(Kopie ≠ Move: Tmp-Verzeichnis bleibt unangetastet, der Fez-046-Resume-Vertrag
liest dort weiter bis zur Ablösung). Ab jetzt gilt: KEINE neuen Scratch-/Ops-/
Log-Artefakte in Job-Tmp — alles nach `scratches/` im Workdir.

**MCP-Rekonstruktionsbeweis:** `fez046_service_ops.py` wurde zusätzlich NICHT
von Disk, sondern aus der Claude-History-MCP-Transkript-Indexierung rekonstruiert
(`get_file_history` der Session 1e27c8b2, 18 Patches; Patch-Index 467 =
2026-09-30T06:35:05Z = 08:35:05 Lokalzeit = die Disk-Mtime; 3718 Zeichen ≈
3724 B, Differenz = 3 Umlaute × 2 B im UTF-8) und gegen die Disk-Version
md5-verifiziert — beide `0849daa2ace1cf1d74015d9b6061bbe8`, Byte-EXAKT.
Damit ist für den ganzen Korpus belegt: Selbst wenn `jobs/1e27c8b2/tmp`
evakuiert, ist jede Datei hier über die Transkript-Historie wiederherstellbar.

**Namensdoppel (gleiches md5, bewusst beibehalten):**
- `deck_4edd1a35_pre_rename.md` = `deck_head.md` = `hyp_head.md` =
  `423b909069b5f709057e604dbb5e5f3a` (39519 B — die bekannte Pre-Rename-Deck-Kopie)
- `write2_konfund.py.txt` = `scratch_test2_smoke.py` (3ae7de1760b701b056872de13cb4e68d)
- `freeze_state.py` = `runner_049_prefix.py` (f482b110c684ac83d53d6dab86c947ac)

| Datei | md5 |
|---|---|
| blas_dust_partial.py | 7a0dfa437c7504580b4bfd80c8bdbc04 |
| book_k2_jobs.py | 3453ccc5943eeb51da55ebfdc6f6b4ee |
| brute2.py | e51ad7a5f432b112aa2362c41d32c955 |
| brute_partial.py | 77e5855609d03fe757687d7a06cef213 |
| commit_msg_12e.txt | f3a7701a58475bc9b5b9888a76d785a1 |
| commit_msg_12f.txt | e3c2f9e2f6d0996a326fb367946c1f60 |
| commit_msg_h9a3_nsweep.txt | 03b42c8ca2ecb6cae4f627216cc14089 |
| commit_msg_h9a_testa.txt | 0d1e1f11f3b9638439b3c17f0c9d5861 |
| commit_msg_h9b_n5atom.txt | b9c2e7a167600864001d83c710e1d905 |
| commit_msg_h9.txt | 515e0063934da0818535a565d24e857f |
| deck_4edd1a35_pre_rename.md | 423b909069b5f709057e604dbb5e5f3a |
| deck_apply.py | 9d2c7fb7734a6c84b1a3ceaa24d4315b |
| deck_head.md | 423b909069b5f709057e604dbb5e5f3a |
| derive_run4.py | a52aa0bfb2c7f05b613e58b0e896013c |
| design_dump_d1_kingston.md | 8a3b220e32dc5e257bce80cd11d5bf26 |
| dump_k2_prereg.py | fc20d0a1b354693ed853a4dab47f31a1 |
| dump_k2_train2.py | 35cdb47091d085288dd07fc3f718cade |
| dump_k2_train.py | e617d1e193961b99ed5fea47ea11c125 |
| fez046_old_isa.json | 64c00f0a744f11ed9f090de7d954b166 |
| fez046_old_jobid_dat3q9dvr3kc73ektkv0.txt | 8e80c913b7ca3a9c91fd374ff36af1c8 |
| fez046_service_dump.json | e0bba292102e64ee29f838538be2c2d9 |
| fez046_service_ops.py | 0849daa2ace1cf1d74015d9b6061bbe8 |
| fid_report.md | b84169f7f3892da0cc949cf0f9ece5d3 |
| fingerprint.py | 2643480ff96955a0eba01103f9c6623e |
| freeze_state.py | f482b110c684ac83d53d6dab86c947ac |
| ftab.json | 37a6697f0728f4db48b205e1da5262f4 |
| gen_049b.py | 70704b53925d321ca428d09bd385e926 |
| git_index_backup_pre_reset.bin | 2c4b731c4c5400ffc77ee37a080a6cdc |
| h9_atom_n5.json | c46542029109257cd76641ad063f45ab |
| h9_atom_n5.jsonl | c346dc1e26260644f1bdce6627a7bb60 |
| h9_atom_n5_run.log | 739d6eb3ba91610702e093445974e119 |
| h9_atom_n5_smoke.jsonl | dd6e893a881f9cbf7d1893bbcbdb8bbf |
| h9_nsweep_1e7.log | 9a0dd72f38108bc95e8b8f4071b7e823 |
| h9_nsweep_1e7_out_erstlauf_crash.json | 02f514e943d054ff944340e008047528 |
| h9_nsweep_1e7_out.json | de8174ddacb19d7626a15ad64ba5786e |
| h9_nsweep_1e7.py | 260b67c4d64cc23c4c654a3f12de4404 |
| h9_nsweep_1e7_resume.log | a380502fe513da3b1c281dcb78329565 |
| h9_s4_unified.json | ec61a01fcb235bafde246c15fee33b55 |
| h9_s4_unified.jsonl | e264039470ea9f2a71dd85c405c0b465 |
| h9_s4_unified_run.log | d1385402073bfadeaa213ecdab06b0b6 |
| hyp.diff | 65f344180604ef4aedd78193ff12f7dd |
| hyp_head.md | 423b909069b5f709057e604dbb5e5f3a |
| msg_048b_freeze.txt | 0c1692b547419b590d9bdc0469088eb8 |
| msg_048b_results.txt | db2372dfe98e0c8e170eef0cf2b0992a |
| msg049b.txt | d49b8d9b5aaaabb3162a935831af660f |
| msg_049_freeze.txt | b5a9d412b63ad12197d078cb36d49fbf |
| msg_049_results.txt | dee9742dfe56240f4aac23d5a94c6675 |
| msg4.txt | 3a76215705d695dec448617ba11071c5 |
| msg7.txt | 554a26f6328ebb28a5ea8aac846e2de8 |
| msg_doku_1032.txt | a4ea30e51267540244656bb2a46173fb |
| plan_head_137.txt | a6d28bd31c94adcf542b0fc095c90d9c |
| plan_ramq.txt | 783446e99e9daa7a441c290e6f78133a |
| plan_wt_137.txt | 92338089ad14495904eeb7eceb39e82b |
| probe_eig_n5.py | 90add4bb4f2737b2694bb9e143554f59 |
| probe_orbit_n5.py | 8367e0c6b711b048cfd0e2b628d138e5 |
| probe_quota.py | 9c5fb001fc46ff973f019659af25e8b0 |
| probe_relabel_pair_n5.log | 406afc446ce00512cf24f8e2ed3bea38 |
| probe_relabel_pair_n5.py | 0c6d6f806e2bf25f8a4ea729d2f12baf |
| probe_rmedian_n5.log | 35dae073c8d7de378e357f445d2b0f15 |
| probe_rmedian_n5.py | 203df197aa08ea72b32fa0d9bf47db71 |
| probe_th_prime_n5.log | d3ceaf61f7e394c6b6f90cea50a1b487 |
| probe_th_prime_n5.py | d1ec0e6db0af94ce1917dd1d10b6c295 |
| pt_test1_gap_invariance_prereg.json | de77b33c21077949c6202c1b7e6994e5 |
| pt_test1_gap_invariance.py | d1f0930d1ce194119f459802bbf72efa |
| pt_test1_gap_invariance_results.json | 1f473ca55fb9c472296e80e9ac42f964 |
| raw_committed_245f115.json | 509c6db6b5d8fbb437bdf55fe64ac549 |
| regen_gate_k2_v2.py | af5a094cb20ae6dd2c37a8e65983da1e |
| rep_gate2.log | d46dd822dccc5d828878d4717e77dd5f |
| rep_gate3.log | 38349771c324a9dba10e0dc046a2da5c |
| rep_submit2.log | dcb64d159478ad2afcb2e650c8b523f7 |
| results_before_fix.json | f8713b7edca88977292086ad85bb9ff5 |
| runner_049_prefix.py | f482b110c684ac83d53d6dab86c947ac |
| run_proof.py | 883a0c2eb5bca440d470e8faea6c06c6 |
| s4_diag_run.log | e38aab2cc0a3308c5e8b4ddc53d431be |
| s4_r2_recompute.run.log | 3e866db4e7603213a5ce622b60e15530 |
| s4_run2.log | 3f1a52314b08d2427b1941ecb1688850 |
| s4_run.log | aa312374b2011b10241e3669f027f5eb |
| s4_t5_probe_b2.py | 1af9321077174e0220d2c4790f868c6d |
| s4_t5_probe_b.py | eb684dc03da8639e9bc8a4d4e26a2be5 |
| s4_t5_probe.py | 28e56086d6cc7a466c346085884a0cff |
| scratches_subtree_input.txt | 555ae4c807da92dec5a592b86c11f789 |
| scratch_test1_diag_norm.py | 3bb5a1d133c5bee34eed31a86200bd77 |
| scratch_test2_conv2.py | 9bfe6991b06c55c0dbb3ff78278d8dfd |
| scratch_test2_conv3.py | 6d4bebef07cc8e41f5c4d3e16f7f591b |
| scratch_test2_conv.py | 1f48e0f42f2afb38e856ce7925037113 |
| scratch_test2_smoke.py | 3ae7de1760b701b056872de13cb4e68d |
| scratch_v3b_probe.py | 0522b6697f890c39000fdae64fdce0c1 |
| suite_final.txt | 66855ce934f4ebd4a9d87dc07a708001 |
| suite_run2.log | a5bf1d3de7c3e9382d5301a39be69fe0 |
| suite_run.log | c8ab912be258d4336b483d2924b94a73 |
| test1_freeze_msg.txt | b6c13e30f1cb340058cea27363031a3c |
| test1_prereg_draft.json | e315e9d8e84b9cdec69f2898d58569f6 |
| test1_results_msg.txt | df0e5dae8c1e56bb0cd7bd4ae0c95410 |
| toplevel_input_new.txt | 39d15cd85855c7d3a4b4da21852359b1 |
| toplevel_input_raw.txt | e533098c0bd893819745de3cb7bb8c5e |
| train_pool.json | 53d640d37985d07d82a4c6e70226f534 |
| train_pool.py | c83db00945058dd7498b83b971684ebe |
| v5r_fez_submit2.log | 48ddfdd5de4f27960b1fc071ec37e873 |
| v5r_fez_submit.log | d96dbc7bc3fd59612f0f79f569e65134 |
| v6r_fez_status.py | 91b3bdbac85c860deb89948b0e837d9d |
| witness_check2.py | b71c1ec71daea57e1d54875eec966a53 |
| witness_check3.py | 30294c1c719eb56ed7b3d0382870ac62 |
| witness_check.py | dfa4e6719a8e546ce4ac682380cbf035 |
| write2_konfund.py.txt | 3ae7de1760b701b056872de13cb4e68d |