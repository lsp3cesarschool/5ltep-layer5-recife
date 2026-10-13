"""Sensitivity of the readings to the policy (Saisana, Saltelli and Tarantola, 2005).

The weights and the cutoff of the paper are defaults, not calibrated values. This script recomputes the
reading of every dataset (band, and whether it reaches the cutoff) under alternative policies and
reports how many datasets keep the same reading in every scenario:

- weights: each weight moved by ±0.05 and renormalised;
- cutoff: 0.80, 0.85, 0.90;
- integrity factor: 0.25, 0.5, 0.69 (decisions should not change: see README);
- aggregation operator: arithmetic (paper), geometric (as the Human Development Index since 2010) and
  minimum (weakest link; Pipino, Lee and Wang 2002). For a partial dataset, missing layers are taken as
  0 and as 1, as in the interval.

Reads docs/data/layer5.json (written by the daily run); writes evaluation/results/sensitivity.json.
Usage: python evaluation/sensitivity.py [path/to/layer5.json]
"""

import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYERS = ("L1", "L2", "L3", "L4")


def aggregate(op, weights, rates):
    if op == "arithmetic":
        return sum(weights[l] * rates[l] for l in LAYERS)
    if op == "geometric":
        return math.prod(max(rates[l], 1e-9) ** weights[l] for l in LAYERS)
    return min(rates[l] for l in LAYERS)


def reading(d, op, weights, cutoff, floor, factor, base_factor=0.5):
    valid = {l: c["rate"] for l, c in d["layers"].items() if c["status"] == "valid"}
    if not any(l in valid for l in ("L1", "L2", "L3")):
        return "none"
    breaks = round(math.log(d["qs"]["factor"]) / math.log(base_factor)) if d["qs"].get("factor", 1) < 1 else 0
    f = factor ** breaks
    lo = f * aggregate(op, weights, {l: valid.get(l, 0.0) for l in LAYERS})
    hi = f * aggregate(op, weights, {l: valid.get(l, 1.0) for l in LAYERS})
    complete = len(valid) == 4
    if complete:
        return "critical" if lo < floor else "alert" if lo < cutoff else ("eligible" if d["qs"].get("current", True) else "info")
    return "critical" if hi < floor else "alert" if hi < cutoff else "info_worst_case" if lo >= cutoff else "undetermined"


def scenarios(policy):
    base = policy["weights"]
    weight_sets = [base]
    for l, delta in itertools.product(LAYERS, (-0.05, 0.05)):
        w = {**base, l: max(0.0, base[l] + delta)}
        total = sum(w.values())
        weight_sets.append({k: v / total for k, v in w.items()})
    for op, w, cutoff, factor in itertools.product(("arithmetic", "geometric", "minimum"), weight_sets,
                                                   (0.80, 0.85, 0.90), (0.25, 0.5, 0.69)):
        yield {"op": op, "weights": w, "cutoff": cutoff, "factor": factor}


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/data/layer5.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    policy = data["policy"]
    base = {d["name"]: reading(d, "arithmetic", policy["weights"], policy["cutoff"], policy["critical_floor"],
                               policy["integrity_factor"], policy["integrity_factor"]) for d in data["datasets"]}
    stable = {name: True for name in base}
    by_op = {}
    count = 0
    for s in scenarios(policy):
        count += 1
        for d in data["datasets"]:
            r = reading(d, s["op"], s["weights"], s["cutoff"], policy["critical_floor"], s["factor"], policy["integrity_factor"])
            if r != base[d["name"]]:
                stable[d["name"]] = False
                by_op.setdefault(s["op"], set()).add(d["name"])
    result = {"generated_from": data["run"], "scenarios": count, "datasets": len(base),
              "stable": sum(stable.values()), "changed_by_operator": {k: sorted(v) for k, v in by_op.items()},
              "baseline_readings": base}
    out = ROOT / "evaluation" / "results" / "sensitivity.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{result['stable']} of {result['datasets']} datasets keep their reading in all {count} scenarios")
    for op, names in result["changed_by_operator"].items():
        print(f"  {op}: {len(names)} dataset(s) change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
