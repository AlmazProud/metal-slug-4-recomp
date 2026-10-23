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
  tools\        audit.py, check_commit.py, hooks\ (more from Phase 0 on)
```

Activate the environment: `. "C:\Projecto Decompile\MS4_Port\env.ps1"` (PowerShell) or
`call "C:\Projecto Decompile\MS4_Port\env.bat"` (cmd). `PD_ROOT` is the workspace, `PD_TOOLS` the
shared tools, `PD_ROMS` the ROM folder. Verify: `MS4_Port\INSTALL.bat -VerifyOnly`. Copy the ROMs:
`INSTALL.bat -CopyRoms` (`Data\rom\*.bin` of the GOG install, `-Gog`, default `K:\METAL SLUG 4`, to
`roms\gog\`; the BIOS, `-Bios`, default the Metal Slug 3 workspace's `roms\mame\neogeo`, to
`roms\neogeo\`).

Oracle (from Phase 0, once the set is rebuilt): `mame mslug4h -bios us -rompath "<workspace>\roms"`.

## Status by phase

| Phase | Status |
|---|---|
| Environment | **Closed** (2026-10-23). Verification 17/17 OK. ROMs copied to `roms\`. |
| 0. Reconnaissance (Code Mystics format, encryption schemes, black-box decryption, rebuilt `mslug4h` set, ROM map, P2 banks, developer menu, oracle) | Next |
| 1. Import Metal Slug 5's runtime and frontend with an empty `mslug4h` descriptor and profile (four executables) | - |
| 2. Metal Slug 4 hardware in the interpreter (minimal GOG loader, P2 banks, decrypted M1, PCM2) | - |
| 3. Analysis and recompilation | - |
| 4. Profile and frontend (boss bar and Boss Rush as a stage of their own) | - |
| 5. Universal loader (GOG, the MAME set decrypted at load) | - |
| 6. Publishing (`AlmazProud/metal-slug-4-recomp`) | - |

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

## The user's GOG copy (to be confirmed in Phase 0)

`K:\METAL SLUG 4\Data\rom`:

| File | Bytes | What it probably is (CRC-32 against `mame -listxml` 0.289, by the user) |
|---|---|---|
| `p1.bin` | 5 MB | exactly `mslug4h`'s program: `263-ph1.p1` (1 MB, `c67f5c8d`) + `263-ph2.sp2` (4 MB, `bc3ec89e`); not `mslug4`'s `263-p1.p1` |
| `c1.bin` | 48 MB | the 6 C ROMs, probably CMC50-decrypted |
| `s1.bin` | 128 KB | the fix taken from the C ROMs |
| `s2.bin` | 512 KB | unknown: none of its 128 KB blocks is MAME's `sfix.sfix` |
| `m1.bin` | 576 KB | probably MAME's `audiocpu` region, decrypted from `263-m1.m1` (128 KB, `46ac8228`) |
| `v1.bin` | 16 MB | does not match `263-v1`/`263-v2`: probably PCM2-decrypted |
| `sp_4j.bin` | 128 KB | `japan-j3.bin` (BIOS `japan-mv1b`, `dff6d41f`) |
| `sp_4s.bin` | 128 KB | `142e97cc`, matches no MAME BIOS: to identify |

`Options\` holds only `Modes.txt` (19 bytes). `Data\` also holds the emulator's interface (`ui\`,
`fonts\`, `logos\`, `borders\`, `strings.txt`...) and the user's `~options.bin`, `~scores.bin`,
`~windows.bin`.

In MAME (`neocart_mslug4`, PCM2 protection): the program is **not** encrypted (P1 1 MB + P2 4 MB
banked), the C ROMs use **CMC50** (the fix comes from them, no S1), the M1 is CMC50-encrypted and
the V ROMs **PCM2**: Metal Slug 5's schemes without the NEO-PVC, with other keys. All to be
confirmed in Phase 0. **The risk is the M1:** its decryption depends on the 16-bit sum of the
encrypted file's first 64 KB; inverting it means finding the key consistent with `263-m1.m1`
(`46ac8228`). If that fails, tell the user before looking for another way.

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
