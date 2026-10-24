# CLAUDE.md: Metal Slug 4 native port

Native Windows port of Metal Slug 4 (Neo Geo MVS, 2002, MAME set `mslug4h`, the NGH program) by
**progressive static recompilation**, following the method of the finished Metal Slug X, Metal
Slug 3 and Metal Slug 5 ports: the 68000 code is translated to C, the Neo Geo hardware is
reimplemented as a native runtime, and everything is verified against MAME.

| Port | Public repository | Local copy | Version |
|---|---|---|---|
| Metal Slug X | https://github.com/AlmazProud/metal-slug-x-recomp | `C:\Projecto Decompile\repo` | - |
| Metal Slug 3 | https://github.com/AlmazProud/metal-slug-3-recomp | `C:\Projecto Decompile\MS3_Port\repo` | v1.2.0 (`7c327dc`) |
| Metal Slug 5 | https://github.com/AlmazProud/metal-slug-5-recomp | `C:\Projecto Decompile\MS5_Port\repo` | v1.0.2 (`ebe3896`) |

- **The base of this project is Metal Slug 5 v1.0.2** (commit `ebe3896`, the user's decision on
  2026-10-23; it includes the Mission mode fix `08fa037`): generic runtime and frontend (game
  descriptor + per-game profile), CMC50, PCM2, encrypted M1, records notice, packaging and CI.
- **Metal Slug 3 is the reference** for the loader of a PC release (GOG).
- The three repositories are **read-only for this project**: code is copied from them (MIT,
  Copyright (c) 2026 AlmazProud) and adapted here.

Goal: the same result as Metal Slug 3 v1.2.0 and Metal Slug 5 v1.0.2. The game identical to MAME
0.289 (`mslug4h`: RAM, palette, image per frame and audio sample by sample, verified by automatic
tests); Metal Slug 5's complete frontend; a universal loader (the GOG copy in Code Mystics' format,
and the MAME set in zip or loose files, recognised by CRC / SHA-1 and decrypted at load); an
interpreter-only release in a new repository `AlmazProud/metal-slug-4-recomp`.

**The difference from the other ports:** the user's copy is GOG's (id 1773574593, `K:\METAL SLUG 4`,
Code Mystics' `NeoGeo.exe`, files `Data\rom\*.bin`), a different format from DotEmu's, and there is
**no MAME set** on disk. As in Metal Slug 3, the MAME set is rebuilt from the GOG files by inverting
MAME's decryption, learned as a black box; it is the oracle and the MAME loader's input.

## Mandatory rules

1. **Bring your own ROM.** The repo never contains ROMs, BIOS, graphics, audio or extracted,
   decrypted or rebuilt data. They are read from `..\roms\` at run time and validated by hash; what
   is rebuilt or dumped lives only in `roms\` or `analysis\`. The `.gitignore` is a whitelist; the
   pre-commit hook (`tools/check_commit.py`) rejects binaries, files over 1 MB and ROM copies (zip
   members included); `tools/audit.py` runs before any publication, with the ROM search on (every
   file under `roms\`, subfolders and zip members included). **Key tables** are accepted only if
   they come from synthetic probes, and **the user decides** (Metal Slug 5's were authorized there;
   for Metal Slug 4 ask again when it comes up).
2. **MAME only as hardware documentation and oracle.** No MAME code is copied or read; behaviour
   is learned by black-box probing. Permissively licensed libraries are preferred, each documented
   in `THIRD_PARTY.md`.
3. **Everything is verified against MAME:** traces, RAM and palette per VBlank, image fingerprints
   per frame, audio with `-wavwrite`. Always fix the date (`--date YYYY-MM-DD-hh-mm-ss-D` in the
   port, the same in MAME).
4. **Stack:** C17, CMake, Ninja, llvm-mingw and SDL3; analysis tools in Python 3
   (`tools\python\python.exe`: the system's `python` hangs). All tools are shared in
   `C:\Projecto Decompile\tools`. No downloads without asking the user.
5. **Language:** the assistant always talks to the user in Spanish. Everything in the repository
   (code, identifiers, comments, docs, commit messages) is written in English. The frontend is
   English and Spanish.
6. **Phases:** before writing code, a short plan and the user's OK; when a phase or stage closes,
   a report (what works, what is missing, risks, next step) and the user's approval. This file and
   the phase's doc are updated at each close.
7. **Commits:** small, author `Alan Jair Zavala Martinez <alvineslomejor@gmail.com>` (set with
   `git config --local`), message ending in
   `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
8. **Nothing public** (creating the GitHub repository, each push, each release) without the user's
   explicit OK for each step.
9. **Metal Slug X, Metal Slug 3 and Metal Slug 5 must not break:** `mslugx.exe`, `mslug3.exe` and
   `mslug5.exe` stay as regression targets when their ROMs are present; after any change to shared
   code their tests must pass. A fix only Metal Slug 4 needs goes in its profile or behind a
   descriptor option.
10. If a tool fails because of disk space, tell the user before looking for a workaround.
11. Build folders always go in `repo\build`, `repo\build-dist` or `repo\build-*`.
12. **The user's saved games:** window tests never use the portable folder or `%APPDATA%`; they
    use fresh preference folders in the session's scratchpad with `PD_PREF` (trailing slash).
13. **The GOG install is read-only:** never write to `K:\METAL SLUG 4` and never run `NeoGeo.exe`
    from a session (it writes its `~*.bin` files there). Its files are copied with
    `INSTALL.bat -CopyRoms`.

## Structure

```
C:\Projecto Decompile\
  tools\        portable tools, shared with the other ports
  repo\         Metal Slug X port (read-only)
  MS3_Port\     Metal Slug 3 port (read-only); its roms\mame\neogeo holds the BIOS used here
  MS5_Port\     Metal Slug 5 port (read-only): the base
  MS4_Port\
    repo\       this repository
    roms\       user's ROMs (outside the repo): gog\ (the GOG copy), neogeo\ (BIOS), later the
                rebuilt MAME set mslug4h, + MANIFEST.sha256
    analysis\   analysis output and MAME runs        logs\   logs
    release\    release zips and notes (outside the repo)        portable_test\
    INSTALL.bat, env.ps1, env.bat, README.md, grabar_partida.bat   (copies from repo\setup\)
repo\
  setup\        installer (setup.ps1, versions.json, env.*, record_game.bat, ci_tools.py, sdl3_test\)
  src\cpu\      dispatcher, 68000 state, Musashi fallback            (imported from Metal Slug 5)
  src\neogeo\   Neo Geo runtime (bus, LSPC, RTC, scheduler, ROMs, sound), shared by the four games
  src\port\     SDL3 frontend (menus, configuration, headless mode), shared
  src\games\    one folder per game: game.c (NgGame), profile.c (GameProfile), sounds.c, crypt.c
  tools\        analysis, recompiler (recomp68k\), MAME Lua scripts (mame\), verification,
                audit.py, check_commit.py, hooks\; Phase 0: verify_set.py, probe_decryption.py,
                rebuild_set.py, mame\oracle_phase0.lua
  tests\        differential\, lockstep\, loader\
  external\     Musashi, ymfm, z80.h, stb_truetype, fonts
  docs\         ROM_MAP.md, PHASE1_IMPORT.md, PHASE2_HARDWARE.md, PHASE3_RECOMP.md,
                PHASE3_COVERAGE.md, functions_p1.csv; ADPCM_B.md and QOL_FEATURES.md (shared code)
```

Build (environment active): `cmake -S repo -B repo\build -G Ninja -DCMAKE_BUILD_TYPE=Release`,
`cmake --build repo\build`, `ctest --test-dir repo\build` (`-L mslug4` / `-L mslug5` / `-L mslug3`
/ `-L mslugx`). Interpreter-only (distributable) build: `-B repo\build-dist -DPD_RECOMPILED=OFF`.
**Before closing any change to shared code: all Metal Slug 5, 3 and X tests must pass.**

Rebuild the MAME set from the GOG copy (once the maps are learned, `analysis\phase0\probe\`):
`python tools/rebuild_set.py` (to `roms\mslug4h\`), then `python tools/verify_set.py mslug4h`.

Activate the environment: `. "C:\Projecto Decompile\MS4_Port\env.ps1"` (PowerShell) or
`call "C:\Projecto Decompile\MS4_Port\env.bat"` (cmd). `PD_ROOT` is the workspace, `PD_TOOLS` the
shared tools, `PD_ROMS` the ROM folder. Verify: `MS4_Port\INSTALL.bat -VerifyOnly`. Copy the ROMs:
`INSTALL.bat -CopyRoms` (`Data\rom\*.bin` of the GOG install, `-Gog`, default `K:\METAL SLUG 4`, to
`roms\gog\`; the BIOS, `-Bios`, default the Metal Slug 3 workspace's `roms\mame\neogeo`, to
`roms\neogeo\`).

Oracle: `mame mslug4h -bios us -rompath "<workspace>\roms"` (the rebuilt set in `roms\mslug4h\`).

## Status by phase

| Phase | Status |
|---|---|
| Environment | **Closed** (2026-10-23). Verification 17/17 OK. ROMs copied to `roms\`. |
| 0. Reconnaissance (Code Mystics format, encryption schemes, black-box decryption, rebuilt `mslug4h` set, ROM map, P2 banks, developer menu, oracle) | **Closed** (2026-10-23). See `docs/ROM_MAP.md`. All 11 game ROMs of `mslug4h` rebuilt from GOG (CRC-32 and SHA-1), the M1 included. |
| 1. Import Metal Slug 5's runtime and frontend with an empty `mslug4h` descriptor and profile (four executables) | **Closed** (2026-10-23). See `docs/PHASE1_IMPORT.md`. `ctest`: 122/122 (interpreter-only 116/116). |
| 2. Metal Slug 4 hardware in the interpreter (minimal GOG loader, P2 banks, decrypted M1, PCM2) | **Closed** (2026-10-23). See `docs/PHASE2_HARDWARE.md`. Image and RAM identical to MAME (attract: 224 known VBlanks, 4 known images; start: no difference); audio as Metal Slug 5's (0.92 / 0.94), reported. `ctest`: 126/126 (interpreter-only 120/120). |
| 3. Analysis and recompilation | **Closed**, pending approval (2026-10-23). See `docs/PHASE3_RECOMP.md` and `docs/PHASE3_COVERAGE.md`. No code runs from the P2 banks; P1 and the BIOS recompiled; lockstep identical; the user's game `partida1` identical to MAME (7 known stack-only VBlanks). `ctest`: 129/129 (interpreter-only 121/121). |
| 4. Profile and frontend (boss bar and Boss Rush as a stage of their own) | Part A (profile and frontend) **closed**, pending approval (2026-10-24). See `docs/PHASE4_PROFILE.md`. Part B (boss bar, Boss Rush): `docs/BOSS_RUSH.md`, stages 0-3 closed (stage 3 pending approval). `ctest`: 161/161 (interpreter-only 153/153). |
| 5. Universal loader (GOG, the MAME set decrypted at load) | **Closed**, pending approval (2026-10-24). See `docs/PHASE5_LOADER.md`. The MAME set (zip or loose) decrypted at load, identical to the GOG copy; GOG-only installs: the system files from `neogeo.zip` in the `game` folder next to the program. `ctest`: 164/164 (interpreter-only 156/156). |
| 6. Publishing (`AlmazProud/metal-slug-4-recomp`) | Stages 1-3 (local) done, pending approval (2026-10-24). See `docs/PHASE6_RELEASE.md`. Version 1.0.0, audits clean, `release/metal-slug-4-recomp-v1.0.0-win64.zip`. Stage 4 (public): each step with the user's OK. |

### Phase 4, part A: result

Details in `docs/PHASE4_PROFILE.md`.

- **Engine addresses** from Metal Slug 3's and 5's profile windows found in Metal Slug 4's P1
  (`tools/match_windows.py`), each checked in the listing and in MAME. Start mission bytes
  `0x10ED62/3`, current mission `0x100BCC` (bytes 0-5 = Missions 1-6), score `0x1066D8`, player
  tables `0x10EDEA/FA`, give routine `0xC52EC`, form table `0xC508A`, stage table `0xB9CAE`
  (`analysis/phase4/stage_table.txt`).
- **Against MAME** (`analysis/phase4`): developer mode, every debug dip, load meter, red blood,
  Missions 2-6 (`PD_POKE` at 4600), the "Start mission" option, cheats, the Metal Slug, the forms
  (fat, mummy, zombie, monkey): images identical; RAM only in checked known VBlanks.
- **Soldiers** Marco, Fio, Trevor, Nadia (internal 0, 3, 1, 2); **music in mode 08** (07 the same
  catalog), effects 1A, voices 18; silence `03 0A A0 08 20 07 20`.
- **Shared code** (Metal Slug X, 3, 5 unchanged): `form_weapon_classes`, `form_classes`,
  `form_events`, `soldier_names`, `soldier_internal_of`; the sound menu test measures the silence
  after the silence sequence.
- **Not identified:** weapons 1, 16-18 (listed by number), the vehicles other than the Metal Slug
  and the walking machine.
- **Lessons:** MAME's `PD_BLOOD` is `word,mask` (the port only checks it is set); a re-recorded
  MAME run has a new date: reconfigure CMake; RAM dumps need `--fingerprints`; tests that write
  progress or records files need them removed first (a fixture).

### Phase 3: result

Details in `docs/PHASE3_RECOMP.md`.

- **The 68000 files:** `tools/make_reference.py --mslug4 analysis/phase3/program` writes
  `mslug4_game_m68k` (GOG's `p1.bin`, equal to MAME's `maincpu`) and `mslug4_bios_m68k` (the us
  BIOS) **outside `roms\`** (there the loader would take `mslug4_*` for a DotEmu copy). The
  analysis, the recompiler and the lockstep read them.
- **Coverage** (`analysis/phase3/coverage_*.json`): playback of the attract and start recordings,
  the bot (180 s) and the user's `partida1`: 62 965 P1 addresses, all reached by the static
  analysis; 0 code bytes on data MAME read; no code from the P2 banks, 644 RAM addresses (the ROM
  checksum) interpreted.
- **Recompiled `mslug4.exe`:** 116 297 instructions, 0 unsupported; `partida1` in 44 s (143 s in
  the interpreter). Same results against MAME as the interpreter.
- **Lockstep:** `lockstep_mslug4_reset` and `_game` (frame 8 000 of the start run,
  `analysis/phase3/state_start_f8000.bin`): every point verified, final memory identical.
- **The user's game:** `partida1` (13.1 min, `analysis/phase3/play`, test
  `mslug4_play_partida1_vs_mame`): images identical on all 46 540 frames; 7 known VBlanks, stack
  only (`partida1_known_vblank.txt`).
- Tools: `coverage.py --game mslug4h --p2-banks 4` (defaults), `analyze68k.py --game mslug4`
  (defaults); the generated program now depends on the listings and the coverage files.

### Phase 2: result

Details in `docs/PHASE2_HARDWARE.md`.

- **The GOG copy loads** (`roms.c`, `NG_FORMAT_CODEMYSTICS`): no decryption, no key table; the
  sprites are DotEmu's tiles with each half-row's pixels reversed. The system files (BIOS,
  `000-lo.lo`, `sfix.sfix`) come from a MAME BIOS set below the path (`roms\neogeo\`); a GOG-only
  install lacks them (Phase 5, the user's decision). Every loaded part equals MAME's regions
  (`tools/check_load.py`, `PD_DUMP_ROMS`).
- **Hardware:** `NG_CART_STANDARD` (P2 bank from the low 3 bits of a write to `0x2FFFF0-F`, 4-7
  give bank 0: Metal Slug X's rule, learned with `bus_probe.py`); the 512 KB fix with Metal Slug
  3's row banking (`NG_FIX_BANK_ROWS`). `sm1.sm1` in `roms\neogeo\` is the decrypted M1's first
  128 KB (`rebuild_set.py --sm1`).
- **Against MAME:** `mslug4_start_vs_mame` identical on every VBlank and frame;
  `mslug4_attract_vs_mame` with 224 known VBlanks (interrupt one instruction apart: stack, and in 16
  of them bytes equal again a VBlank later) and 4 known images (4-11 pixels on one line).
- **Audio:** not sample-exact (47 % / 26 % exact, correlation 0.92 / 0.94), Metal Slug 5's
  power-on alignment; reported to the user, not chased.
- Shared code (Metal Slug 5, 3 and X unchanged): `NG_CART_STANDARD`, the Code Mystics loader,
  `PD_DUMP_ROMS`.

### Phase 1: result

Details in `docs/PHASE1_IMPORT.md`.

- **Import:** Metal Slug 5 v1.0.2's code (commit `ebe3896`) in one unchanged commit; against the
  Metal Slug 5, 3 and X copies it passed the same 119 tests (`repo\build-ms5`).
- **Four executables:** `mslug4.exe` (the product, interpreter only) and the regression targets
  `mslug5.exe`, `mslug3.exe` and `mslugx.exe`, built when their copies are next to this workspace
  (`PD_MS5_ROMS` / `PD_MS5_ANALYSIS`, default `<parent>\MS5_Port\roms` and `analysis`).
- **`mslug4` descriptor:** the 11 files of `mslug4h` (CRC-32, SHA-1), the 5 Code Mystics files
  (SHA-256), GOG id `1773574593`, `mame_encrypted`, a standard cartridge, no fix banking yet. Both
  copies are recognized and reported, not loaded (tests `mslug4_roms_gog`, `mslug4_roms_mame`).
  Empty profile; version 0.1.0.
- **Shared code** (Metal Slug 5, 3 and X unchanged): `NgGame.codemystics`, a PC release in Code
  Mystics' format (roms.c reports it; find_game.c finds its install by `Data\rom\p1.bin`). The
  "game not found" screen found the user's GOG install by itself (English and Spanish).
- **Not done here:** loading the GOG copy (Phase 2; it has no `000-lo.lo` nor MAME's `sfix.sfix`,
  and its BIOS is `japan-j3`: to decide there); tools still defaulting to `--game mslug5`.

### Phase 0: result

Details in `docs/ROM_MAP.md`.

- **The GOG files are MAME's `mslug4h` regions:** `p1.bin` = `maincpu` (the NGH program, not
  encrypted), `c1.bin` = `sprites` in Code Mystics' packed-pixel layout, `s2.bin` = `fixed`
  (512 KB), `m1.bin` = `audiocpu` (576 KB), `v1.bin` = `adpcma`, `sp_4j.bin` = `japan-j3.bin`.
  `s1.bin` (another 128 KB fix) and `sp_4s.bin` (an MVS BIOS MAME does not list) are not needed.
- **Learned as a black box** (`tools/probe_decryption.py`, synthetic patterns with zero-filled
  stand-ins, no MAME code read): program identity; CMC50 sprites and fix affine (XOR per byte, the
  fix = the decrypted sprites' last 512 KB rearranged); PCM2 only an address XOR 4; the M1 a byte
  permutation keyed by the 16-bit sum of the first 64 KB, whose banks stay in place, so the key
  comes from the decrypted data: 0xB5E6. Each map checked on a fresh random image and on the
  rebuilt set against MAME's dumps.
- **The set rebuilt** (`tools/rebuild_set.py`, the maps inverted, the packed pixels converted back
  to bit planes): all 11 game ROMs of `mslug4h` with MAME's CRC-32 and SHA-1, `263-m1.m1`
  included (the risk the user flagged: resolved). `mame -verifyroms`: only the BIOS stand-ins
  differ. `roms\mslug4h\` (the set) and `roms\decrypted\` (MAME's regions) are outside the repo.
- **Hardware:** standard P2 bank switching (`0x2FFFF0` = 0-3, and 7 three times at boot), no
  protection chip; the Z80 uses only the default NEO-ZMC banks; **the fix is 512 KB** (fix
  banking, as in Metal Slug 3).
- **Developer menu:** `SET DEBUG DIP`, `TEST STAGE`, `COLOR BAR`, `STAGE SELECT` (6 stages),
  `SOUND TEST`; 4 references to `0x10FE80` and 17 to `0x10F000`. P1 also keeps the developers'
  **debug symbols** (1 495 `NAME $ADDRESS` pairs: bosses, player, vehicles, tasks).
- **Soft dips:** PLAY MANUAL (option 4) and BLOOD (option 8) in the header tables.
- **Oracle:** `mame mslug4h -bios us -rompath roms` boots to the title and the attract demo, and a
  scripted game plays Mission 1 to game over, with sound (95 of 122 s).
- Tools added: `verify_set.py`, `probe_decryption.py` (mslug4h, stand-ins, `--key`, constant
  outputs), `rebuild_set.py`; Lua: `dump_region.lua`, `oracle_phase0.lua`, `trace_banks.lua`,
  `trace_z80_banks.lua`, `screenshots.lua`.

### Environment phase: result

- Workspace `C:\Projecto Decompile\MS4_Port\` with `repo\`, `roms\`, `analysis\`, `logs\`,
  `release\`, `portable_test\`.
- **Shared tools**, already installed (nothing downloaded): `INSTALL.bat -VerifyOnly` passed
  17/17: 7-Zip 26.04, Python 3.14.8 + pip, CMake 4.4.4, Ninja 1.13.2, clang 23.1.3, Java 21, MAME
  0.289, MinGit 2.56, GitHub CLI 2.102, ImHex 1.38.1 (portable), SDL3 3.4.18 (configure, build and
  window) and Ghidra headless (nothing left outside its folder).
- Copied from the Metal Slug 5 repo (`ebe3896`) and adapted:
  - `setup\`: `-CopyRoms` takes the GOG install's `Data\rom\*.bin` (`-Gog`, only read) and the BIOS
    folder (`-Bios`); `-Yes` skips the question; `record_game.bat` runs `mslug4h` with
    `-rompath roms`;
  - `.gitignore` (adds `mslug4_*`; `*.bin` was already out), `.gitattributes`, `LICENSE` (MIT,
    AlmazProud), `THIRD_PARTY.md` (tools only for now);
  - `tools/audit.py` (executable `mslug4.exe`; Metal Slug 3's and 5's key tables stay allowed, for
    their regression targets), `tools/check_commit.py` and the hook. Checked: the hook rejects a
    binary, a file over 1 MB, a copy of a BIOS file and a source file the `.gitignore` leaves out.
- **ROMs:** `roms\gog\` (the 8 `Data\rom\*.bin` files) and `roms\neogeo\` (4 BIOS files),
  identical to their sources by SHA-256, with `MANIFEST.sha256`.
- Root copies: `INSTALL.bat`, `env.ps1`, `env.bat`, `README.md`, `grabar_partida.bat`.

## The user's GOG copy (confirmed in Phase 0, `docs/ROM_MAP.md`)

`K:\METAL SLUG 4\Data\rom` holds MAME's `mslug4h` regions after MAME's own transformations:

| File | Bytes | What it is |
|---|---|---|
| `p1.bin` | 5 MB | `maincpu`: `263-ph1.p1` + `263-ph2.sp2` as they are (not encrypted) |
| `c1.bin` | 48 MB | `sprites` (after CMC50) in Code Mystics' packed-pixel layout |
| `s2.bin` | 512 KB | `fixed` (taken from the C ROMs) |
| `m1.bin` | 576 KB | `audiocpu` (`263-m1.m1` after CMC50; key 0xB5E6) |
| `v1.bin` | 16 MB | `adpcma` (`263-v1` + `263-v2` after PCM2) |
| `sp_4j.bin` | 128 KB | `japan-j3.bin` (BIOS `japan-mv1b`) |
| `s1.bin`, `sp_4s.bin` | 128 KB each | another fix and an MVS BIOS MAME does not list: not needed |

`Options\` holds only `Modes.txt` (two emulator settings); `Data\` the emulator's interface and the
user's `~*.bin` settings: nothing of the game.

BIOS: the set has none. The Metal Slug 3 workspace's files are used (`sp-u2.sp1`, `000-lo.lo`,
`sm1.sm1`, `sfix.sfix`): `sfix.sfix` is GOG's Metal Slug 3 one, 28 bytes different from MAME's, and
`sm1.sm1` a stand-in (the first 128 KB of Metal Slug 3's M1); MAME warns and boots. `-bios us`, as
in Metal Slug 3 and 5 (the user's decision, 2026-10-23).

## Lessons from Metal Slug X, 3 and 5 (apply them)

The full list is in the user's prompt (`MS4_Port\PROMPT_MS4.md`); the essentials:

- **Lua in MAME:** subscriptions and taps in global variables; a fresh nvram folder per run;
  Windows paths, not `/c/...`; MAME reruns the autoboot script after a soft reset (guard it with a
  global); write taps on the LSPC registers `0x3C0000-3` never fire: use the debugger trace
  (`beamx`/`beamy`, `totalcycles`). Big-endian regions compose words big-endian
  (`dump_region.lua` handles both).
- **MAME timing already reproduced in the runtime:** watchdog reset, MOVEM video write order, Z80
  interrupts two T-states early, 68000 commands one cycle into the access, MAME's ADPCM-B, SSG soft
  reset, an NMI that does not interrupt the YM2610's IRQ acknowledge. If Metal Slug 4 diverges,
  suspect these first.
- **Audio:** Metal Slug 5's is not exact because of the power-on alignment of 68000, Z80 and
  YM2610 (its two fixes broke Metal Slug 3). Measure it in Phase 2 and tell the user what is seen
  before investing much; a generic fix would serve Metal Slug 5 too.
- **MAME's scheduler:** rare ~2-cycle shifts of raster interrupts are a known difference: bound
  them and ask the user before chasing them. **Known residue:** stack-only VBlanks, listed per run
  (`*_known_vblank.txt`) after a byte-by-byte check; MAME's boot is not deterministic in some runs
  (the reference is the replay that matches).
- **Reaching sections without playing:** the developer menu (developer mode + debug dips,
  `0x10FE80` / `0x10F000`) has a stage select; find it before recording long games. `PD_POKE` and
  `PD_DIPS` take hexadecimal; `PD_MISSION_ONCE=n` starts a mission.
- **The engine is Metal Slug 3's:** start from Metal Slug 3's profile windows, check every address
  against MAME; the player, object and form tables move fields. Assume nothing about the game:
  find every form, weapon, vehicle and boss (middle ones too), with their official names.
- **Mission mode** (Metal Slug 5 `08fa037`): reset, coin and START after the fast boot, PLAY MANUAL
  read as off, the mission rewritten each time the game clears the bytes until loaded (section byte
  0xFF). **Records:** only clean games count, and the notice says why one was not saved.
- **Editing:** bash heredocs break `\n`, `\\` and `\b` in C and Python: write patch scripts with
  the Write tool. `.bat` and `.ps1` need CRLF.
- **Window executable:** GUI subsystem, no stderr (debug to a file, remove before committing).
  Window tests: `PD_WINDOW_TEST`, `PD_PREF` (fresh folder), `PD_LOAD_STATE`; extras in order.
  **Headless** needs `--roms <folder>` and the full date.
- **CMake** only sees the known lists that exist at configure time: reconfigure after creating
  them. **Deletions:** `rm` with variables is blocked by the harness: use `"${VAR:?}"` or fresh
  folders.
- **`gh`:** AlmazProud's session lives in `GH_CONFIG_DIR = C:\Projecto Decompile\tools\_cache\gh`
  (set by `env.ps1`); PowerShell breaks `--jq` (use bash); `gh release create --target` needs the
  full SHA. **Packaging:** `tools/package_release.py` refuses a recompiled build and needs
  `PD_ROMS`; test the unzipped release in an empty folder with the game in `game\`.
- **Run-ahead:** disable every hook, no audio in the frames run ahead, run it after queueing the
  real audio. **Boss Rush:** a RAM write hook (`ng_hook_word`) on the section start bytes, not PC
  ranges.
