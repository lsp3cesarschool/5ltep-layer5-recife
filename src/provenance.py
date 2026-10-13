"""Quality measurements in W3C DQV, with their provenance in W3C PROV-O (JSON-LD).

Each score is a dqv:QualityMeasurement computed on the exact dataset state that Layer 4 recorded
(its content-addressed PROV entity, `<portal>/dataset/<id>#<hash>`), derived (prov:wasDerivedFrom)
from the per-layer measurements, which are derived from the public summaries of each layer at a known
commit. The policy is a dqv:QualityPolicy. This realises the "W3C DQV integration" listed as future
work in the Layer 4 paper (WFA/WebMedia 2026).
"""

from .config import LAYERS

CONTEXT = {
    "prov": "http://www.w3.org/ns/prov#",
    "dqv": "http://www.w3.org/ns/dqv#",
    "dcterms": "http://purl.org/dc/terms/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "5ltep": "https://5ltep.example.org/ontology#",
}
METRICS = {
    "L1": "5ltep:metric/L1-conformance-rate", "L2": "5ltep:metric/L2-check-pass-rate",
    "L3": "5ltep:metric/L3-pair-pass-rate", "L4": "5ltep:metric/L4-intact-observation-rate",
    "Qs": "5ltep:metric/Qs-global-quality-score", "Qs-low": "5ltep:metric/Qs-partial-lower-bound",
    "Qs-high": "5ltep:metric/Qs-partial-upper-bound",
}


def _dt(value):
    return {"@value": value, "@type": "xsd:dateTime"} if value else None


def build(run: dict, layers: dict, datasets: list, policy: dict, portal: dict) -> dict:
    repo_url = f"https://github.com/{run['repository']}"
    activity = f"{repo_url}/actions/runs/{run['run_id']}" if run.get("run_id") else f"5ltep:l5-run-{run['generated_at']}"
    agent = f"{repo_url}/tree/{run['commit']}" if run.get("commit") else repo_url
    policy_id = f"{repo_url}/blob/{run.get('commit') or 'main'}/policy.json"
    graph = [
        {"@id": agent, "@type": ["prov:SoftwareAgent", "prov:Agent"], "dcterms:title": "5L-TEP Layer 5"},
        {"@id": policy_id, "@type": "dqv:QualityPolicy", "dcterms:title": "Layer 5 quality policy",
         "5ltep:policyVersion": policy["policy_version"], "5ltep:cutoff": policy["cutoff"],
         "5ltep:criticalFloor": policy["critical_floor"], "5ltep:integrityFactor": policy["integrity_factor"],
         "5ltep:aggregation": policy["aggregation"]},
    ]
    summaries = {}
    used = []
    for layer, meta in layers.items():
        for f in meta.get("files", []):
            commit = (f.get("commit") or {}).get("sha")
            iri = f"https://github.com/{meta['repository']}/blob/{commit}/{f['path']}" if commit else f["url"]
            summaries.setdefault(layer, iri)
            used.append(iri)
            graph.append({"@id": iri, "@type": "prov:Entity", "5ltep:layer": layer,
                          "prov:generatedAtTime": _dt(meta.get("generated_at"))})
    graph.append({"@id": activity, "@type": "prov:Activity", "prov:wasAssociatedWith": {"@id": agent},
                  "prov:endedAtTime": _dt(run["generated_at"]), "prov:used": [{"@id": u} for u in used + [policy_id]]})
    for d in datasets:
        target = d.get("entity") or f"{portal['portal_url']}/dataset/{d['name']}"
        base = f"5ltep:l5/{run['generated_at']}/{d['name']}"
        parts = []
        for layer in LAYERS:
            info = d["layers"][layer]
            if info["rate"] is None:
                continue
            mid = f"{base}/{layer}"
            parts.append(mid)
            node = {"@id": mid, "@type": "dqv:QualityMeasurement", "dqv:computedOn": {"@id": target},
                    "dqv:isMeasurementOf": {"@id": METRICS[layer]}, "dqv:value": round(info["rate"], 6),
                    "5ltep:evidenceStatus": info["status"], "prov:wasGeneratedBy": {"@id": activity},
                    "5ltep:evaluatedAt": _dt(info["evaluated_at"])}
            if layer in summaries:
                node["prov:wasDerivedFrom"] = {"@id": summaries[layer]}
            graph.append(node)
        qs = d["qs"]
        derived = [{"@id": p} for p in parts] + [{"@id": policy_id}]
        if qs["kind"] == "complete":
            graph.append({"@id": f"{base}/Qs", "@type": "dqv:QualityMeasurement", "dqv:computedOn": {"@id": target},
                          "dqv:isMeasurementOf": {"@id": METRICS["Qs"]}, "dqv:value": round(qs["value"], 6),
                          "5ltep:integrityFactor": qs["factor"], "5ltep:band": qs["band"],
                          "5ltep:eligible": qs["eligible"], "prov:wasDerivedFrom": derived,
                          "prov:wasGeneratedBy": {"@id": activity}})
        elif qs["kind"] == "partial":
            for key, value in (("Qs-low", qs["low"]), ("Qs-high", qs["high"])):
                graph.append({"@id": f"{base}/{key}", "@type": "dqv:QualityMeasurement", "dqv:computedOn": {"@id": target},
                              "dqv:isMeasurementOf": {"@id": METRICS[key]}, "dqv:value": round(value, 6),
                              "5ltep:coverage": qs["coverage"], "5ltep:band": qs["band"],
                              "prov:wasDerivedFrom": derived, "prov:wasGeneratedBy": {"@id": activity}})
    return {"@context": CONTEXT, "@graph": graph}
