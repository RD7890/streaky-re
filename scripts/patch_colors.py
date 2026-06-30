#!/usr/bin/env python3
"""
patch_colors.py — Streaky to Patchify
Patches colors, app name and package ID in a decompiled APK directory.
"""
import re, sys
from pathlib import Path

COLOR_MAP = {
    "#FF6B35": "#7C3AED", "#FF5722": "#6D28D9",
    "#FF9800": "#8B5CF6", "#FFC107": "#A78BFA",
    "#F44336": "#7C3AED", "#E91E63": "#6D28D9",
    "#FF4081": "#8B5CF6", "#FF6F00": "#6D28D9",
    "#E65100": "#5B21B6", "#BF360C": "#4C1D95",
    "#2196F3": "#0D9488", "#1976D2": "#0F766E",
    "#03A9F4": "#14B8A6", "#1565C0": "#0F766E",
    "#0D47A1": "#134E4A", "#4CAF50": "#059669",
    "#388E3C": "#047857", "#1B5E20": "#064E3B",
}

def patch_xml_files(d):
    files = list(d.rglob("res/**/*.xml"))
    print(f"[colors] Scanning {len(files)} XML files")
    n = 0
    for f in files:
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
            new = t
            for old, new_c in COLOR_MAP.items():
                new = re.sub(re.escape(old), new_c, new, flags=re.IGNORECASE)
            if new != t:
                f.write_text(new, encoding="utf-8")
                n += 1
                print(f"  patched: {f.relative_to(d)}")
        except Exception as e:
            print(f"  skip {f.name}: {e}")
    print(f"[colors] {n}/{len(files)} files patched")

def patch_app_name(d):
    print("[name] Patching app name")
    for f in d.rglob("res/**/strings.xml"):
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
            new = re.sub(r'(<string\s+name="app_name"\s*>)[^<]*(</string>)', r'\1Patchify\2', t)
            new = re.sub(r'\bStreaky\b', 'Patchify', new)
            if new != t:
                f.write_text(new, encoding="utf-8")
                print(f"  patched: {f.relative_to(d)}")
        except Exception as e:
            print(f"  skip {f.name}: {e}")

def patch_manifest(d):
    m = d / "AndroidManifest.xml"
    if not m.exists():
        return
    print("[manifest] Patching package ID")
    try:
        t = m.read_text(encoding="utf-8", errors="replace")
        new = re.sub(r'(package=")[^"]*(")', r'\1com.patchify.app\2', t, count=1)
        if new != t:
            m.write_text(new, encoding="utf-8")
            print("  package → com.patchify.app")
        else:
            print("  package unchanged (may already be patched)")
    except Exception as e:
        print(f"  skip manifest: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: patch_colors.py <decompiled_dir>")
        sys.exit(1)
    d = Path(sys.argv[1]).resolve()
    print(f"=== Patcher: {d} ===")
    patch_xml_files(d)
    patch_app_name(d)
    patch_manifest(d)
    print("=== Done ===")
