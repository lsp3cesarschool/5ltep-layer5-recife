"""5L-TEP Layer 5: read the public summaries of Layers 1-4, assess every dataset and write the outputs.

Usage:
  python main.py                         # read the layers on GitHub, write docs/data and results/ here
  python main.py --out build             # write into build/ (the workflow publishes it after checks)
  python main.py --fixtures tests/fixtures --now 2026-10-09T18:00:00Z   # offline, from local copies
  python main.py --siblings ../..        # local trial: ../../5ltep-layerN/public as the IBAMA layers

Only standard library. Numbers for the thesis come from the GitHub Actions runs, never from local trials.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from src import VERSION
from src.adapters import read_layer
from src.assess import assess_dataset, combinations, digest_analysis, simultaneous_groups
from src.config import CONTENT_LAYERS, LAYERS, Instance
from src.fetch import Fetcher
from src.inference import infer
from src.provenance import build as build_provenance
from src.report import NOTICE, badges, ficha, findings, write_json
from src.timeutil import iso, parse, utcnow

ROOT = Path(__file__).resolve().parent
HISTORY_LIMIT = 1000


def layer_meta(rep, policy, now) -> dict:
    age = (now - parse(rep.generated_at)).total_seconds() / 86400 if rep.generated_at else None
    return {
        "layer": rep.layer, "status": rep.status, "reason": rep.reason, "detail": rep.detail,
        "generated_at": rep.generated_at, "age_days": round(age, 2) if age is not None else None,
        "validity_days": policy.validity_days(rep.layer),
        "expired": age is not None and age > policy.validity_days(rep.layer),
        "repository": rep.repository, "dashboard": rep.dashboard, "workflow": rep.workflow,
        "files": rep.files, "portal": rep.portal,
    }


def run(root: Path, out: Path, now, fetcher: Fetcher) -> dict:
    inst = Instance.load(root)
    policy = inst.policy
    reports = {layer: read_layer(layer, fetcher, inst, now) for layer in LAYERS}
    l4_ok = reports["L4"].status == "ok"
    if l4_ok:
        universe = reports["L4"].extra["universe"]
    else:  # without Layer 4 the universe is what the other layers reached
        universe = {name: {"events": []} for layer in CONTENT_LAYERS for name in reports[layer].datasets}

    state_file = root / "results" / "state.json"
    previous = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}
    digests = digest_analysis(reports, universe, previous.get("digests"), l4_ok)
    datasets = [assess_dataset(name, reports, universe, digests, policy, now) for name in sorted(universe)]
    groups = simultaneous_groups(reports, policy, now)

    if l4_ok:
        removed = reports["L4"].extra["cross_check"].get("removed", [])
        inf = infer(previous, datasets, digests["latest"], removed, now)
    else:  # the universe is unknown: keep the previous state untouched
        inf = {"state": previous, "observed": [], "lost": {},
               "summary": {"paused": "layer4_unavailable", "rounds_observed": previous.get("rounds", 0)}}

    run_meta = {"generated_at": iso(now), "repository": inst.repository, "version": VERSION,
                "commit": os.environ.get("GITHUB_SHA"), "run_id": os.environ.get("GITHUB_RUN_ID")}
    layers_meta = {layer: layer_meta(reports[layer], policy, now) for layer in LAYERS}
    policy_dict = policy.as_dict()

    totals = {"datasets": len(datasets),
              "complete": sum(1 for d in datasets if d["qs"]["kind"] == "complete"),
              "partial": sum(1 for d in datasets if d["qs"]["kind"] == "partial"),
              "no_content": sum(1 for d in datasets if d["qs"]["kind"] == "none"),
              "eligible": sum(1 for d in datasets if d["qs"].get("eligible")),
              "bands": {}}
    for d in datasets:
        key = f"{d['qs']['kind']}:{d['qs'].get('band')}"
        totals["bands"][key] = totals["bands"].get(key, 0) + 1
    coverage = {layer: {"reached": sum(1 for d in datasets if d["layers"][layer]["rate"] is not None),
                        "valid": sum(1 for d in datasets if d["layers"][layer]["status"] == "valid")}
                for layer in LAYERS}

    previous_round = parse(previous.get("round")) if previous.get("round") else None
    integrity_open = sum(1 for d in datasets if any(i["unresolved"] for i in d["qs"]["integrity"]))
    new_integrity = [{"dataset": d["name"], **i} for d in datasets for i in d["qs"]["integrity"]
                     if previous_round is None or parse(i["when"]) > previous_round]
    alerts = {"new_integrity_events": new_integrity,
              "unavailable_layers": [{"layer": l, "status": m["status"], "reason": m["reason"], "detail": m["detail"]}
                                     for l, m in layers_meta.items() if m["status"] in ("rejected", "error")],
              "integrity_open": integrity_open}

    state_ds = inf["state"].get("datasets", {})
    compact, fichas = [], {}
    for d in datasets:
        items = findings(d, inf["lost"].get(d["name"]), groups, policy, now)
        outcomes = {"open": [{"key": k, **v} for k, v in state_ds.get(d["name"], {}).get("signals", {}).items()],
                    "closed": [o for o in inf["state"].get("outcomes", []) if o.get("dataset") == d["name"]]}
        fichas[d["name"]] = ficha(d, items, outcomes, run_meta, layers_meta, policy_dict, inst.portal)
        compact.append({
            "name": d["name"], "title": d["title"], "resources": d["resources"], "last_change": d["last_change"],
            "layers": {l: {"status": d["layers"][l]["status"], "rate": d["layers"][l]["rate"],
                           "reason": d["layers"][l]["reason"], "evaluated_at": d["layers"][l]["evaluated_at"],
                           "current": d["layers"][l]["current"]} for l in LAYERS},
            "qs": {k: v for k, v in d["qs"].items() if k != "integrity"}
            | {"integrity_open": any(i["unresolved"] for i in d["qs"]["integrity"])},
            "findings": len(items), "finding_kinds": sorted({i["kind"] for i in items}),
            "ficha_id": fichas[d["name"]]["ficha"]["id"],
        })

    hitl = reports["L3"].extra.get("hitl", []) if reports["L3"].status == "ok" else []
    aggregate = {
        "layer": 5, "run": run_meta, "portal": inst.portal, "policy": policy_dict, "notice": NOTICE,
        "layers": layers_meta, "totals": totals, "coverage": coverage, "combinations": combinations(datasets),
        "groups": groups, "unrecorded_changes": digests["unrecorded"], "alerts": alerts,
        "hitl": {"status": "instrumented_awaiting_steward" if not any(h.get("decided") for h in hitl) else "collecting",
                 "profiles": hitl},
        "inference": inf["summary"], "datasets": compact,
    }

    # ---- write (under out/, with the repository layout)
    data = out / "docs" / "data"
    if (data / "fichas").exists():
        shutil.rmtree(data / "fichas")
    write_json(data / "layer5.json", aggregate)
    for name, body in fichas.items():
        write_json(data / "fichas" / f"{name}.json", body)
    en, pt = badges(totals, layers_meta, integrity_open)
    write_json(data / "status.json", en)
    write_json(data / "status.pt.json", pt)
    write_json(data / "quality.jsonld", build_provenance(run_meta, layers_meta, datasets, policy_dict, inst.portal))
    write_json(out / "results" / "state.json", inf["state"])
    history_file = root / "results" / "history.json"
    history = json.loads(history_file.read_text(encoding="utf-8")) if history_file.exists() else []
    history.append({"at": run_meta["generated_at"], "commit": run_meta["commit"], "run_id": run_meta["run_id"],
                    "totals": totals, "coverage": coverage,
                    "layers": {l: {"status": m["status"], "generated_at": m["generated_at"]} for l, m in layers_meta.items()},
                    "integrity_open": integrity_open})
    write_json(out / "results" / "history.json", history[-HISTORY_LIMIT:])
    return aggregate


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=ROOT, help="instance folder (portal.json, sources.json, policy.json)")
    ap.add_argument("--out", type=Path, default=None, help="output folder (default: the instance folder)")
    ap.add_argument("--now", help="reference instant, ISO 8601 (default: now, UTC)")
    ap.add_argument("--fixtures", type=Path, help="offline: read <dir>/<repository-name>/<path>")
    ap.add_argument("--siblings", type=Path, help="local trial: read <dir>/5ltep-layerN/public for the main repositories")
    args = ap.parse_args(argv)
    now = parse(args.now) if args.now else utcnow()
    if args.fixtures:
        fetcher = Fetcher(roots={p.name: p for p in args.fixtures.iterdir() if p.is_dir()}, offline=True)
    elif args.siblings:
        fetcher = Fetcher(roots={f"5ltep-layer{n}": args.siblings / f"5ltep-layer{n}" / "public" for n in range(1, 5)})
    else:
        fetcher = Fetcher()
    result = run(args.root, args.out or args.root, now, fetcher)
    t = result["totals"]
    print(f"{result['portal']['name']}: {t['datasets']} datasets · {t['complete']} complete · {t['partial']} partial · "
          f"{t['no_content']} without content evaluation · {t['eligible']} reach the cutoff")
    for layer, meta in result["layers"].items():
        print(f"  {layer}: {meta['status']}{' (' + meta['reason'] + ')' if meta['reason'] else ''} · "
              f"generated {meta['generated_at']} · reached {result['coverage'][layer]['reached']}, "
              f"valid {result['coverage'][layer]['valid']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
