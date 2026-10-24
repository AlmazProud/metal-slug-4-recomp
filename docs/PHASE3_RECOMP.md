# Phase 3: analysis and recompilation of Metal Slug 4

**State:** closed, pending approval (2026-10-23).

## Plan

1. The 68000 files the analysis and the recompiler read, from the user's GOG copy.
2. Where Metal Slug 4's 68000 runs in MAME (P1, each P2 bank, the BIOS, RAM), from traces of the
   attract and scripted runs, the bot and the user's game.
3. Coverage and static analysis (`tools/coverage.py`, `tools/analyze68k.py`):
   `docs/PHASE3_COVERAGE.md`.
4. Recompilation with `tools/recomp68k` (P1 and the BIOS, as for Metal Slug 3 and 5). If code ran
   from the P2 banks, the dispatcher would be the user's decision.
5. Tests: lockstep and image, RAM and palette against MAME for the recompiled build. The audio is
   deferred (Phase 2) and stays out of the pass criteria.
6. A game recorded by the user (`grabar_partida.bat partida1`) for coverage and verification.

The distributable build stays interpreter-only (`-DPD_RECOMPILED=OFF`); the recompiled build is
the development and verification target, as in Metal Slug 3 and 5.

## Result

- **The 68000 files** (`tools/make_reference.py --mslug4 analysis/phase3/program`):
  `mslug4_game_m68k` is GOG's `p1.bin` (checked equal to MAME's `maincpu` region) and
  `mslug4_bios_m68k` the us BIOS (`sp-u2.sp1`). They live outside `roms\`: there the loader would
  take the `mslug4_*` names for a DotEmu copy. The recompiled program carries the SHA-256 of the
  first MB of `p1.bin` (the runtime's P1 hash, `roms.c`), so it is used with the GOG copy and the
  MAME set alike.
- **Where the code runs** (MAME, `docs/PHASE3_COVERAGE.md`, 1 430 M traced instructions in four
  runs): P1 and the BIOS. **No code runs from the P2 banks**, so the dispatcher did not change:
  P1 and the BIOS recompiled, everything else interpreted. Code in RAM (644 addresses, the
  attract's ROM checksum, bulk reader at `0x10018C`) stays interpreted.
- **Coverage** (`analysis/phase3/coverage_*.json`, all used by the build): the playback of the
  attract and scripted recordings (`analysis/phase2`), the bot (180 s) and the user's game
  `partida1`. The scripted runs alone executed 39 215 P1 addresses; with the bot and the user's
  game, 62 965.
- **Analysis:** all 62 965 P1 addresses executed in MAME reached by the static analysis; 0 bytes of
  code where MAME read data; 5 496 functions (`docs/functions_p1.csv`).
- **`mslug4.exe` recompiled:** 3 405 regions, 116 297 instructions, 0 unsupported.

  | Run | Frames | Recompiled dispatches | Interpreted steps | Time (interpreter only) |
  |---|---:|---:|---:|---|
  | scripted (`start`) | 9 001 | 4 837 708 | 3 191 | 8.7 s |
  | `attract` | 10 007 | 5 353 646 | 11 596 517 (the RAM checksum) | 10.3 s |
  | `partida1` (the user's game) | 46 541 | 33 769 110 | 17 241 | 44.1 s (142.9 s) |

  The interpreted steps of the scripted run and the user's game are dispatches at an expired
  cycle limit and a few BIOS and RAM instructions.
- **Against MAME:** `mslug4_attract_vs_mame` and `mslug4_start_vs_mame` give the same result as
  the interpreter (Phase 2: start identical, attract with its known VBlanks and images).
- **Lockstep** (`lockstep_mslug4_reset`, `lockstep_mslug4_game`): the machine model's standard P2
  banks are `bus.c`'s (values outside the four banks show bank 0); Metal Slug X's protection
  registers only on its cartridge. The game dump is frame 8 000 of the scripted run (Mission 1,
  `tools/mame/dump_state.lua`, version 1: the bank deduced from the window). From reset 20 097 of
  20 097 points verified; from the dump 267 351 of 267 351 (591 VBlanks); final memory identical.
- **The user's game** (`partida1`, 13.1 min recorded with `grabar_partida.bat`; MAME reference by
  `mame_run.py --replay --name partida1`, test `mslug4_play_partida1_vs_mame`): images identical on
  all 46 540 frames, in the interpreter and recompiled; RAM and palette identical except 7 known
  VBlanks (`partida1_known_vblank.txt`: 19093-19097, 32296-32297), checked byte by byte: only the
  stack (`0x10F29E-0x10F2FB`), MAME taking the VBlank one instruction apart; RAM identical one
  VBlank before and after. A second MAME replay gave the same fingerprints (deterministic here).

- `ctest`: **129/129** (interpreter-only build 121/121), Metal Slug 5, 3 and X included.

## Changes

- `tools/make_reference.py --mslug4`: the 68000 files above.
- `tools/coverage.py`: `--game mslug4h` by default; `--p2-banks` (4): a bank select value outside
  P2's banks shows bank 0, as `bus.c` (the boot writes 7).
- `tools/analyze68k.py`: `--game mslug4` and `--roms analysis/phase3/program` by default.
- `src/CMakeLists.txt`: Metal Slug 4's recompiled program from those files; the generated program
  also depends on the listings and the coverage files (it was regenerated only when the recompiler
  changed); `mslug4_play_<NAME>_vs_mame` for the games in `analysis/phase3/play`.
- `tests/lockstep`: the `mslug4` tests; Metal Slug X's protection writes only on its cartridge.

## Pending

- The other missions' bosses and sections (Phase 4: the developer menu, Boss Rush).
- The audio (deferred by the user, Phase 2).
