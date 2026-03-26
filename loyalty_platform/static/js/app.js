// LoyaltyHub Frontend Application
const API = '/api';
let modal, toast, toastEl;

document.addEventListener('DOMContentLoaded', () => {
  modal = new bootstrap.Modal(document.getElementById('mainModal'));
  toastEl = document.getElementById('toast');
  toast = new bootstrap.Toast(toastEl, { delay: 3000 });

  // Sidebar toggle
  document.getElementById('sidebarToggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('collapsed');
  });

  // Navigation
  document.querySelectorAll('[data-page]').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      navigateTo(link.dataset.page);
    });
  });

  navigateTo('dashboard');
});

function navigateTo(page) {
  document.querySelectorAll('[data-page]').forEach(l => l.classList.remove('active'));
  const activeLink = document.querySelector(`[data-page="${page}"]`);
  if (activeLink) activeLink.classList.add('active');

  const titles = {
    dashboard: 'Dashboard', members: 'Members', tiers: 'Membership Tiers',
    activities: 'Activities', rewards: 'Rewards Catalog', campaigns: 'Campaigns',
    transactions: 'Recent Transactions'
  };
  document.getElementById('page-title').textContent = titles[page] || page;

  const pages = {
    dashboard: loadDashboard,
    members: loadMembers,
    tiers: loadTiers,
    activities: loadActivities,
    rewards: loadRewards,
    campaigns: loadCampaigns,
    transactions: loadTransactions,
  };
  if (pages[page]) pages[page]();
}

async function apiFetch(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

function showToast(message, type = 'success') {
  toastEl.className = `toast align-items-center text-white border-0 bg-${type}`;
  document.getElementById('toast-body').textContent = message;
  toast.show();
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString();
}

function tierBadge(tier) {
  if (!tier) return '<span class="text-muted">—</span>';
  return `<span class="tier-badge" style="background:${tier.color}20;color:${tier.color};border:1px solid ${tier.color}40">${tier.name}</span>`;
}

function pointsPill(pts, type = '') {
  if (type === 'earn') return `<span class="earn-pill">+${pts}</span>`;
  if (type === 'redeem') return `<span class="redeem-pill">${pts}</span>`;
  if (type === 'adjust') return `<span class="adjust-pill">${pts > 0 ? '+' : ''}${pts}</span>`;
  return `<span class="points-pill">${pts.toLocaleString()} pts</span>`;
}

// ─── DASHBOARD ───────────────────────────────────────────────────────────────
async function loadDashboard() {
  document.getElementById('main-content').innerHTML = `<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>`;
  const [summary, topMembers, recentTxns] = await Promise.all([
    apiFetch('/analytics/summary'),
    apiFetch('/analytics/top_members'),
    apiFetch('/analytics/recent_transactions'),
  ]);

  document.getElementById('main-content').innerHTML = `
    <div class="row g-4 mb-4">
      ${statCard('Total Members', summary.total_members, 'bi-people-fill', 'bg-primary')}
      ${statCard('Active Members', summary.active_members, 'bi-person-check-fill', 'bg-success')}
      ${statCard('Points Issued', summary.total_points_issued.toLocaleString(), 'bi-arrow-up-circle-fill', 'bg-warning')}
      ${statCard('Points Redeemed', summary.total_points_redeemed.toLocaleString(), 'bi-arrow-down-circle-fill', 'bg-info')}
    </div>

    <div class="row g-4 mb-4">
      <div class="col-lg-5">
        <div class="card h-100">
          <div class="card-header bg-white border-0 pt-3 pb-0 fw-semibold">Tier Breakdown</div>
          <div class="card-body">
            ${summary.tier_breakdown.map(tb => `
              <div class="d-flex align-items-center mb-3">
                <span class="tier-badge me-3" style="background:${tb.tier.color}20;color:${tb.tier.color};border:1px solid ${tb.tier.color}40;min-width:70px;text-align:center">${tb.tier.name}</span>
                <div class="flex-grow-1">
                  <div class="progress progress-tier">
                    <div class="progress-bar" style="width:${summary.total_members > 0 ? (tb.count/summary.total_members*100).toFixed(1) : 0}%;background:${tb.tier.color}"></div>
                  </div>
                </div>
                <span class="ms-3 text-muted small">${tb.count}</span>
              </div>`).join('')}
          </div>
        </div>
      </div>
      <div class="col-lg-7">
        <div class="card h-100">
          <div class="card-header bg-white border-0 pt-3 pb-0 fw-semibold">Top Members by Lifetime Points</div>
          <div class="card-body p-0">
            <table class="table table-hover mb-0">
              <thead><tr><th>#</th><th>Member</th><th>Tier</th><th>Lifetime Points</th></tr></thead>
              <tbody>
                ${topMembers.map((m, i) => `<tr>
                  <td class="text-muted">${i+1}</td>
                  <td><strong>${m.first_name} ${m.last_name}</strong><br><small class="text-muted">${m.email}</small></td>
                  <td>${tierBadge(m.tier)}</td>
                  <td>${pointsPill(m.lifetime_points)}</td>
                </tr>`).join('')}
                ${topMembers.length === 0 ? '<tr><td colspan="4" class="text-center text-muted py-3">No members yet</td></tr>' : ''}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header bg-white border-0 pt-3 pb-0 fw-semibold">Recent Transactions</div>
      <div class="card-body p-0">
        ${transactionTable(recentTxns)}
      </div>
    </div>`;
}

function statCard(label, value, icon, bgClass) {
  return `<div class="col-sm-6 col-xl-3">
    <div class="card stat-card">
      <div class="card-body d-flex align-items-center gap-3">
        <div class="stat-icon ${bgClass} bg-opacity-10">
          <i class="bi ${icon} ${bgClass.replace('bg-','text-')}"></i>
        </div>
        <div>
          <div class="text-muted small">${label}</div>
          <div class="fw-bold fs-4">${value}</div>
        </div>
      </div>
    </div>
  </div>`;
}

// ─── MEMBERS ─────────────────────────────────────────────────────────────────
async function loadMembers(page = 1, search = '') {
  const params = new URLSearchParams({ page, per_page: 15 });
  if (search) params.append('search', search);
  const data = await apiFetch(`/members?${params}`);
  const tiers = await apiFetch('/tiers');

  document.getElementById('main-content').innerHTML = `
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div class="input-group" style="max-width:320px">
        <span class="input-group-text bg-white"><i class="bi bi-search"></i></span>
        <input id="member-search" type="text" class="form-control" placeholder="Search members…" value="${search}"/>
      </div>
      <button class="btn btn-primary" onclick="showAddMemberModal()"><i class="bi bi-person-plus me-2"></i>Add Member</button>
    </div>
    <div class="card">
      <div class="card-body p-0">
        <table class="table table-hover mb-0">
          <thead><tr><th>Name</th><th>Email</th><th>Tier</th><th>Points Balance</th><th>Lifetime Points</th><th>Joined</th><th></th></tr></thead>
          <tbody>
            ${data.members.map(m => `<tr>
              <td><strong>${m.first_name} ${m.last_name}</strong></td>
              <td class="text-muted">${m.email}</td>
              <td>${tierBadge(m.tier)}</td>
              <td>${pointsPill(m.points_balance)}</td>
              <td><span class="text-muted small">${m.lifetime_points.toLocaleString()}</span></td>
              <td class="text-muted small">${formatDate(m.joined_at).split(',')[0]}</td>
              <td class="text-end">
                <button class="btn btn-sm btn-outline-secondary me-1" onclick="showMemberDetail(${m.id})"><i class="bi bi-eye"></i></button>
                <button class="btn btn-sm btn-outline-success me-1" onclick="showEarnModal(${m.id})"><i class="bi bi-plus-circle"></i></button>
                <button class="btn btn-sm btn-outline-warning" onclick="showRedeemModal(${m.id})"><i class="bi bi-gift"></i></button>
              </td>
            </tr>`).join('')}
            ${data.members.length === 0 ? '<tr><td colspan="7" class="text-center text-muted py-4">No members found</td></tr>' : ''}
          </tbody>
        </table>
      </div>
    </div>
    <div class="d-flex justify-content-between align-items-center mt-3">
      <small class="text-muted">Showing ${data.members.length} of ${data.total} members</small>
      <nav>${paginationHtml(page, data.pages, p => `loadMembers(${p},'${search}')`)}</nav>
    </div>`;

  document.getElementById('member-search').addEventListener('keydown', e => {
    if (e.key === 'Enter') loadMembers(1, e.target.value);
  });
}

function paginationHtml(current, total, clickFn) {
  if (total <= 1) return '';
  let html = '<ul class="pagination pagination-sm mb-0">';
  for (let i = 1; i <= total; i++) {
    html += `<li class="page-item ${i === current ? 'active' : ''}"><a class="page-link" href="#" onclick="${clickFn(i)};return false">${i}</a></li>`;
  }
  return html + '</ul>';
}

async function showAddMemberModal() {
  document.getElementById('modalTitle').textContent = 'Add New Member';
  document.getElementById('modalBody').innerHTML = `
    <form id="member-form">
      <div class="row g-3">
        <div class="col-6"><label class="form-label">First Name*</label><input name="first_name" class="form-control" required/></div>
        <div class="col-6"><label class="form-label">Last Name*</label><input name="last_name" class="form-control" required/></div>
        <div class="col-12"><label class="form-label">Email*</label><input name="email" type="email" class="form-control" required/></div>
        <div class="col-6"><label class="form-label">Phone</label><input name="phone" class="form-control"/></div>
        <div class="col-6"><label class="form-label">Date of Birth</label><input name="date_of_birth" type="date" class="form-control"/></div>
      </div>
    </form>`;
  document.getElementById('modalFooter').innerHTML = `
    <button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
    <button class="btn btn-primary" onclick="submitAddMember()">Add Member</button>`;
  modal.show();
}

async function submitAddMember() {
  const form = document.getElementById('member-form');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const fd = new FormData(form);
  const body = Object.fromEntries(fd.entries());
  try {
    await apiFetch('/members', { method: 'POST', body: JSON.stringify(body) });
    modal.hide();
    showToast('Member added successfully!');
    loadMembers();
  } catch (e) { showToast(e.message, 'danger'); }
}

async function showMemberDetail(id) {
  const [member, txns, redemptions] = await Promise.all([
    apiFetch(`/members/${id}`),
    apiFetch(`/members/${id}/transactions`),
    apiFetch(`/members/${id}/redemptions`),
  ]);

  const nextTier = member.tier ? await getNextTier(member.tier, member.lifetime_points) : null;

  document.getElementById('modalTitle').textContent = `${member.first_name} ${member.last_name}`;
  document.getElementById('modalBody').innerHTML = `
    <div class="row mb-3">
      <div class="col-md-6">
        <p class="mb-1"><strong>Email:</strong> ${member.email}</p>
        <p class="mb-1"><strong>Phone:</strong> ${member.phone || '—'}</p>
        <p class="mb-1"><strong>DOB:</strong> ${member.date_of_birth || '—'}</p>
        <p class="mb-1"><strong>Joined:</strong> ${formatDate(member.joined_at)}</p>
      </div>
      <div class="col-md-6 text-center">
        ${tierBadge(member.tier)}
        <div class="mt-2">${pointsPill(member.points_balance)}</div>
        <div class="text-muted small mt-1">Lifetime: ${member.lifetime_points.toLocaleString()} pts</div>
        ${nextTier ? `<div class="mt-2 small text-muted">Next tier: <strong>${nextTier.name}</strong> at ${nextTier.min_points.toLocaleString()} pts</div>` : ''}
      </div>
    </div>
    <ul class="nav nav-tabs" id="detailTabs">
      <li class="nav-item"><a class="nav-link active" data-bs-toggle="tab" href="#tab-txn">Transactions (${txns.length})</a></li>
      <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#tab-red">Redemptions (${redemptions.length})</a></li>
    </ul>
    <div class="tab-content border border-top-0 rounded-bottom p-3">
      <div class="tab-pane fade show active" id="tab-txn" style="max-height:300px;overflow-y:auto">
        ${transactionTable(txns.slice(0, 50))}
      </div>
      <div class="tab-pane fade" id="tab-red">
        ${redemptionTable(redemptions.slice(0, 50))}
      </div>
    </div>`;
  document.getElementById('modalFooter').innerHTML = `
    <button class="btn btn-success me-auto" onclick="modal.hide();showEarnModal(${id})"><i class="bi bi-plus-circle me-1"></i>Earn Points</button>
    <button class="btn btn-warning me-2" onclick="modal.hide();showRedeemModal(${id})"><i class="bi bi-gift me-1"></i>Redeem</button>
    <button class="btn btn-secondary" data-bs-dismiss="modal">Close</button>`;
  modal.show();
}

async function getNextTier(currentTier, lifetimePoints) {
  const tiers = await apiFetch('/tiers');
  const sorted = tiers.sort((a, b) => a.min_points - b.min_points);
  return sorted.find(t => t.min_points > currentTier.min_points) || null;
}

async function showEarnModal(memberId) {
  const [member, activities] = await Promise.all([
    apiFetch(`/members/${memberId}`),
    apiFetch('/activities'),
  ]);
  document.getElementById('modalTitle').textContent = `Earn Points — ${member.first_name} ${member.last_name}`;
  document.getElementById('modalBody').innerHTML = `
    <p class="text-muted">Current balance: ${pointsPill(member.points_balance)}</p>
    <div class="mb-3">
      <label class="form-label">Activity*</label>
      <select id="earn-activity" class="form-select">
        ${activities.filter(a => a.is_active).map(a => `<option value="${a.id}">${a.name} (${a.points_per_unit} pts/${a.unit_label})</option>`).join('')}
      </select>
    </div>
    <div class="mb-3">
      <label class="form-label">Quantity</label>
      <input id="earn-qty" type="number" class="form-control" value="1" min="0.01" step="0.01"/>
    </div>
    <div class="mb-3">
      <label class="form-label">Reference ID (optional)</label>
      <input id="earn-ref" type="text" class="form-control" placeholder="e.g. order-12345"/>
    </div>`;
  document.getElementById('modalFooter').innerHTML = `
    <button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
    <button class="btn btn-success" onclick="submitEarnPoints(${memberId})"><i class="bi bi-plus-circle me-1"></i>Award Points</button>`;
  modal.show();
}

async function submitEarnPoints(memberId) {
  const body = {
    activity_id: parseInt(document.getElementById('earn-activity').value),
    quantity: parseFloat(document.getElementById('earn-qty').value),
    reference_id: document.getElementById('earn-ref').value || null,
  };
  try {
    const result = await apiFetch(`/members/${memberId}/earn`, { method: 'POST', body: JSON.stringify(body) });
    modal.hide();
    showToast(`Awarded ${result.points_earned} points!${result.campaign_applied ? ' (Campaign: ' + result.campaign_applied.name + ')' : ''}`);
    loadMembers();
  } catch (e) { showToast(e.message, 'danger'); }
}

async function showRedeemModal(memberId) {
  const [member, rewards] = await Promise.all([
    apiFetch(`/members/${memberId}`),
    apiFetch('/rewards'),
  ]);
  document.getElementById('modalTitle').textContent = `Redeem Reward — ${member.first_name} ${member.last_name}`;
  document.getElementById('modalBody').innerHTML = `
    <p>Available balance: ${pointsPill(member.points_balance)}</p>
    <div class="row g-3">
      ${rewards.filter(r => r.is_active).map(r => `
        <div class="col-md-6">
          <div class="card reward-card ${member.points_balance >= r.points_cost ? '' : 'opacity-50'}" onclick="selectReward(${r.id})" id="reward-card-${r.id}">
            <div class="card-body py-2">
              <div class="d-flex justify-content-between">
                <strong class="small">${r.name}</strong>
                <span class="badge bg-primary">${r.points_cost} pts</span>
              </div>
              <small class="text-muted">${r.description || ''}</small>
              ${r.stock !== null ? `<div class="mt-1"><small class="text-warning"><i class="bi bi-box me-1"></i>${r.stock} left</small></div>` : ''}
              ${r.min_tier ? `<div class="mt-1"><small class="text-info"><i class="bi bi-layers me-1"></i>Requires ${r.min_tier.name}+</small></div>` : ''}
            </div>
          </div>
        </div>`).join('')}
    </div>
    <input type="hidden" id="selected-reward-id"/>`;
  document.getElementById('modalFooter').innerHTML = `
    <button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
    <button class="btn btn-warning" onclick="submitRedeemReward(${memberId})"><i class="bi bi-gift me-1"></i>Redeem Selected</button>`;
  modal.show();
}

function selectReward(id) {
  document.querySelectorAll('[id^="reward-card-"]').forEach(c => c.classList.remove('border-primary'));
  document.getElementById(`reward-card-${id}`).classList.add('border-primary');
  document.getElementById('selected-reward-id').value = id;
}

async function submitRedeemReward(memberId) {
  const rewardId = document.getElementById('selected-reward-id').value;
  if (!rewardId) { showToast('Please select a reward', 'warning'); return; }
  try {
    const result = await apiFetch(`/members/${memberId}/redeem`, { method: 'POST', body: JSON.stringify({ reward_id: parseInt(rewardId) }) });
    modal.hide();
    showToast(`Redemption successful! Spent ${result.points_spent} points.`);
    loadMembers();
  } catch (e) { showToast(e.message, 'danger'); }
}

// ─── TIERS ────────────────────────────────────────────────────────────────────
async function loadTiers() {
  const tiers = await apiFetch('/tiers');
  document.getElementById('main-content').innerHTML = `
    <div class="d-flex justify-content-end mb-3">
      <button class="btn btn-primary" onclick="showAddTierModal()"><i class="bi bi-plus me-2"></i>Add Tier</button>
    </div>
    <div class="row g-4">
      ${tiers.map(t => `
        <div class="col-md-6 col-xl-3">
          <div class="card h-100" style="border-top: 4px solid ${t.color}">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <span class="tier-badge" style="background:${t.color}20;color:${t.color};border:1px solid ${t.color}40;font-size:1rem;padding:4px 16px">${t.name}</span>
                <div>
                  <button class="btn btn-sm btn-outline-secondary" onclick="showEditTierModal(${t.id})"><i class="bi bi-pencil"></i></button>
                </div>
              </div>
              <p class="text-muted small mb-2">${t.description || ''}</p>
              <hr/>
              <div class="row text-center">
                <div class="col-6">
                  <div class="text-muted small">Min Points</div>
                  <div class="fw-bold">${t.min_points.toLocaleString()}</div>
                </div>
                <div class="col-6">
                  <div class="text-muted small">Multiplier</div>
                  <div class="fw-bold text-success">${t.multiplier}×</div>
                </div>
              </div>
            </div>
          </div>
        </div>`).join('')}
    </div>`;
}

function tierFormHtml(t = {}) {
  return `<div class="row g-3">
    <div class="col-8"><label class="form-label">Name*</label><input id="tf-name" class="form-control" value="${t.name || ''}" required/></div>
    <div class="col-4"><label class="form-label">Color</label><input id="tf-color" type="color" class="form-control form-control-color" value="${t.color || '#6c757d'}"/></div>
    <div class="col-6"><label class="form-label">Min Points</label><input id="tf-minpts" type="number" class="form-control" value="${t.min_points ?? 0}" min="0"/></div>
    <div class="col-6"><label class="form-label">Multiplier</label><input id="tf-mult" type="number" class="form-control" value="${t.multiplier ?? 1}" step="0.05" min="1"/></div>
    <div class="col-12"><label class="form-label">Description</label><input id="tf-desc" class="form-control" value="${t.description || ''}"/></div>
  </div>`;
}

async function showAddTierModal() {
  document.getElementById('modalTitle').textContent = 'Add Tier';
  document.getElementById('modalBody').innerHTML = tierFormHtml();
  document.getElementById('modalFooter').innerHTML = `<button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button class="btn btn-primary" onclick="submitTier()">Add</button>`;
  modal.show();
}

async function showEditTierModal(id) {
  const t = await apiFetch(`/tiers/${id}`);
  document.getElementById('modalTitle').textContent = `Edit Tier — ${t.name}`;
  document.getElementById('modalBody').innerHTML = tierFormHtml(t);
  document.getElementById('modalFooter').innerHTML = `<button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button class="btn btn-primary" onclick="submitTier(${id})">Save</button>`;
  modal.show();
}

async function submitTier(id = null) {
  const body = {
    name: document.getElementById('tf-name').value,
    min_points: parseInt(document.getElementById('tf-minpts').value),
    multiplier: parseFloat(document.getElementById('tf-mult').value),
    color: document.getElementById('tf-color').value,
    description: document.getElementById('tf-desc').value,
  };
  try {
    if (id) await apiFetch(`/tiers/${id}`, { method: 'PUT', body: JSON.stringify(body) });
    else await apiFetch('/tiers', { method: 'POST', body: JSON.stringify(body) });
    modal.hide();
    showToast('Tier saved!');
    loadTiers();
  } catch (e) { showToast(e.message, 'danger'); }
}

// ─── ACTIVITIES ───────────────────────────────────────────────────────────────
async function loadActivities() {
  const activities = await apiFetch('/activities');
  document.getElementById('main-content').innerHTML = `
    <div class="d-flex justify-content-end mb-3">
      <button class="btn btn-primary" onclick="showAddActivityModal()"><i class="bi bi-plus me-2"></i>Add Activity</button>
    </div>
    <div class="card">
      <div class="card-body p-0">
        <table class="table table-hover mb-0">
          <thead><tr><th>Name</th><th>Points/Unit</th><th>Unit</th><th>Status</th><th></th></tr></thead>
          <tbody>
            ${activities.map(a => `<tr>
              <td><strong>${a.name}</strong><br><small class="text-muted">${a.description || ''}</small></td>
              <td><span class="earn-pill">+${a.points_per_unit}</span></td>
              <td class="text-muted">${a.unit_label}</td>
              <td>${a.is_active ? '<span class="badge bg-success">Active</span>' : '<span class="badge bg-secondary">Inactive</span>'}</td>
              <td class="text-end"><button class="btn btn-sm btn-outline-secondary" onclick="showEditActivityModal(${a.id})"><i class="bi bi-pencil"></i></button></td>
            </tr>`).join('')}
            ${activities.length === 0 ? '<tr><td colspan="5" class="text-center text-muted py-4">No activities yet</td></tr>' : ''}
          </tbody>
        </table>
      </div>
    </div>`;
}

function activityFormHtml(a = {}) {
  return `<div class="row g-3">
    <div class="col-12"><label class="form-label">Name*</label><input id="af-name" class="form-control" value="${a.name || ''}" required/></div>
    <div class="col-12"><label class="form-label">Description</label><input id="af-desc" class="form-control" value="${a.description || ''}"/></div>
    <div class="col-6"><label class="form-label">Points per Unit</label><input id="af-pts" type="number" class="form-control" value="${a.points_per_unit ?? 10}" min="1"/></div>
    <div class="col-6"><label class="form-label">Unit Label</label><input id="af-unit" class="form-control" value="${a.unit_label || 'action'}"/></div>
    <div class="col-12"><div class="form-check"><input id="af-active" type="checkbox" class="form-check-input" ${a.is_active !== false ? 'checked' : ''}/><label class="form-check-label" for="af-active">Active</label></div></div>
  </div>`;
}

async function showAddActivityModal() {
  document.getElementById('modalTitle').textContent = 'Add Activity';
  document.getElementById('modalBody').innerHTML = activityFormHtml();
  document.getElementById('modalFooter').innerHTML = `<button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button class="btn btn-primary" onclick="submitActivity()">Add</button>`;
  modal.show();
}

async function showEditActivityModal(id) {
  const a = await apiFetch(`/activities/${id}`);
  document.getElementById('modalTitle').textContent = `Edit Activity — ${a.name}`;
  document.getElementById('modalBody').innerHTML = activityFormHtml(a);
  document.getElementById('modalFooter').innerHTML = `<button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button class="btn btn-primary" onclick="submitActivity(${id})">Save</button>`;
  modal.show();
}

async function submitActivity(id = null) {
  const body = {
    name: document.getElementById('af-name').value,
    description: document.getElementById('af-desc').value,
    points_per_unit: parseInt(document.getElementById('af-pts').value),
    unit_label: document.getElementById('af-unit').value,
    is_active: document.getElementById('af-active').checked,
  };
  try {
    if (id) await apiFetch(`/activities/${id}`, { method: 'PUT', body: JSON.stringify(body) });
    else await apiFetch('/activities', { method: 'POST', body: JSON.stringify(body) });
    modal.hide();
    showToast('Activity saved!');
    loadActivities();
  } catch (e) { showToast(e.message, 'danger'); }
}

// ─── REWARDS ─────────────────────────────────────────────────────────────────
async function loadRewards() {
  const rewards = await apiFetch('/rewards');
  document.getElementById('main-content').innerHTML = `
    <div class="d-flex justify-content-end mb-3">
      <button class="btn btn-primary" onclick="showAddRewardModal()"><i class="bi bi-plus me-2"></i>Add Reward</button>
    </div>
    <div class="row g-4">
      ${rewards.map(r => `
        <div class="col-md-6 col-lg-4">
          <div class="card reward-card ${r.is_active ? '' : 'opacity-60'}" onclick="showEditRewardModal(${r.id})">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <h6 class="card-title mb-0">${r.name}</h6>
                <span class="badge bg-primary">${r.points_cost.toLocaleString()} pts</span>
              </div>
              <p class="text-muted small mb-2">${r.description || ''}</p>
              <div class="d-flex flex-wrap gap-1">
                <span class="badge bg-secondary">${r.category}</span>
                ${r.stock !== null ? `<span class="badge bg-warning text-dark"><i class="bi bi-box me-1"></i>${r.stock} left</span>` : ''}
                ${r.min_tier ? `<span class="badge" style="background:${r.min_tier.color}30;color:${r.min_tier.color};border:1px solid ${r.min_tier.color}40"><i class="bi bi-layers me-1"></i>${r.min_tier.name}+</span>` : ''}
                ${r.is_active ? '<span class="badge bg-success">Active</span>' : '<span class="badge bg-secondary">Inactive</span>'}
              </div>
            </div>
          </div>
        </div>`).join('')}
      ${rewards.length === 0 ? '<div class="col-12 text-center text-muted py-5">No rewards yet</div>' : ''}
    </div>`;
}

async function showAddRewardModal() {
  const tiers = await apiFetch('/tiers');
  document.getElementById('modalTitle').textContent = 'Add Reward';
  document.getElementById('modalBody').innerHTML = rewardFormHtml({}, tiers);
  document.getElementById('modalFooter').innerHTML = `<button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button class="btn btn-primary" onclick="submitReward()">Add</button>`;
  modal.show();
}

async function showEditRewardModal(id) {
  const [r, tiers] = await Promise.all([apiFetch(`/rewards/${id}`), apiFetch('/tiers')]);
  document.getElementById('modalTitle').textContent = `Edit Reward — ${r.name}`;
  document.getElementById('modalBody').innerHTML = rewardFormHtml(r, tiers);
  document.getElementById('modalFooter').innerHTML = `<button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button class="btn btn-primary" onclick="submitReward(${id})">Save</button>`;
  modal.show();
}

function rewardFormHtml(r = {}, tiers = []) {
  return `<div class="row g-3">
    <div class="col-12"><label class="form-label">Name*</label><input id="rf-name" class="form-control" value="${r.name || ''}" required/></div>
    <div class="col-12"><label class="form-label">Description</label><input id="rf-desc" class="form-control" value="${r.description || ''}"/></div>
    <div class="col-6"><label class="form-label">Points Cost*</label><input id="rf-cost" type="number" class="form-control" value="${r.points_cost || 500}" min="1"/></div>
    <div class="col-6"><label class="form-label">Category</label>
      <select id="rf-cat" class="form-select">
        ${['discount','shipping','gift','experience','merchandise','general'].map(c => `<option ${r.category===c?'selected':''}>${c}</option>`).join('')}
      </select>
    </div>
    <div class="col-6"><label class="form-label">Stock (blank=unlimited)</label><input id="rf-stock" type="number" class="form-control" value="${r.stock ?? ''}" min="0"/></div>
    <div class="col-6"><label class="form-label">Min Tier Required</label>
      <select id="rf-tier" class="form-select">
        <option value="">None</option>
        ${tiers.map(t => `<option value="${t.id}" ${r.min_tier && r.min_tier.id===t.id?'selected':''}>${t.name}</option>`).join('')}
      </select>
    </div>
    <div class="col-12"><div class="form-check"><input id="rf-active" type="checkbox" class="form-check-input" ${r.is_active !== false ? 'checked' : ''}/><label class="form-check-label" for="rf-active">Active</label></div></div>
  </div>`;
}

async function submitReward(id = null) {
  const stockVal = document.getElementById('rf-stock').value;
  const tierVal = document.getElementById('rf-tier').value;
  const body = {
    name: document.getElementById('rf-name').value,
    description: document.getElementById('rf-desc').value,
    points_cost: parseInt(document.getElementById('rf-cost').value),
    category: document.getElementById('rf-cat').value,
    stock: stockVal !== '' ? parseInt(stockVal) : null,
    min_tier_id: tierVal ? parseInt(tierVal) : null,
    is_active: document.getElementById('rf-active').checked,
  };
  try {
    if (id) await apiFetch(`/rewards/${id}`, { method: 'PUT', body: JSON.stringify(body) });
    else await apiFetch('/rewards', { method: 'POST', body: JSON.stringify(body) });
    modal.hide();
    showToast('Reward saved!');
    loadRewards();
  } catch (e) { showToast(e.message, 'danger'); }
}

// ─── CAMPAIGNS ───────────────────────────────────────────────────────────────
async function loadCampaigns() {
  const campaigns = await apiFetch('/campaigns');
  document.getElementById('main-content').innerHTML = `
    <div class="d-flex justify-content-end mb-3">
      <button class="btn btn-primary" onclick="showAddCampaignModal()"><i class="bi bi-plus me-2"></i>New Campaign</button>
    </div>
    <div class="row g-4">
      ${campaigns.map(c => `
        <div class="col-md-6">
          <div class="card ${c.is_running ? 'campaign-active' : 'campaign-inactive'}">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <h6 class="mb-0">${c.name}</h6>
                <div class="d-flex gap-1">
                  ${c.is_running ? '<span class="badge bg-success">Running</span>' : '<span class="badge bg-secondary">Inactive</span>'}
                  <button class="btn btn-sm btn-outline-secondary" onclick="showEditCampaignModal(${c.id})"><i class="bi bi-pencil"></i></button>
                </div>
              </div>
              <p class="text-muted small mb-2">${c.description || ''}</p>
              <div class="row text-center">
                <div class="col-4"><div class="text-muted small">Multiplier</div><div class="fw-bold text-success">${c.multiplier}×</div></div>
                <div class="col-4"><div class="text-muted small">Bonus</div><div class="fw-bold text-primary">+${c.bonus_points}</div></div>
                <div class="col-4"><div class="text-muted small">Activity</div><div class="fw-bold">${c.activity_id ? '✓' : 'All'}</div></div>
              </div>
              <hr class="my-2"/>
              <small class="text-muted"><i class="bi bi-calendar me-1"></i>${formatDate(c.start_date)} → ${formatDate(c.end_date)}</small>
            </div>
          </div>
        </div>`).join('')}
      ${campaigns.length === 0 ? '<div class="col-12 text-center text-muted py-5">No campaigns yet</div>' : ''}
    </div>`;
}

async function showAddCampaignModal() {
  const activities = await apiFetch('/activities');
  document.getElementById('modalTitle').textContent = 'New Campaign';
  document.getElementById('modalBody').innerHTML = campaignFormHtml({}, activities);
  document.getElementById('modalFooter').innerHTML = `<button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button class="btn btn-primary" onclick="submitCampaign()">Create</button>`;
  modal.show();
}

async function showEditCampaignModal(id) {
  const [c, activities] = await Promise.all([apiFetch(`/campaigns/${id}`), apiFetch('/activities')]);
  document.getElementById('modalTitle').textContent = `Edit Campaign — ${c.name}`;
  document.getElementById('modalBody').innerHTML = campaignFormHtml(c, activities);
  document.getElementById('modalFooter').innerHTML = `<button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button class="btn btn-primary" onclick="submitCampaign(${id})">Save</button>`;
  modal.show();
}

function toLocalDatetimeValue(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

function campaignFormHtml(c = {}, activities = []) {
  return `<div class="row g-3">
    <div class="col-12"><label class="form-label">Name*</label><input id="cf-name" class="form-control" value="${c.name || ''}" required/></div>
    <div class="col-12"><label class="form-label">Description</label><input id="cf-desc" class="form-control" value="${c.description || ''}"/></div>
    <div class="col-6"><label class="form-label">Multiplier</label><input id="cf-mult" type="number" class="form-control" value="${c.multiplier ?? 2}" step="0.1" min="1"/></div>
    <div class="col-6"><label class="form-label">Bonus Points</label><input id="cf-bonus" type="number" class="form-control" value="${c.bonus_points ?? 0}" min="0"/></div>
    <div class="col-12"><label class="form-label">Activity (blank = applies to all)</label>
      <select id="cf-activity" class="form-select">
        <option value="">All Activities</option>
        ${activities.map(a => `<option value="${a.id}" ${c.activity_id===a.id?'selected':''}>${a.name}</option>`).join('')}
      </select>
    </div>
    <div class="col-6"><label class="form-label">Start Date*</label><input id="cf-start" type="datetime-local" class="form-control" value="${toLocalDatetimeValue(c.start_date)}" required/></div>
    <div class="col-6"><label class="form-label">End Date*</label><input id="cf-end" type="datetime-local" class="form-control" value="${toLocalDatetimeValue(c.end_date)}" required/></div>
    <div class="col-12"><div class="form-check"><input id="cf-active" type="checkbox" class="form-check-input" ${c.is_active !== false ? 'checked' : ''}/><label class="form-check-label" for="cf-active">Active</label></div></div>
  </div>`;
}

async function submitCampaign(id = null) {
  const actVal = document.getElementById('cf-activity').value;
  const body = {
    name: document.getElementById('cf-name').value,
    description: document.getElementById('cf-desc').value,
    multiplier: parseFloat(document.getElementById('cf-mult').value),
    bonus_points: parseInt(document.getElementById('cf-bonus').value),
    activity_id: actVal ? parseInt(actVal) : null,
    start_date: document.getElementById('cf-start').value,
    end_date: document.getElementById('cf-end').value,
    is_active: document.getElementById('cf-active').checked,
  };
  try {
    if (id) await apiFetch(`/campaigns/${id}`, { method: 'PUT', body: JSON.stringify(body) });
    else await apiFetch('/campaigns', { method: 'POST', body: JSON.stringify(body) });
    modal.hide();
    showToast('Campaign saved!');
    loadCampaigns();
  } catch (e) { showToast(e.message, 'danger'); }
}

// ─── TRANSACTIONS ────────────────────────────────────────────────────────────
async function loadTransactions() {
  const txns = await apiFetch('/analytics/recent_transactions');
  document.getElementById('main-content').innerHTML = `
    <div class="card">
      <div class="card-header bg-white border-0 pt-3 pb-0 fw-semibold">Recent Transactions (last 20)</div>
      <div class="card-body p-0">
        ${transactionTable(txns)}
      </div>
    </div>`;
}

function transactionTable(txns) {
  if (!txns.length) return '<div class="text-center text-muted py-4">No transactions yet</div>';
  return `<table class="table table-hover mb-0">
    <thead><tr><th>Date</th><th>Member</th><th>Type</th><th>Points</th><th>Description</th><th>Campaign</th></tr></thead>
    <tbody>
      ${txns.map(t => `<tr>
        <td class="text-muted small">${formatDate(t.created_at)}</td>
        <td class="text-muted small">#${t.member_id}</td>
        <td>${pointsPill(t.points, t.transaction_type)}</td>
        <td class="fw-bold">${t.points > 0 ? '+' : ''}${t.points}</td>
        <td class="small">${t.description || '—'}</td>
        <td class="small">${t.campaign ? `<span class="badge bg-info text-dark">${t.campaign.name}</span>` : '—'}</td>
      </tr>`).join('')}
    </tbody>
  </table>`;
}

function redemptionTable(redemptions) {
  if (!redemptions.length) return '<div class="text-center text-muted py-4">No redemptions yet</div>';
  return `<table class="table table-hover mb-0">
    <thead><tr><th>Date</th><th>Reward</th><th>Points</th><th>Status</th></tr></thead>
    <tbody>
      ${redemptions.map(r => `<tr>
        <td class="text-muted small">${formatDate(r.redeemed_at)}</td>
        <td>${r.reward ? r.reward.name : '—'}</td>
        <td><span class="redeem-pill">-${r.points_spent}</span></td>
        <td><span class="badge ${r.status === 'fulfilled' ? 'bg-success' : r.status === 'cancelled' ? 'bg-danger' : 'bg-warning text-dark'}">${r.status}</span></td>
      </tr>`).join('')}
    </tbody>
  </table>`;
}
