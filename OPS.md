# CA FirmHub — Operations guide

## Daily digest cron (Render)

1. Render Dashboard → your web service → **Environment**
2. Add:

```
CRON_SECRET=long-random-string
SMTP_HOST=...
SMTP_USER=...
SMTP_PASS=...
SMTP_FROM=...
DIGEST_EMAIL_TO=partners@yourfirm.com
```

Optional WhatsApp:

```
WHATSAPP_WEBHOOK_URL=https://...
DIGEST_WHATSAPP_TO=9198xxxxxxxx
```

3. Create a **Cron Job** (Render Cron or external):

- Schedule (3:00 AM IST ≈ `30 21 * * *` UTC)
- HTTP:

```bash
curl -sS -X POST "https://cafh.onrender.com/api/ops/notify/cron?channel=both" \
  -H "X-Cron-Secret: long-random-string"
```

4. Test once:

```bash
curl -sS "https://cafh.onrender.com/api/ops/notify/cron?channel=email&secret=YOUR_SECRET"
```

Empty digests are skipped unless `CRON_FORCE=1`.

## Health check

```
GET https://cafh.onrender.com/api/ops/health
```

Shows loaded modules, cron/SMTP/WhatsApp flags.

## Dashboard buttons (staff)

- Reminders · Receivables · Portal inbox · Email digest · WhatsApp
