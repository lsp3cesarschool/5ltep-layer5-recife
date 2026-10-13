"""Outputs: dashboard data, one citable record ("ficha") per dataset, badges, history and state.

Everything is written under an output folder with the repository layout (docs/data/..., results/...),
so the job that reads the other layers never writes to the repository; the publish job checks the
folder (src/accept.py) and commits it.
"""

import hashlib
import json
from datetime import timedelta
from pathlib import Path

from .config import LAYERS
from .timeutil import parse

NOTICE = {
    "en": ("Layer 5 informs; it does not decide. The publication decision, if any, happens in the agency's "
           "own systems. Signals are things to check, never verdicts; a gap is missing evidence, never a "
           "low score. Outcomes after a report are observations, with no attribution of cause."),
    "pt": ("A Camada 5 informa; não decide. A decisão de publicação, se houver, acontece nos sistemas do "
           "próprio órgão. Sinais são itens a conferir, nunca vereditos; lacuna é falta de evidência, nunca "
           "nota baixa. Desfechos depois de um relato são observações, sem atribuição de causa."),
}


def canonical(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def write_json(path: Path, obj, indent: int | None = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8", newline="\n")


def findings(d: dict, lost: dict, groups: list, policy, now) -> list:
    """What can already be checked for this dataset, with or without a complete score."""
    out = []
    for layer in LAYERS:
        for s in d["layers"][layer].get("signals", []):
            out.append({"layer": layer, "kind": "signal", "key": s["key"], "count": s.get("count"),
                        "when": s.get("when"), "en": s.get("en"), "pt": s.get("pt")})
    for i in d["qs"]["integrity"]:
        out.append({"layer": "L4", "kind": "integrity", "when": i["when"], "unresolved": i["unresolved"],
                    "awaiting": i["awaiting"],
                    "en": "metadata changed without the portal's modification date advancing (RETRO_ALTER)",
                    "pt": "metadados alterados sem a data de modificação do portal avançar (RETRO_ALTER)"})
    start = now - timedelta(days=policy.findings_window_days)
    for e in d.get("events", []):
        if e["type"] in policy.scope_types and parse(e["when"]) >= start:
            out.append({"layer": "L4", "kind": "scope", "when": e["when"],
                        "en": "the dataset structure changed (SCHEMA_DRIFT): earlier evaluations no longer cover it",
                        "pt": "a estrutura do conjunto mudou (SCHEMA_DRIFT): avaliações anteriores deixam de cobri-lo"})
    for u in d.get("unrecorded_changes", []):
        out.append({"layer": "L5", "kind": "unrecorded_change", "when": u["to"], "resource_id": u["resource_id"],
                    "en": f"the bytes of resource {u['resource_id']} changed between {u['from'][:10]} and {u['to'][:10]} with no change in the portal metadata",
                    "pt": f"os bytes do recurso {u['resource_id']} mudaram entre {u['from'][:10]} e {u['to'][:10]} sem mudança nos metadados do portal"})
    for layer, item in (lost or {}).items():
        out.append({"layer": layer, "kind": "evidence_lost", "when": item["since"], "reason": item.get("reason"),
                    "en": f"{layer} had evidence on this dataset and no longer has it",
                    "pt": f"a {layer} tinha evidência sobre este conjunto e deixou de ter"})
    for g in groups:
        if d["name"] in g["datasets"]:
            out.append({"layer": "L4", "kind": "simultaneous", "when": g["when"], "count": len(g["datasets"]),
                        "en": f"{g['type']} in {len(g['datasets'])} datasets in the same monitoring cycle (probably one operational event)",
                        "pt": f"{g['type']} em {len(g['datasets'])} conjuntos no mesmo ciclo de monitoramento (provavelmente um único evento operacional)"})
    return out


def ficha(d: dict, items: list, outcomes: dict, run: dict, layers_meta: dict, policy: dict, portal: dict) -> dict:
    """A self-contained, citable record of one dataset; its id is the SHA-256 of its content."""
    owner, repo = run["repository"].split("/")
    body = {
        "dataset": {k: d.get(k) for k in ("name", "title", "id", "resources", "last_change", "last_type", "entity")}
        | {"portal_page": f"{portal['portal_url']}/dataset/{d['name']}"},
        "qs": d["qs"], "layers": d["layers"], "findings": items, "outcomes": outcomes,
        "sources": {layer: {k: m.get(k) for k in ("status", "reason", "generated_at", "files", "dashboard")}
                    for layer, m in layers_meta.items()},
        "policy": policy, "portal": portal, "notice": NOTICE,
        "generated_at": run["generated_at"], "engine": {"repository": run["repository"], "commit": run.get("commit"),
                                                        "run_id": run.get("run_id")},
    }
    digest = hashlib.sha256(canonical(body)).hexdigest()
    page = f"https://{owner}.github.io/{repo}/ficha.html?d={d['name']}"
    body["ficha"] = {
        "id": f"sha256:{digest}", "page": page,
        "data": f"https://raw.githubusercontent.com/{run['repository']}/main/docs/data/fichas/{d['name']}.json",
        "how_to_cite": {
            "en": f"5L-TEP Layer 5 record of '{d['name']}' ({portal['name']}), {run['generated_at'][:10]}, sha256:{digest[:16]}…, {page}",
            "pt": f"Ficha da Camada 5 do 5L-TEP para '{d['name']}' ({portal['name']}), {run['generated_at'][:10]}, sha256:{digest[:16]}…, {page}",
        },
    }
    return body


def badges(totals: dict, layers_meta: dict, integrity_open: int) -> tuple[dict, dict]:
    unavailable = [l for l, m in layers_meta.items() if m["status"] != "ok"]
    color = "red" if integrity_open else ("orange" if unavailable else "blue")
    en = f"{totals['datasets']} datasets · {totals['complete']} complete · {totals['partial']} partial"
    pt = f"{totals['datasets']} conjuntos · {totals['complete']} completos · {totals['partial']} parciais"
    if integrity_open:
        en += f" · {integrity_open} integrity alert(s)"
        pt += f" · {integrity_open} alerta(s) de integridade"
    return ({"schemaVersion": 1, "label": "Layer 5", "message": en, "color": color},
            {"schemaVersion": 1, "label": "Camada 5", "message": pt, "color": color})
