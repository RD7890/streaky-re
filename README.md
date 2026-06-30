# streaky-re 🔧

Reverse engineering pipeline for **Streaky** APK.  
Decompiles → patches theme/colors/name → recompiles → signs → uploads as artifact — all in GitHub Actions.

## How it works

```
push APK to main
      │
      ▼
┌─────────────────────────────────────────┐
│         GitHub Actions CI               │
│                                         │
│  1. apktool d *.apk → decompiled/       │
│  2. python3 scripts/patch_colors.py     │  ← changes colors, app name, package
│  3. apktool b decompiled/ → patched.apk │
│  4. jarsigner (debug key) → signed.apk  │
│  5. upload-artifact                     │
└─────────────────────────────────────────┘
```

## Trigger

The workflow runs automatically whenever you push a new APK or change any file under `scripts/`.  
You can also trigger it manually via **Actions → Run workflow**.

## Download the patched APK

After the workflow finishes, go to **Actions → latest run → Artifacts** and download `modified-apk-<run>`.

## What gets patched

| Change | Detail |
|--------|--------|
| App name | `Streaky` → `Patchify` |
| Package ID | original → `com.patchify.app` |
| Primary colors | orange/red/blue → deep purple/violet/teal |
| Accent colors | original palette → violet shades |

> **Educational use only** — this repo is for learning Android reverse engineering on an app you own.

## Tools used

- [apktool](https://github.com/iBotPeaches/Apktool) — decompile & recompile
- Python 3 — resource patching
- `jarsigner` (JDK) — APK signing with debug key

