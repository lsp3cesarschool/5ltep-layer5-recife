// Shared by the dashboard (app.js) and the dataset record (ficha.js): language, formatting, labels,
// and the score ruler. Every text coming from data is inserted with textContent; links only http(s).
"use strict";

const L5 = (() => {
  const params = new URLSearchParams(location.search);
  const lang = params.get("lang") || ((navigator.language || "").toLowerCase().startsWith("pt") ? "pt" : "en");

  const T = {
    en: {
      back: "← Back to the repository", eyebrow: "5L-TEP · Layer 5 · Governance and Publication",
      loading: "Loading…", failed: "Could not load the data of this page.",
      cutoff_label: "Nota de corte (θ)", cutoff_en: "cutoff score", floor_label: "Critical floor",
      layer: "Layer", L1: "Structural contracts", L2: "Semantic policies", L3: "Anomaly detection", L4: "Observability and provenance",
      status_valid: "valid evidence", status_missing: "no evidence", status_expired: "expired evidence",
      status_out_of_scope: "out of scope", status_superseded: "superseded",
      band_critical: "Critical", band_alert: "Alert", band_info: "Info", band_info_worst_case: "Reaches the cutoff even in the worst case",
      band_undetermined: "Undetermined (depends on missing layers)", band_none: "No content evaluation",
      band_critical_partial: "Critical even in the best case", band_alert_partial: "Below the cutoff even in the best case",
      kind_complete: "complete", kind_partial: "partial", kind_none: "no content evaluation",
      eligible: "reaches the cutoff", previous_version: "reached the cutoff on the version of {d}; awaiting re-evaluation",
      r_not_reached: "not reached by this layer", r_l1_level0: "no data dictionary (level 0)",
      r_l1_nothing_verifiable: "no verifiable file", r_l2_not_evaluated: "rules not evaluated",
      r_l2_no_checks_in_scope: "no check in scope", r_l3_no_rate: "no rate", r_l4_not_observed: "not observed in the window",
      r_layer_not_deployed: "layer not deployed for this portal yet", r_summary_inconsistent: "summary rejected (inconsistent)",
      r_summary_unreadable: "summary rejected (unreadable)", r_fetch_failed: "could not read the summary",
      r_summary_too_old: "expired (summary too old)", r_structure_changed_after: "structure changed after the evaluation",
      r_content_changed_unrecorded: "bytes changed with no metadata record",
      s_not_reached: "not reached", s_l1_level0: "no dictionary", s_l1_nothing_verifiable: "nothing verifiable",
      s_l2_not_evaluated: "not evaluated", s_l2_no_checks_in_scope: "no checks", s_l3_no_rate: "no rate",
      s_l4_not_observed: "not observed", s_layer_not_deployed: "not deployed", s_summary_inconsistent: "rejected",
      s_summary_unreadable: "rejected", s_fetch_failed: "read failed", s_summary_too_old: "expired",
      s_structure_changed_after: "out of scope", s_content_changed_unrecorded: "superseded",
      o_reported: "reported", o_unchanged: "unchanged (status quo)", o_changed_signal_persists: "data changed, signal persists",
      o_not_reassessed: "not re-evaluated yet", o_remediated_observed: "signal gone after the data changed",
      o_cleared_without_data_change: "signal gone with no data change (method or rule)",
      o_withdrawn_observed: "dataset no longer listed",
      k_signal: "signal", k_integrity: "integrity", k_scope: "structure", k_unrecorded_change: "unrecorded change",
      k_evidence_lost: "evidence lost", k_simultaneous: "same cycle",
      earlier_version: "↻ evaluated on an earlier version of the file (it counts, but cannot reach the cutoff until re-evaluated)",
    },
    pt: {
      back: "← Voltar ao repositório", eyebrow: "5L-TEP · Camada 5 · Governança e Publicação",
      loading: "Carregando…", failed: "Não foi possível carregar os dados desta página.",
      cutoff_label: "Nota de corte (θ)", cutoff_en: "nota de corte", floor_label: "Piso crítico",
      layer: "Camada", L1: "Contratos estruturais", L2: "Políticas semânticas", L3: "Detecção de anomalias", L4: "Observabilidade e proveniência",
      status_valid: "evidência válida", status_missing: "sem evidência", status_expired: "evidência vencida",
      status_out_of_scope: "fora do escopo", status_superseded: "superada",
      band_critical: "Crítico", band_alert: "Alerta", band_info: "Info", band_info_worst_case: "Atinge a nota de corte mesmo no pior caso",
      band_undetermined: "Indefinido (depende das camadas ausentes)", band_none: "Sem avaliação de conteúdo",
      band_critical_partial: "Crítico mesmo no melhor caso", band_alert_partial: "Abaixo da nota de corte mesmo no melhor caso",
      kind_complete: "completo", kind_partial: "parcial", kind_none: "sem avaliação de conteúdo",
      eligible: "atinge a nota de corte", previous_version: "atingia a nota de corte na versão de {d}; aguardando reavaliação",
      r_not_reached: "não alcançado por esta camada", r_l1_level0: "sem dicionário de dados (nível 0)",
      r_l1_nothing_verifiable: "nenhum arquivo verificável", r_l2_not_evaluated: "regras não avaliadas",
      r_l2_no_checks_in_scope: "nenhuma verificação no escopo", r_l3_no_rate: "sem taxa", r_l4_not_observed: "não observado na janela",
      r_layer_not_deployed: "camada ainda não implantada neste portal", r_summary_inconsistent: "resumo rejeitado (inconsistente)",
      r_summary_unreadable: "resumo rejeitado (ilegível)", r_fetch_failed: "falha ao ler o resumo",
      r_summary_too_old: "vencida (resumo antigo)", r_structure_changed_after: "a estrutura mudou depois da avaliação",
      r_content_changed_unrecorded: "bytes mudaram sem registro nos metadados",
      s_not_reached: "não alcançado", s_l1_level0: "sem dicionário", s_l1_nothing_verifiable: "nada verificável",
      s_l2_not_evaluated: "não avaliado", s_l2_no_checks_in_scope: "sem verificações", s_l3_no_rate: "sem taxa",
      s_l4_not_observed: "não observado", s_layer_not_deployed: "não implantada", s_summary_inconsistent: "rejeitado",
      s_summary_unreadable: "rejeitado", s_fetch_failed: "falha", s_summary_too_old: "vencida",
      s_structure_changed_after: "fora do escopo", s_content_changed_unrecorded: "superada",
      o_reported: "relatado", o_unchanged: "sem mudança (status quo)", o_changed_signal_persists: "dados mudaram, sinal continua",
      o_not_reassessed: "ainda não reavaliado", o_remediated_observed: "sinal sumiu depois de os dados mudarem",
      o_cleared_without_data_change: "sinal sumiu sem mudança nos dados (método ou regra)",
      o_withdrawn_observed: "conjunto deixou de ser listado",
      k_signal: "sinal", k_integrity: "integridade", k_scope: "estrutura", k_unrecorded_change: "mudança sem registro",
      k_evidence_lost: "evidência perdida", k_simultaneous: "mesmo ciclo",
      earlier_version: "↻ avaliada numa versão anterior do arquivo (conta, mas não atinge a nota de corte até ser reavaliada)",
    },
  };

  const t = (key, vars) => {
    let s = (T[lang] && T[lang][key]) || T.en[key] || key;
    for (const [k, v] of Object.entries(vars || {})) s = s.replace(`{${k}}`, v);
    return s;
  };
  const num = (x, digits = 2) => x == null ? "—" : new Intl.NumberFormat(lang === "pt" ? "pt-BR" : "en",
    { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(x);
  const int = (x) => x == null ? "—" : new Intl.NumberFormat(lang === "pt" ? "pt-BR" : "en").format(x);
  const date = (iso) => iso ? new Date(iso).toLocaleDateString(lang === "pt" ? "pt-BR" : "en-GB",
    { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" }) : "—";
  const dateTime = (iso) => iso ? new Date(iso).toLocaleString(lang === "pt" ? "pt-BR" : "en-GB",
    { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" }) + " UTC" : "—";
  const safeUrl = (u) => typeof u === "string" && /^https?:\/\//i.test(u) ? u : null;

  function el(tag, attrs, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === "class") node.className = v;
      else if (k === "href") { const u = safeUrl(v) || (v.startsWith("?") || v.startsWith("ficha.html") || v.startsWith("data/") ? v : null); if (u) node.setAttribute("href", u); }
      else node.setAttribute(k, v);
    }
    for (const c of children.flat()) if (c != null) node.append(c instanceof Node ? c : String(c));
    return node;
  }

  // Rate bins of the blue ramp (ordinal; the number is always written next to the colour).
  const rateBin = (r) => r < 0.5 ? 0 : r < 0.7 ? 1 : r < 0.85 ? 2 : r < 0.95 ? 3 : 4;

  // Readings: a short label for tables and a long explanation (tooltip, record, formula block).
  const READINGS = {
    en: {
      complete_eligible: ["Reaches the cutoff", "The four layers evaluated the current version and Qs = {v} is at or above the Nota de corte (θ) {cutoff}."],
      complete_previous: ["Reached it on an older version", "Qs = {v} reached the cutoff {cutoff}, but the data changed afterwards; it counts again once the layers re-evaluate."],
      complete_info: ["Above the cutoff", "Qs = {v} is at or above the cutoff {cutoff}."],
      complete_alert: ["Below the cutoff", "Qs = {v}: between the critical floor {floor} and the Nota de corte (θ) {cutoff}."],
      complete_critical: ["Critical", "Qs = {v} is below the critical floor {floor}{integrity}."],
      partial_critical: ["Critical in any case", "Qs is between {lo} and {hi}. Even if the missing layers ({missing}) passed 100%, it would stay below the critical floor {floor}{integrity}."],
      partial_alert: ["Cannot reach the cutoff", "Qs is between {lo} and {hi}. Even if the missing layers ({missing}) passed 100%, it would not reach the Nota de corte (θ) {cutoff}."],
      partial_worst_ok: ["Reaches the cutoff in any case", "Qs is between {lo} and {hi}: even with the missing layers ({missing}) at 0% it reaches the cutoff {cutoff}. Still partial: the complete score needs the four layers."],
      partial_undetermined: ["Depends on missing layers", "Qs is between {lo} and {hi}. Whether it reaches the cutoff {cutoff} depends on the layers that have not evaluated this dataset ({missing})."],
      none: ["No content evaluation", "None of the layers that examine the data itself (L1–L3) has valid evidence on this dataset, so there is no score. Layer 4 only follows its history."],
      none_integrity: ["Integrity alert", "No score (no content layer), but the metadata changed without the modification date advancing (RETRO_ALTER)."],
    },
    pt: {
      complete_eligible: ["Atinge a nota de corte", "As quatro camadas avaliaram a versão atual e Qs = {v} está na Nota de corte (θ) {cutoff} ou acima."],
      complete_previous: ["Atingia numa versão anterior", "Qs = {v} atingia a nota de corte {cutoff}, mas os dados mudaram depois; volta a contar quando as camadas reavaliarem."],
      complete_info: ["Acima da nota de corte", "Qs = {v} está na nota de corte {cutoff} ou acima."],
      complete_alert: ["Abaixo da nota de corte", "Qs = {v}: entre o piso crítico {floor} e a Nota de corte (θ) {cutoff}."],
      complete_critical: ["Crítico", "Qs = {v} está abaixo do piso crítico {floor}{integrity}."],
      partial_critical: ["Crítico em qualquer caso", "Qs está entre {lo} e {hi}. Mesmo que as camadas ausentes ({missing}) aprovassem 100%, ficaria abaixo do piso crítico {floor}{integrity}."],
      partial_alert: ["Não chega à nota de corte", "Qs está entre {lo} e {hi}. Mesmo que as camadas ausentes ({missing}) aprovassem 100%, não chegaria à Nota de corte (θ) {cutoff}."],
      partial_worst_ok: ["Atinge a nota de corte em qualquer caso", "Qs está entre {lo} e {hi}: mesmo com as camadas ausentes ({missing}) em 0% atinge a nota de corte {cutoff}. Continua parcial: a nota completa precisa das quatro camadas."],
      partial_undetermined: ["Depende das camadas ausentes", "Qs está entre {lo} e {hi}. Se atinge a nota de corte {cutoff} depende das camadas que ainda não avaliaram este conjunto ({missing})."],
      none: ["Sem avaliação do conteúdo", "Nenhuma das camadas que examinam os próprios dados (L1–L3) tem evidência válida sobre este conjunto, então não há nota. A Camada 4 só acompanha a história dele."],
      none_integrity: ["Alerta de integridade", "Sem nota (nenhuma camada de conteúdo), mas os metadados mudaram sem a data de modificação avançar (RETRO_ALTER)."],
    },
  };
  const READING_ORDER = ["complete_eligible", "complete_previous", "complete_info", "complete_alert", "complete_critical",
    "partial_worst_ok", "partial_undetermined", "partial_alert", "partial_critical", "none_integrity", "none"];
  const READING_STYLE = {
    complete_eligible: ["good", "✓"], complete_previous: ["neutral", "↻"], complete_info: ["good", "✓"],
    complete_alert: ["warning", "⚠"], complete_critical: ["critical", "⛔"], partial_worst_ok: ["good", "✓"],
    partial_undetermined: ["neutral", "?"], partial_alert: ["warning", "⚠"], partial_critical: ["critical", "⛔"],
    none_integrity: ["critical", "⛔"], none: ["neutral", "—"],
  };

  function readingKey(qs) {
    if (qs.kind === "complete") {
      if (qs.eligible) return "complete_eligible";
      if (qs.note === "met_cutoff_previous_version") return "complete_previous";
      return { info: "complete_info", alert: "complete_alert", critical: "complete_critical" }[qs.band];
    }
    if (qs.kind === "partial") {
      return { critical: "partial_critical", alert: "partial_alert", info_worst_case: "partial_worst_ok" }[qs.band] || "partial_undetermined";
    }
    return qs.band === "critical" ? "none_integrity" : "none";
  }

  function bandStatus(qs, policy) {
    const key = readingKey(qs);
    const [short, long] = (READINGS[lang] || READINGS.en)[key];
    const [cls, icon] = READING_STYLE[key];
    const p = policy || { cutoff: 0.85, critical_floor: 0.7 };
    const integrity = qs.factor < 1 ? (lang === "pt" ? `, já multiplicada pelo fator de integridade ${num(qs.factor)}` : `, already multiplied by the integrity factor ${num(qs.factor)}`) : "";
    const vars = { v: num(qs.value), lo: num(qs.low), hi: num(qs.high), cutoff: num(p.cutoff), floor: num(p.critical_floor),
      missing: (qs.missing_layers || []).join(", "), integrity };
    let text = long;
    for (const [k, v] of Object.entries(vars)) text = text.replaceAll(`{${k}}`, v);
    return { key, cls, icon, text: short, long: text };
  }

  function readingLabel(key) {
    const [short, long] = (READINGS[lang] || READINGS.en)[key];
    return { short, long, cls: READING_STYLE[key][0], icon: READING_STYLE[key][1] };
  }

  // Score ruler: 0..1 track, the critical floor and the cutoff as ticks; a point (complete) or an
  // interval (partial: missing layers counted as 0 and as 1).
  function ruler(qs, policy, width = 140) {
    const h = 18, x = (v) => 2 + v * (width - 4);
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("width", width); svg.setAttribute("height", h); svg.setAttribute("role", "img");
    const add = (name, attrs) => { const n = document.createElementNS(ns, name); for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v); svg.append(n); return n; };
    add("rect", { x: 2, y: 7, width: width - 4, height: 4, rx: 2, fill: "var(--grid)" });
    add("line", { x1: x(policy.critical_floor), x2: x(policy.critical_floor), y1: 3, y2: 15, stroke: "var(--axis)", "stroke-width": 2 });
    add("line", { x1: x(policy.cutoff), x2: x(policy.cutoff), y1: 1, y2: 17, stroke: "var(--cutoff)", "stroke-width": 2 });
    let label;
    if (qs.kind === "complete") {
      add("circle", { cx: x(qs.value), cy: 9, r: 5, fill: "var(--bar)", stroke: "var(--surface)", "stroke-width": 2 });
      label = `Qs ${num(qs.value)}`;
    } else if (qs.kind === "partial") {
      add("rect", { x: x(qs.low), y: 5, width: Math.max(4, x(qs.high) - x(qs.low)), height: 8, rx: 4, fill: "var(--bar)", opacity: .85 });
      label = `Qs ${num(qs.low)}–${num(qs.high)}`;
    } else {
      label = t("band_none");
    }
    const title = document.createElementNS(ns, "title");
    title.textContent = `${label} · ${t("cutoff_label")} ${num(policy.cutoff)} · ${t("floor_label")} ${num(policy.critical_floor)}`;
    svg.prepend(title);
    return svg;
  }

  function qsText(qs) {
    if (qs.kind === "complete") return num(qs.value);
    if (qs.kind === "partial") return `${num(qs.low)}–${num(qs.high)}`;
    return "—";
  }

  function langSwitch() {
    for (const code of ["en", "pt"]) {
      const a = document.getElementById(`lang-${code}`);
      if (!a) continue;
      const p = new URLSearchParams(location.search); p.set("lang", code);
      a.href = `?${p}`;
      if (code === lang) a.classList.add("current");
    }
    document.documentElement.lang = lang === "pt" ? "pt-BR" : "en";
  }

  function tooltip() {
    const tip = document.getElementById("tooltip");
    if (!tip) return;
    document.addEventListener("mouseover", (e) => {
      const target = e.target.closest("[data-tip]");
      if (!target) { tip.hidden = true; return; }
      tip.textContent = target.getAttribute("data-tip");
      tip.hidden = false;
    });
    document.addEventListener("mousemove", (e) => {
      if (tip.hidden) return;
      const x = Math.min(e.clientX + 14, window.innerWidth - tip.offsetWidth - 8);
      tip.style.left = `${x}px`; tip.style.top = `${e.clientY + 14}px`;
    });
  }

  function repo() {
    // github.io/<repo>/ -> owner/repo; otherwise the main instance
    const m = location.hostname.match(/^([^.]+)\.github\.io$/);
    const name = location.pathname.split("/").filter(Boolean)[0];
    return m && name ? `${m[1]}/${name}` : "lsp3cesarschool/5ltep-layer5";
  }

  return { lang, t, num, int, date, dateTime, el, safeUrl, rateBin, bandStatus, readingKey, readingLabel, READING_ORDER,
    ruler, qsText, langSwitch, tooltip, repo };
})();
