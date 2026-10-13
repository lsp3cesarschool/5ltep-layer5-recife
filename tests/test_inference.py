"""Inferred steward outcome across rounds, and lost evidence (R6). Observations, never decisions."""

from conftest import NOW
from src.config import LAYERS
from src.inference import infer
from src.timeutil import parse

T0 = parse("2026-10-01T05:10:00Z")


def dataset(name="ds", evaluated="2026-10-01T00:00:00+00:00", signal=3, last_change=None, l1_rate=0.5):
    layers = {layer: {"rate": 1.0, "reason": None, "evaluated_at": evaluated, "signals": []} for layer in LAYERS}
    layers["L1"]["rate"] = l1_rate
    layers["L1"]["reason"] = None if l1_rate is not None else "l1_level0"
    if signal:
        layers["L2"]["signals"] = [{"key": "L2:rule-a", "count": signal, "en": "x", "pt": "x"}]
    return {"name": name, "last_change": last_change, "layers": layers}


def round_two(second, digests_before=None, digests_after=None, removed=None):
    first = infer({}, [dataset()], digests_before or {}, [], T0)
    return infer(first["state"], second, digests_after or {}, removed or [], NOW)


def outcome(result):
    return {(o["dataset"], o["key"]): o["outcome"] for o in result["observed"]}


def test_first_round_only_reports():
    r = infer({}, [dataset()], {}, [], T0)
    assert r["summary"]["open_by_status"]["reported"] == 1 and not r["observed"]


def test_not_reassessed_until_the_layer_runs_again():
    r = round_two([dataset()])
    assert outcome(r)[("ds", "L2:rule-a")] == "not_reassessed"


def test_unchanged_data_and_signal_is_status_quo():
    r = round_two([dataset(evaluated="2026-10-08T00:00:00+00:00")])
    assert outcome(r)[("ds", "L2:rule-a")] == "unchanged"


def test_signal_gone_after_data_changed_is_remediation_observed():
    r = round_two([dataset(evaluated="2026-10-08T00:00:00+00:00", signal=0, last_change="2026-10-05T00:00:00+00:00")])
    assert outcome(r)[("ds", "L2:rule-a")] == "remediated_observed"
    assert r["summary"]["closed"]["remediated_observed"] == 1
    assert r["summary"]["median_days_to_first_change"] is not None


def test_signal_gone_without_data_change_is_not_called_remediation():
    r = round_two([dataset(evaluated="2026-10-08T00:00:00+00:00", signal=0)])
    assert outcome(r)[("ds", "L2:rule-a")] == "cleared_without_data_change"


def test_changed_bytes_count_as_data_change():
    before = {"r1": {"sha256": "a", "dataset": "ds", "at": "2026-09-30T00:00:00+00:00", "layer": "L2"}}
    after = {"r1": {"sha256": "b", "dataset": "ds", "at": "2026-10-08T00:00:00+00:00", "layer": "L2"}}
    r = round_two([dataset(evaluated="2026-10-08T00:00:00+00:00")], before, after)
    assert outcome(r)[("ds", "L2:rule-a")] == "changed_signal_persists"


def test_dataset_no_longer_listed_is_withdrawal_observed():
    r = round_two([], removed=["ds"])
    assert outcome(r)[("ds", "L2:rule-a")] == "withdrawn_observed"


def test_r6_lost_evidence_becomes_a_finding():
    r = round_two([dataset(evaluated="2026-10-08T00:00:00+00:00", l1_rate=None)])
    assert "L1" in r["lost"]["ds"] and r["lost"]["ds"]["L1"]["reason"] == "l1_level0"


def test_unavailable_layer_is_not_lost_evidence():
    d = dataset(evaluated="2026-10-08T00:00:00+00:00", l1_rate=None)
    d["layers"]["L1"]["reason"] = "fetch_failed"
    r = round_two([d])
    assert "ds" not in r["lost"]
