function renderAdminPage(businesses, tapStats, errorMsg, successMsg) {
  const businessRows = businesses.map(b => {
    const stats = tapStats[b.id] || { today: 0, week: 0, total: 0, lastTap: null, daily: [] };
    const lastTapStr = stats.lastTap
      ? new Date(stats.lastTap).toLocaleString('en-AU', { timeZone: 'Australia/Sydney' })
      : 'Never';
    const sparkline = renderSparkline(stats.daily);
    const slug = b.slug;
    const baseUrl = process.env.BASE_URL || '';
    const nfcUrl = `${baseUrl}/r/${slug}`;
    const platformLabel = { google: 'Google', yelp: 'Yelp', tripadvisor: 'TripAdvisor' }[b.platform] || b.platform;
    const activeLabel = b.active
      ? '<span class="badge badge-active">Active</span>'
      : '<span class="badge badge-inactive">Inactive</span>';

    return `
      <div class="business-card${!b.active ? ' inactive' : ''}">
        <div class="business-header">
          <div>
            <h3 class="business-name">${escHtml(b.name)}</h3>
            <span class="business-meta">${platformLabel} &bull; <code>/r/${escHtml(slug)}</code> ${activeLabel}</span>
          </div>
          <div class="business-actions">
            <button class="btn btn-copy" onclick="copyLink('${escHtml(nfcUrl)}', this)">Copy NFC Link</button>
            <button class="btn btn-edit" onclick="openEdit('${b.id}')">Edit</button>
          </div>
        </div>
        <div class="stats-row">
          <div class="stat"><span class="stat-num">${stats.today}</span><span class="stat-label">Today</span></div>
          <div class="stat"><span class="stat-num">${stats.week}</span><span class="stat-label">This Week</span></div>
          <div class="stat"><span class="stat-num">${stats.total}</span><span class="stat-label">All Time</span></div>
          <div class="stat"><span class="stat-label">Last Tap</span><span class="stat-sub">${lastTapStr}</span></div>
        </div>
        <div class="sparkline-wrap">
          <div class="sparkline-label">Last 7 days</div>
          ${sparkline}
        </div>
      </div>`;
  }).join('');

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AusTap Admin</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0f2f5; color: #1a1a2e; }
  header { background: #1a1a2e; color: #fff; padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; }
  header h1 { font-size: 1.4rem; font-weight: 700; letter-spacing: -0.5px; }
  header h1 span { color: #4ade80; }
  .logout { color: #aaa; text-decoration: none; font-size: 0.85rem; }
  .logout:hover { color: #fff; }
  main { max-width: 960px; margin: 0 auto; padding: 24px 16px; }
  .alert { padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; font-size: 0.9rem; }
  .alert-error { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
  .alert-success { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
  .section-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 16px; color: #374151; }
  .business-card { background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
  .business-card.inactive { opacity: 0.6; }
  .business-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
  .business-name { font-size: 1.1rem; font-weight: 600; margin-bottom: 4px; }
  .business-meta { font-size: 0.8rem; color: #6b7280; }
  .business-meta code { background: #f3f4f6; padding: 1px 5px; border-radius: 4px; }
  .business-actions { display: flex; gap: 8px; flex-shrink: 0; }
  .badge { display: inline-block; font-size: 0.7rem; padding: 2px 8px; border-radius: 99px; font-weight: 600; margin-left: 6px; }
  .badge-active { background: #dcfce7; color: #166534; }
  .badge-inactive { background: #f3f4f6; color: #6b7280; }
  .stats-row { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 16px; }
  .stat { display: flex; flex-direction: column; align-items: center; background: #f9fafb; border-radius: 8px; padding: 10px 16px; min-width: 70px; }
  .stat-num { font-size: 1.4rem; font-weight: 700; color: #1a1a2e; line-height: 1; }
  .stat-label { font-size: 0.7rem; color: #9ca3af; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.5px; }
  .stat-sub { font-size: 0.75rem; color: #6b7280; margin-top: 2px; text-align: center; }
  .sparkline-wrap { }
  .sparkline-label { font-size: 0.7rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
  .sparkline { display: flex; align-items: flex-end; gap: 4px; height: 40px; }
  .sparkline-bar { flex: 1; background: #4ade80; border-radius: 3px 3px 0 0; min-height: 3px; transition: background 0.2s; }
  .sparkline-bar:hover { background: #16a34a; }
  .sparkline-bar-wrap { display: flex; flex-direction: column; align-items: center; flex: 1; }
  .sparkline-day { font-size: 0.6rem; color: #d1d5db; margin-top: 3px; }
  .btn { padding: 8px 14px; border: none; border-radius: 7px; cursor: pointer; font-size: 0.82rem; font-weight: 500; transition: all 0.15s; }
  .btn-copy { background: #1a1a2e; color: #fff; }
  .btn-copy:hover { background: #374151; }
  .btn-copy.copied { background: #16a34a; }
  .btn-edit { background: #f3f4f6; color: #374151; }
  .btn-edit:hover { background: #e5e7eb; }
  .btn-primary { background: #4ade80; color: #1a1a2e; font-weight: 600; }
  .btn-primary:hover { background: #22c55e; }
  .btn-danger { background: #fee2e2; color: #991b1b; }
  .btn-danger:hover { background: #fca5a5; }
  .add-section { background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,.08); margin-top: 24px; }
  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  @media (max-width: 600px) { .form-grid { grid-template-columns: 1fr; } }
  .form-group { display: flex; flex-direction: column; gap: 5px; }
  .form-group.full { grid-column: 1 / -1; }
  label { font-size: 0.82rem; font-weight: 500; color: #374151; }
  input, select, textarea { border: 1px solid #d1d5db; border-radius: 7px; padding: 9px 12px; font-size: 0.9rem; width: 100%; outline: none; transition: border 0.15s; }
  input:focus, select:focus, textarea:focus { border-color: #4ade80; box-shadow: 0 0 0 3px rgba(74,222,128,.15); }
  .form-actions { display: flex; gap: 10px; margin-top: 8px; }
  .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 100; align-items: center; justify-content: center; padding: 16px; }
  .modal-overlay.open { display: flex; }
  .modal { background: #fff; border-radius: 14px; padding: 24px; width: 100%; max-width: 500px; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
  .modal h2 { font-size: 1.1rem; margin-bottom: 20px; }
  .modal .form-actions { justify-content: flex-end; }
</style>
</head>
<body>
<header>
  <h1>Aus<span>Tap</span> Admin</h1>
  <a href="/admin/logout" class="logout">Logout</a>
</header>
<main>
  ${errorMsg ? `<div class="alert alert-error">${escHtml(errorMsg)}</div>` : ''}
  ${successMsg ? `<div class="alert alert-success">${successMsg}</div>` : ''}

  <div class="section-title">Businesses (${businesses.length})</div>
  ${businesses.length === 0 ? '<p style="color:#6b7280;font-size:.9rem;">No businesses yet. Add one below.</p>' : businessRows}

  <div class="add-section">
    <div class="section-title">Add New Business</div>
    <form method="POST" action="/admin/business">
      <div class="form-grid">
        <div class="form-group">
          <label for="name">Business Name *</label>
          <input type="text" id="name" name="name" required placeholder="Joe's Barbershop">
        </div>
        <div class="form-group">
          <label for="slug">URL Slug *</label>
          <input type="text" id="slug" name="slug" required placeholder="joes-barbershop" pattern="[a-z0-9\\-]+" title="Lowercase letters, numbers and hyphens only">
        </div>
        <div class="form-group full">
          <label for="redirect_url">Review Page URL *</label>
          <input type="url" id="redirect_url" name="redirect_url" required placeholder="https://g.page/r/your-google-review-link">
        </div>
        <div class="form-group">
          <label for="platform">Platform *</label>
          <select id="platform" name="platform">
            <option value="google">Google</option>
            <option value="yelp">Yelp</option>
            <option value="tripadvisor">TripAdvisor</option>
          </select>
        </div>
        <div class="form-group">
          <label for="owner_email">Owner Email</label>
          <input type="email" id="owner_email" name="owner_email" placeholder="owner@example.com">
        </div>
      </div>
      <div class="form-actions" style="margin-top:16px;">
        <button type="submit" class="btn btn-primary">Add Business</button>
      </div>
    </form>
  </div>
</main>

<!-- Edit Modal -->
<div class="modal-overlay" id="editModal">
  <div class="modal">
    <h2>Edit Business</h2>
    <form method="POST" action="/admin/business">
      <input type="hidden" name="_id" id="edit_id">
      <div class="form-grid">
        <div class="form-group">
          <label>Business Name *</label>
          <input type="text" name="name" id="edit_name" required>
        </div>
        <div class="form-group">
          <label>URL Slug *</label>
          <input type="text" name="slug" id="edit_slug" required pattern="[a-z0-9\\-]+">
        </div>
        <div class="form-group full">
          <label>Review Page URL *</label>
          <input type="url" name="redirect_url" id="edit_redirect_url" required>
        </div>
        <div class="form-group">
          <label>Platform *</label>
          <select name="platform" id="edit_platform">
            <option value="google">Google</option>
            <option value="yelp">Yelp</option>
            <option value="tripadvisor">TripAdvisor</option>
          </select>
        </div>
        <div class="form-group">
          <label>Owner Email</label>
          <input type="email" name="owner_email" id="edit_owner_email">
        </div>
        <div class="form-group full">
          <label>
            <input type="checkbox" name="active" id="edit_active" value="true" style="width:auto;margin-right:6px;">
            Active (uncheck to disable this redirect)
          </label>
        </div>
      </div>
      <div class="form-actions" style="margin-top:16px;">
        <button type="button" class="btn btn-danger" onclick="closeEdit()">Cancel</button>
        <button type="submit" class="btn btn-primary">Save Changes</button>
      </div>
    </form>
  </div>
</div>

<script>
var BUSINESSES = ${JSON.stringify(businesses)};

function copyLink(url, btn) {
  navigator.clipboard.writeText(url).then(() => {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy NFC Link'; btn.classList.remove('copied'); }, 2000);
  });
}

function openEdit(id) {
  const b = BUSINESSES.find(function(x){ return x.id === id; });
  if (!b) return;
  document.getElementById('edit_id').value = b.id;
  document.getElementById('edit_name').value = b.name;
  document.getElementById('edit_slug').value = b.slug;
  document.getElementById('edit_redirect_url').value = b.redirect_url;
  document.getElementById('edit_platform').value = b.platform;
  document.getElementById('edit_owner_email').value = b.owner_email || '';
  document.getElementById('edit_active').checked = b.active;
  document.getElementById('editModal').classList.add('open');
}

function closeEdit() {
  document.getElementById('editModal').classList.remove('open');
}

document.getElementById('editModal').addEventListener('click', function(e) {
  if (e.target === this) closeEdit();
});

// Auto-generate slug from business name in add form
document.getElementById('name').addEventListener('input', function() {
  const slugField = document.getElementById('slug');
  if (!slugField.dataset.manual) {
    slugField.value = this.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  }
});
document.getElementById('slug').addEventListener('input', function() {
  this.dataset.manual = '1';
});
</script>
</body>
</html>`;
}

function renderSparkline(daily) {
  const days = daily.length ? daily : Array(7).fill({ count: 0, label: '' });
  const max = Math.max(...days.map(d => d.count), 1);
  return `<div class="sparkline">${days.map(d => {
    const pct = Math.max((d.count / max) * 100, 5);
    return `<div class="sparkline-bar-wrap"><div class="sparkline-bar" style="height:${pct}%" title="${d.count} taps on ${d.label}"></div><div class="sparkline-day">${d.label || ''}</div></div>`;
  }).join('')}</div>`;
}

function escHtml(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

module.exports = { renderAdminPage };
