# 5L-TEP Layer 5: Governance and Publication

[Leia em português](LEIAME.md) · [Dashboard](https://lsp3cesarschool.github.io/5ltep-layer5-recife/) ·
![Layer 5](https://img.shields.io/endpoint?url=https%3A%2F%2Flsp3cesarschool.github.io%2F5ltep-layer5-recife%2Fdata%2Fstatus.json)

Layer 5 of the Five-Layer Trust Engineering Pyramid (5L-TEP, SOFTENG 2026) for open government data
published on CKAN portals. Every day it reads what Layers 1 to 4 already publish about each dataset of
the portal and puts the evidence side by side: how far each layer reaches, what is missing, the global
quality score (Qs) where the four layers meet, and what can already be checked where they do not.

This instance follows the Recife open data portal (<https://dados.recife.pe.gov.br>), as a cross-context application case: the code of
[5ltep-layer5](https://github.com/lsp3cesarschool/5ltep-layer5) at commit 5afce44, reused by the researcher
with three files changed (see *Running your own instance*). It is not an evaluation of the agency nor a ranking.

## What it does and what it does not

- It **informs**. It never decides whether a dataset is published: that decision, if any, happens in
  the agency's own systems and procedures. Each dataset has a printable, citable record that can be
  attached to such a procedure.
- A **signal** is something to check, never a verdict. A **gap** is missing evidence, never a low score.
- After a report it only **observes** what happened to the data in the next rounds (inferred outcome).
  "Unchanged" does not tell "seen and accepted" from "not seen"; a change is "after the report", never
  "because of it".
- Human review (HitL) is instrumented and ready; numbers appear only if a steward adopts the flow. The
  author of this repository records no steward decision (that would be self-assessment).

## How the score works

The paper defines Qs = 0.3·L1 + 0.3·L2 + 0.2·L3 + 0.2·L4, each Lᵢ being the pass rate of a layer, and a
cutoff θ = 0.85 set by the data owner. On the dashboard θ is called **Nota de corte (θ)**. Alert bands:
critical below 0.70 (the critical floor), alert below the cutoff, info above. Layer 5 keeps this formula
and adds what real portals require:

- **Two flows.** *Complete*: the four layers have valid evidence, Qs is exactly the paper's formula.
  *Partial*: an interval instead of a point, with the missing layers counted as 0 (lower bound) and as 1
  (upper bound). Removing evidence can only widen it; "below the cutoff even in the best case" is
  already useful. A dataset reached only by Layer 4 has no content evaluation and no score.
- **Competence compensates, integrity does not.** A change of the metadata without the portal's
  modification date advancing (RETRO_ALTER, from the Layer 4 taxonomy) multiplies the score by 0.5
  until every layer re-evaluates the dataset. Any factor below the critical floor gives the same
  decisions; 0.5 reads "the evidence counts half until renewed".
- **Evidence expires.** A layer's summary counts for twice its cadence (L1 and L2 14 days, L3 62 days,
  L4 12 hours). A structural change (SCHEMA_DRIFT) after an evaluation takes it out of scope. Bytes that
  changed with no record in the metadata (seen by comparing the SHA-256 the layers record) become a
  finding; the older evaluation still counts, marked as an earlier version (`unrecorded_change` in the
  policy: `finding` by default, or `supersede` to stop counting it).
- **Reaching the cutoff** also requires every layer to have evaluated the current version.
- **Layer 4 in the sum** is the share of successful monitoring cycles of the last 30 days in which the
  dataset had no critical change. A failed cycle is missing coverage, not a failure.

Everything above is a parameter of [`policy.json`](policy.json) (a `dqv:QualityPolicy`), versioned and
changed only by commit.

## Where the numbers come from

Pull over HTTPS, no token between repositories ([`sources.json`](sources.json)):

| Layer | Repository | File read | Unit |
|---|---|---|---|
| L1 Structural contracts | [5ltep-layer1-recife](https://github.com/lsp3cesarschool/5ltep-layer1-recife) | `results/layer1_summary.json`, `results/validation.json` | files per dataset |
| L2 Semantic policies | [5ltep-layer2-recife](https://github.com/lsp3cesarschool/5ltep-layer2-recife) | `docs/data/layer2.json` | checks of the rules that evaluate the dataset |
| L3 Anomaly detection | [5ltep-layer3-recife](https://github.com/lsp3cesarschool/5ltep-layer3-recife) | `results/<profile>/layer3_summary.json` | series × month pairs |
| L4 Observability and provenance | [5ltep-layer4-recife](https://github.com/lsp3cesarschool/5ltep-layer4-recife) | `docs/data/layer4.json`, `cross_check.json`, `data/hash_store.json` | monitoring cycles |

A summary that fails its consistency checks (rates outside [0, 1], counts that do not add up, dates in
the future) is rejected as a whole and shown as a gap with its reason.

## Outputs

- `docs/data/layer5.json`: the aggregate behind the [dashboard](https://lsp3cesarschool.github.io/5ltep-layer5-recife/).
- `docs/data/fichas/<dataset>.json`: one record per dataset, identified by the SHA-256 of its content,
  shown by `ficha.html?d=<dataset>` (print or save as PDF).
- `docs/data/quality.jsonld`: W3C DQV quality measurements computed on the exact dataset state recorded
  by Layer 4 (its content-addressed PROV entity), derived (PROV) from the layer summaries.
- `docs/data/status.json`, `status.pt.json`: badges. `results/history.json`, `results/state.json`:
  history of the rounds and what the inference remembers.

## Schedule and alerts

Daily at 05:10 UTC, after the Layer 4 cross-check (03:30). Layer 5 reads the last published summary of
each layer and never waits for one. The run fails on purpose (and GitHub e-mails the maintainer) on a
new integrity break or a rejected summary, after the data is committed.

## Security

- The job that reads other repositories has a read-only token and only hands over an artifact; the job
  that writes reads nothing external and accepts only the expected files (`src/accept.py`).
- No `${{ }}` inside `run:`; values come in through `env:`.
- Only the standard library at run time; the dashboard escapes all data and follows only http(s) links.

## Running your own instance

1. Fork this repository and edit three files: [`portal.json`](portal.json) (the portal),
   [`sources.json`](sources.json) (where your Layer 1–4 repositories are) and, if your data owner wants,
   [`policy.json`](policy.json). A layer you have not deployed is shown as a structural gap.
2. Enable Actions and Pages (branch `main`, folder `/docs`), then run *Actions → 5L-TEP Layer 5
   Governance → Run workflow*.

This instance was built this way (reuse demonstrated by the researcher).

## Run locally

```bash
python main.py --out build                      # read the layers on GitHub, write into build/
python main.py --fixtures tests/fixtures --now 2026-10-09T18:00:00Z --out build   # offline
python -m pytest tests -q
python -m http.server --directory docs          # preview the dashboard (needs docs/data)
```

Numbers for research come from the GitHub Actions runs; local runs are for testing only.

## Cite

See [`CITATION.cff`](CITATION.cff). Framework: Pinheiro et al., *Towards Trust Engineering in Open Data
Systems*, SOFTENG 2026 (IARIA). Layer 4: Pinheiro and Sérgio, *5LTEP-L4*, WFA/WebMedia 2026.

## License

MIT (code). See [`LICENSE`](LICENSE).
