# AusTap — NFC Tap-to-Review System

When a customer taps an NFC sticker, they're instantly sent to your Google (or Yelp/TripAdvisor) review page. Every tap is logged so you can track how each client's sticker is performing.

---

## Quick-start checklist

- [ ] Set up Supabase database
- [ ] Deploy to Railway
- [ ] Set environment variables
- [ ] Add your businesses in the Admin dashboard
- [ ] Program your NFC stickers

---

## Step 1 — Set up Supabase

1. Go to [supabase.com](https://supabase.com) and create a **free** account.
2. Click **New project**, give it a name like `austap`, choose a region close to Australia, and set a database password (save it somewhere safe).
3. Once the project loads, click **SQL Editor** in the left sidebar.
4. Click **New query**, then paste the entire contents of `supabase-setup.sql` into the editor.
5. Click **Run**. This creates your tables and adds two demo businesses.
6. Go to **Project Settings → API** and copy:
   - **Project URL** → this is your `SUPABASE_URL`
   - **anon / public** key → this is your `SUPABASE_ANON_KEY`

---

## Step 2 — Deploy to Railway

1. Go to [railway.app](https://railway.app) and sign up with GitHub (free).
2. Click **New Project → Deploy from GitHub repo**.
3. Connect your GitHub account and select this repository.
4. Railway will detect it's a Node.js app and deploy automatically.
5. Once deployed, go to **Settings → Networking** and generate a **public domain** (e.g. `austap-production.up.railway.app`). Copy this URL.

---

## Step 3 — Set environment variables in Railway

In your Railway project, go to **Variables** and add these one by one:

| Variable | Value |
|---|---|
| `SUPABASE_URL` | Your Supabase Project URL |
| `SUPABASE_ANON_KEY` | Your Supabase anon/public key |
| `ADMIN_PASSWORD` | A strong password you choose (e.g. `BlueSky#2024`) |
| `BASE_URL` | Your Railway domain, e.g. `https://austap-production.up.railway.app` |

Railway will automatically restart the app after you save variables.

**Test it's working:** Visit `https://your-domain.up.railway.app/health` — you should see `{"status":"ok"}`.

---

## Step 4 — Access the Admin dashboard

1. Go to `https://your-domain.up.railway.app/admin`
2. Enter the `ADMIN_PASSWORD` you set.
3. You'll see the two demo businesses. Replace the demo redirect URLs with real Google review links (see below for how to get those).

### How to get a Google review link

1. Search for the business on [Google Maps](https://maps.google.com).
2. Click **Share → Copy link**.
3. Or go to the business's Google Maps page and click the **Write a review** button — copy that URL from your browser.

---

## Step 5 — Program the NFC stickers

Use the free **NFC Tools** app (available on iPhone and Android):

1. Open **NFC Tools** → tap **Write** → **Add a record** → **URL / URI**.
2. Enter your redirect URL: `https://your-domain.up.railway.app/r/business-slug`
   - Example: `https://austap-production.up.railway.app/r/joes-barbershop`
3. Tap **OK** → **Write**.
4. Hold your phone against the NFC sticker until it confirms success.
5. Test it by tapping the sticker with a different phone — it should open the review page.

> **Tip:** Copy the NFC link from the Admin dashboard using the "Copy NFC Link" button next to each business.

---

## Adding a new business client

1. Log in to the Admin dashboard at `/admin`.
2. Scroll to the bottom and fill in the **Add New Business** form:
   - **Business Name** — e.g. `Maria's Cafe`
   - **URL Slug** — a short lowercase identifier, e.g. `marias-cafe` (no spaces or special characters)
   - **Review Page URL** — the Google/Yelp/TripAdvisor review URL
   - **Platform** — select the platform
   - **Owner Email** — optional, for your records
3. Click **Add Business**.
4. Program the NFC sticker with the new URL (shown via "Copy NFC Link" in the dashboard).
5. Hand the sticker to the business owner.

---

## How the redirect works

```
Customer taps NFC sticker
         |
Phone opens:  https://your-domain.up.railway.app/r/joes-barbershop
         |
Server looks up "joes-barbershop" in Supabase (under 50ms)
         |
Logs the tap in background (device type, city, timestamp)
         |
Instantly redirects (302) to Google review page
```

The analytics log never blocks the redirect — if Supabase is slow, the customer still gets redirected instantly.

---

## Monitoring uptime (optional, free)

Use [UptimeRobot](https://uptimerobot.com) (free):
1. Sign up and click **Add New Monitor**.
2. Type: **HTTP(s)**, URL: `https://your-domain.up.railway.app/health`
3. Check interval: 5 minutes.
4. Add your email for alerts.
5. This also keeps the app awake on Railway's free tier.

---

## Troubleshooting

**Redirect not working / 404**
- Check the slug in the admin dashboard matches exactly what's programmed on the NFC sticker.
- Make sure the business is set to **Active** (edit it in the dashboard).

**Admin dashboard shows a database error**
- Double-check your `SUPABASE_URL` and `SUPABASE_ANON_KEY` in Railway's Variables tab.
- Make sure you ran the SQL setup script in Supabase.

**NFC sticker not detected by phones**
- Ensure the sticker is NTAG213, NTAG215, or NTAG216 type (standard white NFC stickers are fine).
- iPhone requires iOS 13+ and the phone must be unlocked.

**App is slow to respond the first time**
- Railway free tier may sleep after inactivity. Use UptimeRobot pinging `/health` every 5 minutes to keep it awake.
