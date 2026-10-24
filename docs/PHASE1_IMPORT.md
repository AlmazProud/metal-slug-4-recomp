# Phase 1: the Metal Slug 5 runtime and frontend, imported

**State:** closed, pending approval.

The code of the Metal Slug 5 port (v1.0.2), whose runtime and frontend are generic (a game
descriptor and a game profile), now lives in this repository. One source tree builds four
executables:

- **`mslug4.exe`**, the product. Interpreter only. It recognizes the user's GOG copy (Code
  Mystics' `Data\rom\*.bin`, by SHA-256) and the `mslug4h` MAME set (every file by CRC-32 and
  SHA-1), and says that loading them is not in the runtime yet (Phase 2).
- **`mslug5.exe`**, **`mslug3.exe`** and **`mslugx.exe`**, regression targets, built only when
  those ports' workspaces are next to this one (`<parent>\MS5_Port\roms`, `<parent>\MS3_Port\roms`,
  `<parent>\roms`), never released. Their tests against MAME guard the shared runtime and frontend.

## Import

- **One commit** (`Import the Metal Slug 5 port's code`) copies `src/`, `external/`, `tests/`,
  `tools/`, `CMakeLists.txt`, the GitHub Actions workflow and the docs that describe shared code
  (`docs/ADPCM_B.md`, `docs/QOL_FEATURES.md`) from
  https://github.com/AlmazProud/metal-slug-5-recomp at v1.0.2 (commit `ebe3896`), unchanged.
  - MIT license, Copyright (c) 2026 AlmazProud.
  - Kept from this repository: `tools/audit.py`, `tools/check_commit.py`, `tools/probe_decryption.py`,
    `tools/verify_set.py`, `tools/requirements.txt` and the Phase 0 Lua scripts.
  - Not imported: Metal Slug 5's phase docs, ROM map, `BOSS_RUSH.md` and `docs/functions_p1.csv`
    (its analysis output). Code comments that cite `docs/PHASE*.md`, `docs/BOSS_RUSH.md` or
    `docs/ROM_MAP.md` for Metal Slug 5 or 3 facts refer to those repositories.
- **Baseline:** the imported code, built against the Metal Slug 5, Metal Slug 3 and Metal Slug X
  copies (`repo\build-ms5`, `PD_ROMS` = `MS5_Port\roms`), passed **119/119** tests (Metal Slug 3:
  63, Metal Slug 5: 35, Metal Slug X: 21).
- The Metal Slug 5 repository was not modified.

## What changed

| Where | Change |
|---|---|
| `CMakeLists.txt` | `PD_ROMS` / `PD_ANALYSIS` are Metal Slug 4's; `PD_MS5_ROMS` / `PD_MS5_ANALYSIS` (default `<parent>\MS5_Port\roms` / `analysis`) join Metal Slug 3's and X's. |
| `src/CMakeLists.txt` | `mslug4.exe` (installed by `cmake --install`); `mslug5.exe` only when its reference files exist (`PD_HAVE_MSLUG5`), like `mslug3.exe` and `mslugx.exe`; Metal Slug 5's tests read `PD_MS5_*`; Metal Slug 4's tests (label `mslug4`) are kept out of Metal Slug X's label. |
| `tests/lockstep/CMakeLists.txt` | Metal Slug 5's lockstep only with `PD_HAVE_MSLUG5`. |
| `src/games/mslug4/` | `game.c`: the 11 cartridge files of `mslug4h` (CRC-32, SHA-1), the 5 Code Mystics files (SHA-256), GOG id `1773574593`, `mame_encrypted`, a standard cartridge, no fix banking yet; `profile.c`: empty profile (title only). |
| `src/port/mslug4.rc` | executable properties. |
| `src/port/version.h` | 0.1.0 (0.x until the first release). |
| `neogeo.h` | `NgGame.codemystics` (`NG_CM_P`, `_TILES`, `_FIX_GAME`, `_Z80`, `_ADPCM`): a PC release in Code Mystics' format; names NULL for the other games. |
| `roms.c` | Code Mystics' files are candidates by name and size; the folder of `p1.bin` is checked file by file (SHA-256) and reported ("GOG copy (Code Mystics) found and verified (5 files), but loading it is not in the runtime yet", or what is missing); that message wins over the MAME set's when both fail. |
| `find_game.c` | An install folder is recognized by DotEmu's `resources\game\<id>_game_m68k` or Code Mystics' `Data\rom\p1.bin` (GOG registry, Steam libraries, usual folders). |
| `.github/workflows/build.yml` | builds and uploads `mslug4.exe`. |

Metal Slug 5's, 3's and X's behaviour is unchanged: their descriptors have no Code Mystics files.

## Verification

| Build | Tests | Result |
|---|---|---|
| Baseline (`repo\build-ms5`, imported code, Metal Slug 5 + 3 + X) | 119 | **119/119** |
| Personal (`repo\build`: Metal Slug 4 interpreter only, Metal Slug 5, 3 and X recompiled) | 119 + 3 of Metal Slug 4 | **122/122** |
| Interpreter only (`repo\build-dist`, `-DPD_RECOMPILED=OFF`) | Metal Slug 5, 3 and X's 113 + Metal Slug 4's 3 | **116/116** |

- `mslug4_roms_gog`: `roms\gog` is recognized and verified (5 files).
- `mslug4_roms_mame`: the rebuilt `mslug4h` set with the BIOS, linked into the build folder, is
  recognized: "MAME set found and verified (11 files, BIOS us), but its decryption is not in the
  runtime yet".
- The "game not found" screen of `mslug4.exe` (`PD_FIND_TEST`, a fresh `PD_PREF` folder in the
  session's scratchpad), in English and Spanish: it found the user's GOG install (`K:\METAL SLUG 4`,
  only read) by itself and shows the Code Mystics message. The loader's messages are English only,
  as in the other ports.
- `mslug4.exe` (interpreter only): 1.9 MB.

## Pending (later phases)

- **Phase 2:** loading the GOG copy (the packed-pixel sprites back to the runtime's layout, the
  512 KB fix and its banking, the M1 and ADPCM as they are) and then the game against MAME. The
  GOG copy has no `000-lo.lo` and no MAME `sfix.sfix`, and its BIOS is `japan-j3` (`sp_4j.bin`):
  how the port gets the zoom table, the system fix and the BIOS from a GOG-only install is to be
  decided there (the workspace's tests use `roms\neogeo\`).
- **Tools that still default to Metal Slug 5** (`--game mslug5`): `bus_probe.py`, `coverage.py`,
  `make_portable.py`, `make_reference.py`, `mame_run.py`, `sound_catalog.py`, `recomp68k`;
  `pd_recompiled_program` expects `<id>_game_m68k`. Adapted when Metal Slug 4 needs them
  (Phases 2-3).
- **Release tooling** (`package_release.py`, `make_portable.py`): Phase 6.
