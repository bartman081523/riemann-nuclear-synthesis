"""
EXPERIMENT 025 — QPU Job-ID Inventory Retroactive Fetch.

Systematic retroactive fetch of all QPU job IDs documented anywhere in
the repo (results JSONs, job-id JSONs, run-logs, cron logs, MD docs)
that have not yet been downloaded into a `_results.json` file.

Rationale (SYNTHESIS_2026_06_10.md §V, 2026-07-21):
  - On 2026-07-21, after the 1.7.2026 quota reset, 18 historical QPU
    job results were successfully fetched that had previously only been
    referenced in logs/docs.
  - This script makes that process reproducible for any future
    repository state.

Method:
  1. Scan all pt_*_results.json + pt_*_job_ids.json + *.log files for
     20-char IBM Qiskit job IDs (pattern: d + 19 alphanumerics).
  2. Filter out MD5-hash false positives (heuristic: body context
     contains "md5="/md5-markers or path/error markers, OR the 20-char
     match is followed by >= 6 hex digits — a fragment of a longer hash,
     since real job IDs are exactly 20 characters).
  3. Cross-reference: which IDs are NOT in any _results.json (= not
     yet downloaded)?
  4. For each not-yet-downloaded ID, probe IBM Quantum (TOKEN1 first,
     then TOKEN2 fallback) for status + result.
  5. Save all fetched results to pt_downloaded_job_results.json
     (merged with any existing file).

Constitutional principle: results-in, secrets-out. Tokens are read
from .env but NEVER written to any output file.

Usage:
  python3 pt_qpu_job_inventory_retroactive.py            # dry-run (scan + list only)
  python3 pt_qpu_job_inventory_retroactive.py --fetch     # probe IBM Quantum + save
"""
import argparse
import json
import os
import re
import sys
import warnings
from collections import defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).parent.resolve()
JOB_ID_PATTERN = re.compile(r'd[0-9a-z]{19}')


def scan_job_ids_in_files():
    """Scan all pt_*.json + *.log files for 20-char IBM Qiskit job IDs.

    Returns: dict mapping job_id -> list of (source_file, context).
    """
    records = defaultdict(list)

    # JSON files (results + job_ids)
    for pattern in ["pt_*_results.json", "pt_*_job_ids.json"]:
        for path in sorted(ROOT.glob(pattern)):
            if not path.is_file():
                continue
            try:
                with open(path) as f:
                    text = f.read()
            except Exception:
                continue
            for m in JOB_ID_PATTERN.finditer(text):
                jid = m.group(0)
                if len(jid) == 20:
                    # Take a short context window
                    ctx = text[max(0, m.start() - 30):m.end() + 30]
                    records[jid].append((path.name, ctx[:80]))

    # Log files (run + cron)
    for path in sorted(ROOT.glob("pt_*_run.log")):
        try:
            text = path.read_text()
        except Exception:
            continue
        for m in JOB_ID_PATTERN.finditer(text):
            jid = m.group(0)
            if len(jid) == 20:
                ctx = ""
                for line in text.split("\n"):
                    if jid in line:
                        ctx = line[:120]
                        break
                records[jid].append((path.name, ctx))

    return records


def filter_false_positives(records):
    """Filter out MD5-hash fragments and path/error-context false positives.

    Heuristic: an ID is a false positive if ALL its context strings carry
    an md5/path marker OR embed the ID in a longer hex string — a real IBM
    Qiskit job ID is EXACTLY 20 characters, so a match inside a longer hex
    run is a fragment of a longer hash (e.g. a 32-char counts_md5 whose
    context line says "raw fetched: d19f..." without any "md5=" marker).

    REGRESSION EXPERIMENT 042 (Fez-Raw): Fragment "d19f4a563d88e0cf3ffd"
    des counts_md5 d19f4a563d88e0cf3ffd4b187a10ca73 — Hex-Fortsetzung
    >= 6 Zeichen hinter dem Match.
    AMENDMENT (EXPERIMENT 043, Fez-Raw 2): Fragment "d02f81cf623862b4910c"
    des counts_md5 16ca44bd02f81cf623862b4910ccedf8 (Match beginnt INNEN
    im Hash, am 'd' von "16ca44bd") hat nur 5 Zeichen Fortsetzung
    ("cedf8") — die 6er-Regel greift nicht.  Verallgemeinerung: das Match
    liegt in einem maximalen Hex-Run der Laenge >= 21 (echte 20-Zeichen-
    Job-IDs sind alleine im Run; auch ein all-hex echter Job-ID in Quotes
    ist ein Run von GENAU 20).
    """
    real = {}
    fake = {}
    for jid, sources in records.items():
        marker = ("md5=", "md5:", "counts_md5", ".local/lib",
                  "site-packages", "QiskitRuntime")
        cont = re.compile(re.escape(jid) + r"[0-9a-f]{6}")
        hexrun = re.compile(r"[0-9a-f]{21,}")
        all_md5_or_path = all(
            (any(m in ctx for m in marker)
             or cont.search(ctx) is not None
             or any(jid in run.group(0) for run in hexrun.finditer(ctx)))
            for _, ctx in sources
        )
        if all_md5_or_path:
            fake[jid] = sources
        else:
            real[jid] = sources
    return real, fake


def find_downloaded_ids():
    """Find job IDs already present in any _results.json file."""
    downloaded = set()
    for path in sorted(ROOT.glob("pt_*_results.json")):
        try:
            with open(path) as f:
                text = f.read()
        except Exception:
            continue
        for m in JOB_ID_PATTERN.finditer(text):
            jid = m.group(0)
            if len(jid) == 20:
                downloaded.add(jid)
    return downloaded


def load_tokens():
    """Load IBM Quantum tokens from .env."""
    tokens = {}
    env_path = ROOT / ".env"
    if not env_path.exists():
        raise RuntimeError(f".env not found at {env_path}")
    with open(env_path) as f:
        for line in f:
            if line.startswith("IBMQ_TOKEN="):
                tokens["IBMQ_TOKEN"] = line.split("=", 1)[1].strip()
            elif line.startswith("IBMQ_TOKEN2="):
                tokens["IBMQ_TOKEN2"] = line.split("=", 1)[1].strip()
    return tokens


def probe_and_fetch(job_ids, tokens):
    """Probe IBM Quantum for each job ID, fetch results where DONE.

    Returns: dict mapping job_id -> {status, account, backend,
    creation_date, data, error}.
    """
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError:
        print("ERROR: qiskit_ibm_runtime not installed", file=sys.stderr)
        return {}

    services = {}
    for name, tok in tokens.items():
        try:
            services[name] = QiskitRuntimeService(
                channel="ibm_quantum_platform", token=tok
            )
        except Exception as e:
            print(f"  Service {name} init failed: {e}", file=sys.stderr)

    results = {}
    for jid in job_ids:
        found = False
        for account, svc in services.items():
            try:
                job = svc.job(jid)
                status = str(job.status())
                data = {}
                try:
                    result = job.result()
                    if hasattr(result, '__len__') and len(result) > 0:
                        d = result[0].data
                        if hasattr(d, 'evs'):
                            data['evs'] = float(d.evs)
                        if hasattr(d, 'stds'):
                            data['stds'] = float(d.stds)
                    results[jid] = {
                        "status": status,
                        "account": account,
                        "backend": str(job.backend().name) if hasattr(job, 'backend') else "?",
                        "creation_date": str(job.creation_date),
                        "data": data,
                    }
                except Exception as e:
                    results[jid] = {
                        "status": status,
                        "account": account,
                        "backend": str(job.backend().name) if hasattr(job, 'backend') else "?",
                        "error": str(e)[:120],
                    }
                found = True
                break
            except Exception:
                continue
        if not found:
            results[jid] = {
                "status": "NOT_FOUND",
                "account": None,
                "error": "Not found on any configured token account",
            }
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true",
                        help="Probe IBM Quantum and fetch results")
    args = parser.parse_args()

    print("=== Step 1: Scan all repo files for QPU job IDs ===")
    records = scan_job_ids_in_files()
    print(f"  Found {len(records)} unique 20-char IDs (incl. false positives)")

    print("\n=== Step 2: Filter false positives ===")
    real, fake = filter_false_positives(records)
    print(f"  Real IBM job IDs: {len(real)}")
    print(f"  Filtered false positives: {len(fake)}")

    print("\n=== Step 3: Cross-reference with already-downloaded ===")
    downloaded = find_downloaded_ids()
    missing = {jid: srcs for jid, srcs in real.items() if jid not in downloaded}
    print(f"  Already downloaded (in _results.json): {len(downloaded)}")
    print(f"  Referenced but NOT yet downloaded: {len(missing)}")

    print("\n=== Missing job IDs (candidates for retroactive fetch) ===")
    for jid in sorted(missing):
        sources = missing[jid]
        print(f"  {jid}")
        for sf, ctx in sources[:2]:
            print(f"    src: {sf} | {ctx[:60]}")

    if not args.fetch:
        print("\n(dry-run — pass --fetch to probe IBM Quantum and download)")
        return

    print("\n=== Step 4: Probe IBM Quantum + fetch ===")
    tokens = load_tokens()
    fetch_results = probe_and_fetch(sorted(missing), tokens)

    # Merge with any existing downloaded results
    out_path = ROOT / "pt_downloaded_job_results.json"
    existing = {"results": {"IBMQ_TOKEN": [], "IBMQ_TOKEN2": []}}
    if out_path.exists():
        try:
            with open(out_path) as f:
                existing = json.load(f)
        except Exception:
            pass

    # Build a flat map of already-saved results
    already_saved = {}
    for acc, recs in existing.get("results", {}).items():
        for r in recs:
            already_saved[r.get("job_id")] = r

    # Add new fetches
    for jid, info in fetch_results.items():
        if info.get("status") == "DONE" and jid not in already_saved:
            existing["results"].setdefault(info["account"], []).append({
                "job_id": jid,
                "status": info["status"],
                "backend": info.get("backend", "?"),
                "creation_date": info.get("creation_date", "?"),
                "data": info.get("data", {}),
            })

    with open(out_path, "w") as f:
        json.dump(existing, f, indent=2, default=str)
    print(f"\nSaved merged results to {out_path}")

    # Summary
    done = sum(1 for r in fetch_results.values() if r.get("status") == "DONE")
    cancelled = sum(1 for r in fetch_results.values() if r.get("status") == "CANCELLED")
    not_found = sum(1 for r in fetch_results.values() if r.get("status") == "NOT_FOUND")
    print(f"\n=== Summary ===")
    print(f"  DONE (fetchable): {done}")
    print(f"  CANCELLED: {cancelled}")
    print(f"  NOT_FOUND: {not_found}")


if __name__ == "__main__":
    main()