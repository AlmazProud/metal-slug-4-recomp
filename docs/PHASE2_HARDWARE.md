# Phase 2: Metal Slug 4 hardware in the interpreter

**State:** closed (2026-10-23; the audio deferred by the user). Image and RAM identical to MAME (known residue listed); the
audio is the known difference of Metal Slug 5 (below), reported to the user before going further.

`mslug4.exe` (interpreter, no recompiled code yet) loads the user's GOG copy and runs identical to
MAME 0.289 (`mslug4h -bios us`) in image on every frame and in work RAM and palette on every
VBlank, except VBlanks where MAME takes the interrupt one instruction apart (listed per run).

## The data the runtime loads: the GOG copy (`roms.c`)

The Code Mystics files are MAME's regions after MAME's own transformations (`docs/ROM_MAP.md`), so
loading them needs no decryption and no key table:

| File | Runtime part | Conversion |
|---|---|---|
| `p1.bin` (5 MB) | `p` | none (MAME's program order) |
| `c1.bin` (48 MB) | `tiles` | DotEmu's tile layout with the 8 pixels of each half-row reversed: per 4 bytes, the bytes in reverse order and the two nibbles of each swapped (`codemystics_tiles`, its own inverse) |
| `s2.bin` (512 KB) | `fix_game` | Neo Geo S format to the runtime's (`fix_to_dotemu`, as a MAME set's S1) |
| `m1.bin` (576 KB) | `z80` (128 KB) | the M1 is MAME's `audiocpu` region from 0x10000 |
| `v1.bin` (16 MB) | `adpcm` | none |

- **System files:** the GOG release has none of MAME's (its `sp_4j.bin` is the `japan-j3` BIOS; no
  `000-lo.lo`, no MAME `sfix.sfix`). The loader takes them, by hash, from a MAME BIOS set anywhere
  below the path (in the workspace, `roms\neogeo\`); without them it says which are missing
  (`mslug4_roms_gog_alone`). How a GOG-only user gets them is a Phase 5 decision (the user's).
- **Checked against MAME:** `tools/check_load.py` (`mslug4_roms_gog_vs_mame`) dumps every part the
  runtime loaded (`PD_DUMP_ROMS`, headless), converts it back with the Metal Slug 3 port's verified
  conversions (`tools/extract_roms.py`) and compares it with MAME's regions (`roms\decrypted\`) and
  the BIOS files: program, sprites, fix, M1, ADPCM, system fix, zoom table and BIOS identical.
- **`sm1.sm1`** (MAME's sound BIOS stand-in in `roms\neogeo\`): the first 128 KB of the decrypted
  M1 (`tools/rebuild_set.py --sm1`), as in the Metal Slug 3 and 5 workspaces: the port boots the
  Z80 from the M1, so MAME must run the same code.

## Cartridge hardware

- **P2 banks** (`NG_CART_STANDARD`, `bus.c`), learned with `tools/bus_probe.py` (one fresh MAME per
  probe, the word read back at `0x2FFFF0` identifying the bank): a word or byte write anywhere in
  `0x2FFFF0-0x2FFFFF` selects the bank from the value's low 3 bits; 0-3 are P2's four 1 MB banks
  and every other value (4-7: the boot writes 7) shows bank 0. Exactly Metal Slug X's bank select
  (`p2_bank`), without its protection. No protection chip, nothing read back.
- **Fix banks** (`NG_FIX_BANK_ROWS`): the 512 KB fix uses Metal Slug 3's banking (one 128 KB bank
  per tile row, from the table the game writes at VRAM `0x7500`/`0x7580`); with it every image
  matches MAME (without it the game's text used the wrong bank).
- **Unmapped writes:** 3 in the start run, 8 in the attract run, none affecting RAM or images. The
  boot's bank check (`0x8A0-0x8E8`) writes `0x8FAE` through a pointer from its table at `0x2CC`
  (`move.w #$8FAE,(a0)` at `0x8D2`): a write over ROM, ignored, as MAME does.

## Verification

References: `tools/mame_run.py --game mslug4h` (MAME 0.289, the rebuilt set in `roms\`, written to
`analysis\phase2`). The scripted game: a coin at 1800, START at 2000, the game's "How to play",
Soldier Select from about 4500 (A at 4700: Marco), Mission 1 with the bot.

| Run (`ctest`) | Frames | RAM + palette (VBlank acks) | Images |
|---|---|---|---|
| `mslug4_attract_vs_mame` | 10 007 | 10 066 / 10 290, 224 known | 9 998 / 10 002, 4 known |
| `mslug4_start_vs_mame` | 9 001 | all identical | all identical |

### Known differences (`attract_known_vblank.txt`, checked byte by byte)

VBlanks 4178-4329 and 6822-6900 (in five windows): MAME takes the VBlank interrupt one instruction
apart, the residue documented in Metal Slug 3 and 5. On all 224, the differing bytes are the stack
(`0x10F288-0x10F2FF`) and, in 16 of them, single bytes the interrupted routine was writing, equal
again one VBlank later (4191: two). RAM is identical before and after each window. Four images of
the first window (4435, 4485, 4500, 4512) differ by 4-11 pixels on one line.

## Audio: the same difference as Metal Slug 5 (not chased)

| Run | Exact samples | Correlation | Offset |
|---|---|---|---|
| attract | 47.3 % | 0.923 | 0 |
| start | 26.2 % | 0.944 | 0 |

Silence, start and length agree (sound from second 15 in both); per second the correlation is
mostly 0.99-1.00, with whole seconds identical, and drops where effects overlap. This is what
Metal Slug 5 showed (0.91 / 0.97): the power-on alignment of the 68000, the Z80 and the YM2610
(Metal Slug 5's `docs/PHASE2_HARDWARE.md`); its two Metal Slug 5-only corrections are not in the
code, so they were not tried here. Per the user's instruction, reported before investing more;
a generic fix would serve Metal Slug 5 too.

## Tools

- `tools/check_load.py` and `PD_DUMP_ROMS` (headless, `main.c`): what the runtime loaded against
  MAME's regions.
- `tools/rebuild_set.py --sm1`: the `sm1.sm1` stand-in.
- `tools/mame_run.py`: `--game mslug4h` (default), its menu steps.

## Pending

- The audio (above): deferred by the user, as in Metal Slug 5.
- A longer game (Phase 3's recordings) and the other missions (Phase 4).
- GOG-only installs: the system files (Phase 5).
