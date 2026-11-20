// IDBMS Frontend Controller

function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.tab-btn').forEach(el => {
    el.classList.remove('border-b-2', 'border-blue-500', 'text-blue-400', 'bg-slate-800/40');
    el.classList.add('text-slate-400');
  });

  const activeContent = document.getElementById(tabId);
  if (activeContent) activeContent.classList.remove('hidden');

  const activeBtn = document.getElementById(`btn-${tabId}`);
  if (activeBtn) {
    activeBtn.classList.add('border-b-2', 'border-blue-500', 'text-blue-400', 'bg-slate-800/40');
    activeBtn.classList.remove('text-slate-400');
  }

  if (tabId === 'tab-concurrency') {
    fetchLocks();
  }
}

async function refreshAll() {
  await fetchClusterStatus();
}

async function fetchClusterStatus() {
  try {
    const res = await fetch('/api/cluster/status');
    const data = await res.json();
    renderNodeCards(data.cluster_nodes);
  } catch (err) {
    console.error('Failed to fetch cluster status:', err);
  }
}

function renderNodeCards(nodes) {
  const container = document.getElementById('node-cards-container');
  if (!container) return;

  container.innerHTML = nodes.map(n => {
    const isOnline = n.status === 'ONLINE';
    const statusColor = isOnline ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border-rose-500/30';
    const badgeDot = isOnline ? 'bg-emerald-400' : 'bg-rose-400';

    return `
      <div class="p-5 rounded-2xl bg-slate-800/40 border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition">
        <div>
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-mono font-semibold text-slate-400">${n.node_id}</span>
            <span class="px-2 py-0.5 rounded-full text-[11px] font-medium border flex items-center gap-1.5 ${statusColor}">
              <span class="w-1.5 h-1.5 rounded-full ${badgeDot}"></span> ${n.status}
            </span>
          </div>
          <h3 class="font-bold text-slate-200 text-sm mb-1">${n.name}</h3>
          <p class="text-xs text-slate-400 mb-3"><i class="fa-solid fa-location-dot text-slate-500 mr-1"></i> Region: ${n.region}</p>

          <div class="space-y-1 text-xs border-t border-slate-800/80 pt-3">
            <div class="flex justify-between text-slate-400">
              <span>Accounts Hosted:</span>
              <span class="font-mono text-slate-200">${n.table_stats.accounts || 0}</span>
            </div>
            <div class="flex justify-between text-slate-400">
              <span>WAL Records:</span>
              <span class="font-mono text-slate-200">${n.wal_records || 0}</span>
            </div>
            <div class="flex justify-between text-slate-400">
              <span>Active Locks:</span>
              <span class="font-mono text-slate-200">${n.active_locks ? n.active_locks.length : 0}</span>
            </div>
          </div>
        </div>

        <div class="mt-4 pt-3 border-t border-slate-800 flex gap-2">
          <button onclick="toggleNodeFault('${n.node_id}', '${isOnline ? 'OFFLINE' : 'ONLINE'}')" class="flex-1 py-1.5 px-3 rounded-lg text-xs font-medium transition ${isOnline ? 'bg-rose-600/20 text-rose-300 hover:bg-rose-600/30 border border-rose-600/30' : 'bg-emerald-600/20 text-emerald-300 hover:bg-emerald-600/30 border border-emerald-600/30'}">
            ${isOnline ? '<i class="fa-solid fa-power-off mr-1"></i> Kill Node' : '<i class="fa-solid fa-play mr-1"></i> Start Node'}
          </button>
          <button onclick="toggleNodeFault('${n.node_id}', 'SIMULATE_ABORT')" title="Force cohort to vote ABORT in 2PC" class="py-1.5 px-3 rounded-lg text-xs font-medium bg-amber-600/20 text-amber-300 hover:bg-amber-600/30 border border-amber-600/30 transition">
            <i class="fa-solid fa-bug"></i>
          </button>
        </div>
      </div>
    `;
  }).join('');
}

async function toggleNodeFault(nodeId, action) {
  try {
    await fetch('/api/nodes/fault', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ node_id: nodeId, action: action })
    });
    fetchClusterStatus();
  } catch (err) {
    alert('Failed to toggle node fault: ' + err);
  }
}

async function togglePartition(partitioned) {
  const nodeA = document.getElementById('part-node-a').value;
  const nodeB = document.getElementById('part-node-b').value;
  const msgEl = document.getElementById('partition-status-msg');

  if (nodeA === nodeB) {
    msgEl.innerText = "Cannot partition a node from itself!";
    msgEl.className = "mt-3 text-xs text-rose-400";
    return;
  }

  try {
    const res = await fetch('/api/network/partition', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ node_a: nodeA, node_b: nodeB, partitioned: partitioned })
    });
    const data = await res.json();
    msgEl.innerText = partitioned
      ? `Network partition active between ${nodeA} and ${nodeB}. Packets will be dropped.`
      : `Network partition between ${nodeA} and ${nodeB} healed successfully.`;
    msgEl.className = partitioned ? "mt-3 text-xs text-rose-400 font-medium" : "mt-3 text-xs text-emerald-400 font-medium";
  } catch (err) {
    msgEl.innerText = 'Partition toggle failed: ' + err;
    msgEl.className = "mt-3 text-xs text-rose-400";
  }
}

// ----------------- TAB 2: Two-Phase Commit -----------------
async function trigger2PCTransfer() {
  const fromAcc = document.getElementById('transfer-from').value;
  const toAcc = document.getElementById('transfer-to').value;
  const amount = parseFloat(document.getElementById('transfer-amount').value);
  const badge = document.getElementById('2pc-badge');
  const container = document.getElementById('2pc-timeline-container');

  badge.innerText = "Executing 2PC...";
  badge.className = "px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400 animate-pulse";

  try {
    const res = await fetch('/api/transaction/transfer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from_account: fromAcc, to_account: toAcc, amount: amount })
    });

    const data = await res.json();

    if (!res.ok) {
      badge.innerText = "GLOBAL_ABORT";
      badge.className = "px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30";
      container.innerHTML = `
        <div class="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs">
          <div class="font-bold mb-1 flex items-center gap-2"><i class="fa-solid fa-triangle-exclamation"></i> 2PC Transaction Aborted</div>
          <div>${data.detail || "Transaction aborted by participant cohort or coordinator."}</div>
        </div>
      `;
      return;
    }

    badge.innerText = "GLOBAL_COMMIT";
    badge.className = "px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";

    const trace = data.trace || [];
    container.innerHTML = trace.map(t => {
      let icon = "fa-circle-info text-blue-400";
      let badgeColor = "bg-blue-500/10 text-blue-400";
      if (t.phase.includes("PREPARE")) { icon = "fa-paper-plane text-amber-400"; badgeColor = "bg-amber-500/10 text-amber-400"; }
      if (t.phase.includes("VOTE")) { icon = "fa-check-to-slot text-indigo-400"; badgeColor = "bg-indigo-500/10 text-indigo-400"; }
      if (t.phase.includes("DECISION")) { icon = "fa-gavel text-emerald-400"; badgeColor = "bg-emerald-500/10 text-emerald-400"; }
      if (t.phase.includes("ACK")) { icon = "fa-check-double text-teal-400"; badgeColor = "bg-teal-500/10 text-teal-400"; }

      return `
        <div class="timeline-step">
          <div class="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <div class="flex items-center justify-between mb-1">
              <span class="px-2 py-0.5 rounded font-mono font-semibold text-[10px] ${badgeColor}">
                <i class="fa-solid ${icon} mr-1"></i> ${t.phase}
              </span>
              <span class="text-slate-500 text-[10px]">${new Date(t.timestamp * 1000).toLocaleTimeString()}</span>
            </div>
            <div class="text-slate-300 font-medium">${t.event}</div>
            ${t.details && Object.keys(t.details).length ? `<pre class="mt-2 p-2 rounded bg-slate-950 font-mono text-[10px] text-slate-400 overflow-x-auto">${JSON.stringify(t.details, null, 2)}</pre>` : ''}
          </div>
        </div>
      `;
    }).join('');

    fetchClusterStatus();
  } catch (err) {
    badge.innerText = "NETWORK_ERROR";
    badge.className = "px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-400";
    container.innerHTML = `<div class="text-xs text-rose-400 p-4">Error executing transaction: ${err}</div>`;
  }
}

// ----------------- TAB 3: Distributed SQL -----------------
function setQueryTemplate(tpl) {
  const input = document.getElementById('sql-input');
  if (tpl === 'prune') {
    input.value = "SELECT * FROM accounts WHERE branch_id = 'BRANCH_LON'";
  } else if (tpl === 'join') {
    input.value = "SELECT accounts.account_id, branch_name, balance, currency FROM accounts JOIN branches ON accounts.branch_id = branches.branch_id WHERE branch_id = 'BRANCH_LON'";
  } else if (tpl === 'vertical') {
    input.value = "SELECT cust_id, name, branch_id, credit_score, risk_tier FROM customers";
  } else if (tpl === 'agg') {
    input.value = "SELECT branch_id, COUNT(account_id), SUM(balance) FROM accounts GROUP BY branch_id ORDER BY branch_id ASC";
  }
}

async function runSQLQuery() {
  const sql = document.getElementById('sql-input').value.trim();
  const metaInfo = document.getElementById('query-meta-info');
  const qepContainer = document.getElementById('qep-container');
  const tableWrapper = document.getElementById('query-result-table-wrapper');
  const countEl = document.getElementById('result-count');

  metaInfo.innerText = "Executing distributed query...";

  try {
    const res = await fetch('/api/query/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql: sql })
    });

    const data = await res.json();

    if (!res.ok) {
      metaInfo.innerText = `Error: ${data.detail || "Query execution failed"}`;
      metaInfo.className = "text-xs text-rose-400";
      return;
    }

    metaInfo.innerText = `Executed in ${data.execution_time_ms} ms | Nodes queried: ${data.nodes_queried.join(', ')}`;
    metaInfo.className = "text-xs text-emerald-400 font-medium";
    countEl.innerText = data.row_count;

    // Render QEP
    const plan = data.plan_explanation || {};
    qepContainer.innerHTML = `
      <div class="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
        <div class="flex justify-between items-center pb-2 border-b border-slate-800">
          <span class="text-slate-400">Join Strategy:</span>
          <span class="font-mono text-indigo-400 font-bold">${plan.join_strategy || 'NONE'}</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-slate-400">Target Nodes:</span>
          <span class="text-slate-200 font-mono">${(plan.target_nodes || []).join(', ')}</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-slate-400">Pruned Fragments:</span>
          <span class="text-emerald-400 font-mono">${(plan.pruned_nodes || []).length ? plan.pruned_nodes.join(', ') : 'None'}</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-slate-400">Est. Net Transfer:</span>
          <span class="text-amber-400 font-mono">${plan.total_estimated_network_bytes || 0} bytes</span>
        </div>
      </div>

      <div class="space-y-1.5 mt-3">
        <div class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Plan Steps:</div>
        ${(plan.plan_steps || []).map(s => `
          <div class="p-2 rounded-lg bg-slate-900/80 border border-slate-800 text-[11px]">
            <div class="font-bold text-slate-200 flex justify-between">
              <span>${s.step}</span>
              <span class="font-mono text-blue-400">${s.cost_ms}ms</span>
            </div>
            <div class="text-slate-400 text-[10px]">${s.type} on <span class="text-slate-300 font-mono">${s.node}</span></div>
          </div>
        `).join('')}
      </div>
    `;

    // Render Table
    if (!data.rows || data.rows.length === 0) {
      tableWrapper.innerHTML = '<div class="text-xs text-slate-400 italic p-4">Query returned 0 rows.</div>';
      return;
    }

    const cols = data.columns || Object.keys(data.rows[0]);
    tableWrapper.innerHTML = `
      <table class="w-full text-xs text-left divide-y divide-slate-800">
        <thead class="bg-slate-900 text-slate-300 font-semibold sticky top-0">
          <tr>
            ${cols.map(c => `<th class="px-3 py-2.5">${c}</th>`).join('')}
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800/60 font-mono text-slate-300">
          ${data.rows.map(r => `
            <tr class="hover:bg-slate-800/40 transition">
              ${cols.map(c => `<td class="px-3 py-2 text-slate-200">${r[c] !== undefined ? r[c] : ''}</td>`).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

  } catch (err) {
    metaInfo.innerText = "Error: " + err;
    metaInfo.className = "text-xs text-rose-400";
  }
}

// ----------------- TAB 4: Concurrency & Deadlocks -----------------
async function fetchLocks() {
  const container = document.getElementById('lock-tables-container');
  try {
    const res = await fetch('/api/concurrency/locks');
    const data = await res.json();

    container.innerHTML = Object.entries(data.locks_by_node).map(([nodeId, locks]) => `
      <div class="p-5 rounded-2xl bg-slate-800/40 border border-slate-800">
        <h3 class="font-bold text-sm text-slate-200 mb-3 flex items-center justify-between">
          <span><i class="fa-solid fa-server mr-2 text-blue-400"></i> ${nodeId} Lock Table</span>
          <span class="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-300">${locks.length} active</span>
        </h3>
        ${locks.length === 0 ? '<p class="text-xs text-slate-500 italic">No active locks held.</p>' : `
          <div class="space-y-2">
            ${locks.map(l => `
              <div class="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
                <div class="font-mono text-emerald-400 font-semibold mb-1">${l.resource}</div>
                <div class="text-[11px] text-slate-400">Exclusive Holder: <span class="font-mono text-rose-400">${l.exclusive_holder || 'None'}</span></div>
                <div class="text-[11px] text-slate-400">Shared Holders: <span class="font-mono text-blue-400">${l.shared_holders.length ? l.shared_holders.join(', ') : 'None'}</span></div>
                ${l.waiters.length ? `<div class="text-[10px] text-amber-400 mt-1">Waiters: ${l.waiters.map(w => `${w.tx_id} (${w.mode})`).join(', ')}</div>` : ''}
              </div>
            `).join('')}
          </div>
        `}
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to fetch locks:', err);
  }
}

async function runDeadlockDetection() {
  try {
    const res = await fetch('/api/concurrency/deadlock/detect', { method: 'POST' });
    const data = await res.json();
    alert(`Deadlock Detection Run Complete: ${data.active_deadlocks_resolved} deadlock cycle(s) detected and resolved.`);
    fetchLocks();
  } catch (err) {
    alert('Deadlock detection failed: ' + err);
  }
}

// ----------------- TAB 6: Benchmarks -----------------
async function runLiveEvaluation() {
  const btn = document.getElementById('btn-eval');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Running Benchmarks...';

  try {
    const res = await fetch('/api/evaluation/run', { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      const ts = Date.now();
      document.getElementById('chart-throughput').src = `/static/charts/benchmark_throughput.png?t=${ts}`;
      document.getElementById('chart-latency').src = `/static/charts/benchmark_latency.png?t=${ts}`;
      document.getElementById('chart-semijoin').src = `/static/charts/benchmark_semijoin.png?t=${ts}`;
      document.getElementById('chart-consistency').src = `/static/charts/benchmark_consistency.png?t=${ts}`;
      alert('Performance Evaluation Completed! Charts and metrics refreshed.');
    }
  } catch (err) {
    alert('Benchmark run failed: ' + err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-play"></i> Run Live Benchmark Suite';
  }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  fetchClusterStatus();
});
