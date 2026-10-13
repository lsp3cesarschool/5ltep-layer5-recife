"""Adapters: read what each layer already publishes and normalise it per dataset.

Each layer measures a different unit (L1 files per dataset, L2 rules, L3 one series per profile,
L4 metadata changes), so each adapter turns its layer into the same shape: per dataset, a pass rate in
[0, 1] or the reason there is none, when it was evaluated, the digests of the bytes it evaluated, and
the signals worth checking. A summary that fails its consistency checks is rejected as a whole
(refinement R4): a wrong summary becomes a gap with a reason, never a score.
"""

from dataclasses import dataclass, field
from datetime import timedelta

from .config import Instance
from .fetch import Fetcher, Missing
from .timeutil import iso, parse

CRITICAL_TYPES = ("SCHEMA_DRIFT", "RETRO_ALTER")


class Rejected(Exception):
    """The summary is inconsistent; the layer is shown as a gap with this reason."""


@dataclass
class DatasetEvidence:
    layer: str
    dataset: str
    rate: float | None = None
    reason: str | None = None          # why there is no rate (code, translated by the dashboard)
    evaluated_at: str | None = None
    digests: list = field(default_factory=list)   # {"resource_id", "sha256", "at"}
    signals: list = field(default_factory=list)   # {"key", "count", "en", "pt"}
    facts: dict = field(default_factory=dict)


@dataclass
class LayerReport:
    layer: str
    status: str                      # ok | missing | rejected | error
    reason: str | None = None
    detail: str | None = None
    generated_at: str | None = None
    files: list = field(default_factory=list)     # {"path", "url", "commit"}
    repository: str | None = None
    dashboard: str | None = None
    workflow: str | None = None
    datasets: dict = field(default_factory=dict)  # name -> DatasetEvidence
    portal: dict = field(default_factory=dict)    # layer-wide numbers
    extra: dict = field(default_factory=dict)


def _future(value: str | None, now) -> bool:
    dt = parse(value)
    return bool(dt and dt > now + timedelta(hours=1))


def _unit(x) -> bool:
    return isinstance(x, (int, float)) and 0 <= x <= 1


def _read(fetcher: Fetcher, report: LayerReport, path: str, optional: bool = False):
    try:
        data = fetcher.get_json(report.repository, path)
    except Missing:
        if optional:
            return None
        raise
    report.files.append({"path": path, "url": fetcher.url(report.repository, path),
                         "commit": fetcher.last_commit(report.repository, path)})
    return data


# --------------------------------------------------------------------------------------- Layer 1

def layer1(fetcher: Fetcher, inst: Instance, report: LayerReport, now) -> None:
    files = inst.sources["L1"]["files"]
    summary = _read(fetcher, report, files["summary"])
    validation = _read(fetcher, report, files["validation"], optional=True) or {}
    report.generated_at = summary.get("generated_at")
    if _future(report.generated_at, now):
        raise Rejected("generated_at is in the future")
    if not _unit(summary.get("l1_rate", 0) or 0):
        raise Rejected("l1_rate outside [0, 1]")
    by_dataset: dict = {}
    for resource_id, entry in validation.items():
        by_dataset.setdefault(entry.get("dataset"), []).append((resource_id, entry))
    for item in summary["per_dataset"]:
        name, rate = item["name"], item.get("l1_rate")
        verifiable, conformant = item.get("verifiable", 0), item.get("conformant", 0)
        if not 0 <= conformant <= verifiable:
            raise Rejected(f"{name}: conformant > verifiable")
        if rate is not None and (not _unit(rate) or verifiable == 0 or abs(rate - conformant / verifiable) > 0.001):
            raise Rejected(f"{name}: l1_rate does not match conformant / verifiable")
        entries = by_dataset.get(name, [])
        ev = DatasetEvidence("L1", name, rate=rate,
                             facts={"level": item.get("level"), "tables": item.get("tables"),
                                    "verifiable": verifiable, "conformant": conformant})
        if rate is None:
            ev.reason = "l1_level0" if item.get("level") == 0 else "l1_nothing_verifiable"
        checked = [e.get("checked_at") for _, e in entries if e.get("checked_at")]
        ev.evaluated_at = max(checked, key=parse) if checked else report.generated_at
        ev.digests = [{"resource_id": rid, "sha256": e["sha256"], "at": e.get("validated_at") or e.get("checked_at")}
                      for rid, e in entries if e.get("sha256")]
        if verifiable > conformant:
            n = verifiable - conformant
            ev.signals.append({"key": f"L1:{name}", "count": n,
                               "en": f"{n} of {verifiable} verifiable file(s) do not conform to the declared schema",
                               "pt": f"{n} de {verifiable} arquivo(s) verificável(is) fora do esquema declarado"})
        report.datasets[name] = ev
    report.portal = {"rate": summary.get("l1_rate"), "verifiable": summary.get("verifiable"),
                     "conformant": summary.get("conformant"),
                     "datasets_by_level": summary.get("datasets", {}).get("by_level")}


# --------------------------------------------------------------------------------------- Layer 2

def layer2(fetcher: Fetcher, inst: Instance, report: LayerReport, now) -> None:
    data = _read(fetcher, report, inst.sources["L2"]["files"]["summary"])
    report.generated_at = data.get("generated_at")
    if _future(report.generated_at, now):
        raise Rejected("generated_at is in the future")
    if not _unit(data.get("totals", {}).get("l2_rate", 0) or 0):
        raise Rejected("l2_rate outside [0, 1]")
    host = inst.host
    sources = {s["label"]: s for s in data.get("sources", [])}
    per: dict = {}
    references = set()
    for rule in data["rules"]:
        evaluated = None
        for entry in rule.get("datasets", []):
            parts = entry["label"].split(" › ")
            if parts[0] != host:
                references.add(entry["label"])
            if entry.get("source") == rule.get("evaluated_source"):
                evaluated = parts
        if not evaluated or evaluated[0] != host or len(evaluated) < 2:
            continue  # the rule checks data of another portal: a reference, not this portal's dataset
        slot = per.setdefault(evaluated[1], {"checks": 0, "signals": 0, "rules": [], "not_evaluated": [],
                                             "labels": set(), "evaluated_at": []})
        slot["labels"].add(" › ".join(evaluated))
        if rule.get("status") != "evaluated":
            slot["not_evaluated"].append({"rule": rule["id"], "reason": rule.get("reason_code") or rule.get("reason")})
            continue
        counts = rule.get("counts") or {}
        if sum(counts.values()) != rule.get("total"):
            raise Rejected(f"rule {rule['id']}: counts do not add up to total")
        if rule.get("signals") != sum((rule.get("signals_by_outcome") or {}).values()):
            raise Rejected(f"rule {rule['id']}: signals do not match signals_by_outcome")
        checks = rule["total"] - counts.get("out_of_scope", 0)
        slot["checks"] += checks
        slot["signals"] += rule["signals"]
        slot["rules"].append(rule["id"])
        slot["evaluated_at"].append(rule.get("evaluated_at"))
        if rule["signals"]:
            title_en = (rule.get("title_translations") or {}).get("en") or rule.get("title")
            slot.setdefault("signal_list", []).append({
                "key": f"L2:{rule['id']}", "count": rule["signals"],
                "en": f"{rule['signals']} signal(s) of rule '{title_en}' in {checks} check(s)",
                "pt": f"{rule['signals']} sinal(is) da regra '{rule.get('title')}' em {checks} verificação(ões)"})
    for name, slot in per.items():
        ev = DatasetEvidence("L2", name, facts={"rules": slot["rules"], "checks": slot["checks"],
                                                "signals": slot["signals"], "not_evaluated": slot["not_evaluated"]})
        if slot["checks"] > 0:
            ev.rate = 1 - slot["signals"] / slot["checks"]
        else:
            ev.reason = "l2_not_evaluated" if slot["not_evaluated"] else "l2_no_checks_in_scope"
        dates = [d for d in slot["evaluated_at"] if d]
        ev.evaluated_at = min(dates, key=parse) if dates else report.generated_at
        for label in slot["labels"]:
            src = sources.get(label) or {}
            sha = (src.get("download") or {}).get("sha256")
            rid = (src.get("resource") or {}).get("id")
            if sha and rid:
                ev.digests.append({"resource_id": rid, "sha256": sha, "at": data.get("started_at") or ev.evaluated_at})
        ev.signals = slot.get("signal_list", [])
        report.datasets[name] = ev
    report.portal = {"rate": data["totals"].get("l2_rate"), "rules": data["totals"].get("rules"),
                     "evaluated": data["totals"].get("evaluated"), "references": sorted(references),
                     "run_url": data.get("run_url")}


# --------------------------------------------------------------------------------------- Layer 3

def layer3(fetcher: Fetcher, inst: Instance, report: LayerReport, now) -> None:
    files = inst.sources["L3"]["files"]
    index = _read(fetcher, report, files["index"])
    stamps, hitl = [], []
    for profile in index.get("profiles", []):
        summary = _read(fetcher, report, files["summary"].format(profile=profile["id"]))
        if _future(summary.get("generated_at"), now):
            raise Rejected("generated_at is in the future")
        stamps.append(summary.get("generated_at"))
        block, source = summary.get("layer3", {}), summary.get("source", {})
        rate = block.get("l3_rate")
        if rate is not None and not _unit(rate):
            raise Rejected(f"{profile['id']}: l3_rate outside [0, 1]")
        name = source.get("dataset_id")
        if not name:
            raise Rejected(f"{profile['id']}: source.dataset_id missing")
        ev = DatasetEvidence("L3", name, rate=rate, evaluated_at=source.get("download_started_at") or summary.get("generated_at"),
                             facts={"profile": profile["id"], "window": block.get("window"),
                                    "pairs_evaluated": block.get("pairs_evaluated"),
                                    "anomalies": summary.get("anomalies", {}).get("flagged")})
        if rate is None:
            ev.reason = "l3_no_rate"
        if source.get("checksum_sha256") and source.get("resource_id"):
            ev.digests.append({"resource_id": source["resource_id"], "sha256": source["checksum_sha256"],
                               "at": ev.evaluated_at})
        flags = block.get("anomaly_flags") or []
        if flags:
            ev.signals.append({"key": f"L3:{profile['id']}", "count": len(flags),
                               "en": f"{len(flags)} anomaly flag(s) in the window {block.get('window')}",
                               "pt": f"{len(flags)} anomalia(s) sinalizada(s) na janela {block.get('window')}"})
        report.datasets[name] = ev
        hitl.append({"profile": profile["id"], **summary.get("hitl", {})})
    report.generated_at = max(stamps, key=parse) if stamps else None
    report.extra["hitl"] = hitl


# --------------------------------------------------------------------------------------- Layer 4

def layer4(fetcher: Fetcher, inst: Instance, report: LayerReport, now) -> None:
    files = inst.sources["L4"]["files"]
    data = _read(fetcher, report, files["summary"])
    cross = _read(fetcher, report, files["cross_check"], optional=True) or {}
    hashes = _read(fetcher, report, files["hashes"], optional=True) or {}
    report.generated_at = data.get("generated_at")
    monitoring = data.get("monitoring", {})
    if _future(report.generated_at, now) or _future(monitoring.get("last_cycle"), now):
        raise Rejected("generated_at or last_cycle is in the future")
    cycles = monitoring.get("cycles_by_day") or {}
    if any((not isinstance(n, int)) or n < 0 for n in cycles.values()):
        raise Rejected("cycles_by_day has invalid counts")
    policy = inst.policy
    window_start = now - timedelta(days=policy.l4_window_days)
    findings_start = now - timedelta(days=policy.findings_window_days)
    events = sorted(data.get("events", []), key=lambda e: parse(e["when"]))
    first_seen = {e["name"]: parse(e["when"]) for e in events if e.get("type") == "NEW"}
    since = parse(monitoring.get("since"))
    modified = {str(x.get("name") if isinstance(x, dict) else x) for x in cross.get("modified", [])}
    universe = {}
    for d in data.get("datasets", []):
        name = d["name"]
        start = max(window_start, first_seen.get(name) or since or window_start)
        observations = sum(n for day, n in cycles.items() if parse(day + "T23:59:59+00:00") >= start)
        own = [e for e in events if e.get("name") == name]
        critical = [e for e in own if e.get("type") in CRITICAL_TYPES and parse(e["when"]) >= window_start]
        content_hash = (hashes.get(d["id"]) or {}).get("content_hash")
        ev = DatasetEvidence("L4", name, evaluated_at=monitoring.get("last_cycle"),
                             facts={"observations": observations, "critical_in_window": len(critical),
                                    "entity": f"{inst.portal['portal_url']}/dataset/{d['id']}#{content_hash[:12]}" if content_hash else None})
        if observations > 0:
            ev.rate = max(0.0, 1 - len(critical) / observations)
        else:
            ev.reason = "l4_not_observed"
        for e in own:
            if parse(e["when"]) < findings_start:
                continue
            moved = sum(p[2] for p in e.get("host_pairs", []))
            repack = e.get("zip_to_plain", 0) + e.get("plain_to_zip", 0)
            if moved or repack:
                ev.signals.append({"key": f"L4:access:{e['when']}", "count": max(moved, repack), "when": e["when"],
                                   "en": e.get("summary"), "pt": e.get("summary_pt") or e.get("summary")})
        if name in modified or d["id"] in modified:
            ev.signals.append({"key": f"L4:cross_check:{name}", "count": 1,
                               "en": "unreconciled divergence in the independent cross-check",
                               "pt": "divergência não reconciliada no cross-check independente"})
        report.datasets[name] = ev
        universe[name] = {"id": d["id"], "title": d.get("title"), "resources": d.get("resources"),
                          "organization": d.get("organization"), "last_change": d.get("last_change"),
                          "last_type": d.get("last_type"), "metadata_modified": d.get("metadata_modified"),
                          "events": [{"when": e["when"], "type": e["type"], "severity": e.get("severity"),
                                      "summary": e.get("summary"), "summary_pt": e.get("summary_pt")} for e in own]}
    report.extra.update({
        "universe": universe, "events": events, "since": monitoring.get("since"),
        "last_cycle": monitoring.get("last_cycle"), "cycles_30d": monitoring.get("cycles_30d"),
        "max_gap_hours_30d": monitoring.get("max_gap_hours_30d"),
        "cross_check": {"status": cross.get("status"), "checked_at": cross.get("checked_at"),
                        "removed": (cross.get("datasets") or {}).get("removed", []),
                        "added": (cross.get("datasets") or {}).get("added", [])},
    })
    report.portal = {"datasets": len(universe), "relocations": data.get("relocations"),
                     "toolkit_version": data.get("toolkit_version")}


ADAPTERS = {"L1": layer1, "L2": layer2, "L3": layer3, "L4": layer4}


def read_layer(layer: str, fetcher: Fetcher, inst: Instance, now) -> LayerReport:
    cfg = inst.sources[layer]
    report = LayerReport(layer, "ok", repository=cfg["repository"], dashboard=cfg.get("dashboard"),
                         workflow=f"https://github.com/{cfg['repository']}/actions/workflows/{cfg['workflow']}"
                         if cfg.get("workflow") else None)
    try:
        ADAPTERS[layer](fetcher, inst, report, now)
    except Missing as err:
        report.status, report.reason, report.detail = "missing", "layer_not_deployed", str(err)
        report.datasets = {}
    except Rejected as err:
        report.status, report.reason, report.detail = "rejected", "summary_inconsistent", str(err)
        report.datasets = {}
    except (KeyError, TypeError, ValueError) as err:
        report.status, report.reason, report.detail = "rejected", "summary_unreadable", f"{type(err).__name__}: {err}"
        report.datasets = {}
    except OSError as err:  # network
        report.status, report.reason, report.detail = "error", "fetch_failed", f"{type(err).__name__}: {err}"
        report.datasets = {}
    report.extra.setdefault("read_at", iso(now))
    return report
