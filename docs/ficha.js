// Dataset record ("ficha"): renders data/fichas/<name>.json. Its id is the SHA-256 of its content,
// so a process (for example in the agency's own system) can cite exactly this version.
"use strict";

(() => {
  const { lang, t, num, int, date, dateTime, el, bandStatus, ruler, qsText, langSwitch, tooltip } = L5;
  const TEXT = {
    en: {
      dash: "← Dashboard", eyebrow: "5L-TEP · Layer 5 · Dataset record", print: "Print / save as PDF", json: "Download JSON",
      id_h: "Identification", qs_h: "Quality score", layers_h: "Evidence of each layer", check_h: "What can already be checked",
      outcomes_h: "After the report: what was observed", sources_h: "Sources and policy",
      outcomes_note: "Observations after the report, with no attribution of cause. The publication decision, if any, happens in the agency's own systems.",
      record_id: "Record id", generated: "Generated", portal_page: "Dataset on the portal", cite: "How to cite",
      entity: "Dataset state (Layer 4, PROV)", last_change: "Last recorded change",
      kind: "Flow", coverage: "Coverage (weight of valid layers)", factor: "Integrity factor", interval_note: "Interval: missing layers counted as 0 (lower bound) and as 1 (upper bound).",
      missing_layers: "Missing layers", col_layer: "Layer", col_status: "Evidence", col_rate: "Pass rate",
      col_evaluated: "Evaluated", col_current: "Current version", yes: "yes", no: "no", none: "Nothing to check was reported.",
      no_outcomes: "No signal followed yet.", since: "first reported {d}", file: "summary", commit: "commit",
      p_cutoff: "Nota de corte (θ)", p_floor: "Critical floor", p_weights: "Weights", p_version: "Policy version",
      not_found: "No record for this dataset.", no_change: "none recorded in the metadata since monitoring began",
    },
    pt: {
      dash: "← Painel", eyebrow: "5L-TEP · Camada 5 · Ficha do conjunto", print: "Imprimir / salvar em PDF", json: "Baixar JSON",
      id_h: "Identificação", qs_h: "Nota de qualidade", layers_h: "Evidência de cada camada", check_h: "O que já dá para conferir",
      outcomes_h: "Depois do relato: o que se observou", sources_h: "Fontes e política",
      outcomes_note: "Observações posteriores ao relato, sem atribuição de causa. A decisão de publicação, se houver, acontece nos sistemas do próprio órgão.",
      record_id: "Identificador da ficha", generated: "Gerada em", portal_page: "Conjunto no portal", cite: "Como citar",
      entity: "Estado do conjunto (Camada 4, PROV)", last_change: "Última mudança registrada",
      kind: "Fluxo", coverage: "Cobertura (peso das camadas válidas)", factor: "Fator de integridade", interval_note: "Intervalo: camadas ausentes contadas como 0 (limite inferior) e como 1 (limite superior).",
      missing_layers: "Camadas ausentes", col_layer: "Camada", col_status: "Evidência", col_rate: "Taxa de aprovação",
      col_evaluated: "Avaliada em", col_current: "Versão atual", yes: "sim", no: "não", none: "Nada a conferir foi relatado.",
      no_outcomes: "Nenhum sinal acompanhado ainda.", since: "relatado pela primeira vez em {d}", file: "resumo", commit: "commit",
      p_cutoff: "Nota de corte (θ)", p_floor: "Piso crítico", p_weights: "Pesos", p_version: "Versão da política",
      not_found: "Não há ficha para este conjunto.", no_change: "nenhuma registrada nos metadados desde o início do monitoramento",
    },
  };
  const tt = (k, vars) => { let s = (TEXT[lang] || TEXT.en)[k] || TEXT.en[k] || t(k, vars); for (const [a, b] of Object.entries(vars || {})) s = s.replace(`{${a}}`, b); return s; };
  const kv = (box, pairs) => document.getElementById(box).replaceChildren(...pairs.flatMap(([k, v]) => [el("dt", {}, k), el("dd", {}, v)]));

  async function main() {
    langSwitch(); tooltip();
    document.querySelectorAll("[data-i18n]").forEach((n) => { n.textContent = tt(n.dataset.i18n); });
    document.getElementById("dash-link").href = `./?lang=${lang}`;
    document.getElementById("print").addEventListener("click", () => window.print());
    const name = new URLSearchParams(location.search).get("d") || "";
    if (!/^[a-z0-9][a-z0-9_.-]{0,199}$/.test(name)) { document.getElementById("title").textContent = tt("not_found"); return; }
    const path = `data/fichas/${name}.json`;
    document.getElementById("json-link").href = path;
    document.getElementById("json-link").setAttribute("download", `${name}.json`);
    let f;
    try { f = await (await fetch(path, { cache: "no-cache" })).json(); }
    catch (e) { document.getElementById("title").textContent = tt("not_found"); return; }
    const d = f.dataset;
    document.title = `${d.title || d.name} · 5L-TEP L5`;
    document.getElementById("title").textContent = d.title || d.name;
    document.getElementById("subtitle").textContent = `${f.portal.title} · ${d.name}`;

    kv("ident", [
      [tt("record_id"), el("span", { class: "mono" }, f.ficha.id)],
      [tt("generated"), dateTime(f.generated_at)],
      [tt("portal_page"), el("a", { href: d.portal_page, target: "_blank", rel: "noopener" }, d.portal_page)],
      [tt("entity"), d.entity ? el("span", { class: "mono" }, d.entity) : "—"],
      [tt("last_change"), d.last_change ? `${dateTime(d.last_change)} (${d.last_type || ""})` : tt("no_change")],
      [tt("cite"), (f.ficha.how_to_cite || {})[lang] || f.ficha.how_to_cite.en],
    ]);

    const qs = f.qs, b = bandStatus(qs, f.policy);
    const qsBox = document.getElementById("qs");
    qsBox.replaceChildren(
      el("div", { class: "qs" }, ruler(qs, f.policy, 320), el("strong", {}, qsText(qs))),
      el("p", {}, el("span", { class: `status ${b.cls}` }, `${b.icon} ${b.text}`), el("span", {}, ` — ${b.long}`),
        qs.note === "met_cutoff_previous_version" ? el("span", { class: "muted" }, ` · ${t("previous_version", { d: date(qs.last_change) })}`) : null),
      el("dl", { class: "kv" },
        el("dt", {}, tt("kind")), el("dd", {}, t("kind_" + qs.kind)),
        el("dt", {}, tt("coverage")), el("dd", {}, num(qs.coverage)),
        el("dt", {}, tt("factor")), el("dd", {}, num(qs.factor)),
        qs.missing_layers ? el("dt", {}, tt("missing_layers")) : null,
        qs.missing_layers ? el("dd", {}, qs.missing_layers.join(", ")) : null),
      qs.kind === "partial" ? el("p", { class: "muted small" }, tt("interval_note")) : null);

    const rows = ["L1", "L2", "L3", "L4"].map((l) => {
      const c = f.layers[l];
      return el("tr", {},
        el("td", {}, el("strong", {}, l), " ", el("span", { class: "muted" }, t(l))),
        el("td", {}, t("status_" + c.status), c.reason ? el("div", { class: "muted small" }, t("r_" + c.reason)) : null),
        el("td", { class: "num" }, c.rate != null ? num(c.rate, 4) : "—"),
        el("td", {}, c.evaluated_at ? date(c.evaluated_at) : "—"),
        el("td", {}, c.current == null ? "—" : c.current ? tt("yes") : tt("no")));
    });
    document.getElementById("layers").replaceChildren(
      el("thead", {}, el("tr", {}, ...["col_layer", "col_status", "col_rate", "col_evaluated", "col_current"].map((k) => el("th", { class: k === "col_rate" ? "num" : null }, tt(k))))),
      el("tbody", {}, rows));

    const items = f.findings.map((x) => el("li", {}, el("span", { class: "chip" }, x.layer), el("strong", {}, t("k_" + x.kind)), " · ",
      (lang === "pt" ? x.pt : x.en) || "", x.when ? el("span", { class: "muted" }, ` (${date(x.when)})`) : null));
    document.getElementById("findings").replaceChildren(...(items.length ? items : [el("li", { class: "muted" }, tt("none"))]));

    const outs = [...(f.outcomes.open || []), ...(f.outcomes.closed || [])].map((o) => el("li", {},
      el("span", { class: "chip" }, o.layer), el("strong", {}, t("o_" + (o.outcome || o.status))), " · ",
      (lang === "pt" ? o.pt : o.en) || o.key, el("span", { class: "muted" }, ` (${tt("since", { d: date(o.first_reported) })})`)));
    document.getElementById("outcomes").replaceChildren(...(outs.length ? outs : [el("li", { class: "muted" }, tt("no_outcomes"))]));

    const src = Object.entries(f.sources).map(([l, s]) => el("li", {}, el("strong", {}, l), ` · ${s.status}`,
      s.generated_at ? ` · ${dateTime(s.generated_at)}` : "",
      ...(s.files || []).map((file) => el("span", {}, " · ", el("a", { href: file.url, target: "_blank", rel: "noopener" }, file.path),
        file.commit ? el("span", { class: "mono" }, ` @${file.commit.sha.slice(0, 7)}`) : null))));
    document.getElementById("sources").replaceChildren(...src);
    const p = f.policy;
    kv("policy", [[tt("p_cutoff"), num(p.cutoff)], [tt("p_floor"), num(p.critical_floor)],
      [tt("p_weights"), Object.entries(p.weights).map(([l, w]) => `${l} ${num(w)}`).join(" · ")], [tt("p_version"), p.policy_version]]);
    document.getElementById("notice").textContent = f.notice[lang] || f.notice.en;
    document.getElementById("footer").textContent = `${f.ficha.id} · ${f.engine.repository}${f.engine.commit ? "@" + f.engine.commit.slice(0, 7) : ""}`;
  }
  main();
})();
