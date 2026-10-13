"""README and LEIAME walk together; texts keep the humility premise; workflows keep the security rules."""

import re

import pytest

from conftest import ROOT

README = (ROOT / "README.md").read_text(encoding="utf-8")
LEIAME = (ROOT / "LEIAME.md").read_text(encoding="utf-8")


def headings(text):
    return re.findall(r"^#{1,6} ", text, flags=re.M)


def code_blocks(text):
    return re.findall(r"```.*?```", text, flags=re.S)


def test_readme_and_leiame_have_the_same_structure():
    assert len(headings(README)) == len(headings(LEIAME))
    assert headings(README) == headings(LEIAME)


def test_readme_and_leiame_have_the_same_code_blocks():
    assert code_blocks(README) == code_blocks(LEIAME)


def test_readme_and_leiame_link_to_each_other():
    assert "(LEIAME.md)" in README.split("\n\n")[1]
    assert "(README.md)" in LEIAME.split("\n\n")[1]


def test_the_cutoff_is_named_on_the_dashboard_and_in_both_texts():
    assert "Nota de corte (θ)" in README and "Nota de corte (θ)" in LEIAME
    assert "Nota de corte (θ)" in (ROOT / "docs" / "common.js").read_text(encoding="utf-8")


FORBIDDEN = [
    r"gestores validar", r"será adotad", r"a ANEEL utiliza", r"o IBAMA (adotou|utiliza)",
    r"managers will validate", r"will be adopted", r"ANEEL uses", r"approved for publication",
    r"aprovado para publica", r"\bfraud", r"\bfraude",
]
TEXTS = ["README.md", "LEIAME.md", "docs/app.js", "docs/ficha.js", "docs/common.js", "src/report.py"]


@pytest.mark.parametrize("name", TEXTS)
def test_texts_keep_the_humility_premise(name):
    text = (ROOT / name).read_text(encoding="utf-8")
    for pattern in FORBIDDEN:
        assert not re.search(pattern, text, flags=re.I), f"{name}: '{pattern}'"


@pytest.mark.parametrize("workflow", sorted((ROOT / ".github" / "workflows").glob("*.yml")), ids=lambda p: p.name)
def test_no_expression_inside_run(workflow):
    text = workflow.read_text(encoding="utf-8")
    for block in re.findall(r"run: \|\n((?:\s{10,}.*\n)+)|run: (.*)", text):
        body = "".join(block)
        assert "${{" not in body, f"{workflow.name}: expression inside run:"


def test_the_job_that_reads_does_not_write():
    text = (ROOT / ".github" / "workflows" / "layer5.yml").read_text(encoding="utf-8")
    aggregate = text.split("  publish:")[0].split("  aggregate:")[1]
    assert "contents: read" in aggregate and "contents: write" not in aggregate
    assert "git push" not in aggregate
