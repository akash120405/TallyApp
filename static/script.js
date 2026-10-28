(() => {
  const els = {
    monthlyTotal: document.getElementById('monthly-total'),
    yearlyTotal: document.getElementById('yearly-total'),
    budgetInput: document.getElementById('budget-input'),
    headroomFill: document.getElementById('headroom-fill'),
    headroomNote: document.getElementById('headroom-note'),
    renewalsBlock: document.getElementById('renewals-block'),
    renewalsChips: document.getElementById('renewals-chips'),
    ledgerRows: document.getElementById('ledger-rows'),
    ledgerEmpty: document.getElementById('ledger-empty'),
    quickAddForm: document.getElementById('quick-add-form'),
    addName: document.getElementById('add-name'),
    addRenewal: document.getElementById('add-renewal'),
    addCost: document.getElementById('add-cost'),
    clerkThread: document.getElementById('clerk-thread'),
    clerkForm: document.getElementById('clerk-form'),
    clerkInput: document.getElementById('clerk-input'),
    clerkSend: document.getElementById('clerk-send'),
    resetBtn: document.getElementById('reset-btn'),
    ledgerTab: document.getElementById('ledger-tab'),
    recommendationsTab: document.getElementById('recommendations-tab'),
    ledgerView: document.getElementById('ledger-view'),
    recommendationsView: document.getElementById('recommendations-view'),
    recommendationList: document.getElementById('recommendation-list'),
    searchInput: document.getElementById('search-input'),
    exportBtn: document.getElementById('export-btn'),
  };

  const money = (n) => new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(Number(n || 0));
  let currentBudget = null;

  function renderHeadroom(monthlyTotal) {
    const budget = currentBudget;
    els.headroomFill.classList.remove('state-warn', 'state-over');
    els.headroomNote.classList.remove('state-over');

    if (budget === null || budget <= 0) {
      els.headroomFill.style.width = '0%';
      els.headroomNote.textContent = 'Set a budget to see your headroom.';
      return;
    }

    const ratio = monthlyTotal / budget;
    const pct = Math.min(ratio, 1) * 100;
    els.headroomFill.style.width = `${pct}%`;

    if (ratio > 1) {
      els.headroomFill.classList.add('state-over');
      els.headroomNote.classList.add('state-over');
      els.headroomNote.textContent = `${money(monthlyTotal - budget)} over your ${money(budget)} budget.`;
    } else if (ratio > 0.85) {
      els.headroomFill.classList.add('state-warn');
      els.headroomNote.textContent = `${money(budget - monthlyTotal)} of headroom left this month.`;
    } else {
      els.headroomNote.textContent = `${money(budget - monthlyTotal)} of headroom left this month.`;
    }
  }

  function renderRenewals(subs) {
    if (!subs.length) {
      els.renewalsBlock.hidden = true;
      return;
    }
    els.renewalsBlock.hidden = false;
    els.renewalsChips.innerHTML = '';
    subs.forEach((s) => {
      const chip = document.createElement('span');
      chip.className = 'renewal-chip';
      chip.textContent = `${s.name} — ${s.renewal_date}`;
      els.renewalsChips.appendChild(chip);
    });
  }

  let currentSubscriptions = [];

  function renderLedger(subs) {
    els.ledgerRows.innerHTML = '';
    els.ledgerEmpty.style.display = subs.length ? 'none' : 'block';

    subs.forEach((s) => {
      const row = document.createElement('div');
      row.className = 'ledger-row';
      row.innerHTML = `
        <span class="ledger-row-name">${escapeHtml(s.name)}</span>
        <span class="ledger-row-renewal">${escapeHtml(s.renewal_date)}</span>
        <span class="ledger-row-cost">${money(s.cost)}</span>
        <button class="row-remove" title="Remove ${escapeHtml(s.name)}" aria-label="Remove ${escapeHtml(s.name)}">&times;</button>
      `;
      row.querySelector('.row-remove').addEventListener('click', () => removeSubscription(s.name));
      els.ledgerRows.appendChild(row);
    });
  }

  function renderRecommendations(state) {
    const unlocked = state.monthly_total > state.recommendation_threshold;
    els.recommendationsTab.hidden = !unlocked;
    if (!unlocked) {
      els.recommendationsView.hidden = true;
      els.ledgerView.hidden = false;
      els.ledgerTab.classList.add('is-active');
      els.ledgerTab.setAttribute('aria-selected', 'true');
      return;
    }

    els.recommendationList.innerHTML = '';
    state.recommendations.forEach((recommendation) => {
      const card = document.createElement('article');
      card.className = 'recommendation-card';
      card.innerHTML = `
        <div>
          <h4>${escapeHtml(recommendation.title)}</h4>
          <p>${escapeHtml(recommendation.detail)}</p>
        </div>
        <div class="recommendation-saving">
          <strong>${money(recommendation.monthly_saving)}</strong>
          <span>possible monthly saving</span>
          <small>${money(recommendation.yearly_saving)} yearly</small>
        </div>
      `;
      els.recommendationList.appendChild(card);
    });
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function renderState(state) {
    els.monthlyTotal.textContent = money(state.monthly_total);
    els.yearlyTotal.textContent = money(state.yearly_total);
    currentSubscriptions = state.subscriptions;
    currentBudget = state.monthly_budget;
    els.budgetInput.value = currentBudget === null ? '' : currentBudget;
    renderHeadroom(state.monthly_total);
    renderRenewals(state.subscriptions);
    renderLedger(state.subscriptions);
    renderRecommendations(state);
  }

  function showView(view) {
    const recommendations = view === 'recommendations';
    els.ledgerView.hidden = recommendations;
    els.recommendationsView.hidden = !recommendations;
    els.ledgerTab.classList.toggle('is-active', !recommendations);
    els.recommendationsTab.classList.toggle('is-active', recommendations);
    els.ledgerTab.setAttribute('aria-selected', String(!recommendations));
    els.recommendationsTab.setAttribute('aria-selected', String(recommendations));
  }

  function exportCsv() {
    const rows = [['Subscription', 'Renewal date', 'Monthly cost (INR)']];
    currentSubscriptions.forEach((s) => rows.push([s.name, s.renewal_date, s.cost]));
    const csv = rows.map((row) => row.map((value) => `"${String(value).replace(/"/g, '""')}"`).join(',')).join('\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'tally-subscriptions.csv';
    link.click();
    URL.revokeObjectURL(url);
  }

  async function fetchState() {
    const res = await fetch('/api/subscriptions');
    const state = await res.json();
    renderState(state);
  }

  async function addSubscriptionDirect(name, cost, renewal_date) {
    const res = await fetch('/api/subscriptions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, cost, renewal_date }),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.error || 'Could not add that subscription.');
      return;
    }
    renderState(data);
  }

  async function removeSubscription(name) {
    const res = await fetch(`/api/subscriptions/${encodeURIComponent(name)}`, { method: 'DELETE' });
    const data = await res.json();
    renderState(data);
  }

  function addBubble(text, kind) {
    const bubble = document.createElement('div');
    bubble.className = `bubble bubble--${kind}`;
    bubble.textContent = text;
    els.clerkThread.appendChild(bubble);
    els.clerkThread.scrollTop = els.clerkThread.scrollHeight;
    return bubble;
  }

  async function sendToClerk(message) {
    addBubble(message, 'user');
    const pending = addBubble('The clerk is working through the ledger…', 'clerk');
    pending.classList.add('bubble--pending');
    els.clerkSend.disabled = true;

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      pending.remove();

      if (!res.ok) {
        addBubble(data.error || 'The clerk could not reach the agent.', 'error');
        return;
      }
      addBubble(data.reply || '(No response.)', 'clerk');
      if (data.state) renderState(data.state);
    } catch (err) {
      pending.remove();
      addBubble('Could not reach the server. Is the app running?', 'error');
    } finally {
      els.clerkSend.disabled = false;
    }
  }

  els.quickAddForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = els.addName.value.trim();
    const cost = els.addCost.value;
    const renewal = els.addRenewal.value.trim() || '1st of next month';
    if (!name || !cost) return;
    addSubscriptionDirect(name, cost, renewal);
    els.quickAddForm.reset();
  });

  els.clerkForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const message = els.clerkInput.value.trim();
    if (!message) return;
    els.clerkInput.value = '';
    sendToClerk(message);
  });

  els.clerkInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      els.clerkForm.requestSubmit();
    }
  });

  els.budgetInput.addEventListener('change', () => {
    const val = els.budgetInput.value === '' ? null : Number(els.budgetInput.value);
    if (val !== null && (!Number.isFinite(val) || val <= 0)) return;
    fetch('/api/budget', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount: val }),
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || 'Could not save your budget.');
        return;
      }
      renderState(data);
    }).catch(() => {
      alert('Could not save your budget. Is the app running?');
    });
  });

  els.resetBtn.addEventListener('click', async () => {
    if (!confirm('Clear every subscription and start the ledger over?')) return;
    const res = await fetch('/api/reset', { method: 'POST' });
    const data = await res.json();
    renderState(data);
    els.clerkThread.innerHTML = '';
    addBubble("Ledger's clear. Tell me about a subscription whenever you're ready.", 'clerk');
  });

  els.ledgerTab.addEventListener('click', () => showView('ledger'));
  els.recommendationsTab.addEventListener('click', () => showView('recommendations'));
  els.exportBtn.addEventListener('click', exportCsv);
  els.searchInput.addEventListener('input', () => {
    const query = els.searchInput.value.trim().toLowerCase();
    renderLedger(currentSubscriptions.filter((s) => s.name.toLowerCase().includes(query)));
  });

  // Init
  fetchState();
})();
