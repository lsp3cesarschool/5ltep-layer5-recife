"""Instance configuration: portal, sources of the layer summaries and the quality policy."""

import json
from dataclasses import dataclass
from pathlib import Path

LAYERS = ("L1", "L2", "L3", "L4")
CONTENT_LAYERS = ("L1", "L2", "L3")  # layers that examine the data itself; L4 examines its history


def read_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@dataclass(frozen=True)
class Policy:
    version: str
    aggregation: str
    weights: dict
    cutoff: float
    critical_floor: float
    integrity_factor: float
    integrity_types: tuple
    scope_types: tuple
    unrecorded_change: str
    cadence_days: dict
    validity_multiplier: float
    l4_window_days: int
    findings_window_days: int
    simultaneous_event_min_datasets: int

    @classmethod
    def load(cls, path: Path) -> "Policy":
        raw = read_json(path)
        policy = cls(
            version=raw["policy_version"],
            aggregation=raw["aggregation"],
            weights=dict(raw["weights"]),
            cutoff=float(raw["cutoff"]),
            critical_floor=float(raw["critical_floor"]),
            integrity_factor=float(raw["integrity_factor"]),
            integrity_types=tuple(raw["integrity_types"]),
            scope_types=tuple(raw["scope_types"]),
            unrecorded_change=raw.get("unrecorded_change", "finding"),
            cadence_days=dict(raw["cadence_days"]),
            validity_multiplier=float(raw["validity_multiplier"]),
            l4_window_days=int(raw["l4_window_days"]),
            findings_window_days=int(raw["findings_window_days"]),
            simultaneous_event_min_datasets=int(raw["simultaneous_event_min_datasets"]),
        )
        policy.check()
        return policy

    def check(self) -> None:
        """Refuse a policy that would make the score meaningless."""
        if self.aggregation != "arithmetic":
            raise ValueError("only the arithmetic aggregation of the paper is implemented")
        if set(self.weights) != set(LAYERS) or abs(sum(self.weights.values()) - 1) > 1e-9:
            raise ValueError("weights must cover L1-L4 and sum to 1")
        if not 0 < self.critical_floor < self.cutoff <= 1:
            raise ValueError("expected 0 < critical_floor < cutoff <= 1")
        # Below the critical floor, one integrity break always lands a perfect dataset in CRITICAL:
        # decisions then do not depend on the exact factor (see README).
        if not 0 < self.integrity_factor < self.critical_floor:
            raise ValueError("integrity_factor must be above 0 and below critical_floor")
        if self.unrecorded_change not in ("finding", "supersede"):
            raise ValueError("unrecorded_change must be 'finding' or 'supersede'")
        if set(self.cadence_days) != set(LAYERS):
            raise ValueError("cadence_days must cover L1-L4")

    def validity_days(self, layer: str) -> float:
        return self.cadence_days[layer] * self.validity_multiplier

    def as_dict(self) -> dict:
        return {
            "policy_version": self.version, "aggregation": self.aggregation, "weights": self.weights,
            "cutoff": self.cutoff, "critical_floor": self.critical_floor,
            "integrity_factor": self.integrity_factor, "integrity_types": list(self.integrity_types),
            "scope_types": list(self.scope_types), "unrecorded_change": self.unrecorded_change, "cadence_days": self.cadence_days,
            "validity_days": {layer: self.validity_days(layer) for layer in LAYERS},
            "l4_window_days": self.l4_window_days, "findings_window_days": self.findings_window_days,
            "simultaneous_event_min_datasets": self.simultaneous_event_min_datasets,
        }


@dataclass(frozen=True)
class Instance:
    root: Path
    portal: dict
    sources: dict
    policy: Policy

    @classmethod
    def load(cls, root: Path) -> "Instance":
        return cls(root=root, portal=read_json(root / "portal.json"),
                   sources=read_json(root / "sources.json")["layers"], policy=Policy.load(root / "policy.json"))

    @property
    def host(self) -> str:
        return self.portal["portal_url"].split("://", 1)[1].rstrip("/")

    @property
    def repository(self) -> str:
        return self.portal["repository"]
