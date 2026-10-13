// Layer 5 dashboard: reads data/layer5.json (written by the daily workflow) and draws it.
"use strict";

(() => {
  const { lang, t, num, int, date, dateTime, el, rateBin, bandStatus, ruler, langSwitch, tooltip, repo } = L5;

  const TEXT = {
    en: {
      run: "Aggregate now ↗", policy_btn: "Policy ↗",
      intro: "Every day this repository reads what Layers 1 to 4 already publish about each dataset of the portal and puts it side by side: how far each layer reaches, what is missing, the quality score where the four layers meet, and what can already be checked where they do not.",
      sources_h: "Layers and their evidence",
      sources_note: "Each layer runs on its own schedule. Its last summary counts as evidence for twice its cadence; after that it becomes a gap, never a low score.",
      coverage_h: "How far each layer reaches",
      coverage_note: "Full bar = all datasets of the portal. Solid: the layer evaluated the dataset and the evidence is valid. Hatched: reached, but the evidence is not valid now (expired, out of scope or superseded). Empty: not evaluated by this layer.",
      combos_h: "Which layers meet on each dataset",
      combos_note: "Number of datasets for each combination of layers with valid evidence. The complete score of the paper needs the four of them.",
      matrix_h: "Datasets × layers",
      matrix_note: "Each cell is the pass rate of the layer for the dataset (the number is written; darker = higher). A hatched cell is missing evidence, with its reason. Score: a dot when the four layers are present; otherwise an interval, from the missing layers counted as 0 to counted as 1. The black tick is the Nota de corte (θ), the grey one the critical floor.",
      check_h: "What can already be checked",
      check_note: "Signals are things to check, never verdicts. A missing layer does not stop anyone from checking and fixing what is confirmed.",
      outcomes_h: "After the report: what was observed",
      outcomes_note: "Layer 5 informs; the publication decision, if any, happens in the agency's own systems. In the next rounds it only observes whether the data changed and whether each signal is still there. These are observations after the report, with no attribution of cause; \"unchanged\" does not tell \"seen and accepted\" from \"not seen\".",
      outcomes_open: "Signals followed", hitl_h: "Human review (HitL)",
      policy_h: "How the score works",
      policy_note: "Qs = sum of weight × pass rate of the four layers (SOFTENG 2026). Competence compensates, integrity does not: a change of the metadata without the modification date advancing (RETRO_ALTER) multiplies the score by the integrity factor until every layer re-evaluates the dataset. The policy is a versioned file set by the data owner.",
      table_view: "Table view", search: "Search datasets",
      f_all: "All datasets", f_complete: "Complete (four layers)", f_partial: "Partial", f_none: "No content evaluation",
      f_findings: "With something to check", f_integrity: "With an integrity alert",
      s_coverage: "Most evidence first", s_worst: "Lowest score first", s_name: "By name",
      click_note: "Click a dataset to open its record (printable, citable).", all_kinds: "All kinds",
      tile_datasets: "Datasets in the portal", tile_datasets_note: "all datasets listed in the portal catalogue",
      tile_datasets_tip: "Every dataset the portal lists today (CKAN catalogue). Each one is shown below, whatever the layers reached.",
      tile_complete: "With a complete score", tile_complete_note: "the four layers evaluated it",
      tile_complete_tip: "Datasets on which the four layers have valid evidence: only these get the score of the paper as a single number, and only these can reach the cutoff.",
      tile_partial: "With a partial score", tile_partial_note: "an interval: some layer has not evaluated it",
      tile_partial_tip: "At least one of the layers that examine the data (L1-L3) evaluated the dataset, but not all four. The score is an interval: from the missing layers at 0% to the missing layers at 100%.",
      tile_below: "Already known below the cutoff", tile_below_note: "would not reach {c} even in the best case",
      tile_below_tip: "Datasets whose score cannot reach the Nota de corte (θ) {c} even if every missing layer passed 100%. This is already known, with no need to wait for the missing layers.",
      tile_none: "No evaluation of the content", tile_none_note: "no layer that examines the data reached them",
      tile_none_tip: "None of Layers 1-3 (schema, rules, anomalies) has valid evidence on these datasets, so there is no score. They are still followed (Layer 4 records their changes).",
      tile_integrity: "Integrity alerts", tile_integrity_note: "metadata changed with no record of it",
      tile_integrity_tip: "Datasets whose metadata changed without the portal's modification date advancing (RETRO_ALTER), not yet re-evaluated. The score is multiplied by the integrity factor until then.",
      formula_h: "How the score (Qs) is reached", readings_h: "Result in this portal",
      term_reach: "valid on {v} of {n} datasets", term_tip: "{l} weighs {w}: its pass rate on the dataset times {w}. Valid evidence on {v} of {n} datasets.",
      cutoff_meaning: "score a dataset needs to reach (set by the data owner)", floor_meaning: "below it the reading is critical",
      f_li: "L1…L4", li_meaning: "pass rate of each layer on the dataset, from 0 (nothing passes) to 1 (everything passes)",
      f_missing: "Missing layer", missing_meaning: "counted as 0 and as 1: the score becomes an interval, never an invented number",
      factor_meaning: "the score is multiplied by {f} while a metadata change with no record (RETRO_ALTER) has not been re-evaluated",
      example: "Real example:", example_partial: "[0…1] = layer with no valid evidence on this dataset ({m}).", no_example: "No dataset has a score yet.",
      col_reading: "Reading", col_count: "Datasets", col_meaning: "What it means",
      m_complete_eligible: "four layers, current version, score at or above {c}", m_complete_previous: "it reached {c}, but the data changed after the evaluation",
      m_complete_info: "four layers, score at or above {c}", m_complete_alert: "four layers, score between {f} and {c}", m_complete_critical: "four layers, score below {f}",
      m_partial_worst_ok: "reaches {c} even with the missing layers at 0%", m_partial_undetermined: "may or may not reach {c}: depends on the missing layers",
      m_partial_alert: "does not reach {c} even with the missing layers at 100%", m_partial_critical: "stays below {f} even with the missing layers at 100%",
      m_none_integrity: "no score, with an integrity alert", m_none: "no layer that examines the data reached it: no score",
      col_layer: "Layer", col_status: "Status", col_generated: "Last summary", col_validity: "Age / valid for",
      col_reached: "Reached", col_valid: "Valid", col_links: "Links", dashboard: "dashboard ↗", rerun: "run ↗",
      days: "{n} d", ok: "available", missing: "not deployed", rejected: "rejected", error: "read failed",
      col_dataset: "Dataset", col_qs: "Score", col_band: "Reading", col_check: "To check",
      leg_valid: "valid evidence", leg_reached: "reached, evidence not valid now", leg_gap: "not evaluated",
      leg_hatch: "missing evidence (reason written)", combo_all4: "all four layers", combo_none: "no dataset",
      more: "Show {n} more", col_kind: "Kind", col_what: "What", col_when: "When",
      o_open: "Open signals", o_closed: "Closed (observed)", o_median: "Median days to the first change",
      o_rounds: "Rounds observed", o_none: "—",
      hitl_status: "Status", hitl_awaiting: "instrumented, awaiting a steward", hitl_collecting: "collecting",
      hitl_issues: "Review issues (Layer 3)", hitl_decided: "Decided", hitl_agreement: "Human–AI agreement",
      p_weights: "Weights", p_cutoff: "Nota de corte (θ)", p_floor: "Critical floor", p_factor: "Integrity factor",
      p_validity: "Evidence valid for", p_window: "Layer 4 window", p_version: "Policy version",
      footer: "Generated {g} · engine ",
      cov_text: "{v} valid · {r} reached, not valid now · {g} not evaluated",
    },
    pt: {
      run: "Agregar agora ↗", policy_btn: "Política ↗",
      intro: "Todo dia este repositório lê o que as Camadas 1 a 4 já publicam sobre cada conjunto de dados do portal e coloca lado a lado: até onde cada camada chega, o que falta, a nota de qualidade onde as quatro se encontram e o que já dá para conferir onde não se encontram.",
      sources_h: "As camadas e sua evidência",
      sources_note: "Cada camada roda no próprio calendário. O último resumo dela vale como evidência por duas vezes a sua cadência; depois disso vira lacuna, nunca nota baixa.",
      coverage_h: "Até onde cada camada chega",
      coverage_note: "Barra cheia = todos os conjuntos do portal. Sólido: a camada avaliou o conjunto e a evidência é válida. Hachurado: alcançado, mas a evidência não vale agora (vencida, fora do escopo ou superada). Vazio: não avaliado por esta camada.",
      combos_h: "Quais camadas se encontram em cada conjunto",
      combos_note: "Número de conjuntos para cada combinação de camadas com evidência válida. A nota completa do artigo precisa das quatro.",
      matrix_h: "Conjuntos × camadas",
      matrix_note: "Cada célula é a taxa de aprovação da camada para o conjunto (o número está escrito; mais escuro = maior). Célula hachurada é falta de evidência, com o motivo. Nota: um ponto quando as quatro camadas estão presentes; senão, um intervalo, das camadas ausentes contadas como 0 até contadas como 1. O traço preto é a Nota de corte (θ); o cinza, o piso crítico.",
      check_h: "O que já dá para conferir",
      check_note: "Sinais são itens a conferir, nunca vereditos. Uma camada ausente não impede ninguém de conferir e corrigir o que se confirmar.",
      outcomes_h: "Depois do relato: o que se observou",
      outcomes_note: "A Camada 5 informa; a decisão de publicação, se houver, acontece nos sistemas do próprio órgão. Nas rodadas seguintes ela só observa se os dados mudaram e se cada sinal continua. São observações posteriores ao relato, sem atribuição de causa; \"sem mudança\" não distingue \"viu e aceitou\" de \"não viu\".",
      outcomes_open: "Sinais acompanhados", hitl_h: "Revisão humana (HitL)",
      policy_h: "Como a nota funciona",
      policy_note: "Qs = soma de peso × taxa de aprovação das quatro camadas (SOFTENG 2026). Competência compensa, integridade não: uma mudança dos metadados sem a data de modificação avançar (RETRO_ALTER) multiplica a nota pelo fator de integridade até todas as camadas reavaliarem o conjunto. A política é um arquivo versionado definido pelo responsável pelos dados (data owner).",
      table_view: "Ver como tabela", search: "Buscar conjuntos",
      f_all: "Todos os conjuntos", f_complete: "Completos (quatro camadas)", f_partial: "Parciais", f_none: "Sem avaliação de conteúdo",
      f_findings: "Com algo a conferir", f_integrity: "Com alerta de integridade",
      s_coverage: "Mais evidência primeiro", s_worst: "Menor nota primeiro", s_name: "Por nome",
      click_note: "Clique num conjunto para abrir a ficha (imprimível e citável).", all_kinds: "Todos os tipos",
      tile_datasets: "Conjuntos no portal", tile_datasets_note: "todos os listados no catálogo do portal",
      tile_datasets_tip: "Todos os conjuntos que o portal lista hoje (catálogo CKAN). Cada um aparece abaixo, seja qual for o alcance das camadas.",
      tile_complete: "Com nota completa", tile_complete_note: "as quatro camadas o avaliaram",
      tile_complete_tip: "Conjuntos em que as quatro camadas têm evidência válida: só eles recebem a nota do artigo como um número único, e só eles podem atingir a nota de corte.",
      tile_partial: "Com nota parcial", tile_partial_note: "um intervalo: alguma camada ainda não o avaliou",
      tile_partial_tip: "Ao menos uma das camadas que examinam os dados (L1-L3) avaliou o conjunto, mas não as quatro. A nota é um intervalo: das camadas ausentes em 0% até as camadas ausentes em 100%.",
      tile_below: "Já se sabe: abaixo da nota de corte", tile_below_note: "não chegaria a {c} nem no melhor caso",
      tile_below_tip: "Conjuntos cuja nota não chega à Nota de corte (θ) {c} nem que todas as camadas ausentes aprovassem 100%. Isso já se sabe, sem esperar as camadas que faltam.",
      tile_none: "Sem avaliação do conteúdo", tile_none_note: "nenhuma camada que examina os dados chegou a eles",
      tile_none_tip: "Nenhuma das Camadas 1-3 (esquema, regras, anomalias) tem evidência válida sobre estes conjuntos, então não há nota. Eles continuam acompanhados (a Camada 4 registra as mudanças).",
      tile_integrity: "Alertas de integridade", tile_integrity_note: "metadados alterados sem registro",
      tile_integrity_tip: "Conjuntos cujos metadados mudaram sem a data de modificação do portal avançar (RETRO_ALTER), ainda não reavaliados. Até lá, a nota é multiplicada pelo fator de integridade.",
      formula_h: "Como se chega à nota (Qs)", readings_h: "Resultado neste portal",
      term_reach: "válida em {v} de {n} conjuntos", term_tip: "{l} pesa {w}: a taxa de aprovação dela no conjunto vezes {w}. Evidência válida em {v} de {n} conjuntos.",
      cutoff_meaning: "nota que um conjunto precisa atingir (definida pelo responsável pelos dados)", floor_meaning: "abaixo dele a leitura é crítica",
      f_li: "L1…L4", li_meaning: "taxa de aprovação de cada camada no conjunto, de 0 (nada passa) a 1 (tudo passa)",
      f_missing: "Camada ausente", missing_meaning: "contada como 0 e como 1: a nota vira um intervalo, nunca um número inventado",
      factor_meaning: "a nota é multiplicada por {f} enquanto uma mudança de metadados sem registro (RETRO_ALTER) não for reavaliada",
      example: "Exemplo real:", example_partial: "[0…1] = camada sem evidência válida neste conjunto ({m}).", no_example: "Nenhum conjunto tem nota ainda.",
      col_reading: "Leitura", col_count: "Conjuntos", col_meaning: "O que significa",
      m_complete_eligible: "quatro camadas, versão atual, nota {c} ou acima", m_complete_previous: "atingia {c}, mas os dados mudaram depois da avaliação",
      m_complete_info: "quatro camadas, nota {c} ou acima", m_complete_alert: "quatro camadas, nota entre {f} e {c}", m_complete_critical: "quatro camadas, nota abaixo de {f}",
      m_partial_worst_ok: "atinge {c} mesmo com as camadas ausentes em 0%", m_partial_undetermined: "pode ou não atingir {c}: depende das camadas ausentes",
      m_partial_alert: "não chega a {c} nem com as camadas ausentes em 100%", m_partial_critical: "fica abaixo de {f} mesmo com as camadas ausentes em 100%",
      m_none_integrity: "sem nota, com alerta de integridade", m_none: "nenhuma camada que examina os dados chegou a ele: sem nota",
      col_layer: "Camada", col_status: "Situação", col_generated: "Último resumo", col_validity: "Idade / vale por",
      col_reached: "Alcança", col_valid: "Válidos", col_links: "Links", dashboard: "painel ↗", rerun: "rodar ↗",
      days: "{n} d", ok: "disponível", missing: "não implantada", rejected: "rejeitado", error: "falha na leitura",
      col_dataset: "Conjunto", col_qs: "Nota", col_band: "Leitura", col_check: "A conferir",
      leg_valid: "evidência válida", leg_reached: "alcançado, evidência não vale agora", leg_gap: "não avaliado",
      leg_hatch: "falta de evidência (motivo escrito)", combo_all4: "as quatro camadas", combo_none: "nenhum conjunto",
      more: "Mostrar mais {n}", col_kind: "Tipo", col_what: "O quê", col_when: "Quando",
      o_open: "Sinais abertos", o_closed: "Encerrados (observados)", o_median: "Mediana de dias até a primeira mudança",
      o_rounds: "Rodadas observadas", o_none: "—",
      hitl_status: "Situação", hitl_awaiting: "instrumentada, aguardando gestor", hitl_collecting: "em coleta",
      hitl_issues: "Issues de revisão (Camada 3)", hitl_decided: "Decididas", hitl_agreement: "Concordância humano–IA",
      p_weights: "Pesos", p_cutoff: "Nota de corte (θ)", p_floor: "Piso crítico", p_factor: "Fator de integridade",
      p_validity: "Evidência vale por", p_window: "Janela da Camada 4", p_version: "Versão da política",
      footer: "Gerado {g} · motor ",
      cov_text: "{v} válidos · {r} alcançados, sem evidência válida agora · {g} não avaliados",
    },
  };
  const tt = (key, vars) => {
    let s = (TEXT[lang] && TEXT[lang][key]) || TEXT.en[key] || t(key, vars);
    for (const [k, v] of Object.entries(vars || {})) s = s.replace(`{${k}}`, v);
    return s;
  };
  const LAYERS = ["L1", "L2", "L3", "L4"];
  const PAGE = 40;

  function i18n() {
    document.querySelectorAll("[data-i18n]").forEach((n) => { n.textContent = tt(n.dataset.i18n); });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((n) => { n.placeholder = tt(n.dataset.i18nPlaceholder); });
  }

  const readingCounts = (data) => {
    const counts = {};
    for (const d of data.datasets) { const k = L5.readingKey(d.qs); counts[k] = (counts[k] || 0) + 1; }
    return counts;
  };

  function tiles(data) {
    const tot = data.totals, p = data.policy;
    const counts = readingCounts(data);
    const box = document.getElementById("tiles");
    // every tile says what it counts in words and explains itself on hover (ⓘ)
    const tile = (label, value, note, tip, cls) => el("div", { class: "tile", "data-tip": tip },
      el("div", { class: "label" }, label, el("span", { class: "info", "aria-hidden": "true" }, "ⓘ")),
      el("div", { class: `value ${cls || ""}` }, value), el("div", { class: "note" }, note));
    const integ = data.alerts.integrity_open;
    const below = (counts.partial_alert || 0) + (counts.partial_critical || 0) + (counts.complete_alert || 0) + (counts.complete_critical || 0);
    box.replaceChildren(
      tile(tt("tile_datasets"), int(tot.datasets), tt("tile_datasets_note"), tt("tile_datasets_tip")),
      tile(tt("tile_complete"), int(tot.complete), tt("tile_complete_note"), tt("tile_complete_tip")),
      tile(tt("tile_partial"), int(tot.partial), tt("tile_partial_note"), tt("tile_partial_tip")),
      tile(tt("tile_below"), int(below), tt("tile_below_note", { c: num(p.cutoff) }), tt("tile_below_tip", { c: num(p.cutoff) })),
      tile(tt("tile_none"), int(tot.no_content), tt("tile_none_note"), tt("tile_none_tip")),
      tile(tt("tile_integrity"), integ ? `⛔ ${int(integ)}` : "✓ 0", tt("tile_integrity_note"), tt("tile_integrity_tip"),
        integ ? "status critical" : "status good"),
    );
  }

  function formula(data) {
    const p = data.policy, n = data.totals.datasets || 1;
    const terms = [el("span", { class: "lhs" }, "Qs =")];
    LAYERS.forEach((l, i) => {
      const c = data.coverage[l];
      if (i) terms.push(el("span", { class: "op" }, "+"));
      terms.push(el("div", { class: "term", "data-tip": tt("term_tip", { l, w: num(p.weights[l]), v: int(c.valid), n: int(n) }) },
        el("div", { class: "expr" }, `${num(p.weights[l])} × ${l}`),
        el("div", { class: "name" }, t(l)),
        el("div", { class: "reach" }, tt("term_reach", { v: int(c.valid), n: int(n) })),
        el("div", { class: "meter" }, el("span", { style: `width:${(100 * c.valid) / n}%` }))));
    });
    document.getElementById("formula-terms").replaceChildren(...terms);
    const kv = [
      [tt("p_cutoff"), `${num(p.cutoff)} · ${tt("cutoff_meaning")}`],
      [tt("p_floor"), `${num(p.critical_floor)} · ${tt("floor_meaning")}`],
      [tt("f_li"), tt("li_meaning")],
      [tt("f_missing"), tt("missing_meaning")],
      [tt("p_factor"), tt("factor_meaning", { f: num(p.integrity_factor) })],
    ];
    document.getElementById("formula-params").replaceChildren(...kv.flatMap(([k, v]) => [el("dt", {}, k), el("dd", {}, v)]));

    // a real worked example: the dataset with the most valid layers (then the highest upper bound)
    const scored = data.datasets.filter((d) => d.qs.kind !== "none");
    const ex = scored.sort((a, b) => b.qs.coverage - a.qs.coverage || (b.qs.high ?? b.qs.value) - (a.qs.high ?? a.qs.value))[0];
    const box = document.getElementById("formula-example");
    if (!ex) { box.replaceChildren(tt("no_example")); return; }
    const parts = LAYERS.map((l) => {
      const c = ex.layers[l];
      const valid = c.status === "valid";
      return `${num(p.weights[l])} × ${valid ? num(c.rate) : "[0…1]"}`;
    });
    const b = L5.bandStatus(ex.qs, p);
    const result = ex.qs.kind === "complete" ? num(ex.qs.value) : `${num(ex.qs.low)} … ${num(ex.qs.high)}`;
    box.replaceChildren(
      el("div", {}, el("strong", {}, tt("example")), " ",
        el("a", { href: `ficha.html?d=${encodeURIComponent(ex.name)}&lang=${lang}` }, ex.title || ex.name)),
      el("div", { class: "calc" }, `Qs = ${parts.join(" + ")}${ex.qs.factor < 1 ? ` × ${num(ex.qs.factor)}` : ""} = ${result}`),
      el("div", { class: "muted small" }, ex.qs.kind === "partial" ? tt("example_partial", { m: (ex.qs.missing_layers || []).join(", ") }) : ""),
      el("div", {}, el("span", { class: `status ${b.cls}` }, `${b.icon} ${b.text}`), " — ", b.long));

    const counts = readingCounts(data);
    const rows = L5.READING_ORDER.filter((k) => counts[k] || ["complete_eligible", "partial_alert", "partial_critical", "partial_undetermined", "none"].includes(k))
      .map((k) => {
        const r = L5.readingLabel(k);
        return el("tr", {}, el("td", {}, el("span", { class: `status ${r.cls}` }, `${r.icon} ${r.short}`)),
          el("td", { class: "num" }, int(counts[k] || 0)), el("td", { class: "muted" }, tt("m_" + k, { c: num(p.cutoff), f: num(p.critical_floor) })));
      });
    document.getElementById("readings-table").replaceChildren(
      el("thead", {}, el("tr", {}, el("th", {}, tt("col_reading")), el("th", { class: "num" }, tt("col_count")), el("th", {}, tt("col_meaning")))),
      el("tbody", {}, rows));
  }

  function sources(data) {
    const table = document.getElementById("sources-table");
    const head = el("tr", {}, ...["col_layer", "col_status", "col_generated", "col_validity", "col_reached", "col_valid", "col_links"]
      .map((k) => el("th", { class: ["col_reached", "col_valid"].includes(k) ? "num" : null }, tt(k))));
    const rows = LAYERS.map((layer) => {
      const m = data.layers[layer], cov = data.coverage[layer];
      let status;
      if (m.status === "ok" && !m.expired) status = el("span", { class: "status good" }, `✓ ${tt("ok")}`);
      else if (m.status === "ok") status = el("span", { class: "status warning", "data-tip": t("r_summary_too_old") }, `⚠ ${t("r_summary_too_old")}`);
      else if (m.status === "missing") status = el("span", { class: "status neutral", "data-tip": m.detail || "" }, `— ${t("r_layer_not_deployed")}`);
      else status = el("span", { class: "status critical", "data-tip": m.detail || "" }, `⛔ ${tt(m.status)}: ${m.detail || ""}`);
      const links = el("span", {},
        m.dashboard ? el("a", { href: m.dashboard, target: "_blank", rel: "noopener" }, tt("dashboard")) : null, " ",
        m.workflow ? el("a", { href: m.workflow, target: "_blank", rel: "noopener" }, tt("rerun")) : null);
      return el("tr", {},
        el("td", {}, el("strong", {}, layer), " ", el("span", { class: "muted" }, t(layer))),
        el("td", {}, status),
        el("td", {}, m.generated_at ? dateTime(m.generated_at) : "—"),
        el("td", {}, `${m.age_days != null ? tt("days", { n: num(m.age_days, 1) }) : "—"} / ${tt("days", { n: num(m.validity_days, m.validity_days < 1 ? 2 : 0) })}`),
        el("td", { class: "num" }, int(cov.reached)), el("td", { class: "num" }, int(cov.valid)), el("td", {}, links));
    });
    table.replaceChildren(el("thead", {}, head), el("tbody", {}, rows));
  }

  function coverage(data) {
    const n = data.totals.datasets || 1;
    const chart = document.getElementById("coverage-chart");
    const tableRows = [];
    chart.replaceChildren(...LAYERS.map((layer) => {
      const c = data.coverage[layer];
      const notValid = Math.max(0, c.reached - c.valid), gap = n - c.reached;
      const text = tt("cov_text", { v: int(c.valid), r: int(notValid), g: int(gap) });
      tableRows.push(el("tr", {}, el("td", {}, layer), el("td", { class: "num" }, int(c.valid)),
        el("td", { class: "num" }, int(notValid)), el("td", { class: "num" }, int(gap))));
      return el("div", { class: "cov-row" },
        el("div", { class: "name" }, layer),
        el("div", { class: "track", role: "img", "aria-label": `${layer}: ${text}` },
          el("div", { class: "seg-valid", style: `width:${(100 * c.valid) / n}%`, "data-tip": `${layer} · ${tt("leg_valid")}: ${int(c.valid)}` }),
          el("div", { class: "seg-reached", style: `width:${(100 * notValid) / n}%`, "data-tip": `${layer} · ${tt("leg_reached")}: ${int(notValid)}` })),
        el("div", { class: "text" }, text));
    }));
    document.getElementById("coverage-legend").replaceChildren(
      el("li", {}, el("span", { class: "swatch valid" }), tt("leg_valid")),
      el("li", {}, el("span", { class: "swatch reached" }), tt("leg_reached")),
      el("li", {}, el("span", { class: "swatch gap" }), tt("leg_gap")));
    document.getElementById("coverage-table").replaceChildren(
      el("thead", {}, el("tr", {}, el("th", {}, tt("col_layer")), el("th", { class: "num" }, tt("leg_valid")),
        el("th", { class: "num" }, tt("leg_reached")), el("th", { class: "num" }, tt("leg_gap")))),
      el("tbody", {}, tableRows));
  }

  function combos(data) {
    const box = document.getElementById("combos-chart");
    const list = [...data.combinations];
    if (!list.some((c) => c.layers.length === 4)) list.unshift({ layers: LAYERS, datasets: 0 });
    const max = Math.max(1, ...list.map((c) => c.datasets));
    const rows = list.map((c) => el("div", { class: `combo ${c.datasets ? "" : "empty"}` },
      ...LAYERS.map((l) => el("span", { class: `dot ${c.layers.includes(l) ? "on" : ""}`, "data-tip": l })),
      el("div", { class: "bar" },
        c.datasets ? el("span", { class: "fill", style: `width:${(70 * c.datasets) / max}%` }) : null,
        el("span", {}, c.datasets ? `${int(c.datasets)}${c.layers.length === 4 ? " · " + tt("combo_all4") : ""}`
          : `0 · ${c.layers.length === 4 ? tt("combo_all4") : ""} (${tt("combo_none")})`))));
    box.replaceChildren(el("div", { class: "combo head" }, ...LAYERS.map((l) => el("span", {}, l)), el("span", {})), ...rows);
  }

  let matrixShown = PAGE;
  function matrix(data) {
    const q = document.getElementById("search").value.trim().toLowerCase();
    const kind = document.getElementById("kind-filter").value;
    const sort = document.getElementById("sort").value;
    let list = data.datasets.filter((d) => (!q || d.name.includes(q) || (d.title || "").toLowerCase().includes(q))
      && (!kind || (kind === "findings" ? d.findings > 0 : kind === "integrity" ? d.qs.integrity_open : d.qs.kind === kind)));
    const score = (d) => d.qs.kind === "complete" ? d.qs.value : d.qs.kind === "partial" ? d.qs.high : 2;
    if (sort === "coverage") list.sort((a, b) => b.qs.coverage - a.qs.coverage || score(a) - score(b) || a.name.localeCompare(b.name));
    else if (sort === "worst") list.sort((a, b) => score(a) - score(b) || a.name.localeCompare(b.name));
    else list.sort((a, b) => a.name.localeCompare(b.name));
    const head = el("tr", {}, el("th", {}, tt("col_dataset")), ...LAYERS.map((l) => el("th", { "data-tip": t(l) }, l)),
      el("th", {}, tt("col_qs")), el("th", {}, tt("col_band")), el("th", { class: "num" }, tt("col_check")));
    const rows = list.slice(0, matrixShown).map((d) => {
      const cells = LAYERS.map((l) => {
        const c = d.layers[l];
        if (c.rate == null) return el("td", {}, el("span", { class: "cell gap", "data-tip": `${l}: ${t("r_" + c.reason)}` }, t("s_" + c.reason)));
        const tip = `${l}: ${num(c.rate, 3)} · ${t("status_" + c.status)}${c.reason ? " · " + t("r_" + c.reason) : ""}${c.evaluated_at ? " · " + date(c.evaluated_at) : ""}${c.current === false ? " · " + t("earlier_version") : ""}`;
        const label = c.status !== "valid" ? `${num(c.rate)} · ${t("s_" + c.reason)}` : c.current === false ? `${num(c.rate)} ↻` : num(c.rate);
        return el("td", {}, el("span", { class: `cell r${rateBin(c.rate)} ${c.status === "valid" ? "" : "invalid"}`, "data-tip": tip }, label));
      });
      const b = bandStatus(d.qs, data.policy);
      const note = d.qs.note === "met_cutoff_previous_version" ? t("previous_version", { d: date(d.qs.last_change) }) : "";
      return el("tr", { class: "clickable", "data-name": d.name },
        el("td", { class: "ds" }, el("a", { href: `ficha.html?d=${encodeURIComponent(d.name)}&lang=${lang}` }, d.title || d.name),
          el("div", { class: "muted small mono", title: d.name }, d.name)),
        ...cells,
        el("td", {}, el("div", { class: "qs" }, ruler(d.qs, data.policy), el("span", { class: "value" }, L5.qsText(d.qs)))),
        el("td", {}, el("span", { class: `status ${b.cls}`, "data-tip": b.long }, `${b.icon} ${b.text}`, el("span", { class: "info" }, " ⓘ")), note ? el("div", { class: "small muted" }, note) : null),
        el("td", { class: "num" }, d.findings ? int(d.findings) : "—"));
    });
    document.getElementById("matrix-table").replaceChildren(el("thead", {}, head), el("tbody", {}, rows));
    const more = document.getElementById("matrix-more");
    more.hidden = list.length <= matrixShown;
    more.textContent = tt("more", { n: int(Math.min(PAGE, list.length - matrixShown)) });
    document.getElementById("matrix-legend").replaceChildren(
      ...[0, 1, 2, 3, 4].map((i) => el("li", {}, el("span", { class: "swatch", style: `background:var(--level-${i})` }),
        ["< 0,50", "0,50–0,70", "0,70–0,85", "0,85–0,95", "≥ 0,95"][i].replaceAll(",", lang === "pt" ? "," : "."))),
      el("li", {}, el("span", { class: "swatch hatch" }), tt("leg_hatch")));
  }

  let checkItems = [], checkShown = PAGE;
  async function check(data) {
    // findings live in the records; the aggregate only counts them, so load the records that have any
    const names = data.datasets.filter((d) => d.findings > 0).map((d) => d.name);
    const records = await Promise.all(names.map((n) => fetch(`data/fichas/${encodeURIComponent(n)}.json`).then((r) => r.ok ? r.json() : null).catch(() => null)));
    checkItems = [];
    records.forEach((rec, i) => rec && rec.findings.forEach((f) => checkItems.push({ ...f, dataset: names[i], title: rec.dataset.title })));
    checkItems.sort((a, b) => (b.when || "").localeCompare(a.when || "") || (b.count || 0) - (a.count || 0));
    const sel = document.getElementById("check-filter");
    const kinds = [...new Set(checkItems.map((f) => f.kind))];
    sel.replaceChildren(el("option", { value: "" }, tt("all_kinds")), ...kinds.map((k) => el("option", { value: k }, t("k_" + k))));
    drawCheck();
  }
  function drawCheck() {
    const kind = document.getElementById("check-filter").value;
    const list = checkItems.filter((f) => !kind || f.kind === kind);
    const rows = list.slice(0, checkShown).map((f) => el("tr", {},
      el("td", {}, el("a", { href: `ficha.html?d=${encodeURIComponent(f.dataset)}&lang=${lang}` }, f.title || f.dataset)),
      el("td", {}, el("span", { class: "chip" }, f.layer), t("k_" + f.kind)),
      el("td", {}, (lang === "pt" ? f.pt : f.en) || ""),
      el("td", {}, f.when ? date(f.when) : "—")));
    document.getElementById("check-table").replaceChildren(
      el("thead", {}, el("tr", {}, el("th", {}, tt("col_dataset")), el("th", {}, tt("col_kind")), el("th", {}, tt("col_what")), el("th", {}, tt("col_when")))),
      el("tbody", {}, rows));
    const more = document.getElementById("check-more");
    more.hidden = list.length <= checkShown;
    more.textContent = tt("more", { n: int(Math.min(PAGE, list.length - checkShown)) });
  }

  function outcomes(data) {
    const s = data.inference || {};
    const kv = (box, pairs) => document.getElementById(box).replaceChildren(...pairs.flatMap(([k, v]) => [el("dt", {}, k), el("dd", {}, v)]));
    const open = s.open_by_status || {};
    const closed = s.closed || {};
    kv("outcomes-open", [
      [tt("o_open"), int(s.open_signals)],
      ...Object.entries(open).filter(([, n]) => n).map(([k, n]) => [`· ${t("o_" + k)}`, int(n)]),
      [tt("o_closed"), int(Object.values(closed).reduce((a, b) => a + b, 0))],
      ...Object.entries(closed).filter(([, n]) => n).map(([k, n]) => [`· ${t("o_" + k)}`, int(n)]),
      [tt("o_median"), s.median_days_to_first_change != null ? num(s.median_days_to_first_change, 1) : tt("o_none")],
      [tt("o_rounds"), int(s.rounds_observed)],
    ]);
    const h = data.hitl || {};
    const p = (h.profiles || [])[0] || {};
    kv("hitl", [
      [tt("hitl_status"), h.status === "collecting" ? tt("hitl_collecting") : tt("hitl_awaiting")],
      [tt("hitl_issues"), int(p.issues)], [tt("hitl_decided"), int(p.decided)],
      [tt("hitl_agreement"), p.human_llm_agreement != null ? num(p.human_llm_agreement) : tt("hitl_awaiting")],
    ]);
  }

  function policy(data) {
    const p = data.policy;
    const box = document.getElementById("policy-kv");
    const pairs = [
      [tt("p_weights"), LAYERS.map((l) => `${l} ${num(p.weights[l])}`).join(" · ")],
      [tt("p_cutoff"), num(p.cutoff)], [tt("p_floor"), num(p.critical_floor)],
      [tt("p_factor"), `${num(p.integrity_factor)} (${p.integrity_types.join(", ")})`],
      [tt("p_validity"), LAYERS.map((l) => `${l} ${tt("days", { n: num(p.validity_days[l], p.validity_days[l] < 1 ? 2 : 0) })}`).join(" · ")],
      [tt("p_window"), tt("days", { n: p.l4_window_days })], [tt("p_version"), p.policy_version],
    ];
    box.replaceChildren(...pairs.flatMap(([k, v]) => [el("dt", {}, k), el("dd", {}, v)]));
  }

  async function main() {
    langSwitch(); i18n(); tooltip();
    const r = repo();
    document.getElementById("repo-link").href = `https://github.com/${r}`;
    document.getElementById("readme-link").href = `https://github.com/${r}#readme`;
    document.getElementById("leiame-link").href = `https://github.com/${r}/blob/main/LEIAME.md`;
    document.getElementById("run-link").href = `https://github.com/${r}/actions/workflows/layer5.yml`;
    document.getElementById("policy-link").href = `https://github.com/${r}/blob/main/policy.json`;
    let data;
    try {
      data = await (await fetch("data/layer5.json", { cache: "no-cache" })).json();
    } catch (e) {
      document.getElementById("title").textContent = t("failed");
      return;
    }
    document.getElementById("title").textContent = data.portal.title;
    document.getElementById("subtitle").textContent = `${data.portal.portal_url} · ${dateTime(data.run.generated_at)}`;
    document.getElementById("notice").textContent = data.notice[lang] || data.notice.en;
    tiles(data); formula(data); sources(data); coverage(data); combos(data); matrix(data); outcomes(data); policy(data);
    for (const id of ["search", "kind-filter", "sort"]) document.getElementById(id).addEventListener("input", () => { matrixShown = PAGE; matrix(data); });
    document.getElementById("matrix-more").addEventListener("click", () => { matrixShown += PAGE; matrix(data); });
    document.getElementById("matrix-table").addEventListener("click", (e) => {
      const row = e.target.closest("tr[data-name]");
      if (row && !e.target.closest("a")) location.href = `ficha.html?d=${encodeURIComponent(row.dataset.name)}&lang=${lang}`;
    });
    document.getElementById("check-filter").addEventListener("input", () => { checkShown = PAGE; drawCheck(); });
    document.getElementById("check-more").addEventListener("click", () => { checkShown += PAGE; drawCheck(); });
    const run = data.run;
    const commit = run.commit ? el("a", { href: `https://github.com/${r}/commit/${run.commit}` }, run.commit.slice(0, 7)) : "local";
    document.getElementById("footer").replaceChildren(tt("footer", { g: dateTime(run.generated_at) }), commit,
      run.run_id ? el("span", {}, " · ", el("a", { href: `https://github.com/${r}/actions/runs/${run.run_id}` }, "run")) : "");
    check(data);
  }

  main();
})();
