// ─── State ─────────────────────────────────────────────────────────────────
const state = {
  clientName: 'ABC Company',
  pricingRequestId: 'PR-001',
  kickoff: {},
  bidScore: { score: null, recommendation: null, inputs: {} },
  lanes: [],
  chatHistory: [],
};

// ─── Nav ────────────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('page-' + tab.dataset.page).classList.add('active');
  });
});

// ─── Client info ────────────────────────────────────────────────────────────
document.getElementById('client-name-input')?.addEventListener('input', e => {
  state.clientName = e.target.value;
  document.getElementById('client-display').textContent = e.target.value || 'No client';
});
document.getElementById('pr-id-input')?.addEventListener('input', e => {
  state.pricingRequestId = e.target.value;
});

// ─── Bid Score ──────────────────────────────────────────────────────────────
async function loadScoreOptions() {
  const res = await fetch('/api/score/options');
  const options = await res.json();
  const container = document.getElementById('score-form');
  if (!container) return;

  const labels = {
    customer_segment: 'Customer Segment', company_size: 'Company Size',
    industry: 'Industry', commodity: 'Commodity', value_proposition: 'Value Proposition',
    willingness_trials: 'Willingness to Run Trials', stakeholder_relationship: 'Stakeholder Relationship',
    customer_persona: 'Customer Persona', customer_status: 'Customer Status',
    air_volume: 'Air Volume per RFP', lane_serviceability: 'Lane Serviceability',
    volume_details: 'Volume Details', msa_penalty: 'MSA / Penalty',
    accept_pss: 'Accept PSS', rate_type: 'Rate Type', special_requirements: 'Special Requirements',
  };

  container.innerHTML = '';
  for (const [field, config] of Object.entries(options)) {
    const row = document.createElement('div');
    row.className = 'score-row';
    const label = document.createElement('label');
    label.textContent = labels[field] || field;
    const sel = document.createElement('select');
    sel.innerHTML = '<option value="">— Select —</option>';
    for (const [opt] of Object.entries(config.options)) {
      const o = document.createElement('option');
      o.value = opt; o.textContent = opt;
      sel.appendChild(o);
    }
    sel.dataset.field = field;
    sel.addEventListener('change', () => { state.bidScore.inputs[field] = sel.value; });
    const weight = document.createElement('span');
    weight.className = 'score-weight';
    weight.textContent = `${Math.round(config.weight * 100)}%`;
    row.appendChild(label); row.appendChild(sel); row.appendChild(weight);
    container.appendChild(row);
  }
}

async function calculateScore() {
  const res = await fetch('/api/score', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state.bidScore.inputs),
  });
  const data = await res.json();
  state.bidScore.score = data.score;
  state.bidScore.recommendation = data.recommendation;
  updateScoreDisplay(data.score, data.recommendation);
}

function updateScoreDisplay(score, rec) {
  const el = document.getElementById('score-result');
  if (!el) return;
  const cls = score >= 80 ? 'high' : score >= 60 ? 'mid' : 'low';
  const tier = score >= 80 ? 'Ideal — High Win Probability'
    : score >= 60 ? 'Good Probability — Build Strategy'
    : score >= 45 ? 'Low Probability — Deprioritize'
    : 'Very Low — Not Recommended';
  el.innerHTML = `
    <div class="score-ring">
      <div class="score-circle ${cls}">${score}</div>
      <div class="score-meta"><strong>${tier}</strong>${rec}</div>
    </div>
    <div style="margin-top:12px;font-size:11px;color:var(--muted);display:flex;gap:8px;flex-wrap:wrap">
      <span style="padding:3px 8px;border-radius:4px;background:rgba(46,204,113,.15);color:var(--green)">80+ Ideal</span>
      <span style="padding:3px 8px;border-radius:4px;background:rgba(243,156,18,.15);color:var(--yellow)">60–79 Good</span>
      <span style="padding:3px 8px;border-radius:4px;background:rgba(231,76,60,.15);color:var(--red)">45–59 Low</span>
      <span style="padding:3px 8px;border-radius:4px;background:rgba(136,146,170,.15);color:var(--muted)">0–44 Very Low</span>
    </div>`;
  // Update sidebar
  const sidebar = document.getElementById('sidebar-score');
  if (sidebar) {
    sidebar.innerHTML = `<div class="score-ring">
      <div class="score-circle ${cls}">${score}</div>
      <div class="score-meta"><strong>${tier}</strong><span style="display:block;margin-top:3px">${rec.substring(0, 55)}...</span></div>
    </div>`;
  }
}

// ─── Lanes ───────────────────────────────────────────────────────────────────
function renderLaneSidebar() {
  const list = document.getElementById('lane-list');
  if (!list) return;
  if (state.lanes.length === 0) {
    list.innerHTML = '<div style="color:var(--muted);font-size:12px;text-align:center;padding:12px">No lanes added yet</div>';
    return;
  }
  list.innerHTML = state.lanes.map((lane, i) => {
    const origin = lane.origin_airport || lane.origin_city || '?';
    const dest = lane.destination_airport || lane.destination_city || '?';
    const fin = lane._financials;
    const nr = fin ? `$${fin.nr_per_shipment?.toFixed(0)} NR/shipment` : '';
    return `<div class="lane-item" onclick="editLane(${i})">
      <div class="lane-item-route">${origin} → ${dest}</div>
      <div class="lane-item-meta">${lane.service_tier || 'STD'} · ${lane.chargeable_weight_kg || 0}kg CW</div>
      ${nr ? `<div class="lane-item-nr">${nr}</div>` : ''}
    </div>`;
  }).join('');
}

function renderLanesTable() {
  const tbody = document.getElementById('lanes-tbody');
  if (!tbody) return;
  if (state.lanes.length === 0) {
    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:var(--muted);padding:30px">No lanes added yet. Click "+ Add Lane" to get started.</td></tr>';
    return;
  }
  tbody.innerHTML = state.lanes.map((lane, i) => {
    const fin = lane._financials || {};
    const origin = `${lane.origin_city || ''} (${lane.origin_airport || '-'})`;
    const dest = `${lane.destination_city || ''} (${lane.destination_airport || '-'})`;
    const tierClass = { STD: 'tag-std', EXP: 'tag-exp', DEF: 'tag-def' }[lane.service_tier] || 'tag-std';
    const awardStatus = lane.award_status === '1' ? '<span style="color:var(--green);font-weight:700">Awarded</span>'
      : lane.award_status === '0' ? '<span style="color:var(--red)">Lost</span>'
      : '<span style="color:var(--muted)">Pending</span>';
    const roundLabel = lane.round ? `R${lane.round}` : 'R1';
    return `<tr>
      <td>${lane.lane_id}</td>
      <td>${origin}</td>
      <td>${dest}</td>
      <td><span class="tag ${tierClass}">${lane.service_tier || 'STD'}</span></td>
      <td style="color:var(--muted)">${roundLabel}</td>
      <td>${lane.chargeable_weight_kg?.toLocaleString() || '-'} kg</td>
      <td>$${lane.sell_rate_per_kg || '-'}/kg</td>
      <td>$${fin.cost_per_kg || '-'}/kg</td>
      <td style="color:var(--green)">$${fin.nr_per_shipment?.toFixed(0) || '-'}</td>
      <td style="color:var(--muted)">${fin.take_rate_pct || '-'}%</td>
      <td>${awardStatus}</td>
      <td>
        <button class="btn btn-sm" onclick="editLane(${i})">Edit</button>
        <button class="btn btn-sm" style="margin-left:4px" onclick="deleteLane(${i})">✕</button>
      </td>
    </tr>`;
  }).join('');
  updateFinancialSummary();
}

function updateFinancialSummary() {
  const fins = state.lanes.map(l => l._financials).filter(Boolean);
  if (!fins.length) return;
  const totalNR = fins.reduce((s, f) => s + (f.total_net_revenue || 0), 0);
  const avgTake = fins.reduce((s, f) => s + (f.take_rate_pct || 0), 0) / fins.length;
  const totalCW = state.lanes.reduce((s, l) => s + (l.chargeable_weight_kg || 0), 0);
  const awarded = state.lanes.filter(l => l.award_status === '1').length;

  setEl('fin-total-nr', `$${(totalNR/1000).toFixed(1)}K`);
  setEl('fin-avg-take', `${avgTake.toFixed(1)}%`);
  setEl('fin-total-cw', `${totalCW.toLocaleString()} kg`);
  setEl('fin-lanes', state.lanes.length);
  // also sync lanes page cards
  setEl('fin-total-nr2', `$${(totalNR/1000).toFixed(1)}K`);
  setEl('fin-avg-take2', `${avgTake.toFixed(1)}%`);
  setEl('fin-total-cw2', `${totalCW.toLocaleString()} kg`);
  setEl('fin-lanes2', state.lanes.length);
  setEl('fin-awarded2', awarded);
}

function setEl(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }

let editingLaneIndex = null;

function openLaneModal(index = null) {
  editingLaneIndex = index;
  const modal = document.getElementById('lane-modal');
  const lane = index !== null ? state.lanes[index] : {};
  document.getElementById('modal-title').textContent = index !== null ? `Edit Lane ${lane.lane_id}` : 'Add New Lane';

  const allFields = ['origin_country','origin_city','origin_airport','destination_country','destination_city',
    'destination_airport','service_tier','chargeable_weight_kg','total_shipments','avg_shipment_kg',
    'effective_date','expiration_date','incoterms','round',
    'dangerous_goods','stackable','packaging','award_status',
    'origin_currency','pickup_min','pickup_kg_100','pickup_kg_500','pickup_kg_1000','pickup_kg_2000',
    'origin_thc','screening','doc_fee','export_customs',
    'main_currency',
    'buy_rate_min','buy_rate_45','buy_rate_100','buy_rate_300','buy_rate_500','buy_rate_per_kg','buy_rate_2000',
    'sell_rate_min','sell_rate_45','sell_rate_100','sell_rate_300','sell_rate_500','sell_rate_per_kg','sell_rate_2000',
    'fuel_surcharge','security_charge','ams_ens','acas','pss','pss_effective','pss_expiration',
    'air_base_markup','airline','routing','flights_per_week','transit_min','transit_max',
    'dest_currency','delivery_min','delivery_kg_100','delivery_kg_500','delivery_kg_1000','delivery_kg_2000',
    'dest_thc','import_service','import_customs','doc_turnover',
    'extra_charge_1_name','extra_charge_1_amount','extra_charge_2_name','extra_charge_2_amount',
    'margin_recommendation','tonnage_cap',
    'bundled_lane','carrier_partner','procurement_notes','round_feedback','assumptions'];

  allFields.forEach(f => {
    const el = document.getElementById('lane-' + f);
    if (el) el.value = lane[f] !== undefined ? lane[f] : '';
  });
  // Reset QA panel on open
  const qaPanel = document.getElementById('rate-qa-panel');
  if (qaPanel) qaPanel.style.display = 'none';
  const qaResults = document.getElementById('rate-qa-results');
  if (qaResults) qaResults.innerHTML = '';
  const ccyMsg = document.getElementById('currency-autofill-msg');
  if (ccyMsg) ccyMsg.textContent = '';
  modal.style.display = 'flex';
  attachModalQATrigger();
}

function closeLaneModal() {
  document.getElementById('lane-modal').style.display = 'none';
  editingLaneIndex = null;
}

async function saveLane() {
  const fields = ['origin_country','origin_city','origin_airport','destination_country','destination_city',
    'destination_airport','service_tier','chargeable_weight_kg','total_shipments','avg_shipment_kg',
    'effective_date','expiration_date','incoterms','round',
    'dangerous_goods','stackable','packaging','award_status',
    'origin_currency','pickup_min','pickup_kg_100','pickup_kg_500','pickup_kg_1000','pickup_kg_2000',
    'origin_thc','screening','doc_fee','export_customs',
    'main_currency',
    'buy_rate_min','buy_rate_45','buy_rate_100','buy_rate_300','buy_rate_500','buy_rate_per_kg','buy_rate_2000',
    'sell_rate_min','sell_rate_45','sell_rate_100','sell_rate_300','sell_rate_500','sell_rate_per_kg','sell_rate_2000',
    'fuel_surcharge','security_charge','ams_ens','acas','pss','pss_effective','pss_expiration',
    'air_base_markup','airline','routing','flights_per_week','transit_min','transit_max',
    'dest_currency','delivery_min','delivery_kg_100','delivery_kg_500','delivery_kg_1000','delivery_kg_2000',
    'dest_thc','import_service','import_customs','doc_turnover',
    'extra_charge_1_name','extra_charge_1_amount','extra_charge_2_name','extra_charge_2_amount',
    'margin_recommendation','tonnage_cap',
    'bundled_lane','carrier_partner','procurement_notes','round_feedback','assumptions'];

  const numericFields = new Set(['chargeable_weight_kg','total_shipments','avg_shipment_kg',
    'pickup_min','pickup_kg_100','pickup_kg_500','pickup_kg_1000','pickup_kg_2000',
    'origin_thc','screening','doc_fee','export_customs',
    'buy_rate_min','buy_rate_45','buy_rate_100','buy_rate_300','buy_rate_500','buy_rate_per_kg','buy_rate_2000',
    'sell_rate_min','sell_rate_45','sell_rate_100','sell_rate_300','sell_rate_500','sell_rate_per_kg','sell_rate_2000',
    'fuel_surcharge','security_charge','ams_ens','acas','pss','air_base_markup','flights_per_week',
    'delivery_min','delivery_kg_100','delivery_kg_500','delivery_kg_1000','delivery_kg_2000',
    'dest_thc','import_service','import_customs','doc_turnover','transit_min','transit_max',
    'extra_charge_1_amount','extra_charge_2_amount','margin_recommendation','tonnage_cap']);

  const lane = {};
  fields.forEach(f => {
    const el = document.getElementById('lane-' + f);
    if (el && el.value !== '') {
      lane[f] = numericFields.has(f) ? parseFloat(el.value) : el.value;
    }
  });

  // Compute financials
  try {
    const res = await fetch('/api/lanes/financials', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(lane),
    });
    lane._financials = await res.json();
  } catch (e) {}

  if (editingLaneIndex !== null) {
    lane.lane_id = state.lanes[editingLaneIndex].lane_id;
    state.lanes[editingLaneIndex] = lane;
  } else {
    lane.lane_id = state.lanes.length + 1;
    state.lanes.push(lane);
  }

  closeLaneModal();
  renderLaneSidebar();
  renderLanesTable();
}

function editLane(i) { openLaneModal(i); }
function deleteLane(i) {
  if (!confirm('Remove this lane?')) return;
  state.lanes.splice(i, 1);
  state.lanes.forEach((l, idx) => { l.lane_id = idx + 1; });
  renderLaneSidebar();
  renderLanesTable();
}

// ─── Suggest Rates ───────────────────────────────────────────────────────────
async function suggestRates() {
  const fields = ['origin_airport','destination_airport','service_tier','chargeable_weight_kg','avg_shipment_kg'];
  const lane = {};
  fields.forEach(f => {
    const el = document.getElementById('lane-' + f);
    if (el && el.value) lane[f] = el.value;
  });
  const btn = document.getElementById('suggest-btn');
  btn.textContent = 'Thinking...'; btn.disabled = true;
  try {
    const res = await fetch('/api/lanes/suggest-rates', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lane }),
    });
    const data = await res.json();
    document.getElementById('rate-suggestion').innerHTML =
      `<div class="density-result"><pre style="white-space:pre-wrap;font-size:12px;font-family:inherit">${data.suggestion}</pre></div>`;
  } finally {
    btn.textContent = '✨ AI Suggest Rates'; btn.disabled = false;
  }
}

// ─── Chat ────────────────────────────────────────────────────────────────────
function getBidContext() {
  return {
    client_name: state.clientName,
    pricing_request_id: state.pricingRequestId,
    bid_score: state.bidScore,
    lanes: state.lanes,
  };
}

function renderMessage(role, content) {
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = `
    <div class="msg-avatar">${role === 'ai' ? 'AI' : 'U'}</div>
    <div class="msg-bubble">${role === 'ai' ? marked(content) : escHtml(content)}</div>`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return div;
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
}

function marked(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, m => `<ul>${m}</ul>`)
    .replace(/\n{2,}/g, '</p><p>')
    .replace(/^(?!<[hpuol])(.+)$/gm, '<p>$1</p>')
    .replace(/<p><\/p>/g, '');
}

async function sendChat() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  input.style.height = '42px';

  state.chatHistory.push({ role: 'user', content: text });
  renderMessage('user', text);

  // Typing indicator
  const msgs = document.getElementById('chat-messages');
  const typing = document.createElement('div');
  typing.className = 'msg ai';
  typing.innerHTML = '<div class="msg-avatar">AI</div><div class="msg-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div>';
  msgs.appendChild(typing);
  msgs.scrollTop = msgs.scrollHeight;

  document.getElementById('send-btn').disabled = true;
  try {
    const res = await fetch('/api/chat/stream', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: state.chatHistory, bid_data: getBidContext() }),
    });
    typing.remove();

    const msgs = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'msg ai';
    div.innerHTML = '<div class="msg-avatar">AI</div><div class="msg-bubble"></div>';
    msgs.appendChild(div);
    const bubble = div.querySelector('.msg-bubble');

    let fullText = '';
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const raw = line.slice(6).trim();
        if (raw === '[DONE]') break;
        try {
          const parsed = JSON.parse(raw);
          fullText += parsed.text || '';
          bubble.innerHTML = marked(fullText);
          msgs.scrollTop = msgs.scrollHeight;
        } catch {}
      }
    }

    state.chatHistory.push({ role: 'assistant', content: fullText });
  } catch (e) {
    typing.remove();
    renderMessage('ai', 'Error connecting to agent. Please try again.');
  } finally {
    document.getElementById('send-btn').disabled = false;
  }
}

document.getElementById('chat-input')?.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
});

// ─── Density Calc ────────────────────────────────────────────────────────────
async function calcDensity() {
  const actual = parseFloat(document.getElementById('d-actual').value) || 0;
  const cbm = parseFloat(document.getElementById('d-cbm').value) || 0;
  const ratio = parseFloat(document.getElementById('d-ratio').value) || 6;
  const res = await fetch('/api/density/chargeable-weight', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actual_weight_kg: actual, volume_cbm: cbm, dim_ratio: ratio }),
  });
  const data = await res.json();
  document.getElementById('density-result').innerHTML = `
    <div class="density-result">
      <div class="big">${data.chargeable_weight_kg} kg</div>
      <div class="sub">Chargeable Weight (basis: ${data.basis})</div>
      <div style="margin-top:10px;font-size:12px;color:var(--muted)">
        Actual: ${data.actual_weight_kg} kg &nbsp;|&nbsp;
        Volumetric (1:${ratio}): ${data.volumetric_weight_kg} kg
      </div>
    </div>`;
}

// ─── Analyze ─────────────────────────────────────────────────────────────────
async function runAnalysis() {
  const btn = document.getElementById('analyze-btn');
  btn.textContent = 'Analyzing...'; btn.disabled = true;
  try {
    const res = await fetch('/api/analyze', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(getBidContext()),
    });
    const data = await res.json();
    document.getElementById('analysis-result').innerHTML =
      `<div class="msg-bubble" style="background:var(--surface2)">${marked(data.analysis)}</div>`;
  } finally {
    btn.textContent = '🔍 Run Full Bid Analysis'; btn.disabled = false;
  }
}

// ─── Export ──────────────────────────────────────────────────────────────────
async function exportQuote() {
  const res = await fetch('/api/export/quote-html', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(getBidContext()),
  });
  const data = await res.json();
  document.getElementById('quote-preview').innerHTML = data.html;
}

async function exportExcel() {
  const btn = document.getElementById('excel-btn');
  btn.textContent = 'Exporting...'; btn.disabled = true;
  try {
    const res = await fetch('/api/export/excel', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(getBidContext()),
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url;
    a.download = `Air_V7_${state.clientName}.xlsx`;
    a.click(); URL.revokeObjectURL(url);
  } finally {
    btn.textContent = '⬇ Export Air V7 Excel'; btn.disabled = false;
  }
}

// ─── Volume Analysis ─────────────────────────────────────────────────────────
async function runVolumeAnalysis() {
  const awardPct = parseFloat(document.getElementById('vol-award-pct').value) / 100 || 0.5;
  const ftl = parseFloat(document.getElementById('vol-ftl-threshold').value) || 4000;
  if (!state.lanes.length) { alert('Add lanes first.'); return; }

  const res = await fetch('/api/volume/analyze', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lanes: state.lanes, award_pct: awardPct, ftl_threshold: ftl }),
  });
  const data = await res.json();
  const summary = data.summary;

  const badge = document.getElementById('vol-consolidation-badge');
  badge.textContent = `${summary.lanes_that_can_consolidate}/${summary.total_lanes} lanes can consolidate`;

  let html = `<table class="lanes-table">
    <thead><tr><th>Lane</th><th>Annual CW (kg)</th><th>Weekly CW</th><th>Awarded Weekly</th><th>Award %</th><th>FTL Util %</th><th>Consolidation</th></tr></thead><tbody>`;
  for (const lane of data.lanes) {
    const consColor = lane.consolidation === 'Yes' ? 'var(--green)' : 'var(--muted)';
    html += `<tr>
      <td>${lane.port_pair}</td>
      <td>${lane.annual_cw_kg.toLocaleString()}</td>
      <td>${lane.weekly_cw_kg.toLocaleString()}</td>
      <td>${lane.awarded_weekly_kg.toLocaleString()}</td>
      <td>${(lane.award_pct * 100).toFixed(0)}%</td>
      <td>${lane.utilization_pct}%</td>
      <td style="color:${consColor};font-weight:600">${lane.consolidation}</td>
    </tr>`;
  }
  html += `</tbody></table>
    <div style="margin-top:10px;font-size:12px;color:var(--muted)">
      Total annual CW: <strong style="color:var(--text)">${summary.total_annual_cw_kg.toLocaleString()} kg</strong> &nbsp;|&nbsp;
      Awarded: <strong style="color:var(--text)">${summary.total_awarded_cw_kg.toLocaleString()} kg</strong>
    </div>`;
  document.getElementById('volume-table-container').innerHTML = html;
}

async function runSeasonality() {
  if (!state.lanes.length) { alert('Add lanes first.'); return; }
  const res = await fetch('/api/volume/seasonality', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lanes: state.lanes }),
  });
  const data = await res.json();
  const maxVol = Math.max(...data.monthly_volumes.map(m => m.volume_kg));

  let html = '<div style="display:flex;gap:8px;align-items:flex-end;height:120px;margin-bottom:8px">';
  for (const m of data.monthly_volumes) {
    const h = Math.round((m.volume_kg / maxVol) * 100);
    const isPeak = m.is_peak;
    html += `<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px">
      <div style="font-size:10px;color:var(--muted)">${(m.volume_kg/1000).toFixed(0)}t</div>
      <div style="width:100%;height:${h}px;background:${isPeak ? 'var(--accent)' : 'var(--surface2)'};border-radius:3px 3px 0 0;border:1px solid var(--border)"></div>
      <div style="font-size:10px;color:${isPeak ? 'var(--accent)' : 'var(--muted)'}">${m.month}</div>
    </div>`;
  }
  html += `</div>
    <div style="font-size:12px;color:var(--muted)">
      Peak months: <strong style="color:var(--accent)">${data.peak_months.join(', ')}</strong> &nbsp;|&nbsp;
      PSS applicable: <strong style="color:var(--yellow)">${data.pss_applicable_months.join(', ')}</strong> &nbsp;|&nbsp;
      Total annual: <strong style="color:var(--text)">${data.total_annual_kg.toLocaleString()} kg</strong>
    </div>`;
  document.getElementById('seasonality-result').innerHTML = html;
}

async function runWeightedAverage() {
  if (!state.lanes.length) { alert('Add lanes first.'); return; }
  const res = await fetch('/api/volume/weighted-average', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lanes: state.lanes }),
  });
  const data = await res.json();

  let html = `<div class="fin-card" style="margin-bottom:12px">
    <div class="fin-label">Weighted Avg Sell Rate</div>
    <div class="fin-value green">$${data.weighted_avg_sell_per_kg}/kg</div>
  </div>
  <table class="lanes-table"><thead><tr><th>Port Pair</th><th>CW (kg)</th><th>Sell/kg</th><th>Weight %</th><th>Contribution</th></tr></thead><tbody>`;
  for (const lane of data.lanes) {
    html += `<tr>
      <td>${lane.port_pair}</td>
      <td>${lane.cw_kg.toLocaleString()}</td>
      <td>$${lane.sell_per_kg}</td>
      <td>${lane.weight_pct}%</td>
      <td>$${lane.weighted_contribution}</td>
    </tr>`;
  }
  html += '</tbody></table>';
  document.getElementById('weighted-avg-result').innerHTML = html;
}

async function runMilkRun() {
  if (!state.lanes.length) { alert('Add lanes first.'); return; }
  const res = await fetch('/api/volume/milk-run', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lanes: state.lanes }),
  });
  const data = await res.json();

  let html = '';
  if (data.milk_run_candidates.length) {
    html += '<div style="margin-bottom:10px;font-size:13px;color:var(--green);font-weight:600">Milk Run Candidates</div>';
    html += '<table class="lanes-table"><thead><tr><th>Lane</th><th>Dest</th><th>Weekly CW</th><th>Recommendation</th></tr></thead><tbody>';
    for (const l of data.milk_run_candidates) {
      html += `<tr><td>${l.port_pair}</td><td>${l.dest_airport}</td><td>${l.weekly_cw_kg} kg</td><td style="color:var(--green)">${l.recommendation}</td></tr>`;
    }
    html += '</tbody></table>';
  }
  if (data.standard_delivery.length) {
    html += '<div style="margin:10px 0 8px;font-size:13px;color:var(--muted);font-weight:600">Standard Delivery</div>';
    html += '<table class="lanes-table"><thead><tr><th>Lane</th><th>Dest</th><th>Weekly CW</th><th>Recommendation</th></tr></thead><tbody>';
    for (const l of data.standard_delivery) {
      html += `<tr><td>${l.port_pair}</td><td>${l.dest_airport}</td><td>${l.weekly_cw_kg} kg</td><td style="color:var(--muted)">${l.recommendation}</td></tr>`;
    }
    html += '</tbody></table>';
  }
  if (!html) html = '<div style="color:var(--muted)">No lanes to assess.</div>';
  html += `<div style="margin-top:10px;font-size:11px;color:var(--muted);padding:8px;background:var(--surface2);border-radius:6px">${data.note}</div>`;
  document.getElementById('milk-run-result').innerHTML = html;
}

// ─── FX ──────────────────────────────────────────────────────────────────────
async function convertFX() {
  const amount = parseFloat(document.getElementById('fx-amount').value) || 0;
  const from = document.getElementById('fx-from').value;
  const to = document.getElementById('fx-to').value;
  const res = await fetch('/api/fx/convert', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount, from_currency: from, to_currency: to }),
  });
  const data = await res.json();
  document.getElementById('fx-result').innerHTML =
    `<div class="density-result"><div class="big">${data.result.toLocaleString(undefined, {maximumFractionDigits:4})} ${to}</div>
    <div class="sub">${amount} ${from} → ${data.result} ${to}</div></div>`;
}

async function loadFXRates() {
  const res = await fetch('/api/fx/rates');
  const data = await res.json();
  const el = document.getElementById('fx-rates-table');
  if (!el) return;
  const mainCurrencies = ['CNY','EUR','GBP','HKD','CAD','AUD','JPY','SGD'];
  el.innerHTML = mainCurrencies.map(ccy => {
    const rate = data.rates[ccy];
    return `<div style="display:flex;justify-content:space-between;font-size:12px;padding:3px 0;border-bottom:1px solid var(--border)">
      <span style="color:var(--muted)">1 ${ccy}</span>
      <span style="color:var(--text);font-weight:600">= $${rate?.toFixed(4) || '-'} USD</span>
    </div>`;
  }).join('');
}

// ─── Focus Lane / Ownership ───────────────────────────────────────────────────
async function checkFocusLane() {
  const origin = document.getElementById('fl-origin').value.trim().toUpperCase();
  const dest = document.getElementById('fl-dest').value.trim().toUpperCase();
  if (!origin || !dest) return;
  const res = await fetch(`/api/reference/focus-lane/${origin}/${dest}`);
  const data = await res.json();
  const el = document.getElementById('focus-lane-result');
  if (data.is_focus_lane) {
    el.innerHTML = `<div style="color:var(--green);font-weight:600;padding:8px;background:rgba(46,204,113,.1);border-radius:6px">
      ✓ ${origin}-${dest} is a 2026 Focus Lane (${data.lane.tradelane})</div>`;
  } else {
    el.innerHTML = `<div style="color:var(--muted);padding:8px;background:var(--surface2);border-radius:6px">
      ${origin}-${dest} is not a 2026 Focus Lane</div>`;
  }
}

async function checkOwnership() {
  const origin = document.getElementById('own-origin').value.trim().toUpperCase();
  const dest = document.getElementById('own-dest').value.trim().toUpperCase();
  if (!origin || !dest) return;
  const res = await fetch('/api/reference/lane-owners', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ origin_country: origin, destination_country: dest }),
  });
  const data = await res.json();
  document.getElementById('ownership-result').innerHTML =
    `<div style="font-size:12px;padding:8px;background:var(--surface2);border-radius:6px">
      <div>Air Freight: <strong style="color:var(--accent)">${data.origin_air_freight_owner}</strong></div>
      <div>Origin Trucking: <strong>${data.origin_trucking_owner}</strong></div>
      <div>Dest Trucking: <strong>${data.dest_trucking_owner}</strong></div>
    </div>`;
}

// ─── IPS Export ───────────────────────────────────────────────────────────────
async function exportIPS() {
  const btn = document.getElementById('ips-btn');
  btn.textContent = 'Exporting...'; btn.disabled = true;
  try {
    const res = await fetch('/api/export/ips-csv', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(getBidContext()),
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url;
    a.download = `IPS_Upload_${state.clientName}.csv`;
    a.click(); URL.revokeObjectURL(url);
  } finally {
    btn.textContent = '⬇ Export IPS CSV'; btn.disabled = false;
  }
}

// ─── Kickoff save/AI ─────────────────────────────────────────────────────────
function saveKickoff() {
  state.kickoff = {
    client_due_date: document.getElementById('ko-client-due')?.value,
    internal_due_date: document.getElementById('ko-internal-due')?.value,
    commercial_context: document.getElementById('ko-commercial')?.value,
    opportunity_strategy: document.getElementById('ko-strategy')?.value,
    expected_rounds: document.getElementById('ko-rounds')?.value,
    num_providers: document.getElementById('ko-providers')?.value,
    client_transit_times: document.getElementById('ko-transit')?.value,
    financial_penalties: document.getElementById('ko-penalties')?.value,
    fuel_policy: document.getElementById('ko-fuel')?.value,
    cargo_density: document.getElementById('ko-density')?.value,
    accepts_pss: document.getElementById('ko-pss')?.value,
    routing_requirements: document.getElementById('ko-routing')?.value,
    special_delivery: document.getElementById('ko-delivery')?.value,
    pricing_instructions: document.getElementById('ko-pricing-inst')?.value,
    award_methodology: document.getElementById('ko-award')?.value,
    pricing_assessment_logic: document.getElementById('ko-assessment')?.value,
    what_makes_us_win: document.getElementById('ko-win')?.value,
    other_notes: document.getElementById('ko-notes')?.value,
  };
  alert('Kickoff answers saved.');
}

async function askAIOnKickoff() {
  saveKickoff();
  const filled = Object.entries(state.kickoff).filter(([k, v]) => v).map(([k, v]) => `${k}: ${v}`).join('\n');
  if (!filled) { alert('Fill in some kickoff answers first.'); return; }
  const btn = document.querySelector('[onclick="askAIOnKickoff()"]');
  btn.textContent = 'Thinking...'; btn.disabled = true;
  try {
    const res = await fetch('/api/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: `Based on these kickoff answers, give me a pricing strategy recommendation and flag any risks:\n\n${filled}` }],
        bid_data: getBidContext(),
      }),
    });
    const data = await res.json();
    document.getElementById('kickoff-ai-advice').innerHTML =
      `<div class="msg-bubble" style="background:var(--surface2)">${marked(data.reply)}</div>`;
  } finally {
    btn.textContent = '✨ Get AI Strategy Advice'; btn.disabled = false;
  }
}

// ─── Shipment Data Upload ─────────────────────────────────────────────────────
async function uploadShipmentData() {
  const fileInput = document.getElementById('shipment-file');
  if (!fileInput.files.length) { alert('Select a CSV file first.'); return; }
  const file = fileInput.files[0];
  const csvText = await file.text();
  const awardPct = parseFloat(document.getElementById('sd-award-pct').value) / 100 || 0.5;
  const weeks = parseInt(document.getElementById('sd-weeks').value) || 52;
  const ftl = parseFloat(document.getElementById('sd-ftl').value) || 4000;

  const statusEl = document.getElementById('shipment-upload-status');
  statusEl.textContent = 'Analyzing...';
  statusEl.style.color = 'var(--muted)';

  try {
    const res = await fetch('/api/shipment/upload', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ csv_text: csvText, award_pct: awardPct, weeks, ftl_threshold: ftl }),
    });
    const data = await res.json();
    if (data.error) { statusEl.textContent = data.error; statusEl.style.color = 'var(--red)'; return; }

    statusEl.textContent = `Parsed ${data.total_shipments} shipments successfully.`;
    statusEl.style.color = 'var(--green)';
    document.getElementById('sd-consolidation-section').style.display = 'block';
    renderConsolidation(data.consolidation);
    renderDensity(data.density);
    renderShipmentSeasonality(data.seasonality);
    renderWeightBreakDist(data.weighted_average);
  } catch (e) {
    statusEl.textContent = 'Upload failed: ' + e.message;
    statusEl.style.color = 'var(--red)';
  }
}

async function downloadShipmentTemplate() {
  const res = await fetch('/api/shipment/template');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url;
  a.download = 'shipment_data_template.csv';
  a.click(); URL.revokeObjectURL(url);
}

function renderConsolidation(data) {
  const badge = document.getElementById('sd-con-badge');
  const consolidated = data.main_freight.filter(r => r.consolidation === 'Yes').length;
  badge.textContent = `${consolidated}/${data.main_freight.length} lanes can consolidate`;

  let html = `<div style="font-size:12px;color:var(--muted);margin-bottom:10px">
    Total shipments: <strong style="color:var(--text)">${data.total_shipments}</strong> &nbsp;|&nbsp;
    Total CW: <strong style="color:var(--text)">${(data.total_cw_kg||0).toLocaleString()} kg</strong> &nbsp;|&nbsp;
    Award: <strong style="color:var(--text)">${(data.settings.award_pct*100).toFixed(0)}%</strong> &nbsp;|&nbsp;
    FTL threshold: <strong style="color:var(--text)">${data.settings.ftl_threshold_kg.toLocaleString()} kg/week</strong>
  </div>`;

  html += `<table class="lanes-table"><thead><tr>
    <th>Port Pair</th><th>Total CW (kg)</th><th>Weekly CW</th><th>Awarded Weekly</th><th>FTL Util %</th><th>Consolidation</th>
  </tr></thead><tbody>`;
  for (const row of data.main_freight) {
    const consColor = row.consolidation === 'Yes' ? 'var(--green)' : 'var(--muted)';
    html += `<tr>
      <td>${row.port_pair}</td>
      <td>${(row.total_cw_kg||0).toLocaleString()}</td>
      <td>${row.weekly_cw_kg.toLocaleString()}</td>
      <td>${row.awarded_weekly_kg.toLocaleString()}</td>
      <td>${row.ftl_utilization_pct}%</td>
      <td style="color:${consColor};font-weight:600">${row.consolidation}</td>
    </tr>`;
  }
  html += '</tbody></table>';
  document.getElementById('sd-consolidation-table').innerHTML = html;
}

function renderDensity(data) {
  if (!data.by_lane || !data.by_lane.length) {
    document.getElementById('sd-density-table').innerHTML = '<div style="color:var(--muted)">No dimension data available.</div>';
    return;
  }
  const buckets = ['1:3 and below','1:4','1:5','1:6','1:7','1:8','1:9+'];
  let html = `<table class="lanes-table"><thead><tr>
    <th>Port Pair</th><th>Shipments</th><th>Dominant</th>`;
  for (const b of buckets) html += `<th style="font-size:11px">${b}</th>`;
  html += '</tr></thead><tbody>';

  for (const row of data.by_lane) {
    html += `<tr>
      <td>${row.port_pair}</td>
      <td>${row.total_shipments}</td>
      <td style="color:var(--accent);font-weight:600">${row.dominant_bucket} (${row.dominant_pct}%)</td>`;
    for (const b of buckets) {
      const pct = row.density_profile[b] || 0;
      const intensity = Math.min(pct / 50, 1);
      const bg = pct > 0 ? `rgba(100,160,255,${0.1 + intensity*0.5})` : 'transparent';
      html += `<td style="background:${bg};font-size:12px">${pct > 0 ? pct+'%' : ''}</td>`;
    }
    html += '</tr>';
  }
  html += '</tbody></table>';
  document.getElementById('sd-density-table').innerHTML = html;

  // Overall density
  if (data.overall && Object.keys(data.overall).length) {
    let overallHtml = `<div style="font-size:12px;color:var(--muted);margin-bottom:6px">Overall density profile (${data.total_shipments_with_dims} shipments with dimensions):</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap">`;
    for (const [label, pct] of Object.entries(data.overall)) {
      if (pct > 0) {
        const isNeutral = label === '1:6';
        const isDense = ['1:3 and below','1:4','1:5'].includes(label);
        const color = isDense ? 'var(--green)' : isNeutral ? 'var(--yellow)' : 'var(--muted)';
        overallHtml += `<div style="padding:4px 10px;border-radius:4px;background:var(--surface2);border:1px solid var(--border);font-size:12px">
          <span style="color:${color};font-weight:600">${label}</span> <span style="color:var(--text)">${pct}%</span>
        </div>`;
      }
    }
    overallHtml += '</div>';
    document.getElementById('sd-density-overall').innerHTML = overallHtml;
  }
}

function renderShipmentSeasonality(data) {
  if (!data.monthly || !data.monthly.length) return;
  const maxPct = Math.max(...data.monthly.map(m => m.pct));
  let html = '<div style="display:flex;gap:6px;align-items:flex-end;height:130px;margin-bottom:10px">';
  for (const m of data.monthly) {
    const h = maxPct > 0 ? Math.round((m.pct / maxPct) * 100) : 0;
    const isPeak = m.is_peak;
    const isPss = ['Sep','Oct','Nov','Dec'].includes(m.month);
    const barColor = isPeak ? 'var(--accent)' : isPss ? 'var(--yellow)' : 'var(--surface2)';
    html += `<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:3px">
      <div style="font-size:10px;color:var(--muted)">${m.pct.toFixed(1)}%</div>
      <div style="width:100%;height:${h}px;background:${barColor};border-radius:3px 3px 0 0;border:1px solid var(--border);min-height:4px"></div>
      <div style="font-size:10px;color:${isPeak ? 'var(--accent)' : 'var(--muted)'}">${m.month}</div>
    </div>`;
  }
  html += `</div>
  <div style="font-size:12px;color:var(--muted)">
    Peak months: <strong style="color:var(--accent)">${data.peak_months.join(', ') || 'None'}</strong> &nbsp;|&nbsp;
    PSS period (Sep–Dec): <strong style="color:var(--yellow)">${data.pss_volume_pct}% of volume</strong> &nbsp;|&nbsp;
    Total CW: <strong style="color:var(--text)">${(data.total_cw_kg||0).toLocaleString()} kg</strong>
  </div>`;
  document.getElementById('sd-seasonality-chart').innerHTML = html;
}

function renderWeightBreakDist(data) {
  if (!data.by_lane || !data.by_lane.length) return;
  const breaks = ['Min (<45kg)','+45kg','+100kg','+300kg','+500kg','+1000kg','+2000kg'];
  let html = `<table class="lanes-table"><thead><tr>
    <th>Port Pair</th><th>Shipments</th><th>Avg CW</th><th>Dominant Break</th>`;
  for (const b of breaks) html += `<th style="font-size:11px">${b}</th>`;
  html += '</tr></thead><tbody>';

  for (const row of data.by_lane) {
    html += `<tr>
      <td>${row.port_pair}</td>
      <td>${row.total_shipments}</td>
      <td>${row.avg_shipment_kg} kg</td>
      <td style="color:var(--accent);font-weight:600">${row.dominant_break} (${row.dominant_break_pct}%)</td>`;
    for (const b of breaks) {
      const info = row.break_distribution[b] || {pct:0,count:0};
      const intensity = Math.min(info.pct / 60, 1);
      const bg = info.pct > 0 ? `rgba(100,200,120,${0.1 + intensity*0.5})` : 'transparent';
      html += `<td style="background:${bg};font-size:12px">${info.pct > 0 ? info.pct+'%' : ''}</td>`;
    }
    html += '</tr>';
  }
  html += '</tbody></table>';
  document.getElementById('sd-weighted-avg-table').innerHTML = html;
}

// ─── Rate QA ──────────────────────────────────────────────────────────────────
async function runLaneQA() {
  // Gather current modal values
  const fields = ['origin_country','origin_city','origin_airport','destination_country','destination_city',
    'destination_airport','service_tier','effective_date','expiration_date',
    'buy_rate_min','buy_rate_45','buy_rate_100','buy_rate_300','buy_rate_500','buy_rate_per_kg','buy_rate_2000',
    'sell_rate_min','sell_rate_45','sell_rate_100','sell_rate_300','sell_rate_500','sell_rate_per_kg','sell_rate_2000',
    'pickup_min','pickup_kg_100','pickup_kg_500','pickup_kg_1000','pickup_kg_2000',
    'delivery_min','delivery_kg_100','delivery_kg_500','delivery_kg_1000','delivery_kg_2000'];

  const lane = {};
  fields.forEach(f => {
    const el = document.getElementById('lane-' + f);
    if (el && el.value !== '') lane[f] = el.value;
  });

  const res = await fetch('/api/lanes/qa', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(lane),
  });
  const data = await res.json();
  renderQAResults(data);
}

function renderQAResults(data) {
  const panel = document.getElementById('rate-qa-panel');
  const results = document.getElementById('rate-qa-results');
  panel.style.display = 'block';

  if (!data.violations || data.violations.length === 0) {
    panel.style.borderColor = 'var(--green)';
    results.innerHTML = '<div style="color:var(--green);font-weight:600">All rate checks passed</div>';
    return;
  }

  panel.style.borderColor = data.error_count > 0 ? '#c0392b' : 'var(--yellow)';
  let html = '';
  for (const v of data.violations) {
    const isError = v.severity === 'error';
    const color = isError ? '#e74c3c' : 'var(--yellow)';
    const bg = isError ? 'rgba(231,76,60,0.1)' : 'rgba(241,196,15,0.1)';
    html += `<div style="padding:6px 10px;border-radius:5px;background:${bg};margin-bottom:6px;font-size:12px">
      <span style="color:${color};font-weight:700">${isError ? 'ERROR' : 'WARN'}</span>
      <span style="color:var(--text);margin-left:8px">${escHtml(v.message)}</span>
    </div>`;
  }
  if (data.error_count > 0) {
    html = `<div style="font-size:12px;margin-bottom:8px;color:#e74c3c;font-weight:600">${data.error_count} error(s), ${data.warning_count} warning(s) — rates cannot be saved with errors</div>` + html;
  } else {
    html = `<div style="font-size:12px;margin-bottom:8px;color:var(--yellow)">${data.warning_count} warning(s) — review before finalizing</div>` + html;
  }
  results.innerHTML = html;
}

// ─── Currency Auto-fill ───────────────────────────────────────────────────────
async function autofillCurrencies() {
  const originCountry = document.getElementById('lane-origin_country')?.value?.trim();
  const destCountry = document.getElementById('lane-destination_country')?.value?.trim();
  if (!originCountry && !destCountry) {
    document.getElementById('currency-autofill-msg').textContent = 'Enter origin/destination country codes first.';
    return;
  }

  const res = await fetch('/api/currency/suggest', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ origin_country: originCountry, destination_country: destCountry }),
  });
  const data = await res.json();

  const originCcyEl = document.getElementById('lane-origin_currency');
  const mainCcyEl = document.getElementById('lane-main_currency');
  const destCcyEl = document.getElementById('lane-dest_currency');

  if (originCcyEl) setSelectValue(originCcyEl, data.origin_currency);
  if (mainCcyEl) setSelectValue(mainCcyEl, data.main_currency);
  if (destCcyEl) setSelectValue(destCcyEl, data.dest_currency);

  document.getElementById('currency-autofill-msg').textContent = data.note;
}

function setSelectValue(selectEl, value) {
  // Try to select existing option, otherwise add it
  const opts = Array.from(selectEl.options).map(o => o.value);
  if (opts.includes(value)) {
    selectEl.value = value;
  } else {
    const opt = document.createElement('option');
    opt.value = value; opt.textContent = value;
    selectEl.appendChild(opt);
    selectEl.value = value;
  }
}

// Trigger QA check whenever a rate field changes in the modal
function attachModalQATrigger() {
  const rateFields = ['buy_rate_min','buy_rate_45','buy_rate_100','buy_rate_300','buy_rate_500','buy_rate_per_kg','buy_rate_2000',
    'sell_rate_min','sell_rate_45','sell_rate_100','sell_rate_300','sell_rate_500','sell_rate_per_kg','sell_rate_2000'];
  rateFields.forEach(f => {
    const el = document.getElementById('lane-' + f);
    if (el) el.addEventListener('change', () => {
      // Only auto-run QA if panel is already visible (after first manual check)
      if (document.getElementById('rate-qa-panel').style.display !== 'none') {
        runLaneQA();
      }
    });
  });
}

// ─── Init ────────────────────────────────────────────────────────────────────
loadScoreOptions();
renderLanesTable();
renderLaneSidebar();
loadFXRates();

// Welcome message
setTimeout(() => {
  if (document.getElementById('chat-messages')) {
    renderMessage('ai', `Hi! I'm the **Air V7 Agent** — your air freight RFP pricing assistant.

I can help you with:
- **Kickoff questions** — capture commercial context and strategy
- **Bid scoring** — assess win probability
- **Lane pricing** — suggest buy/sell rates and surcharges
- **Financial analysis** — compute net revenue, take rates
- **Customer quotes** — generate client-facing rate summaries

To get started, set your client name and pricing request ID above, then tell me about the opportunity. Or use the tabs to fill in data directly.

What can I help you with today?`);
  }
}, 100);
