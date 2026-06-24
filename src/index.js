require('dotenv').config();
const express = require('express');
const supabase = require('./db');
const { renderAdminPage } = require('./admin.html.js');

let geoip;
try { geoip = require('geoip-lite'); } catch (_) {}

const app = express();
const PORT = process.env.PORT || 3000;
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'changeme';

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// ─── Health check ─────────────────────────────────────────────────────────────

app.get('/health', (_req, res) => {
  res.status(200).json({ status: 'ok', ts: new Date().toISOString() });
});

// ─── Redirect endpoint ────────────────────────────────────────────────────────

app.get('/r/:slug', async (req, res) => {
  const { slug } = req.params;

  // Fetch business first — redirect is the priority
  let business;
  try {
    const { data, error } = await supabase
      .from('businesses')
      .select('id, redirect_url, active')
      .eq('slug', slug)
      .single();

    if (error || !data) {
      return res.status(404).send(`
        <html><head><title>Not Found</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:60px">
          <h2>Review link not found</h2>
          <p>This NFC sticker hasn't been set up yet. Contact AusTap support.</p>
        </body></html>`);
    }
    business = data;
  } catch (err) {
    return res.status(500).send('Server error. Please try again.');
  }

  if (!business.active) {
    return res.status(404).send(`
      <html><head><title>Inactive</title></head>
      <body style="font-family:sans-serif;text-align:center;padding:60px">
        <h2>This review link is currently inactive</h2>
        <p>Please contact the business for assistance.</p>
      </body></html>`);
  }

  // Fire-and-forget analytics — never block the redirect
  logTap(business.id, req).catch(() => {});

  return res.redirect(302, business.redirect_url);
});

async function logTap(businessId, req) {
  const ua = req.headers['user-agent'] || '';
  const deviceType = /mobile|android|iphone|ipad/i.test(ua) ? 'mobile' : 'desktop';

  const ip = (req.headers['x-forwarded-for'] || req.socket.remoteAddress || '').split(',')[0].trim();
  let city = null;
  if (geoip && ip) {
    const geo = geoip.lookup(ip);
    if (geo) city = geo.city || null;
  }

  await supabase.from('taps').insert({
    business_id: businessId,
    tapped_at: new Date().toISOString(),
    device_type: deviceType,
    city,
  });
}

// ─── Admin auth middleware ────────────────────────────────────────────────────

function adminAuth(req, res, next) {
  const session = req.headers.cookie || '';
  if (session.includes('austap_auth=1')) return next();
  res.redirect('/admin/login');
}

app.get('/admin/login', (_req, res) => {
  res.send(`<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AusTap Login</title>
<style>
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0f2f5;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}
  .box{background:#fff;border-radius:14px;padding:40px;width:100%;max-width:360px;box-shadow:0 4px 20px rgba(0,0,0,.1)}
  h1{font-size:1.5rem;margin-bottom:6px}h1 span{color:#4ade80}
  p{color:#6b7280;font-size:.85rem;margin-bottom:24px}
  input{width:100%;padding:10px 14px;border:1px solid #d1d5db;border-radius:8px;font-size:1rem;margin-bottom:14px;box-sizing:border-box}
  input:focus{outline:none;border-color:#4ade80;box-shadow:0 0 0 3px rgba(74,222,128,.2)}
  button{width:100%;padding:11px;background:#1a1a2e;color:#fff;border:none;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer}
  button:hover{background:#374151}
  .err{color:#991b1b;background:#fee2e2;padding:10px;border-radius:7px;font-size:.85rem;margin-bottom:14px}
</style></head>
<body><div class="box">
  <h1>Aus<span>Tap</span></h1>
  <p>Admin dashboard — enter your password to continue</p>
  <form method="POST" action="/admin/login">
    <input type="password" name="password" placeholder="Password" autofocus>
    <button type="submit">Login</button>
  </form>
</div></body></html>`);
});

app.post('/admin/login', (req, res) => {
  if (req.body.password === ADMIN_PASSWORD) {
    res.setHeader('Set-Cookie', 'austap_auth=1; HttpOnly; Path=/; SameSite=Strict; Max-Age=86400');
    return res.redirect('/admin');
  }
  res.send(`<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AusTap Login</title>
<style>
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0f2f5;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}
  .box{background:#fff;border-radius:14px;padding:40px;width:100%;max-width:360px;box-shadow:0 4px 20px rgba(0,0,0,.1)}
  h1{font-size:1.5rem;margin-bottom:6px}h1 span{color:#4ade80}
  p{color:#6b7280;font-size:.85rem;margin-bottom:24px}
  input{width:100%;padding:10px 14px;border:1px solid #d1d5db;border-radius:8px;font-size:1rem;margin-bottom:14px;box-sizing:border-box}
  button{width:100%;padding:11px;background:#1a1a2e;color:#fff;border:none;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer}
  .err{color:#991b1b;background:#fee2e2;padding:10px;border-radius:7px;font-size:.85rem;margin-bottom:14px}
</style></head>
<body><div class="box">
  <h1>Aus<span>Tap</span></h1>
  <p>Admin dashboard — enter your password to continue</p>
  <div class="err">Incorrect password. Try again.</div>
  <form method="POST" action="/admin/login">
    <input type="password" name="password" placeholder="Password" autofocus>
    <button type="submit">Login</button>
  </form>
</div></body></html>`);
});

app.get('/admin/logout', (_req, res) => {
  res.setHeader('Set-Cookie', 'austap_auth=; HttpOnly; Path=/; Max-Age=0');
  res.redirect('/admin/login');
});

// ─── Admin dashboard ──────────────────────────────────────────────────────────

app.get('/admin', adminAuth, async (req, res) => {
  try {
    const { data: businesses, error: bErr } = await supabase
      .from('businesses')
      .select('*')
      .order('created_at', { ascending: false });

    if (bErr) throw bErr;

    const tapStats = await buildTapStats(businesses || []);
    const html = renderAdminPage(businesses || [], tapStats, req.query.error, req.query.success);
    res.send(html);
  } catch (err) {
    res.status(500).send(`<pre>Error loading dashboard: ${err.message}</pre>`);
  }
});

async function buildTapStats(businesses) {
  if (!businesses.length) return {};

  const now = new Date();
  const todayStart = new Date(now); todayStart.setHours(0, 0, 0, 0);
  const weekStart = new Date(now); weekStart.setDate(now.getDate() - 7); weekStart.setHours(0, 0, 0, 0);

  const { data: taps } = await supabase
    .from('taps')
    .select('business_id, tapped_at')
    .gte('tapped_at', weekStart.toISOString());

  const { data: allTimeTaps } = await supabase
    .from('taps')
    .select('business_id, tapped_at')
    .order('tapped_at', { ascending: false });

  const stats = {};
  for (const b of businesses) {
    stats[b.id] = { today: 0, week: 0, total: 0, lastTap: null, daily: buildDailyBuckets(now) };
  }

  const todayMs = todayStart.getTime();
  const weekMs = weekStart.getTime();

  for (const tap of (taps || [])) {
    const s = stats[tap.business_id];
    if (!s) continue;
    const t = new Date(tap.tapped_at).getTime();
    if (t >= weekMs) s.week++;
    if (t >= todayMs) s.today++;
    const dayIdx = 6 - Math.floor((now.getTime() - t) / 86400000);
    if (dayIdx >= 0 && dayIdx < 7) s.daily[dayIdx].count++;
  }

  for (const tap of (allTimeTaps || [])) {
    const s = stats[tap.business_id];
    if (!s) continue;
    s.total++;
    if (!s.lastTap) s.lastTap = tap.tapped_at;
  }

  return stats;
}

function buildDailyBuckets(now) {
  const days = [];
  const dayLabels = ['Su','Mo','Tu','We','Th','Fr','Sa'];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    days.push({ count: 0, label: dayLabels[d.getDay()] });
  }
  return days;
}

// ─── Admin: add/update business ──────────────────────────────────────────────

app.post('/admin/business', adminAuth, async (req, res) => {
  const { _id, name, slug, redirect_url, platform, owner_email, active } = req.body;

  if (!name || !slug || !redirect_url || !platform) {
    return res.redirect('/admin?error=All+required+fields+must+be+filled+in');
  }

  const cleanSlug = slug.toLowerCase().trim();
  if (!/^[a-z0-9-]+$/.test(cleanSlug)) {
    return res.redirect('/admin?error=Slug+must+be+lowercase+letters%2C+numbers+and+hyphens+only');
  }

  const record = {
    name: name.trim(),
    slug: cleanSlug,
    redirect_url: redirect_url.trim(),
    platform,
    owner_email: owner_email?.trim() || null,
    active: active === 'true' || active === true || active === 'on',
  };

  try {
    if (_id) {
      const { error } = await supabase.from('businesses').update(record).eq('id', _id);
      if (error) throw error;
      return res.redirect('/admin?success=Business+updated+successfully');
    } else {
      record.active = true;
      const { error } = await supabase.from('businesses').insert(record);
      if (error) {
        if (error.message?.includes('unique') || error.code === '23505') {
          return res.redirect('/admin?error=That+URL+slug+is+already+taken.+Choose+a+different+one.');
        }
        throw error;
      }
      return res.redirect('/admin?success=Business+added+successfully');
    }
  } catch (err) {
    return res.redirect(`/admin?error=${encodeURIComponent('Database error: ' + err.message)}`);
  }
});

// ─── Start ────────────────────────────────────────────────────────────────────

app.listen(PORT, () => {
  console.log(`AusTap running on port ${PORT}`);
});
