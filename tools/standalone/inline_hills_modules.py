"""Inline Hills Lua modules into production scripts before packaging.

LuaJIT's loadfile/dofile path handling on Windows can fail when the portable
folder contains non-ASCII characters. mpv itself can load the top-level script,
so embedding the small local modules removes that second filesystem open while
keeping the standalone module files for source-level tests.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULES = ROOT / "portable_config" / "script-modules"
SCRIPTS = ROOT / "portable_config" / "scripts"


def wrapped(module_name: str) -> str:
    body = (MODULES / module_name).read_text(encoding="utf-8-sig").rstrip()
    return "(function()\n-- inlined module: " + module_name + "\n" + body + "\nend)()"


def replace_once(path: Path, needle: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8-sig")
    marker = "-- inlined module: "
    if needle not in text:
        if marker in text:
            return
        raise RuntimeError(f"Hills module inclusion context changed: {path.name}: {needle}")
    if text.count(needle) != 1:
        raise RuntimeError(f"Ambiguous Hills module inclusion: {path.name}: {needle}")
    path.write_text(text.replace(needle, replacement), encoding="utf-8")


hills = SCRIPTS / "hills.lua"
replace_once(
    hills,
    "dofile(mp.command_native({'expand-path','~~/script-modules/hills_core.lua'}))",
    wrapped("hills_core.lua"),
)
replace_once(
    hills,
    "dofile(mp.command_native({'expand-path','~~/script-modules/hills_metrics.lua'}))",
    wrapped("hills_metrics.lua"),
)
replace_once(
    hills,
    "dofile(mp.command_native({'expand-path','~~/script-modules/hills_menu.lua'}))",
    wrapped("hills_menu.lua"),
)

replace_once(
    SCRIPTS / "hills_danmaku.lua",
    "dofile(mp.command_native({'expand-path','~~/script-modules/hills_core.lua'}))",
    wrapped("hills_core.lua"),
)

for path in (hills, SCRIPTS / "hills_danmaku.lua"):
    text = path.read_text(encoding="utf-8")
    if "dofile(mp.command_native({'expand-path','~~/script-modules/" in text:
        raise RuntimeError(f"Runtime module loader remains in {path.name}")

print("Hills runtime modules inlined for Unicode-safe portable paths")
