/* AURA Shield frontend logic. Every rendered value comes from the API,
   which reads the real backend state - no placeholder data anywhere. */

const $ = (sel) => document.querySelector(sel);
const api = async (path, opts) => {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
};
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = (v, digits = 2) => (v === null || v === undefined) ? "—" : Number(v).toFixed(digits);
const decisionBadge = (d) => `<span class="decision-badge decision-${esc(d)}">${esc(d).toUpperCase()}</span>`;

/* ------------------------------------------------ navigation */
document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
    btn.classList.add("active");
    $(`#view-${btn.dataset.view}`).classList.remove("hidden");
    if (btn.dataset.view === "logs") loadLogs();
    if (btn.dataset.view === "constitution") loadConstitution();
    if (btn.dataset.view === "benchmark") loadBenchmark();
  });
});

/* ------------------------------------------------ 1. prompt tester */
$("#analyze-btn").addEventListener("click", async () => {
  const prompt = $("#prompt").value.trim();
  if (!prompt) return;
  const btn = $("#analyze-btn");
  btn.disabled = true;
  btn.textContent = "Analyzing…";
  $("#result-panel").innerHTML = `<p class="muted empty-note">Running pipeline…</p>`;
  try {
    const r = await api("/api/analyze", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({user_prompt: prompt, source_content: $("#source").value.trim() || null}),
    });
    renderResult(r);
  } catch (e) {
    $("#result-panel").innerHTML = `<p class="muted empty-note">Analysis failed: ${esc(e.message)}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Submit";
  }
});

function renderResult(r) {
  const s = r.signals;
  const viol = s.constitution.violations || [];
  const fallbackNote = (b, name) => b
    ? `<div class="signal-note">${esc(name)} check was unavailable (fallback) — signal is not a model judgment.</div>`
    : "";

  $("#result-panel").innerHTML = `
    <div class="decision-line">
      ${decisionBadge(r.decision)}
      <span><span class="score-label">blended risk score</span><br>
      <span class="score mono">${fmt(r.risk_score)}</span></span>
      <span class="request-id">${esc(r.request_id)}</span>
    </div>
    <div class="score-bar"><div style="width:${Math.round((r.risk_score || 0) * 100)}%"></div></div>

    ${viol.length ? `
    <div class="violation-box">
      <div class="violation-title">Constitution violation</div>
      ${viol.map((v) => `
        <div><span class="p-id">${esc(v.principle_id)}</span>
        <span class="conf">confidence ${fmt(v.confidence)}</span></div>
        <div>${esc(v.explanation)}</div>
        <div class="p-rationale muted" data-principle="${esc(v.principle_id)}"></div>
      `).join("")}
    </div>` : ""}

    <div class="signal-grid">
      <div class="signal-card">
        <div class="signal-name">Rule-based</div>
        <div class="signal-value">${fmt(s.rule.signal)}</div>
        <div class="signal-note">${s.rule.matched
          ? `matched: ${esc((s.rule.patterns || []).join(", "))}`
          : "no pattern matched"}</div>
      </div>
      <div class="signal-card">
        <div class="signal-name">LLM semantic</div>
        <div class="signal-value">${fmt(s.llm.signal)}</div>
        <div class="signal-note">${esc(s.llm.reasoning)}</div>
        ${fallbackNote(s.llm.used_fallback, "LLM analyzer")}
      </div>
      <div class="signal-card">
        <div class="signal-name">Constitution</div>
        <div class="signal-value">${fmt(s.constitution.signal)}</div>
        <div class="signal-note">${viol.length
          ? `${viol.length} principle(s) violated (constitution v${s.constitution.version})`
          : `no violation across v${s.constitution.version} principles`}</div>
        ${fallbackNote(s.constitution.used_fallback, "Constitution")}
      </div>
    </div>

    <div class="explanation">
      <span class="score-label">policy engine explanation</span>
      <div>${esc(r.explanation)}</div>
    </div>`;

  // Fetch each violated principle's rationale inline (prominent display).
  viol.forEach(async (v) => {
    try {
      const c = await api("/api/constitution");
      const p = c.principles.find((p) => p.id === v.principle_id);
      if (p) {
        const el = document.querySelector(`[data-principle="${v.principle_id}"]`);
        if (el) el.innerHTML = `Principle: "${esc(p.principle_text)}" — <em>${esc(p.rationale)}</em>`;
      }
    } catch { /* rationale is supplementary; absence is not an error the reviewer needs */ }
  });
}

/* ------------------------------------------------ 2. audit log */
let logsState = {sortKey: "timestamp", sortDir: -1, rows: []};

$("#reload-logs").addEventListener("click", loadLogs);
$("#filter-decision").addEventListener("change", loadLogs);
$("#filter-since").addEventListener("change", loadLogs);
$("#filter-until").addEventListener("change", loadLogs);
document.querySelectorAll("#logs-table th[data-sort]").forEach((th) => {
  th.addEventListener("click", () => {
    const key = th.dataset.sort;
    logsState.sortDir = logsState.sortKey === key ? -logsState.sortDir : -1;
    logsState.sortKey = key;
    renderLogs();
  });
});

async function loadLogs() {
  const params = new URLSearchParams();
  if ($("#filter-decision").value !== "all") params.set("decision", $("#filter-decision").value);
  if ($("#filter-since").value) params.set("since", $("#filter-since").value);
  if ($("#filter-until").value) params.set("until", $("#filter-until").value);
  try {
    const data = await api(`/api/logs?${params}`);
    logsState.rows = data.rows;
    renderLogs();
  } catch (e) {
    $("#logs-count").textContent = `Failed to load logs: ${e.message}`;
  }
}

function renderLogs() {
  const {sortKey, sortDir, rows} = logsState;
  const sorted = [...rows].sort((a, b) => {
    const va = a[sortKey] ?? "", vb = b[sortKey] ?? "";
    return (va > vb ? 1 : va < vb ? -1 : 0) * sortDir;
  });
  const tbody = $("#logs-table tbody");
  if (!sorted.length) {
    tbody.innerHTML = `<tr><td colspan="8" class="muted" style="text-align:center;padding:1.5rem">no data yet</td></tr>`;
    $("#logs-count").textContent = "";
    return;
  }
  tbody.innerHTML = sorted.map((r) => `
    <tr>
      <td class="mono-cell">${esc((r.timestamp || "").replace("T", " ").slice(0, 19))}</td>
      <td class="snippet" title="${esc(r.user_prompt)}">${esc(r.user_prompt)}</td>
      <td>${decisionBadge(r.decision)}</td>
      <td class="mono-cell">${fmt(r.risk_score)}</td>
      <td class="mono-cell">${fmt(r.rule_signal)}</td>
      <td class="mono-cell">${fmt(r.llm_signal)}${r.llm_used_fallback ? "*" : ""}</td>
      <td class="mono-cell">${r.constitution_signal === null || r.constitution_signal === undefined
        ? "—" : fmt(r.constitution_signal)}${r.constitution_fallback ? "*" : ""}</td>
      <td><button class="flag-btn" data-rid="${esc(r.request_id)}" ${r.human_flagged ? "disabled" : ""}>
        ${r.human_flagged ? "flagged" : "flag"}</button></td>
    </tr>`).join("");
  $("#logs-count").textContent =
    `${sorted.length} row(s). * = fallback (check unavailable, not a model judgment). Scores as recorded at decision time.`;
  tbody.querySelectorAll(".flag-btn:not(:disabled)").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await api(`/api/logs/${encodeURIComponent(btn.dataset.rid)}/flag`, {method: "POST"});
        btn.disabled = true;
        btn.textContent = "flagged";
      } catch (e) { alert(`Flag failed: ${e.message}`); }
    });
  });
}

/* ------------------------------------------------ 3. constitution */
async function loadConstitution() {
  try {
    const c = await api("/api/constitution");
    $("#constitution-version").textContent = `v${c.version}`;
    $("#principles-list").innerHTML = c.principles.length
      ? c.principles.map((p) => `
        <div class="principle-card">
          <span class="p-id">${esc(p.id)}</span>
          <span class="p-ver">· added v${esc(p.version_added)}</span>
          <div>${esc(p.principle_text)}</div>
          <div class="p-rationale">${esc(p.rationale)}</div>
        </div>`).join("")
      : `<p class="muted">no data yet</p>`;

    $("#pending-list").innerHTML = c.pending.length
      ? c.pending.map((p) => `
        <div class="pending-card">
          <span class="p-id mono">${esc(p.principle_id)}</span>
          <div>${esc(p.principle_text)}</div>
          <div class="p-rationale muted">Rationale: ${esc(p.rationale)}</div>
          <div class="p-rationale muted">How it catches the case: ${esc(p.drafted_reasoning)}</div>
          <div class="trigger-case">${esc(JSON.stringify(p.triggered_by, null, 1))}</div>
          <div class="pending-actions">
            <button data-act="approve" data-id="${p.id}">Approve</button>
            <button data-act="reject" data-id="${p.id}">Reject</button>
            <input type="text" placeholder="reviewer name" data-actor="${p.id}" style="max-width:12rem">
          </div>
        </div>`).join("")
      : `<p class="muted">Nothing pending. Run the adaptive scan (Streamlit or CLI) after a benchmark run or after flagging requests in the Audit Log.</p>`;

    $("#changelog-table tbody").innerHTML = c.changelog.length
      ? c.changelog.map((e) => `
        <tr>
          <td class="mono-cell">v${esc(e.version)}</td>
          <td>${esc(e.action)}</td>
          <td class="mono-cell">${esc(e.principle_id)}</td>
          <td>${esc(e.actor)}</td>
          <td class="mono-cell">${esc((e.timestamp || "").replace("T", " ").slice(0, 19))}</td>
          <td>${esc(e.reason || "")}</td>
        </tr>`).join("")
      : `<tr><td colspan="6" class="muted" style="text-align:center">no data yet</td></tr>`;

    document.querySelectorAll(".pending-actions button").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.dataset.id;
        const actor = document.querySelector(`[data-actor="${id}"]`).value.trim() || "anonymous";
        const reason = btn.dataset.act === "reject" ? (prompt("Reason for rejection:") || "") : null;
        if (btn.dataset.act === "reject" && reason === null) return;
        try {
          await api(`/api/constitution/pending/${id}/${btn.dataset.act}`, {
            method: "POST", headers: {"Content-Type": "application/json"},
            body: JSON.stringify({actor, reason}),
          });
          loadConstitution();
        } catch (e) { alert(`Action failed: ${e.message}`); }
      });
    });
  } catch (e) {
    $("#principles-list").innerHTML = `<p class="muted">Failed to load: ${esc(e.message)}</p>`;
  }
}

/* ------------------------------------------------ 4. benchmark */
async function loadBenchmark() {
  const body = $("#benchmark-body");
  try {
    const b = await api("/api/benchmark");
    if (!b.has_data) {
      body.innerHTML = `<p class="muted empty-note">no data yet — run <code>python evaluation/evaluate.py</code> to produce results</p>`;
      return;
    }
    $("#benchmark-source").textContent =
      `Source: evaluation/metrics_summary.json + results.json (produced by evaluation/evaluate.py). ` +
      `LLM calls were ${b.real_llm_calls_used ? "real" : "NOT available (fallback run)"} during this run.`;
    const m = b.metrics;
    body.innerHTML = `
      <div class="metric-row">
        <div class="metric-card"><div class="score-label">precision</div><div class="metric-value">${pct(m.precision)}</div></div>
        <div class="metric-card"><div class="score-label">recall</div><div class="metric-value">${pct(m.recall)}</div></div>
        <div class="metric-card"><div class="score-label">attack success rate</div><div class="metric-value">${pct(m.attack_success_rate)}</div></div>
        <div class="metric-card"><div class="score-label">false positive rate</div><div class="metric-value">${pct(m.false_positive_rate)}</div></div>
      </div>
      <div class="bench-tables">
        <div>
          <h3 style="margin-top:0">By attack category</h3>
          <div class="table-wrap"><table>
            <thead><tr><th>Category</th><th>Flagged</th><th>Total</th><th></th></tr></thead>
            <tbody>${Object.entries(b.by_category).map(([cat, v]) => `
              <tr>
                <td class="mono-cell">${esc(cat)}</td>
                <td class="mono-cell">${v.flagged}</td>
                <td class="mono-cell">${v.total}</td>
                <td><div class="score-bar" style="margin:0"><div style="width:${v.total ? Math.round(100 * v.flagged / v.total) : 0}%"></div></div></td>
              </tr>`).join("")}</tbody>
          </table></div>
        </div>
        <div>
          <h3 style="margin-top:0">Signal attribution of flagged attacks</h3>
          <div class="table-wrap"><table>
            <thead><tr><th>Attribution</th><th>Count</th></tr></thead>
            <tbody>
              <tr><td>Rule matched + LLM live</td><td class="mono-cell">${b.attribution.rule_and_llm}</td></tr>
              <tr><td>Rule matched, LLM in fallback</td><td class="mono-cell">${b.attribution.rule_only_support}</td></tr>
              <tr><td>LLM-only (no rule match)</td><td class="mono-cell">${b.attribution.llm_only}</td></tr>
              <tr><td>Constitution-only</td><td class="mono-cell">n/a</td></tr>
            </tbody>
          </table></div>
          <p class="muted">A full per-signal ablation (rule-only / LLM-only / constitution-only pipelines) has not been run; the counts above are derived from per-row fields recorded during the single benchmark run, and per-row constitution attribution is not recorded in results.json — shown as n/a rather than estimated.</p>
        </div>
      </div>
      <div class="caveat">
        <strong>Honest caveat:</strong> n=${b.n} prompts, single run, benchmark authored alongside the detector.
        100% recall on this set cannot be distinguished from benchmark overfitting.
        See the <a href="https://github.com/manaal6/Aura-Shield/blob/main/docs/technical-report.md" target="_blank" rel="noopener">technical report</a>, Section 7.
      </div>`;
  } catch (e) {
    body.innerHTML = `<p class="muted empty-note">Failed to load: ${esc(e.message)}</p>`;
  }
}
const pct = (v) => (v === null || v === undefined) ? "—" : `${(v * 100).toFixed(2)}%`;
