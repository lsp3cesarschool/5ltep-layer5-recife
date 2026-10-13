"""Fail the run on purpose when something needs a person: GitHub then e-mails the maintainer, at no
cost and with no mail server (the same mechanism as Layers 3 and 4). The data is already committed.

Fails on: a new integrity break (RETRO_ALTER) since the previous round, or a layer summary that was
rejected as inconsistent or could not be read. A layer not deployed for this portal is not a failure.

Usage: python -m src.alerts docs/data/layer5.json
"""

import json
import sys
from pathlib import Path


def main(argv=None) -> int:
    path = Path((argv if argv is not None else sys.argv[1:])[0])
    alerts = json.loads(path.read_text(encoding="utf-8"))["alerts"]
    failed = False
    for event in alerts["new_integrity_events"]:
        print(f"::error::{event['dataset']}: {event['type']} at {event['when']} "
              "(metadata changed without the modification date advancing)")
        failed = True
    for layer in alerts["unavailable_layers"]:
        print(f"::error::{layer['layer']} summary {layer['status']} ({layer['reason']}): {layer['detail']}")
        failed = True
    if not failed:
        print("No new integrity alert; every available summary was consistent.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
