"""Per-dataset assessment: evidence validity, integrity factor and the two flows of the quality score.

Qs (SOFTENG 2026, Eq. 1) = sum of w_i * L_i over the four layers. Layer 5 extends it without changing
it when everything is present and nothing breaks integrity:

- each layer's evidence must be valid: summary within 2x the layer's cadence and no structural change
  (SCHEMA_DRIFT) after it. Bytes that changed with no record in the metadata (refinement R3) are a
  finding; by policy they either supersede the older evaluation or keep it as an earlier version;
- complete flow (all four layers valid): Qs = F * sum(w_i * L_i), the only flow that can reach the
  cutoff ("Nota de corte (θ)"), and only if every layer evaluated the current version (R1);
- partial flow: an interval, never a point (R5). Lower bound = missing layers counted as 0, upper
  bound = counted as 1, both times F. Removing evidence can only widen it;
- F = integrity_factor ** (unresolved integrity breaks): competence compensates, integrity does not.
  A break (RETRO_ALTER) stays unresolved until every content layer re-evaluates after it.
"""

from collections import Counter
from datetime import timedelta

from .config import CONTENT_LAYERS, LAYERS, Policy
from .timeutil import iso, parse

GROUPABLE = ("CONTENT_MOD", "SCHEMA_DRIFT", "RETRO_ALTER")


def digest_analysis(reports: dict, universe: dict, previous: dict, l4_ok: bool) -> dict:
    """R3: bytes that changed between two evaluations with no change recorded in the metadata.

    Observations of each resource (current layers + digests remembered from earlier rounds) are put in
    time order; two consecutive different digests with no Layer 4 event of the dataset in between mean
    the content changed without a metadata record. Without Layer 4 nothing can be concluded.
    """
    by_resource: dict = {}
    for layer in CONTENT_LAYERS:
        for name, ev in reports[layer].datasets.items():
            for d in ev.digests:
                if d.get("at"):
                    by_resource.setdefault(d["resource_id"], []).append(
                        {"layer": layer, "dataset": name, "sha256": d["sha256"], "at": d["at"]})
    for rid, obs in (previous or {}).items():
        if rid in by_resource:
            by_resource[rid].append({**obs, "layer": f"{obs.get('layer')} (previous round)"})
    latest, unrecorded, superseded = {}, [], set()
    for rid, obs in by_resource.items():
        obs.sort(key=lambda o: parse(o["at"]))
        latest[rid] = obs[-1]
        if not l4_ok:
            continue
        for before, after in zip(obs, obs[1:]):
            if before["sha256"] == after["sha256"]:
                continue
            name = after["dataset"]
            t1, t2 = parse(before["at"]), parse(after["at"])
            events = (universe.get(name) or {}).get("events", [])
            if any(t1 < parse(e["when"]) <= t2 and e["type"] != "NEW" for e in events):
                continue  # documented change: R1 handles it (not eligible until re-evaluated)
            unrecorded.append({"dataset": name, "resource_id": rid, "from": before["at"], "to": after["at"],
                               "layers": [before["layer"], after["layer"]]})
        for o in obs:
            if o["sha256"] != latest[rid]["sha256"] and not o["layer"].endswith("(previous round)"):
                if any(u["resource_id"] == rid and parse(o["at"]) <= parse(u["from"]) for u in unrecorded):
                    superseded.add((o["dataset"], o["layer"]))
    return {"latest": latest, "unrecorded": unrecorded, "superseded": superseded}


def band(value: float, policy: Policy) -> str:
    if value < policy.critical_floor:
        return "critical"
    return "alert" if value < policy.cutoff else "info"


def partial_band(lo: float, hi: float, policy: Policy) -> str:
    if hi < policy.critical_floor:
        return "critical"            # below the critical floor even in the best case
    if hi < policy.cutoff:
        return "alert"               # does not reach the cutoff even in the best case
    if lo >= policy.cutoff:
        return "info_worst_case"     # reaches the cutoff even in the worst case
    return "undetermined"            # depends on the missing layers


def assess_dataset(name: str, reports: dict, universe: dict, digests: dict, policy: Policy, now) -> dict:
    info = universe.get(name, {})
    events = info.get("events", [])
    changes = [e for e in events if e["type"] != "NEW"]
    # the events list of Layer 4 holds the recent ones; each dataset also carries its last change
    last_change = max([parse(e["when"]) for e in changes] + ([parse(info["last_change"])] if info.get("last_change") else []),
                      default=None)
    layers = {}
    for layer in LAYERS:
        rep = reports[layer]
        ev = rep.datasets.get(name) if rep.status == "ok" else None
        out = {"status": "missing", "reason": None, "rate": None, "evaluated_at": None, "current": None,
               "facts": {}, "signals": []}
        if rep.status != "ok":
            out["reason"] = rep.reason
        elif ev is None:
            out["reason"] = "not_reached"
        else:
            out.update(rate=ev.rate, evaluated_at=ev.evaluated_at, facts=ev.facts, signals=ev.signals)
            evaluated = parse(ev.evaluated_at)
            age_days = (now - parse(rep.generated_at)).total_seconds() / 86400 if rep.generated_at else None
            if ev.rate is None:
                out["reason"] = ev.reason
            elif age_days is None or age_days > policy.validity_days(layer):
                out["status"], out["reason"] = "expired", "summary_too_old"
            elif layer != "L4" and any(e["type"] in policy.scope_types and parse(e["when"]) > evaluated for e in events):
                out["status"], out["reason"] = "out_of_scope", "structure_changed_after"
            elif policy.unrecorded_change == "supersede" and (name, layer) in digests["superseded"]:
                out["status"], out["reason"] = "superseded", "content_changed_unrecorded"
            else:
                out["status"] = "valid"
                out["current"] = _current(ev, last_change, digests["latest"]) if layer != "L4" else True
        layers[layer] = out

    valid = [layer for layer in LAYERS if layers[layer]["status"] == "valid"]
    content_valid = [layer for layer in CONTENT_LAYERS if layer in valid]
    integrity = []
    for e in events:
        if e["type"] not in policy.integrity_types:
            continue
        when = parse(e["when"])
        stale = [layer for layer in content_valid if parse(layers[layer]["evaluated_at"]) < when]
        recent = when >= now - timedelta(days=policy.findings_window_days)
        integrity.append({"when": e["when"], "type": e["type"], "unresolved": bool(stale) or (not content_valid and recent),
                          "awaiting": stale})
    unresolved = sum(1 for i in integrity if i["unresolved"] and i["awaiting"])
    factor = policy.integrity_factor ** unresolved
    weights = policy.weights
    qs = {"kind": "none", "factor": factor, "coverage": round(sum(weights[layer] for layer in valid), 6),
          "valid_layers": valid, "integrity": integrity}
    if not content_valid:
        qs["band"] = "critical" if any(i["unresolved"] for i in integrity) else None
    elif len(valid) == len(LAYERS):
        base = sum(weights[layer] * layers[layer]["rate"] for layer in LAYERS)
        value = factor * base
        current = all(layers[layer]["current"] for layer in LAYERS)
        qs.update(kind="complete", base=base, value=value, band=band(value, policy), current=current,
                  eligible=value >= policy.cutoff and current and factor == 1)
        if value >= policy.cutoff and not current:
            qs["note"] = "met_cutoff_previous_version"
            qs["last_change"] = iso(last_change)
    else:
        known = sum(weights[layer] * layers[layer]["rate"] for layer in valid)
        missing = sum(weights[layer] for layer in LAYERS if layer not in valid)
        lo, hi = factor * known, factor * (known + missing)
        qs.update(kind="partial", low=lo, high=hi, band=partial_band(lo, hi, policy), eligible=False,
                  missing_layers=[layer for layer in LAYERS if layer not in valid])
    return {"name": name, "id": info.get("id"), "title": info.get("title"), "resources": info.get("resources"),
            "last_change": iso(last_change), "last_type": info.get("last_type"),
            "entity": (reports["L4"].datasets.get(name).facts.get("entity")
                       if reports["L4"].status == "ok" and name in reports["L4"].datasets else None),
            "layers": layers, "qs": qs, "events": events,
            "unrecorded_changes": [u for u in digests["unrecorded"] if u["dataset"] == name]}


def _current(ev, last_change, latest: dict) -> bool:
    """R1: the evaluation is of the current version (after the last recorded change, or same bytes).

    Bytes known to have changed after the evaluation (another layer saw newer, different bytes) mean an
    earlier version, recorded in the metadata or not.
    """
    for d in ev.digests:
        newest = latest.get(d["resource_id"])
        if newest and newest["sha256"] != d["sha256"] and parse(newest["at"]) > parse(d["at"]):
            return False
    if last_change is None or parse(ev.evaluated_at) >= last_change:
        return True
    if not ev.digests:
        return False
    return all(d["sha256"] == latest.get(d["resource_id"], {}).get("sha256")
               and parse(latest[d["resource_id"]]["at"]) >= last_change for d in ev.digests)


def simultaneous_groups(reports: dict, policy: Policy, now) -> list:
    """R2: many datasets changed in the same Layer 4 cycle = probably one operational event."""
    if reports["L4"].status != "ok":
        return []
    start = now - timedelta(days=policy.findings_window_days)
    counter = Counter((e["type"], e["when"]) for e in reports["L4"].extra["events"]
                      if e["type"] in GROUPABLE and parse(e["when"]) >= start)
    groups = []
    for (kind, when), n in counter.items():
        if n >= policy.simultaneous_event_min_datasets:
            names = sorted(e["name"] for e in reports["L4"].extra["events"] if e["type"] == kind and e["when"] == when)
            groups.append({"type": kind, "when": when, "datasets": names})
    return sorted(groups, key=lambda g: g["when"], reverse=True)


def combinations(datasets: list) -> list:
    counter = Counter(tuple(d["qs"]["valid_layers"]) for d in datasets)
    return [{"layers": list(k), "datasets": n} for k, n in counter.most_common()]
