"""Rebuilds MAME's `mslug4h` set from the user's GOG copy, by inverting the black-box maps.

The GOG copy (Code Mystics' format, roms/gog/*.bin) holds MAME's regions after decryption. The
maps learned by tools/probe_decryption.py (synthetic patterns, no MAME code read) give every output
unit of a region as pi_i(input unit sigma(i)) XOR c(i); each input unit is recovered from the
outputs that come from it (all of them must agree), so the files MAME loads are rebuilt and checked
by CRC-32 and SHA-1 against `mame -listxml mslug4h` (tools/verify_set.py).

Usage:
    python tools/rebuild_set.py [--gog DIR] [--maps DIR] [--out DIR]

  --gog   the copy of the GOG files (default <workspace>/roms/gog)
  --maps  the learned maps (default <workspace>/analysis/phase0/probe: program/, graphics/,
          audio/, adpcm/)
  --out   where the set goes (default <workspace>/roms/mslug4h, loose files MAME reads with
          -rompath roms)
  --sm1   also replaces <workspace>/roms/neogeo/sm1.sm1 (MAME's sound BIOS, not in the user's
          files) by the first 128 KB of the decrypted M1 (m1.bin from 0x10000): the port has no
          SM1 and boots the Z80 from the M1, so MAME must run the same code (as the Metal Slug 3
          and 5 workspaces did with their own M1). roms/MANIFEST.sha256 is updated.

Nothing here holds game data; the rebuilt files stay outside the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_decryption import TARGETS, apply  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

# Probe target -> (GOG file, MAME region it equals).
GOG = {
    "program": ("p1.bin", "maincpu"),
    "graphics": ("c1.bin", "sprites"),
    "audio": ("m1.bin", "audiocpu"),
    "adpcm": ("v1.bin", "adpcma"),
}


def packed_to_planar(packed: np.ndarray) -> np.ndarray:
    """Code Mystics' c1.bin holds the sprites as packed pixels: per 128-byte tile, 16 rows of 8
    bytes, two 4-bit pixels a byte (low nibble first), left to right. MAME's region holds bit
    planes: 4 bytes per 8-pixel line (planes 0, 2, 1, 3), bit x = pixel x; the tile's right half in
    bytes 0-63, the left half in 64-127, rows 8-15 32 bytes after rows 0-7. (Learned from the GOG
    files: the region's last 512 KB, which MAME also shows as the fix layer, are s2.bin; every
    tile bit matched one bit.)"""
    t = packed.reshape(-1, 16, 8)
    pix = np.empty((t.shape[0], 16, 16), np.uint8)
    pix[:, :, 0::2] = t & 15
    pix[:, :, 1::2] = t >> 4
    out = np.zeros((t.shape[0], 128), np.uint8)
    rows = np.arange(16)
    for h, base in ((0, 64), (1, 0)):
        half = pix[:, :, 8 * h:8 * h + 8]
        for n, plane in enumerate((0, 2, 1, 3)):
            bits = ((half >> n) & 1).astype(np.uint8)
            byte = np.zeros(half.shape[:2], np.uint8)
            for x in range(8):
                byte |= bits[:, :, x] << x
            out[:, base + 32 * (rows >= 8) + 4 * (rows % 8) + plane] = byte
    return out.reshape(-1)


def invert(m: dict[str, np.ndarray], out: np.ndarray, units: int, bits: int, label: str) -> np.ndarray:
    """Input image of a map from its output: every input unit from the outputs it reaches."""
    s, p, x, c = m["sigma"], m["pi"], m["xor"], m["const"]
    live = np.flatnonzero(~c)
    if out.size != s.size:
        sys.exit(f"{label}: the GOG data has {out.size} units, the map {s.size}")
    v = (out[live] ^ x[live]).astype(np.uint32)
    src = np.zeros(live.size, np.uint32)
    for b in range(bits):                       # input bit b went to output bit p[i, b]
        src |= ((v >> p[live, b].astype(np.uint32)) & 1) << np.uint32(b)
    image = np.zeros(units, np.uint32)
    seen = np.zeros(units, bool)
    image[s[live]] = src
    seen[s[live]] = True
    if not seen.all():
        sys.exit(f"{label}: {int((~seen).sum())} input units reach no output; cannot rebuild")
    bad = np.count_nonzero(image[s[live]] != src)
    if bad:
        sys.exit(f"{label}: {bad} outputs disagree with the rebuilt input")
    const_bad = np.count_nonzero(out[c] != x[c])
    if const_bad:
        sys.exit(f"{label}: {const_bad} constant outputs differ from the GOG data")
    return image


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gog", type=Path, default=ROOT / "roms" / "gog")
    ap.add_argument("--maps", type=Path, default=ROOT / "analysis" / "phase0" / "probe")
    ap.add_argument("--out", type=Path, default=ROOT / "roms" / "mslug4h")
    ap.add_argument("--sm1", action="store_true")
    a = ap.parse_args()
    if a.sm1:
        roms = ROOT / "roms"
        (roms / "neogeo" / "sm1.sm1").write_bytes((a.gog / "m1.bin").read_bytes()[0x10000:0x30000])
        lines = []
        for f in sorted(p for p in roms.rglob("*") if p.is_file() and not p.name.upper().startswith("MANIFEST")):
            lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()} *{f.relative_to(roms).as_posix()}")
        (roms / "MANIFEST.sha256").write_text("\r\n".join(lines) + "\r\n")
        print(f"sm1.sm1: the first 128 KB of the decrypted M1; {len(lines)} files in MANIFEST.sha256")
        return 0
    a.out.mkdir(parents=True, exist_ok=True)
    for name, (gog_file, label) in GOG.items():
        t = TARGETS[name]
        m = dict(np.load(a.maps / name / f"{label}_map.npz"))
        out = np.frombuffer((a.gog / gog_file).read_bytes(), t.dtype)
        if name == "graphics":
            out = packed_to_planar(out)
        image = invert(m, out, t.units, t.bits, label).astype(t.dtype)
        again = apply(m, image, t.bits)
        if np.count_nonzero(again != out):
            sys.exit(f"{label}: the rebuilt files do not give the GOG data back")
        for n, data in t.split(image).items():
            (a.out / n).write_bytes(data)
            print(f"{name}: {n} ({len(data)} bytes)")
        print(f"{name}: {gog_file} rebuilt; the map gives it back byte for byte")
    return 0


if __name__ == "__main__":
    sys.exit(main())
