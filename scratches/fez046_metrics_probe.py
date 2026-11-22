# -*- coding: utf-8 -*-
"""fez046_metrics_probe.py — ORIGIN-Identifikation der zwei Fez-QUEUED-Jobs.

Fortschreibung von fez046_queue_probe.py: das metrics()-Dict enthaelt
'caller'/'timestamps'/'usage' — das identifiziert, WER/ORIGIN-Programm den
Orphan-Job daua5hahcrkc73dv9eh0 (Sampler, created 2026-09-30 07:48) eingereicht
hat, im Vergleich zum eigenen 046-Repeat-Job dauassrojkfs738rrcsg (estimator,
08:38). READ_ONLY: keine Mutation, kein cancel, kein Token-Print.
"""
import json
import sys

sys.path.insert(0, "/run/media/julian/ML4/riemann")

import pt_v5_kingston_rep as rep  # noqa: E402

IDS = ["dauassrojkfs738rrcsg", "daua5hahcrkc73dv9eh0"]

SECRET_HINTS = ("token", "api", "credential", "ibmq_token")


def scrub(obj):
    """JSON-sicher + ohne moegliche Geheimnisse (key-geloescht)."""
    if isinstance(obj, dict):
        return {str(k): scrub(v) for k, v in obj.items()
                if not any(h in str(k).lower() for h in SECRET_HINTS)}
    if isinstance(obj, (list, tuple)):
        return [scrub(v) for v in obj]
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def main():
    svc = rep.make_service_for("fez")
    for jid in IDS:
        job = svc.job(jid)
        print("===", jid, str(job.status()), "===")
        try:
            m = scrub(job.metrics())
            print(json.dumps(m, indent=1, default=str, ensure_ascii=True))
        except Exception as exc:  # noqa: BLE001
            print("metrics_error:", type(exc).__name__, exc)


if __name__ == "__main__":
    main()