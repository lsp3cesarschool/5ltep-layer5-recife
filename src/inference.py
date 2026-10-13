"""Inferred steward outcome: what happened to the data after Layer 5 reported a signal.

Layer 5 informs; it never decides. The publication decision happens in the agency's own systems. What
can be observed, round after round, is whether the data changed and whether each reported signal is
still there. The labels describe what was observed after the report, never why: "unchanged" does not
tell "seen and accepted" from "not seen", and a change is "after the report", not "because of it".

The researcher records no decision (that would be self-assessment); everything here is computed.
Also keeps refinement R6: a layer that had evidence on a dataset and lost it becomes a finding.
"""

from statistics import median

from .config import LAYERS
from .timeutil import iso, parse

LAYER_WIDE = ("layer_not_deployed", "summary_inconsistent", "summary_unreadable", "fetch_failed")
OPEN = ("unchanged", "changed_signal_persists", "not_reassessed")
CLOSED = ("remediated_observed", "cleared_without_data_change", "withdrawn_observed")


def _data_changed(dataset: dict, since: str, latest_digests: dict, reported_digests: dict) -> bool:
    if dataset.get("last_change") and parse(dataset["last_change"]) > parse(since):
        return True
    for rid, sha in (reported_digests or {}).items():
        now_sha = (latest_digests.get(rid) or {}).get("sha256")
        if now_sha and now_sha != sha:
            return True
    return False


def infer(previous: dict, datasets: list, latest_digests: dict, removed: list, now) -> dict:
    """Return the new state (signals, presence, digests, outcomes) and this round's observations."""
    previous = previous or {}
    by_name = {d["name"]: d for d in datasets}
    removed = {str(x.get("name") if isinstance(x, dict) else x) for x in removed or []}
    prev_ds = previous.get("datasets", {})
    outcomes = list(previous.get("outcomes", []))
    new_state, observed, lost_findings = {}, [], {}
    stamp = iso(now)

    for name, old in prev_ds.items():
        current = by_name.get(name)
        for key, sig in old.get("signals", {}).items():
            if current is None:
                if name in removed or old.get("in_universe"):
                    outcomes.append({**sig, "key": key, "dataset": name, "outcome": "withdrawn_observed", "at": stamp})
                    observed.append({"dataset": name, "key": key, "outcome": "withdrawn_observed"})
                continue
            layer = sig["layer"]
            info = current["layers"][layer]
            reassessed = info["evaluated_at"] and parse(info["evaluated_at"]) > parse(sig["evaluated_at"])
            present = any(s["key"] == key and s.get("count") for s in info.get("signals", []))
            changed = _data_changed(current, sig["first_reported"], latest_digests, sig.get("digests"))
            if not reassessed:
                status = "not_reassessed"
            elif present:
                status = "changed_signal_persists" if changed else "unchanged"
            else:
                status = "remediated_observed" if changed else "cleared_without_data_change"
            entry = {**sig, "status": status}
            if changed and not sig.get("first_change_seen"):
                entry["first_change_seen"] = stamp
            if status in CLOSED:
                outcomes.append({**entry, "key": key, "dataset": name, "outcome": status, "at": stamp})
            else:
                new_state.setdefault(name, {}).setdefault("signals", {})[key] = entry
            observed.append({"dataset": name, "key": key, "outcome": status})

    for d in datasets:
        name = d["name"]
        slot = new_state.setdefault(name, {})
        slot.setdefault("signals", {})
        slot["in_universe"] = True
        digests = {}
        for layer in LAYERS:
            info = d["layers"][layer]
            for s in info.get("signals", []):
                if not s.get("count") or s["key"] in slot["signals"]:
                    continue
                slot["signals"][s["key"]] = {"layer": layer, "first_reported": stamp, "count": s["count"],
                                             "evaluated_at": info["evaluated_at"] or stamp, "status": "reported",
                                             "en": s.get("en"), "pt": s.get("pt")}
            for rid, obs in latest_digests.items():
                if obs.get("dataset") == name:
                    digests[rid] = obs["sha256"]
        for key, sig in slot["signals"].items():
            sig.setdefault("digests", digests)
        # R6: evidence lost since the previous round
        # (a layer that is unavailable as a whole tells nothing about this dataset: presence unknown)
        presence = {layer: None if d["layers"][layer]["reason"] in LAYER_WIDE else d["layers"][layer]["rate"] is not None
                    for layer in LAYERS}
        before = prev_ds.get(name, {}).get("presence", {})
        lost = dict(prev_ds.get(name, {}).get("lost", {}))
        for layer in LAYERS:
            if presence[layer] is None:
                presence[layer] = before.get(layer)
                continue
            if before.get(layer) and not presence[layer]:
                lost.setdefault(layer, {"since": stamp, "reason": d["layers"][layer]["reason"]})
            elif presence[layer]:
                lost.pop(layer, None)
        slot["presence"], slot["lost"] = presence, lost
        if lost:
            lost_findings[name] = lost

    days = [(parse(o["first_change_seen"]) - parse(o["first_reported"])).total_seconds() / 86400
            for o in outcomes if o.get("first_change_seen")]
    summary = {
        "open_signals": sum(len(s.get("signals", {})) for s in new_state.values()),
        "closed": {label: sum(1 for o in outcomes if o["outcome"] == label) for label in CLOSED},
        "open_by_status": {label: sum(1 for s in new_state.values() for x in s.get("signals", {}).values()
                                      if x.get("status") == label) for label in (*OPEN, "reported")},
        "median_days_to_first_change": round(median(days), 1) if days else None,
        "rounds_observed": previous.get("rounds", 0) + 1,
    }
    state = {"round": stamp, "rounds": previous.get("rounds", 0) + 1, "datasets": new_state,
             "outcomes": outcomes[-5000:],
             "digests": {rid: obs for rid, obs in latest_digests.items()}}
    return {"state": state, "observed": observed, "lost": lost_findings, "summary": summary}
