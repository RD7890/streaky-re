#!/usr/bin/env python3
"""
patch_colors.py — Streaky → Patchify
Patches theme colors, app name, and package ID in a decompiled APK directory.

Usage:
    python3 scripts/patch_colors.py <decompiled_dir>
"""

import os
import re
import sys
from pathlib import Path


# ── Color substitution table ────────────────────────────────────────────────
# Maps original hex colors → new violet/teal palette
COLOR_MAP = {
    # Warm/orange/amber/red → deep purple / violet
    "#FF6B35": "#7C3AED",
    "#FF5722": "#6D28D9",
    "#FF9800": "#8B5CF6",
    "#FFC107": "#A78BFA",
    "#F44336": "#7C3AED",
    "#E91E63": "#6D28D9",
    "#FF4081": "#8B5CF6",
    "#FF6F00": "#6D28D9",
    "#E65100": "#5B21B6",
    "#BF360C": "#4C1D95",
    # Blues → teal
    "#2196F3": "#0D9488",
    "#1976D2": "#0F766E",
    "#03A9F4": "#14B8A6",
    "#1565C0": "#0F766E",
    "#0D47A1": "#134E4A",
    # Greens → emerald (keep readable)
    "#4CAF50": "#059669",
    "#388E3C": "#047857",
    "#1B5E20": "#064E3B",
    # Uppercase variants
    "#FF6B35".lower(): "#7C3AED",
    "#FF5722".lower(): "#6D28D9",
    "#2196F3".lower(): "#0D9488",
}


def patch_xml_files(decompiled: Path) -> int:
    """Replace color hex values in all res/**/*.xml files."""
    xml_files = list(decompiled.rglob("res/**/*.xml"))
    print(f"[colors] Scanning {len(xml_files)} XML files …")
    patched = 0
    for f in xml_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
            new_text = text
            for old, new in COLOR_MAP.items():
                new_text = re.sub(re.escape(old), new, new_text, flags=re.IGNORECASE)
            if new_text != text:
                f.write_text(new_text, encoding="utf-8")
                patched += 1
                print(f"  ✔ {f.relative_to(decompiled)}")
        except Exception as exc:
            print(f"  ✗ {f.name}: {exc}")
    print(f"[colors] Patched {patched}/{len(xml_files)} files.\n")
    return patched


def patch_app_name(decompiled: Path) -> None:
    """Rename app from Streaky to Patchify in strings resources."""
    print("[name] Patching app name …")
    for f in decompiled.rglob("res/**/strings.xml"):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
            new_text = re.sub(
                r'(<string\s+name="app_name"\s*>)[^<]*(</string>)',
                r'\1Patchify\2', text
            )
            new_text = re.sub(r'\bStreaky\b', 'Patchify', new_text)
            if new_text != text:
                f.write_text(new_text, encoding="utf-8")
                print(f"  ✔ {f.relative_to(decompiled)}")
        except Exception as exc:
            print(f"  ✗ {f.name}: {exc}")


def patch_manifest(decompiled: Path) -> None:
    """Update package ID in AndroidManifest.xml."""
    manifest = decompiled / "AndroidManifest.xml"
    if not manifest.exists():
        print("[manifest] AndroidManifest.xml not found — skipping.")
        return
    print("[manifest] Patching package ID …")
    try:
        text = manifest.read_text(encoding="utf-8", errors="replace")
        new_text = re.sub(
            r'(package=")[^"]*(")',
            r'\1com.patchify.app\2',
            text, count=1
        )
        if new_text != text:
            manifest.write_text(new_text, encoding="utf-8")
            print("  ✔ AndroidManifest.xml package → com.patchify.app")
        else:
            print("  ℹ  package attribute unchanged (may already be patched).")
    except Exception as exc:
        print(f"  ✗ manifest: {exc}")


def main():
    if len(sys.argv) < 2:
        print("Usage: patch_colors.py <decompiled_dir>")
        sys.exit(1)

    decompiled = Path(sys.argv[1]).resolve()
    if not decompiled.is_dir():
        print(f"Error: {decompiled} is not a directory.")
        sys.exit(1)

    print(f"=== Patcher starting on: {decompiled} ===\n")
    patch_xml_files(decompiled)
    patch_app_name(decompiled)
    patch_manifest(decompiled)
    print("\n=== Patcher finished ===")


if __name__ == "__main__":
    main()
