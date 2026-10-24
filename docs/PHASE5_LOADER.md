# Phase 5: Metal Slug 4's universal loader

**State:** closed, pending approval (2026-10-24).

Goal: `mslug4.exe` runs from the user's GOG copy (Code Mystics' `Data\rom`, Phase 2) or from the
MAME set `mslug4h` (zipped or loose files, recognized by CRC-32 and SHA-1), decrypted at load,
with the same bytes either way, so the recompiled program, the profile and every test apply as
before.

## Plan

1. Compact descriptions of Phase 0's black-box maps (`docs/ROM_MAP.md`): the program (not
   encrypted), the ADPCM-A samples (PCM2), the sprites and fix (CMC50) and the M1 (a byte
   permutation keyed by the data), each checked against MAME's regions and the GOG copy.
2. The runtime's decryption (`src/games/mslug4/crypt.c`), the set converted to the runtime's layout.
3. Tests: the set zipped and loose loads the same bytes as the GOG copy; the GOG install and the
   usual runs unchanged.
4. The portable copy with the MAME set.

**Key tables:** authorized by the user (2026-10-24): the CMC50 tables with Metal Slug 4's
parameters, the M1's tables for its key and the PCM2 description may be in the repository. They are
learned from black-box probes with synthetic patterns (no game data, no MAME code).

**A GOG-only install** (the user's decision, option A): the GOG release has none of MAME's Neo Geo
system files (no `000-lo.lo`, no MAME `sfix.sfix`; its BIOS is `japan-j3`, and `NeoGeo.exe` does
not hold them either: searched); the port asks for them with a clear message.

## Result

`mslug4.exe` runs from the MAME set (`mslug4h.zip` with `neogeo.zip`, or the loose files) decrypted
at load in about 0.6 s: every part identical to the GOG copy's (`p`, `bios`, `fix_game`,
`fix_bios`, `tiles`, `zoom`, `z80`, `adpcm`), so the recompiled program and the profile are on.

### The compact descriptions (`tools/learn_crypt4.py`, `src/games/mslug4/crypt_tables.h`)

Each checked on the whole of the user's set against the region MAME built from it (Phase 0's
dumps): all identical.

| Region | Description | Size of its tables |
|---|---|---|
| Program (5 MB) | not encrypted: `263-ph1.p1` + `263-ph2.sp2` in order | - |
| ADPCM-A (PCM2, 16 MB) | input byte = `PCM2_BASE` ^ a linear map of the output byte number (Metal Slug 4: bit 2 flipped), XORed by its bits 0-2 (here 0) | 1 + 24 + 8 |
| Sprites (CMC50, 48 MB) and fix (512 KB) | Metal Slug 3's CMC42 form with Metal Slug 4's tables. **New:** the region is 48 MB, not a power of 2: an output address byte at or past `0xC0` goes back by `0x40` (MAME's region wraps); the next step of the address uses it before that. The fix is a linear map into the decrypted sprites (their last 512 KB) | 17 x 256 + 25 |
| M1 (CMC50, 128 KB) | Metal Slug 5's keyed byte permutation (two Feistel steps on two halves of the address bits), learned for Metal Slug 4's key `0xB5E6`: two 64 KB banks, each in place | 2 x (4 x 256 + 16) |

The header is 44 KB: the key tables the user authorized. The M1's tables are for the real set's
key only; the loader only accepts the set by its hashes, and refuses another key.

### Runtime

- `src/games/mslug4/crypt.c`: the four decryptions, through Metal Slug 5's `NgMameCrypt` (the
  program is copied as it is). `game.c` points `crypt` at them.
- **Order:** the GOG copy first, then a MAME set (`roms.c`, unchanged).
- **A GOG-only install** (shared code: Metal Slug X, 3 and 5 unchanged): the loader also searches
  `ng_roms_system_path`, which the window sets to the `game` folder next to the program, so the
  system files can go there whatever the copy's folder is. Without them, the message says what is
  missing and what to do: "GOG copy found, without the Neo Geo system files (sfix.sfix,
  000-lo.lo). Copy neogeo.zip, MAME's Neo Geo BIOS set, to the "game" folder next to the
  program." Checked in the window with the user's install (`K:\METAL SLUG 4`, found by the usual
  places): without `neogeo.zip` the "game not found" screen shows the message; with it next to the
  program the game starts from the install and remembers it.
- **The portable copy** (`tools/make_portable.py`): GOG's files with the system files, or with
  `--mame-set` (or without GOG's files) the MAME set; both checked in `portable_test`.

### Tests

- `mslug4_roms_mame`: the loose set loads (`MAME set, GOG program, BIOS us`), the recompiled
  program and the profile on.
- `mslug4_roms_mame_loose`, `mslug4_roms_mame_zip` (`mslug4h.zip`, finding `neogeo.zip` next to
  it): every part identical to the GOG copy's (`PD_COMPARE_ROMS`).
- `mslug4_roms_gog`, `mslug4_roms_gog_alone` (the new message), `mslug4_roms_gog_vs_mame`:
  unchanged.

- `ctest`: **164/164** (interpreter-only build 156/156), Metal Slug 5, 3 and X included.

## Pending

- Phase 6: publishing.
