"""Turns the black-box maps of Metal Slug 4's encrypted ROMs (tools/probe_decryption.py: MAME as an
oracle fed with synthetic patterns, no game data and no MAME code; analysis/phase0/probe) into a
compact description, and checks it on the user's MAME set against the regions MAME built from it
(Phase 0's dumps) and against the GOG copy.

Program (263-ph1.p1 + 263-ph2.sp2): not encrypted; MAME's region is the files in order.
ADPCM-A (PCM2, bytes, input = 263-v1.v1 + 263-v2.v2, 16 MB): output byte i = input byte
  PCM2_BASE ^ the GF(2)-linear map of i's bits (Metal Slug 4: only bit 2 flipped), XORed with
  PCM2_XOR[i & 7].
Sprites and fix (CMC50): Metal Slug 3's CMC42 form (tools/learn_cmc.py) with Metal Slug 4's tables;
  the region is 48 MB (0xC0 units of 64 K x 4 bytes), not a power of 2: an output address byte b2
  at or past 0xC0 goes back by 0x40. The fix layer (512 KB) is a linear map into the decrypted
  sprites (as tools/learn_crypt5.py's).
M1 (CMC50, bytes, input = 263-m1.m1, 128 KB): Metal Slug 5's keyed byte permutation
  (tools/learn_crypt5.py) for Metal Slug 4's key (the 16-bit sum of the file's first 64 KB): two
  64 KB banks, each in place.

Usage:
  python tools/learn_crypt4.py --maps analysis/phase0/probe --set roms/mslug4h
        --dumps roms/decrypted [--header src/games/mslug4/crypt_tables.h]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from learn_cmc import check  # noqa: E402
from learn_crypt5 import M1_A, M1_B, gather, read_set  # noqa: E402

MB = 1 << 20


def unit_address(t: dict, a0, a1, a2, top: int):
    """CMC's output unit for input unit a0 | a1 << 8 | a2 << 16; with 48 MB (top = 0xC0 units of
    64 K) an address byte b2 at or past the top goes back by 0x100 - top (MAME's region wraps)."""
    b0 = a0 ^ t["T1"][a1]
    raw2 = a2 ^ t["T2"][a1] ^ t["T3"][b0]
    b1 = a1 ^ t["T4"][b0] ^ t["T5"][raw2]
    b2 = np.where(raw2 >= top, raw2 - (0x100 - top), raw2)
    return b0, b1, b2


def learn_sprites(maps: Path) -> dict:
    """Metal Slug 3's CMC42 form (tools/learn_cmc.py) and the wrap of a region that is not a power
    of 2 (Metal Slug 4's 48 MB)."""
    m = np.load(maps / "sprites_map.npz")
    s, x = m["sigma"].astype(np.int64), m["xor"].astype(np.int64)
    check("data bits not permuted", bool((np.unique(m["pi"], axis=0) == np.arange(8)).all()))
    n = len(s) // 4
    top = n >> 16
    o = np.arange(len(s))
    v, p = s >> 2, s & 3
    Q = np.empty((n, 4), np.int64)
    C = np.empty((n, 4), np.int64)
    Q[v, p] = o & 3
    C[v, p] = x
    G = np.empty(n, np.int64)
    G[v[0::4]] = np.arange(n)                          # input unit -> output unit
    V = np.arange(n)
    a0, a1, a2 = V & 0xFF, (V >> 8) & 0xFF, V >> 16
    b0, b1, b2 = G & 0xFF, (G >> 8) & 0xFF, G >> 16
    t = {"TOP": top}
    sel = (a0 == 0) & (a2 == 0); t["T1"] = np.zeros(256, np.int64); t["T1"][a1[sel]] = b0[sel]
    d2 = b2 ^ a2
    sel = (b0 == 0) & (a2 == 0); t["T2"] = np.zeros(256, np.int64); t["T2"][a1[sel]] = d2[sel]
    sel = (a1 == 0) & (a2 == 0); t["T3"] = np.zeros(256, np.int64); t["T3"][b0[sel]] = d2[sel] ^ t["T2"][0]
    raw2 = a2 ^ t["T2"][a1] ^ t["T3"][b0]
    d1 = b1 ^ a1
    sel = b0 == 0; t["T5"] = np.zeros(256, np.int64); t["T5"][raw2[sel]] = d1[sel]
    sel = raw2 == 0; t["T4"] = np.zeros(256, np.int64); t["T4"][b0[sel]] = d1[sel] ^ t["T5"][0]
    p0, p1, p2 = unit_address(t, a0, a1, a2, top)
    check("unit address: three XOR steps with T1-T5, wrapped at the region's end",
          bool(((p0 | p1 << 8 | p2 << 16) == G).all()))

    base = Q[0].copy()
    mid = (Q[:, 1] != base[1]).astype(np.int64)
    end = (Q[:, 0] != base[0]).astype(np.int64)
    for nm, sw in (("M", mid), ("E", end)):
        s2 = np.zeros(256, np.int64); s1 = np.zeros(256, np.int64)
        sel = a1 == 0; s2[a2[sel]] = sw[sel]
        sel = a2 == 0; s1[a1[sel]] = sw[sel] ^ s2[0]
        t[nm + "1"], t[nm + "2"] = s1, s2
    sm = t["M1"][a1] ^ t["M2"][a2]
    se = t["E1"][a1] ^ t["E2"][a2]
    swap = lambda q, cond, i, j: np.where(cond, np.where(q == i, j, np.where(q == j, i, q)), q)
    predq = np.empty_like(Q)
    for pp in range(4):
        q = np.full(n, base[pp])
        q = swap(q, sm == 1, base[1], base[2])
        q = swap(q, se == 1, base[0], base[3])
        predq[:, pp] = q
    check("byte order: base order and two swaps (M1/M2, E1/E2)", bool((predq == Q).all()))

    Cq = np.empty_like(C)
    for pp in range(4):
        Cq[V, Q[:, pp]] = C[:, pp]
    t["X"] = np.zeros((4, 256), np.int64); t["Y"] = np.zeros((4, 256), np.int64)
    for q in range(4):
        sel = b0 == 0; t["Y"][q][a1[sel]] = Cq[sel, q]
        sel = a1 == 0; t["X"][q][b0[sel]] = Cq[sel, q] ^ t["Y"][q][0]
    predc = t["X"][:, b0].T ^ t["Y"][:, a1].T
    check("data XOR: X[q][b0] ^ Y[q][a1]", bool((predc == Cq).all()))
    t["BASE"] = base
    return t


def byte_order(t: dict, a1, a2, p):
    base = t["BASE"]
    sm = (t["M1"][a1] ^ t["M2"][a2]) == 1
    se = (t["E1"][a1] ^ t["E2"][a2]) == 1
    q = base[p]
    q = np.where(sm & (q == base[1]), -1, q); q = np.where(sm & (q == base[2]), base[1], q); q = np.where(q == -1, base[2], q)
    q = np.where(se & (q == base[0]), -2, q); q = np.where(se & (q == base[3]), base[0], q); q = np.where(q == -2, base[3], q)
    return q


def sprites_decrypt(t: dict, img: np.ndarray) -> np.ndarray:
    n = len(img) // 4
    V = np.arange(n)
    a0, a1, a2 = V & 0xFF, (V >> 8) & 0xFF, V >> 16
    b0, b1, b2 = unit_address(t, a0, a1, a2, t["TOP"])
    out_unit = b0 | b1 << 8 | b2 << 16
    src = img.reshape(n, 4)
    out = np.empty((n, 4), np.uint8)
    for p in range(4):
        q = byte_order(t, a1, a2, np.full(n, p))
        out[out_unit, q] = src[:, p] ^ (t["X"][q, b0] ^ t["Y"][q, a1]).astype(np.uint8)
    return out.reshape(-1)


def learn_fix(maps: Path, t: dict) -> dict:
    """The fix layer: fix byte k = decrypted sprite byte FIX_BASE ^ (linear map of k's bits)."""
    f = np.load(maps / "fixed_map.npz")
    fs, fx = f["sigma"].astype(np.int64), f["xor"].astype(np.int64)
    V = fs >> 2
    a0, a1, a2 = V & 0xFF, (V >> 8) & 0xFF, V >> 16
    b0, b1, b2 = unit_address(t, a0, a1, a2, t["TOP"])
    q = byte_order(t, a1, a2, fs & 3)
    spr = (b0 | b1 << 8 | b2 << 16) * 4 + q
    check("fix: decrypted sprite bytes, no extra XOR", bool((fx == (t["X"][q, b0] ^ t["Y"][q, a1])).all()))
    nb = len(fs).bit_length() - 1
    k = np.arange(len(fs))
    cols = [int(spr[1 << b] ^ spr[0]) for b in range(nb)]
    pred = np.full(len(fs), spr[0])
    for b in range(nb):
        pred ^= np.where((k >> b) & 1, cols[b], 0)
    check("fix: sprite byte = base ^ linear map of the fix byte number", bool((pred == spr).all()))
    return {"FIX_BASE": int(spr[0]), "FIX_COLS": cols}


def check_program(maps: Path) -> None:
    m = np.load(maps / "maincpu_map.npz")
    n = len(m["sigma"])
    check("program: not encrypted (each word in place, bits and values unchanged)",
          bool((m["sigma"] == np.arange(n)).all() and (m["pi"] == np.arange(16)).all()
               and (m["xor"] == 0).all() and not m["const"].any()))


def learn_pcm2(maps: Path) -> dict:
    m = np.load(maps / "adpcma_map.npz")
    sigma, xor = m["sigma"].astype(np.int64), m["xor"].astype(np.int64)
    check("adpcm: data bits not permuted", bool((m["pi"] == np.arange(8)).all()) and not bool(m["const"].any()))
    n = len(sigma)
    i = np.arange(n, dtype=np.int64)
    bits = n.bit_length() - 1
    t = {"BASE": int(sigma[0]), "COLS": [int(sigma[1 << b] ^ sigma[0]) for b in range(bits)]}
    pred = np.full(n, t["BASE"], np.int64)
    for b in range(bits):
        pred ^= np.where(i & (1 << b), t["COLS"][b], 0)
    check("adpcm: address = base ^ a linear map of the bits", bool((pred == sigma).all()))
    t["XOR"] = [int(xor[c]) for c in range(8)]
    check("adpcm: XOR by bits 0-2", bool((np.array(t["XOR"])[i & 7] == xor).all()))
    return t


def pcm2_decrypt(t: dict, data: np.ndarray) -> np.ndarray:
    n = len(data)
    i = np.arange(n, dtype=np.int64)
    src = np.full(n, t["BASE"], np.int64)
    for b, c in enumerate(t["COLS"]):
        src ^= np.where(i & (1 << b), c, 0)
    return (data[src] ^ np.array(t["XOR"], np.uint8)[i & 7]).astype(np.uint8)


def learn_m1(maps: Path, banks: int) -> dict:
    """Metal Slug 5's form (learn_crypt5.learn_m1) for `banks` 64 KB banks: the region past the
    file's banks is constant (MAME fills it), the first 64 KB repeat 0x10000-0x1FFFF."""
    m = np.load(maps / "audiocpu_map.npz")
    used = slice(0x10000, 0x10000 + (banks << 16))
    check("m1: a byte permutation (no XOR, no bit permutation)",
          bool((m["xor"][used] == 0).all() and (m["pi"][used] == np.arange(8)).all() and not m["const"][used].any()))
    sigma = m["sigma"].astype(np.int64)
    check("m1: the region's first 64 KB repeat 0x10000-0x1FFFF", bool((sigma[:0x10000] == sigma[0x10000:0x20000]).all()))
    s = sigma[used]
    x = np.arange(0x10000)
    t = {"KEY": int(m["key"]), "XPOS": [], "YPOS": [], "PA": [], "T1": [], "PB": [], "T2": []}
    for k in range(banks):
        L = s[k << 16:(k + 1) << 16]
        check(f"m1: bank {k} stays in place", bool(((L >> 16) == k).all()))
        L = L & 0xFFFF
        g = np.empty(0x10000, np.int64); g[L] = x            # file address -> region address
        xpos = []
        for b in M1_A:                                         # A's bit -> one region bit, always
            d = g ^ g[x ^ (1 << b)]
            xpos.append([o for o in range(16) if ((d >> o) & 1).all()][0])
        ypos = [o for o in range(16) if o not in xpos]
        a, bb = gather(x, M1_A), gather(x, M1_B)
        xx, yy = gather(g, xpos), gather(g, ypos)
        T1 = np.zeros(256, np.int64); sel = a == 0; T1[bb[sel]] = xx[sel]
        PA = np.zeros(256, np.int64); PA[a] = xx ^ T1[bb]
        T2 = np.zeros(256, np.int64); sel = bb == 0; T2[xx[sel]] = yy[sel]
        PB = np.zeros(256, np.int64); PB[bb] = yy ^ T2[xx]
        ok = bool((PA[a] ^ T1[bb] == xx).all() and (PB[bb] ^ T2[xx] == yy).all())
        check(f"m1: bank {k}: X = PA[A] ^ T1[B], Y = PB[B] ^ T2[X]", ok)
        for nm, v in (("XPOS", xpos), ("YPOS", ypos), ("PA", PA), ("T1", T1), ("PB", PB), ("T2", T2)):
            t[nm].append([int(q) for q in v])
    return t


def m1_decrypt(t: dict, data: np.ndarray) -> np.ndarray:
    out = np.empty_like(data)
    x = np.arange(0x10000)
    a, bb = gather(x, M1_A), gather(x, M1_B)
    for k in range(len(t["PA"])):
        X = np.array(t["PA"][k])[a] ^ np.array(t["T1"][k])[bb]
        Y = np.array(t["PB"][k])[bb] ^ np.array(t["T2"][k])[X]
        r = np.zeros(0x10000, np.int64)
        for i, p in enumerate(t["XPOS"][k]):
            r |= ((X >> i) & 1) << p
        for i, p in enumerate(t["YPOS"][k]):
            r |= ((Y >> i) & 1) << p
        out[(k << 16) + r] = data[(k << 16) + x]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--maps", type=Path, required=True, help="analysis/phase0/probe (program, adpcm, audio, graphics)")
    ap.add_argument("--set", type=Path, required=True)
    ap.add_argument("--dumps", type=Path, required=True)
    ap.add_argument("--header", type=Path)
    a = ap.parse_args()

    print("program")
    check_program(a.maps / "program")
    p = read_set(a.set, "263-ph1.p1") + read_set(a.set, "263-ph2.sp2")
    check("program: all 5 MB identical to MAME's region", p == (a.dumps / "maincpu.bin").read_bytes())

    print("adpcm (PCM2)")
    at = learn_pcm2(a.maps / "adpcm")
    data = np.frombuffer(read_set(a.set, "263-v1.v1") + read_set(a.set, "263-v2.v2"), np.uint8)
    check("adpcm: all 16 MB identical to MAME's region",
          bool((pcm2_decrypt(at, data) == np.frombuffer((a.dumps / "adpcma.bin").read_bytes(), np.uint8)).all()))

    print("sprites (CMC50)")
    st = learn_sprites(a.maps / "graphics")
    img = np.empty(48 * MB, np.uint8)
    for k in range(3):
        img[k * 16 * MB:(k + 1) * 16 * MB:2] = np.frombuffer(read_set(a.set, f"263-c{2 * k + 1}.c{2 * k + 1}"), np.uint8)
        img[k * 16 * MB + 1:(k + 1) * 16 * MB:2] = np.frombuffer(read_set(a.set, f"263-c{2 * k + 2}.c{2 * k + 2}"), np.uint8)
    spr = sprites_decrypt(st, img)
    check("sprites: all 48 MB identical to MAME's region",
          bool((spr == np.frombuffer((a.dumps / "sprites.bin").read_bytes(), np.uint8)).all()))
    print("fix layer")
    fx = learn_fix(a.maps / "graphics", st)
    k = np.arange(512 * 1024)
    idx = np.full(len(k), fx["FIX_BASE"])
    for b, c in enumerate(fx["FIX_COLS"]):
        idx ^= np.where((k >> b) & 1, c, 0)
    check("fix: all 512 KB identical to MAME's region",
          bool((spr[idx] == np.frombuffer((a.dumps / "fixed.bin").read_bytes(), np.uint8)).all()))

    print("m1 (CMC50, keyed)")
    m1 = np.frombuffer(read_set(a.set, "263-m1.m1"), np.uint8)
    mt = learn_m1(a.maps / "audio", len(m1) >> 16)
    key = int(m1[:0x10000].astype(np.int64).sum() & 0xFFFF)
    check(f"m1: the set's key {key:04X} is the learned one", key == mt["KEY"])
    ac = np.frombuffer((a.dumps / "audiocpu.bin").read_bytes(), np.uint8)
    check("m1: all 128 KB identical to MAME's region (0x10000-0x2FFFF)",
          bool((m1_decrypt(mt, m1) == ac[0x10000:0x10000 + len(m1)]).all()))
    if a.header:
        write_header(a.header, at, st, fx, mt)
    return 0


def write_header(path: Path, at: dict, st: dict, fx: dict, mt: dict) -> None:
    def arr(ctype, name, v, fmt="0x{:02X}", per=16):
        v = [int(x) for x in v]
        rows = [", ".join(fmt.format(x) for x in v[i:i + per]) for i in range(0, len(v), per)]
        return f"static const {ctype} {name}[{len(v)}] = {{\n    " + ",\n    ".join(rows) + ",\n};\n"
    banks = len(mt["PA"])
    out = ["/* Generated by tools/learn_crypt4.py from black-box probes of MAME (synthetic patterns, no",
           " * game data, no MAME code); checked on the user's MAME set against MAME's regions. Metal Slug",
           " * 4's PCM2 ADPCM-A and CMC50 sprite, fix and M1 encryption (docs/PHASE5_LOADER.md). Key tables",
           " * in the repository: authorized by the user (2026-10-24). */",
           "#ifndef MSLUG4_CRYPT_TABLES_H", "#define MSLUG4_CRYPT_TABLES_H", "", "#include <stdint.h>", ""]
    out.append(f"static const uint32_t PCM2_BASE = 0x{at['BASE']:06X};\n")
    out.append(arr("uint32_t", "PCM2_COLS", at["COLS"], "0x{:06X}", 8))
    out.append(arr("uint8_t", "PCM2_XOR", at["XOR"]))
    for nm in ("T1", "T2", "T3", "T4", "T5", "M1", "M2", "E1", "E2"):
        out.append(arr("uint8_t", f"CMC_{nm}", st[nm]))
    for q in range(4):
        out.append(arr("uint8_t", f"CMC_X{q}", st["X"][q]))
        out.append(arr("uint8_t", f"CMC_Y{q}", st["Y"][q]))
    out.append(arr("uint8_t", "CMC_BASE_ORDER", st["BASE"]))
    out.append(f"/* The region's size in units of 64 K x 4 bytes: an address byte b2 at or past it goes back by\n"
               f"   0x100 - CMC_TOP. */\nstatic const uint32_t CMC_TOP = 0x{st['TOP']:X};\n")
    out.append(f"static const uint32_t CMC_FIX_BASE = 0x{fx['FIX_BASE']:X};")
    out.append(f"static const uint32_t CMC_FIX_COLS[{len(fx['FIX_COLS'])}] = {{" + ", ".join(f"0x{c:X}" for c in fx["FIX_COLS"]) + "};")
    out.append(f"\n/* M1: learned for the key 0x{mt['KEY']:04X} (the 16-bit sum of the file's first 64 KB). */")
    out.append(f"static const uint16_t M1_KEY = 0x{mt['KEY']:04X};")
    out.append("static const uint8_t M1_A_BITS[8] = {" + ", ".join(map(str, M1_A)) + "};")
    out.append("static const uint8_t M1_B_BITS[8] = {" + ", ".join(map(str, M1_B)) + "};")
    for nm in ("XPOS", "YPOS"):
        out.append(f"static const uint8_t M1_{nm}[{banks}][8] = {{\n" + "".join(
            "    {" + ", ".join(str(v) for v in row) + "},\n" for row in mt[nm]) + "};")
    for nm in ("PA", "T1", "PB", "T2"):
        rows = []
        for k in range(banks):
            v = mt[nm][k]
            rows.append("    {\n" + "".join("        " + ", ".join(f"0x{q:02X}" for q in v[i:i + 16]) + ",\n"
                                            for i in range(0, 256, 16)) + "    },\n")
        out.append(f"static const uint8_t M1_{nm}[{banks}][256] = {{\n" + "".join(rows) + "};")
    out += ["", "#endif", ""]
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"header -> {path}")


if __name__ == "__main__":
    sys.exit(main())
