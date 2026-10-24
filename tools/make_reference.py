"""Builds Metal Slug 5's decrypted reference files from the regions MAME decrypts.

Metal Slug 5 has no PC release. Until the port decrypts MAME's set itself (Phase 5), the runtime
loads these files instead: MAME's regions, dumped from the user's set with
tools/mame/dump_region.lua into <roms>/decrypted, converted to the layout the runtime uses (the
DotEmu layout of the PC releases, as Metal Slug X's and Metal Slug 3's GOG files). They live in
<roms> only (the .gitignore keeps mslug5_* out of the repository).

Usage:
    python tools/make_reference.py [--roms DIR] [--sm1]
    python tools/make_reference.py [--roms DIR] --mslug4 OUT   (Metal Slug 4, below)

Writes <roms>/mslug5_game_m68k, _game_sfix, _tiles, _game_z80, _adpcm, _bios_m68k, _bios_sfix,
_zoom_table and prints their SHA-256 (src/games/mslug5/game.c holds them). Every conversion is
checked by converting back with tools/extract_roms.py's functions (Metal Slug 3's, verified there).

--sm1 also replaces <roms>/neogeo/sm1.sm1 (MAME's sound BIOS, not in the user's files) by the
first 128 KB of the decrypted M1: the port has no SM1 and boots the Z80 from the M1, so MAME must
run the same code (the Metal Slug 3 workspace did the same with its own M1).
<roms>/MANIFEST.sha256 is updated.

Input regions (dump_region.lua, file byte order): maincpu.bin (8 MB), sprites.bin (64 MB),
fixed.bin (128 KB), audiocpu.bin (576 KB: 0x10000-0x8FFFF is the decrypted M1), adpcma.bin
(16 MB). This script contains no ROM data: only format conversions.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_roms import fix_dotemu_to_neogeo, sprites_dotemu_to_region   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GAME = "mslug5"


def fix_neogeo_to_dotemu(d: bytes) -> bytes:
    """Neo Geo S format to the DotEmu fix (the inverse of fix_dotemu_to_neogeo)."""
    s = np.frombuffer(d, np.uint8).reshape(-1, 4, 8)          # tile, group, row
    out = np.empty((s.shape[0], 8, 4), np.uint8)              # tile, row, pixel pair
    for k, g in enumerate((2, 3, 0, 1)):
        out[:, :, k] = s[:, g, :]
    return out.tobytes()


def sprites_region_to_dotemu(region: bytes) -> bytes:
    """MAME's decrypted sprite region to DotEmu tiles (the inverse of sprites_dotemu_to_region)."""
    r = np.frombuffer(region, np.uint8).reshape(-1, 128)
    px = np.zeros((r.shape[0], 16, 16), np.uint8)
    for half, base in ((0, 0x40), (1, 0x00)):
        for offset, plane in ((0, 0), (1, 2), (2, 1), (3, 3)):
            rows = r[:, base + offset: base + 64: 4]               # tile, row
            for x in range(8):
                bit = (rows >> (7 - x)) & 1
                px[:, :, half * 8 + x] |= (bit << plane).astype(np.uint8)
    t = px[:, :, 0::2] | (px[:, :, 1::2] << 4)
    return t.astype(np.uint8).tobytes()


def mslug4_program(roms: Path, out: Path) -> int:
    """Metal Slug 4: only the 68000 files the analysis and the recompiler read (the GOG copy loads
    as it is). <out>/mslug4_game_m68k is GOG's p1.bin (MAME's maincpu region, checked against
    <roms>/decrypted/maincpu.bin) and mslug4_bios_m68k the us BIOS (sp-u2.sp1). They live outside
    <roms>: there, the loader would take the mslug4_* names for a DotEmu copy."""
    p1, maincpu = (roms / "gog" / "p1.bin").read_bytes(), (roms / "decrypted" / "maincpu.bin").read_bytes()
    print(f"p1.bin = maincpu.bin: {'OK' if p1 == maincpu else 'FAILED'}")
    if p1 != maincpu:
        return 1
    out.mkdir(parents=True, exist_ok=True)
    for n, d in {"game_m68k": p1, "bios_m68k": (roms / "neogeo" / "sp-u2.sp1").read_bytes()}.items():
        (out / f"mslug4_{n}").write_bytes(d)
        print(f"{out / f'mslug4_{n}'}: {len(d)} bytes, SHA-256 {hashlib.sha256(d).hexdigest()}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--roms", type=Path, default=Path(os.environ.get("PD_ROMS") or ROOT / "roms"))
    ap.add_argument("--sm1", action="store_true")
    ap.add_argument("--mslug4", type=Path, metavar="OUT",
                    help="Metal Slug 4: write the 68000 reference files to OUT instead")
    a = ap.parse_args()
    if a.mslug4:
        return mslug4_program(a.roms, a.mslug4)
    dec, neo = a.roms / "decrypted", a.roms / "neogeo"
    rd = lambda p: p.read_bytes()

    maincpu, sprites, fixed = rd(dec / "maincpu.bin"), rd(dec / "sprites.bin"), rd(dec / "fixed.bin")
    audiocpu, adpcma = rd(dec / "audiocpu.bin"), rd(dec / "adpcma.bin")
    sizes = {"maincpu": (maincpu, 8 << 20), "sprites": (sprites, 64 << 20), "fixed": (fixed, 128 << 10),
             "audiocpu": (audiocpu, 576 << 10), "adpcma": (adpcma, 16 << 20)}
    for n, (d, s) in sizes.items():
        if len(d) != s:
            sys.exit(f"{n}.bin: {len(d)} bytes, expected {s}")
    m1 = audiocpu[0x10000:]

    files = {
        "game_m68k": maincpu,
        "game_sfix": fix_neogeo_to_dotemu(fixed),
        "tiles": sprites_region_to_dotemu(sprites),
        "game_z80": m1,
        "adpcm": adpcma,
        "bios_m68k": rd(neo / "sp-u2.sp1"),
        "bios_sfix": fix_neogeo_to_dotemu(rd(neo / "sfix.sfix")),
        "zoom_table": rd(neo / "000-lo.lo"),
    }
    # Round trips with the Metal Slug 3 port's (verified) conversions.
    checks = {
        "game_sfix": fix_dotemu_to_neogeo(files["game_sfix"]) == fixed,
        "bios_sfix": fix_dotemu_to_neogeo(files["bios_sfix"]) == rd(neo / "sfix.sfix"),
        "tiles": sprites_dotemu_to_region(files["tiles"]).tobytes() == sprites,
    }
    for n, ok in checks.items():
        print(f"round trip {n}: {'OK' if ok else 'FAILED'}")
    if not all(checks.values()):
        return 1

    for n, d in files.items():
        p = a.roms / f"{GAME}_{n}"
        p.write_bytes(d)
        print(f'[NG_DOTEMU_?] = {{"{p.name}", {len(d)}, "{hashlib.sha256(d).hexdigest()}"}},')
    if a.sm1:
        (neo / "sm1.sm1").write_bytes(m1[:0x20000])
        print(f"neogeo/sm1.sm1: the first 128 KB of the decrypted M1, SHA-256 "
              f"{hashlib.sha256(m1[:0x20000]).hexdigest()}")

    # MANIFEST.sha256: every file under <roms> except the manifest itself.
    lines = []
    for p in sorted(x for x in a.roms.rglob("*") if x.is_file() and x.name != "MANIFEST.sha256"):
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()} *{p.relative_to(a.roms).as_posix()}")
    (a.roms / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"MANIFEST.sha256: {len(lines)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
