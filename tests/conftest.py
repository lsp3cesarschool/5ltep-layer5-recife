"""Shared helpers: the real IBAMA summaries in tests/fixtures (downloaded on 2026-10-09), and small
synthetic reports for properties that need exact control."""

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.adapters import DatasetEvidence, LayerReport  # noqa: E402
from src.config import LAYERS, Instance  # noqa: E402
from src.fetch import Fetcher  # noqa: E402
from src.timeutil import parse  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
# the IBAMA configuration the fixtures belong to (an instance build has its own portal.json)
CONFIG = FIXTURES / "instance"
NOW = parse("2026-10-09T18:00:00Z")


@pytest.fixture
def instance():
    return Instance.load(CONFIG)


@pytest.fixture
def fixtures_copy(tmp_path):
    """A writable copy of the fixtures, for fault injection."""
    target = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, target)
    return target


def fetcher_for(folder: Path) -> Fetcher:
    return Fetcher(roots={p.name: p for p in folder.iterdir() if p.is_dir() and p.name != "instance"}, offline=True)


def edit_json(path: Path, change) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def synthetic(rates: dict, evaluated_at="2026-10-08T00:00:00+00:00", generated_at="2026-10-09T12:00:00+00:00",
              events=None, digests=None, name="ds") -> tuple[dict, dict]:
    """Reports for one dataset: rates[layer] = float (evidence), None (reached, no rate) or absent."""
    reports = {}
    for layer in LAYERS:
        rep = LayerReport(layer, "ok", generated_at=generated_at, repository=f"x/{layer}")
        if layer in rates:
            ev = DatasetEvidence(layer, name, rate=rates[layer], evaluated_at=evaluated_at,
                                 reason=None if rates[layer] is not None else "no_rate")
            ev.digests = list((digests or {}).get(layer, []))
            rep.datasets[name] = ev
        reports[layer] = rep
    universe = {name: {"id": "id-1", "title": "T", "events": list(events or [])}}
    return reports, universe
