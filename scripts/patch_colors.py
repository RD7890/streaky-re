#!/usr/bin/env python3
"""
patch_colors.py — Streaky to Patchify
- Finds the app's actual primary color from theme XML and replaces it with #FF2541
- Changes app name to Patchify
- Renames package to com.patchify.app (with proper class-name expansion)
- Injects a DebugActivity smali + registers it in the manifest
Run AFTER: apktool d --only-main-classes
"""
import os, re, sys
from pathlib import Path

NEW_PRIMARY = "#FF2541"


# ── 1. SMART COLOR PATCHING ────────────────────────────────────────────────

def find_primary_color_hex(d: Path) -> str | None:
    """
    Walk themes.xml / styles.xml to find what colorPrimary resolves to.
    Returns a hex string like '#FF6B35' or None if not found.
    """
    ref = None

    # Step A: find colorPrimary in themes/styles
    for f in list(d.rglob("res/**/themes*.xml")) + list(d.rglob("res/**/styles*.xml")):
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
            # <item name="colorPrimary">@color/something</item>
            m = re.search(r'name="colorPrimary"[^>]*>\s*@color/([^\s<]+)', t)
            if m:
                ref = m.group(1).strip()
                print(f"[color] colorPrimary → @color/{ref}  (from {f.name})")
                break
            # <item name="colorPrimary">#XXXXXX</item>
            m = re.search(r'name="colorPrimary"[^>]*>\s*(#[0-9A-Fa-f]{3,8})', t)
            if m:
                hex_val = m.group(1).strip()
                print(f"[color] colorPrimary = {hex_val}  (from {f.name})")
                return hex_val
        except Exception:
            pass

    if not ref:
        return None

    # Step B: resolve the @color/ref to a hex in colors.xml
    for f in d.rglob("res/**/colors.xml"):
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
            m = re.search(rf'name="{re.escape(ref)}"[^>]*>\s*(#[0-9A-Fa-f]{{3,8}})', t)
            if m:
                hex_val = m.group(1).strip()
                print(f"[color] @color/{ref} = {hex_val}  (from {f.name})")
                return hex_val
        except Exception:
            pass

    return None


def patch_primary_color(d: Path):
    """Replace the primary color throughout all XML resource files."""
    print(f"\n[colors] Patching primary color → {NEW_PRIMARY}")

    original_hex = find_primary_color_hex(d)

    xml_files = list(d.rglob("res/**/*.xml"))
    n = 0

    for f in xml_files:
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
            new = t

            # A: Replace the exact resolved primary hex everywhere it appears
            if original_hex:
                new = re.sub(re.escape(original_hex), NEW_PRIMARY, new, flags=re.IGNORECASE)

            # B: Replace color name references that are clearly primary/accent
            #    <color name="colorPrimary">...</color>
            #    <color name="primary_color">...</color>
            #    <color name="md_theme_light_primary">...</color>
            new = re.sub(
                r'(<color\s+name="[^"]*(?:colorPrimary|primary_color|md_theme_light_primary|seed|brand_primary)[^"]*"[^>]*>)\s*#[0-9A-Fa-f]{3,8}\s*(</color>)',
                rf'\g<1>{NEW_PRIMARY}\g<2>',
                new, flags=re.IGNORECASE
            )

            # C: Replace <item name="colorPrimary"> direct hex values
            new = re.sub(
                r'(name="colorPrimary"[^>]*>)\s*#[0-9A-Fa-f]{3,8}',
                rf'\g<1>{NEW_PRIMARY}',
                new, flags=re.IGNORECASE
            )

            if new != t:
                f.write_text(new, encoding="utf-8")
                n += 1
                print(f"  patched: {f.relative_to(d)}")
        except Exception as e:
            print(f"  skip {f.name}: {e}")

    print(f"[colors] {n} files patched\n")


# ── 2. APP NAME ────────────────────────────────────────────────────────────

def patch_app_name(d: Path):
    print("[name] Patching app name → Patchify")
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
    print()


# ── 3. MANIFEST (package rename + class expansion) ─────────────────────────

def patch_manifest(d: Path) -> str:
    """Returns the original package name (needed for smali path)."""
    m = d / "AndroidManifest.xml"
    if not m.exists():
        print("[manifest] Not found — skipping")
        return ""

    print("[manifest] Patching package + expanding relative class names")
    t = m.read_text(encoding="utf-8", errors="replace")

    orig_match = re.search(r'package="([^"]+)"', t)
    if not orig_match:
        print("  could not find package attr")
        return ""

    orig_pkg = orig_match.group(1)
    print(f"  original package: {orig_pkg}")

    # Expand relative android:name=".Foo" → "orig.pkg.Foo"
    def expand(match):
        name = match.group(1)
        return f'android:name="{orig_pkg}{name}"' if name.startswith(".") else match.group(0)

    new = re.sub(r'android:name="(\.[^"]+)"', expand, t)

    # Rename package
    new = re.sub(r'(package=")[^"]*(")', r'\1com.patchify.app\2', new, count=1)

    # Inject DebugActivity before </application>
    debug_entry = '''
        <activity
            android:name="com.patchify.app.DebugActivity"
            android:label="Patchify Debug"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>'''

    if 'com.patchify.app.DebugActivity' not in new:
        new = new.replace('</application>', debug_entry + '\n    </application>')
        print("  DebugActivity registered in manifest")

    m.write_text(new, encoding="utf-8")
    print(f"  package → com.patchify.app\n")
    return orig_pkg


# ── 4. DEBUG ACTIVITY SMALI ───────────────────────────────────────────────

SMALI_CONTENT = '''.class public Lcom/patchify/app/DebugActivity;
.super Landroid/app/Activity;
.source "DebugActivity.java"

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V
    return-void
.end method

.method protected onCreate(Landroid/os/Bundle;)V
    .registers 4

    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    # Create a TextView programmatically - no layout file needed
    new-instance v0, Landroid/widget/TextView;
    invoke-direct {v0, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    # Set the debug info text
    const-string v1, "Patchify Debug Screen\\n\\nApp: Patchify\\nPackage: com.patchify.app\\nVersion: 1.0.23 (RE build)\\nPrimary color: #FF2541\\n\\nPatched via GitHub Actions RE Pipeline"
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    # Set padding (32px)
    const/16 v1, 0x20
    invoke-virtual {v0, v1, v1, v1, v1}, Landroid/widget/TextView;->setPadding(IIII)V

    # Set text size to 16sp
    const/4 v1, 0x2
    const v2, 0x41800000
    invoke-virtual {v0, v1, v2}, Landroid/widget/TextView;->setTextSize(IF)V

    # Set as content view
    invoke-virtual {p0, v0}, Landroid/app/Activity;->setContentView(Landroid/view/View;)V

    return-void
.end method
'''


def inject_debug_activity(d: Path):
    """Write DebugActivity.smali into the main smali folder."""
    print("[debug] Injecting DebugActivity smali")
    smali_dir = d / "smali" / "com" / "patchify" / "app"
    smali_dir.mkdir(parents=True, exist_ok=True)
    smali_file = smali_dir / "DebugActivity.smali"
    smali_file.write_text(SMALI_CONTENT, encoding="utf-8")
    print(f"  written: {smali_file.relative_to(d)}\n")


# ── MAIN ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: patch_colors.py <decompiled_dir>")
        sys.exit(1)

    d = Path(sys.argv[1]).resolve()
    print(f"=== Patcher starting: {d} ===\n")

    patch_primary_color(d)
    patch_app_name(d)
    orig_pkg = patch_manifest(d)
    inject_debug_activity(d)

    print("=== Patcher done ===")
