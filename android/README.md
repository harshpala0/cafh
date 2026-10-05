# CA FirmHub — Android (Play Store) via Trusted Web Activity

Ship the live site **https://cafh.onrender.com** as an installable Play Store app using **Bubblewrap** (TWA).
No separate native UI — same backend, same features, mobile-optimised PWA.

## Prerequisites

- Node.js 18+
- JDK 17
- Android SDK / command-line tools
- Google Play Developer account
- Live app domain: `cafh.onrender.com`

## 1. Generate signing key

```bash
keytool -genkey -v -keystore cafirmhub.keystore -alias cafirmhub \
  -keyalg RSA -keysize 2048 -validity 10000
```

Get SHA-256:

```bash
keytool -list -v -keystore cafirmhub.keystore -alias cafirmhub
```

Copy the **SHA-256** fingerprint.

## 2. Publish Digital Asset Links

Route `/.well-known/assetlinks.json` is provided by the app.

Set on Render:

```
TWA_PACKAGE=com.cafirmhub.app
TWA_SHA256=AA:BB:CC:...   # from keytool (colon-separated hex)
```

Verify:

```
https://cafh.onrender.com/.well-known/assetlinks.json
```

Google tester: https://developers.google.com/digital-asset-links/tools/generator

## 3. Bubblewrap init

```bash
npm i -g @bubblewrap/cli
bubblewrap init --manifest https://cafh.onrender.com/static/manifest.json
```

| Field | Value |
|-------|--------|
| Package ID | `com.cafirmhub.app` |
| Name | CA FirmHub |
| Host | `cafh.onrender.com` |
| Start URL | `/` |
| Display | `standalone` |

Use the same keystore as step 1. See also `android/twa-manifest.json`.

## 4. Build & release

```bash
bubblewrap build
```

Upload the **AAB** to Play Console → Internal testing → Production.

## 5. Play Console checklist

- [ ] App name, short & full description
- [ ] Icon 512×512 (`static/app_logo.png`)
- [ ] Feature graphic 1024×500
- [ ] Privacy policy URL
- [ ] Content rating questionnaire
- [ ] Asset Links verified (no URL bar in TWA)

## 6. Updates

Most product updates need **no new Play release** — TWA loads the live website.
Rebuild the AAB only for package/icon/signing changes.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Chrome shows URL bar | Asset Links mismatch (package / SHA-256 / domain) |
| White screen | HTTPS, service worker, manifest `start_url` |
| Login loops | Cookies on domain (Secure, SameSite) |
