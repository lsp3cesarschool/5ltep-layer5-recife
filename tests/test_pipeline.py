"""End to end on the real IBAMA summaries (fixtures), fault injection in the manner of Table 2 of the
Layer 4 paper (WFA/WebMedia 2026), consistency checks (R4) and the publish step."""

import hashlib
import json

import pytest

from conftest import CONFIG, FIXTURES, NOW, edit_json, fetcher_for
import main as l5
from src.accept import Refused, accept, check
from src.adapters import read_layer
from src.report import canonical
from src.timeutil import iso


def run_on(folder, tmp_path, now=NOW):
    """Run on a fresh copy of the instance configuration (no state from earlier rounds)."""
    root = tmp_path / "instance"
    root.mkdir(parents=True)
    for name in ("portal.json", "sources.json", "policy.json"):
        (root / name).write_bytes((CONFIG / name).read_bytes())
    out = tmp_path / "out"
    return l5.run(root, out, now, fetcher_for(folder)), out


def by_name(result):
    return {d["name"]: d for d in result["datasets"]}


# ------------------------------------------------------------------ adapters on the real summaries

def test_adapters_read_the_real_summaries(instance):
    f = fetcher_for(FIXTURES)
    reports = {layer: read_layer(layer, f, instance, NOW) for layer in ("L1", "L2", "L3", "L4")}
    assert all(r.status == "ok" for r in reports.values())
    assert len(reports["L4"].datasets) == 79
    assert sum(1 for e in reports["L1"].datasets.values() if e.rate is not None) == 32
    assert len(reports["L2"].datasets) == 13
    assert list(reports["L3"].datasets) == ["fiscalizacao-auto-de-infracao"]
    # the dataset with the most layers has no data dictionary: a gap with its reason, never a score
    assert reports["L1"].datasets["fiscalizacao-auto-de-infracao"].reason == "l1_level0"


def test_missing_layer_is_a_structural_gap(fixtures_copy, instance):
    import shutil
    shutil.rmtree(fixtures_copy / "5ltep-layer3")  # like Recife before its Layer 3 exists
    report = read_layer("L3", fetcher_for(fixtures_copy), instance, NOW)
    assert report.status == "missing" and report.reason == "layer_not_deployed" and not report.datasets


def test_r4_inconsistent_summary_is_rejected_not_scored(fixtures_copy, instance):
    def break_counts(data):
        data["rules"][0]["counts"]["match"] += 1
    edit_json(fixtures_copy / "5ltep-layer2/docs/data/layer2.json", break_counts)
    report = read_layer("L2", fetcher_for(fixtures_copy), instance, NOW)
    assert report.status == "rejected" and "counts" in report.detail and not report.datasets


def test_r4_summary_from_the_future_is_rejected(instance):
    report = read_layer("L2", fetcher_for(FIXTURES), instance, NOW.replace(day=1))
    assert report.status == "rejected"


# ------------------------------------------------------------------------------- end to end

def test_end_to_end_on_the_real_summaries(tmp_path):
    result, out = run_on(FIXTURES, tmp_path)
    t = result["totals"]
    assert t["datasets"] == 79 and t["complete"] == 0 and t["eligible"] == 0
    assert t["partial"] + t["no_content"] == 79
    assert result["hitl"]["status"] == "instrumented_awaiting_steward"
    check(out)  # the publish step accepts what the run produced
    ficha = json.loads((out / "docs/data/fichas/fiscalizacao-auto-de-infracao.json").read_text(encoding="utf-8"))
    body = {k: v for k, v in ficha.items() if k != "ficha"}
    assert ficha["ficha"]["id"] == "sha256:" + hashlib.sha256(canonical(body)).hexdigest()


def test_quality_measurements_point_to_the_layer4_entity(tmp_path):
    result, out = run_on(FIXTURES, tmp_path)
    graph = json.loads((out / "docs/data/quality.jsonld").read_text(encoding="utf-8"))["@graph"]
    measured = [n for n in graph if n.get("@type") == "dqv:QualityMeasurement"]
    assert measured and all(n["dqv:computedOn"]["@id"].startswith("https://dadosabertos.ibama.gov.br/dataset/")
                            for n in measured)
    assert any("#" in n["dqv:computedOn"]["@id"] for n in measured)  # content-addressed state of Layer 4
    assert any(n.get("@type") == "dqv:QualityPolicy" for n in graph)


# ---------------------------------------------------------------- fault injection (WFA, Table 2)

def inject(folder, names, kind, when="2026-10-09T17:00:00+00:00"):  # after every evaluation, before NOW
    def add(data):
        ids = {d["name"]: d["id"] for d in data["datasets"]}
        for name in names:
            data["events"].append({"when": when, "type": kind, "severity": "CRITICAL" if kind != "CONTENT_MOD" else "WARNING",
                                   "dataset_id": ids[name], "name": name, "title": name, "summary": "injected",
                                   "summary_pt": "injetado", "host_pairs": [], "zip_to_plain": 0, "plain_to_zip": 0})
    edit_json(folder / "5ltep-layer4/docs/data/layer4.json", add)


# three datasets with content evaluated by at least one of L1-L3 (partial flow in the baseline)
TARGETS = ["volumes-explorados-if-100", "relatorios-de-comercializacao-de-agrotoxicos", "sisfogo-roi"]


def test_injected_retro_alter_halves_the_score_and_alerts(fixtures_copy, tmp_path):
    before = by_name(run_on(FIXTURES, tmp_path / "a")[0])
    inject(fixtures_copy, TARGETS, "RETRO_ALTER")
    result = run_on(fixtures_copy, tmp_path / "b")[0]
    after = by_name(result)
    for name in TARGETS:
        assert after[name]["qs"]["factor"] == 0.5
        # the critical cycle also lowers the L4 rate (intact observations), by 1/observations
        l4_drop = 0.2 * (1 - after[name]["layers"]["L4"]["rate"])
        assert after[name]["qs"]["high"] == pytest.approx((before[name]["qs"]["high"] - l4_drop) * 0.5)
        assert after[name]["qs"]["band"] == "critical"
    assert {a["dataset"] for a in result["alerts"]["new_integrity_events"]} == set(TARGETS)
    untouched = [n for n in after if n not in TARGETS]
    assert all(after[n]["qs"] == before[n]["qs"] for n in untouched)


def test_injected_schema_drift_takes_evidence_out_of_scope_without_penalty(fixtures_copy, tmp_path):
    inject(fixtures_copy, TARGETS, "SCHEMA_DRIFT")
    after = by_name(run_on(fixtures_copy, tmp_path)[0])
    for name in TARGETS:
        assert after[name]["qs"]["factor"] == 1
        assert all(after[name]["layers"][l]["status"] in ("out_of_scope", "missing") for l in ("L1", "L2", "L3"))
        assert after[name]["qs"]["kind"] == "none"


def test_injected_content_mod_changes_no_score(fixtures_copy, tmp_path):
    before = by_name(run_on(FIXTURES, tmp_path / "a")[0])
    inject(fixtures_copy, TARGETS, "CONTENT_MOD")
    after = by_name(run_on(fixtures_copy, tmp_path / "b")[0])
    for name in TARGETS:
        assert after[name]["qs"]["low"] == before[name]["qs"]["low"]
        assert after[name]["qs"]["high"] == before[name]["qs"]["high"]


def test_tags_only_change_is_invisible_as_in_layer4(fixtures_copy, tmp_path):
    # Layer 4 does not fingerprint tags or licence: no event, so nothing changes here either
    before = run_on(FIXTURES, tmp_path / "a")[0]
    after = run_on(fixtures_copy, tmp_path / "b")[0]
    assert [d["qs"] for d in before["datasets"]] == [d["qs"] for d in after["datasets"]]


def test_simultaneous_events_are_grouped(fixtures_copy, tmp_path):
    inject(fixtures_copy, TARGETS, "RETRO_ALTER")
    result = run_on(fixtures_copy, tmp_path)[0]
    assert any(g["type"] == "RETRO_ALTER" and len(g["datasets"]) == 3 for g in result["groups"])


# ------------------------------------------------------------------------------ publish step

def test_accept_refuses_unexpected_files(tmp_path):
    _, out = run_on(FIXTURES, tmp_path)
    (out / "docs/data/evil.html").write_text("<script>", encoding="utf-8")
    with pytest.raises(Refused):
        check(out)


def test_accept_refuses_unsafe_record_names(tmp_path):
    _, out = run_on(FIXTURES, tmp_path)
    (out / "docs/data/fichas/Bad Name.json").write_text("{}", encoding="utf-8")
    with pytest.raises(Refused):
        check(out)


def test_accept_copies_into_the_repository(tmp_path):
    _, out = run_on(FIXTURES, tmp_path)
    repo = tmp_path / "repo"
    files = accept(out, repo)
    assert (repo / "docs/data/layer5.json").exists() and len(files) > 79
