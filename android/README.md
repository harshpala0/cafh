# CA FirmHub — Android / Play Store packaging

The web app is a Progressive Web App (PWA).  
To list it on the **Google Play Store** while keeping the same online backend, use a **Trusted Web Activity (TWA)** via [Bubblewrap](https://github.com/GoogleChromeLabs/bubblewrap).

This keeps 100% feature parity with the website and does not require rewriting the app in Flutter/React Native.

## Prerequisites

- Node.js 18+
- Java JDK 17
- Android SDK / command-line tools
- A domain that serves the live CA FirmHub (HTTPS required)
- Google Play Console developer account

## 1. Deploy the enhanced web app first

Push the PWA changes (manifest, service worker, mobile UI) to your Render (or other) deployment and confirm:

- `https://YOUR-DOMAIN/` loads and is installable
- `/static/manifest.json` is reachable
- `/static/sw.js` is reachable
- Chrome → Application → Manifest shows no errors

## 2. Generate the Android project with Bubblewrap

```bash
npm install -g @bubblewrap/cli
bubblewrap init --manifest https://YOUR-DOMAIN/static/manifest.json
```

Answer the prompts:

- Package ID (example): `com.cafirmhub.app`
- App name: `CA FirmHub`
- Launcher name: `FirmHub`
- Display mode: `standalone`
- Theme colour: `#003366`
- Background colour: `#003366`
- Start URL: `/`
- Icon: use the generated or upload `app_logo.png`

Bubblewrap creates a full Android project.

## 3. Digital Asset Links (required for Play Store)

Create a file on your server:

`https://YOUR-DOMAIN/.well-known/assetlinks.json`

Content (replace SHA256 and package name after first build):

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.cafirmhub.app",
    "sha256_cert_fingerprints": ["AA:BB:CC:..."]
  }
}]
```

Get the fingerprint after building the signing key:

```bash
keytool -list -v -keystore android.keystore
```

## 4. Build the release AAB

```bash
bubblewrap build
```

This produces an `.aab` file ready for Play Console upload.

## 5. Play Console checklist

- Create new app → “CA FirmHub”
- Category: Business / Productivity
- Upload the AAB
- Complete store listing (screenshots from a real phone, short description, privacy policy URL)
- Content rating questionnaire
- Target audience & news apps declarations
- Privacy policy must mention data stored on your servers (Neon / Render)

## Alternative: Capacitor (if you prefer more native control later)

```bash
npm init @capacitor/app
# point webDir to a built static export of the SPA
npx cap add android
npx cap sync
```

TWA/Bubblewrap is simpler and keeps a single codebase.

## Important notes

- The app **requires internet** for all data (API calls). Offline only shows the cached shell.
- Do **not** change existing API contracts or desktop layout; the mobile CSS is additive only.
- Test thoroughly on real Android devices before submitting.
- Keep the same SECRET_KEY / DATABASE_URL; no backend changes needed for the mobile wrapper.
