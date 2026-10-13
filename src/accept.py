"""Publish step: check the folder produced by the read-only job and copy it into the repository.

The job that reads the other layers' public files has a read-only token and only hands over an
artifact; this step (with write permission, without reading anything external) accepts only the
expected paths, valid JSON, safe file names and bounded sizes, then replaces the outputs.

Usage: python -m src.accept <artifact-folder> [<repository-folder>]
"""

import json
import re
import shutil
import sys
from pathlib import Path

FIXED = {"docs/data/layer5.json", "docs/data/status.json", "docs/data/status.pt.json",
         "docs/data/quality.jsonld", "results/state.json", "results/history.json"}
FICHA = re.compile(r"^docs/data/fichas/[a-z0-9][a-z0-9_.-]{0,199}\.json$")
MAX_FILE = 20 * 1024 * 1024
MAX_FICHAS = 20000


class Refused(Exception):
    pass


def check(folder: Path) -> list[str]:
    files = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file())
    unexpected = [f for f in files if f not in FIXED and not FICHA.match(f)]
    if unexpected:
        raise Refused(f"unexpected files: {unexpected[:5]}")
    missing = sorted(FIXED - set(files))
    if missing:
        raise Refused(f"missing files: {missing}")
    if sum(1 for f in files if f.startswith("docs/data/fichas/")) > MAX_FICHAS:
        raise Refused("too many records")
    for f in files:
        path = folder / f
        if path.is_symlink() or path.stat().st_size > MAX_FILE:
            raise Refused(f"{f}: symlink or too large")
        data = json.loads(path.read_text(encoding="utf-8"))
        if f == "docs/data/layer5.json" and (data.get("layer") != 5 or not isinstance(data.get("datasets"), list)):
            raise Refused("layer5.json does not look like a Layer 5 aggregate")
        if f.startswith("docs/data/fichas/") and not str(data.get("ficha", {}).get("id", "")).startswith("sha256:"):
            raise Refused(f"{f}: record without its sha256 id")
    return files


def accept(folder: Path, repo: Path) -> list[str]:
    files = check(folder)
    fichas = repo / "docs" / "data" / "fichas"
    if fichas.exists():
        shutil.rmtree(fichas)
    for f in files:
        dest = repo / f
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(folder / f, dest)
    return files


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    folder = Path(argv[0])
    repo = Path(argv[1]) if len(argv) > 1 else Path(".")
    try:
        files = accept(folder, repo)
    except (Refused, ValueError) as err:
        print(f"::error::artifact refused: {err}")
        return 1
    print(f"accepted {len(files)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
