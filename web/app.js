const j = (el) => document.querySelector(el);

async function api(url, method = "GET", body) {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

async function refreshDashboard() {
  const data = await api("/api/dashboard");
  j("#dashboard").innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
}

async function refreshPolicies() {
  const policies = await api("/api/policies");
  j("#policyFeed").innerHTML = policies
    .map(
      (p) => `<li><strong>${p.title}</strong> — ${p.summary}<br/>Ψήφοι: ✅ ${p.votes.yes} / ❌ ${p.votes.no}</li>`
    )
    .join("");
}

j("#citizenForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  await api("/api/register/citizen", "POST", Object.fromEntries(f));
  e.target.reset();
  refreshDashboard();
  refreshPolicies();
});

j("#enterpriseForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  await api("/api/register/enterprise", "POST", Object.fromEntries(f));
  e.target.reset();
  refreshDashboard();
});

j("#policyForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  await api("/api/policies", "POST", Object.fromEntries(f));
  e.target.reset();
  refreshPolicies();
  refreshDashboard();
});

j("#certificateForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  await api("/api/certificates", "POST", { ...Object.fromEntries(f), data: { source: "dashboard" } });
  e.target.reset();
  refreshDashboard();
});

j("#walletForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const holder_id = new FormData(e.target).get("holder_id");
  const data = await api(`/api/wallet?holder_id=${encodeURIComponent(holder_id)}`);
  j("#wallet").innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
});

refreshDashboard();
refreshPolicies();
setInterval(refreshDashboard, 7000);
setInterval(refreshPolicies, 7000);
