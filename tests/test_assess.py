"""Properties of the score: the paper's Eq. 1 when complete, an interval when partial, integrity breaks
that cannot be compensated, evidence that expires, and the refinements R1-R3."""

import itertools
import random

import pytest

from conftest import NOW, synthetic
from src.assess import assess_dataset, digest_analysis, partial_band
from src.config import LAYERS, Policy

from conftest import CONFIG

POLICY = Policy.load(CONFIG / "policy.json")
FULL = {"L1": 0.9, "L2": 0.95, "L3": 1.0, "L4": 1.0}


def assess(rates, policy=POLICY, **kw):
    reports, universe = synthetic(rates, **kw)
    digests = digest_analysis(reports, universe, {}, l4_ok=True)
    return assess_dataset("ds", reports, universe, digests, policy, NOW)


def test_complete_without_events_is_equation_1_of_the_paper():
    d = assess(FULL)
    expected = sum(POLICY.weights[layer] * FULL[layer] for layer in LAYERS)
    assert d["qs"]["kind"] == "complete"
    assert d["qs"]["value"] == pytest.approx(expected)
    assert d["qs"]["factor"] == 1
    assert d["qs"]["eligible"] is (expected >= POLICY.cutoff)


def test_partial_is_an_interval_and_never_eligible():
    d = assess({"L2": 0.9, "L4": 1.0})
    assert d["qs"]["kind"] == "partial"
    assert d["qs"]["low"] == pytest.approx(0.3 * 0.9 + 0.2 * 1.0)
    assert d["qs"]["high"] == pytest.approx(0.47 + 0.3 + 0.2)
    assert d["qs"]["coverage"] == pytest.approx(0.5)
    assert d["qs"]["eligible"] is False


def test_only_layer4_means_no_content_evaluation():
    d = assess({"L4": 1.0})
    assert d["qs"]["kind"] == "none"


@pytest.mark.parametrize("missing_reason", [None])
def test_absence_never_counts_as_a_pass(missing_reason):
    # a layer reached without a rate (e.g. no data dictionary) is a gap, not 1 and not 0
    d = assess({"L1": missing_reason, "L2": 0.5, "L4": 1.0})
    assert d["layers"]["L1"]["status"] == "missing"
    assert d["qs"]["low"] == pytest.approx(0.3 * 0.5 + 0.2)


def test_removing_evidence_never_raises_the_lower_bound():
    rng = random.Random(42)
    for _ in range(200):
        rates = {layer: rng.random() for layer in LAYERS}
        full = assess(rates)
        full_low = full["qs"].get("value", full["qs"].get("low"))
        for k in range(1, 4):
            for drop in itertools.combinations(("L1", "L2", "L3"), k):
                kept = {l: r for l, r in rates.items() if l not in drop}
                d = assess(kept)
                if d["qs"]["kind"] == "partial":
                    assert d["qs"]["low"] <= full_low + 1e-12
                    assert d["qs"]["high"] >= full_low - 1e-12


def test_integrity_break_is_not_compensated():
    events = [{"when": "2026-10-09T01:00:00+00:00", "type": "RETRO_ALTER"}]
    d = assess({layer: 1.0 for layer in LAYERS}, events=events)
    assert d["qs"]["factor"] == POLICY.integrity_factor
    assert d["qs"]["value"] == pytest.approx(POLICY.integrity_factor)
    assert d["qs"]["band"] == "critical" and d["qs"]["eligible"] is False


def test_integrity_break_resolves_when_every_content_layer_reevaluates():
    events = [{"when": "2026-10-07T00:00:00+00:00", "type": "RETRO_ALTER"}]
    d = assess({layer: 1.0 for layer in LAYERS}, events=events, evaluated_at="2026-10-08T00:00:00+00:00")
    assert d["qs"]["factor"] == 1


@pytest.mark.parametrize("factor", [0.05, 0.2, 0.5, 0.69])
def test_decisions_do_not_depend_on_the_exact_factor(factor):
    policy = Policy(**{**POLICY.__dict__, "integrity_factor": factor})
    events = [{"when": "2026-10-09T01:00:00+00:00", "type": "RETRO_ALTER"}]
    d = assess({layer: 1.0 for layer in LAYERS}, policy=policy, events=events)
    assert d["qs"]["band"] == "critical" and d["qs"]["eligible"] is False


def test_policy_refuses_a_factor_that_would_change_decisions():
    with pytest.raises(ValueError):
        Policy(**{**POLICY.__dict__, "integrity_factor": 0.75}).check()
    with pytest.raises(ValueError):
        Policy(**{**POLICY.__dict__, "weights": {"L1": 0.5, "L2": 0.5, "L3": 0.2, "L4": 0.2}}).check()


def test_structural_change_after_evaluation_takes_the_evidence_out_of_scope():
    events = [{"when": "2026-10-09T01:00:00+00:00", "type": "SCHEMA_DRIFT"}]
    d = assess(FULL, events=events)
    assert d["layers"]["L1"]["status"] == "out_of_scope"
    assert d["layers"]["L4"]["status"] == "valid"  # the observer is not out of scope
    # every content evaluation predates the change: no content evidence left, and no penalty either
    assert d["qs"]["kind"] == "none" and d["qs"]["factor"] == 1


def test_expired_summary_is_a_gap_by_each_layer_window():
    d = assess(FULL, generated_at="2026-09-01T00:00:00+00:00")  # 38 days old
    assert [d["layers"][l]["status"] for l in LAYERS] == ["expired", "expired", "valid", "expired"]
    assert d["qs"]["kind"] == "partial" and d["qs"]["valid_layers"] == ["L3"]  # L3 is valid for 62 days


def test_r1_documented_change_after_evaluation_blocks_eligibility_only():
    events = [{"when": "2026-10-09T01:00:00+00:00", "type": "CONTENT_MOD"}]
    d = assess({layer: 1.0 for layer in LAYERS}, events=events)
    assert d["qs"]["kind"] == "complete" and d["qs"]["value"] == pytest.approx(1.0)
    assert d["qs"]["eligible"] is False and d["qs"]["note"] == "met_cutoff_previous_version"


def test_r1_same_bytes_after_the_change_keep_the_evaluation_current():
    events = [{"when": "2026-10-08T12:00:00+00:00", "type": "CONTENT_MOD"}]
    same = {"resource_id": "r1", "sha256": "aaa"}
    digests = {"L1": [{**same, "at": "2026-10-08T00:00:00+00:00"}],
               "L2": [{**same, "at": "2026-10-09T00:00:00+00:00"}]}
    reports, universe = synthetic({layer: 1.0 for layer in LAYERS}, events=events, digests=digests)
    reports["L2"].datasets["ds"].evaluated_at = "2026-10-09T00:00:00+00:00"
    reports["L3"].datasets["ds"].evaluated_at = "2026-10-09T00:00:00+00:00"
    dig = digest_analysis(reports, universe, {}, l4_ok=True)
    d = assess_dataset("ds", reports, universe, dig, POLICY, NOW)
    assert d["layers"]["L1"]["current"] is True and d["qs"]["eligible"] is True


CHANGED_BYTES = {"L1": [{"resource_id": "r1", "sha256": "old", "at": "2026-10-03T00:00:00+00:00"}],
                 "L2": [{"resource_id": "r1", "sha256": "new", "at": "2026-10-09T00:00:00+00:00"}]}


def test_r3_default_keeps_the_older_evaluation_as_an_earlier_version():
    d = assess({layer: 1.0 for layer in LAYERS}, digests=CHANGED_BYTES)
    assert d["unrecorded_changes"] and d["qs"]["factor"] == 1  # finding, not an integrity penalty
    assert d["layers"]["L1"]["status"] == "valid" and d["layers"]["L1"]["current"] is False
    assert d["qs"]["kind"] == "complete" and d["qs"]["eligible"] is False  # counts, cannot reach the cutoff


def test_r3_supersede_policy_drops_the_older_evaluation():
    policy = Policy(**{**POLICY.__dict__, "unrecorded_change": "supersede"})
    d = assess({layer: 1.0 for layer in LAYERS}, policy=policy, digests=CHANGED_BYTES)
    assert d["layers"]["L1"]["status"] == "superseded"
    assert d["unrecorded_changes"] and d["qs"]["kind"] == "partial"


def test_r3_documented_change_is_not_an_unrecorded_change():
    digests = {"L1": [{"resource_id": "r1", "sha256": "old", "at": "2026-10-03T00:00:00+00:00"}],
               "L2": [{"resource_id": "r1", "sha256": "new", "at": "2026-10-09T00:00:00+00:00"}]}
    events = [{"when": "2026-10-05T00:00:00+00:00", "type": "CONTENT_MOD"}]
    d = assess({layer: 1.0 for layer in LAYERS}, digests=digests, events=events)
    assert not d["unrecorded_changes"] and d["layers"]["L1"]["status"] == "valid"


def test_partial_bands_say_what_is_already_certain():
    assert partial_band(0.30, 0.60, POLICY) == "critical"
    assert partial_band(0.40, 0.80, POLICY) == "alert"
    assert partial_band(0.86, 0.99, POLICY) == "info_worst_case"
    assert partial_band(0.40, 0.95, POLICY) == "undetermined"
