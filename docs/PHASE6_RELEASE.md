# Phase 6: publishing on GitHub

**State:** closed (2026-10-24). Public repository and release v1.0.0, each step with the user's
explicit OK.

Metal Slug 3's and 5's method:

| Stage | Content | Status |
|---|---|---|
| 1 | Documentation (`README.md`) and version 1.0.0 | Done |
| 2 | Audits (`tools/audit.py`): the whole history, the ROM search, personal data | Done |
| 3 | Packaging (interpreter-only zip), CI and a clean clone | Done |
| 4 | Publishing `AlmazProud/metal-slug-4-recomp`, each step with the user's OK | Done |

Known exceptions for the audits: the decryption key tables of `src/games/mslug4/crypt_tables.h`
(Phase 5, the user's decision), `src/games/mslug5/crypt_tables.h` and
`src/games/mslug3/cmc_tables.h` (the regression targets', authorized in their ports), each listed
in `audit.py` with its reason.

## Stage 1: documentation and version

- **`README.md`** (new, English): what the port is, the legal notice, quick start with the GOG
  release (plus `neogeo.zip` next to the program: the GOG release lacks the Neo Geo system files)
  or the MAME set, features, controls, where the settings go, how it works and how it was
  verified, known differences (the audio is not sample-exact; four weapons and most vehicles not
  identified), building, layout, licenses. A hidden comment at the top leaves room for the
  author's own note.
- **Version 1.0.0** (`src/port/version.h`): `mslug4.exe --version` says `metal-slug-4-recomp 1.0.0`.

## Stage 2: audits (`tools/audit.py`)

- **History:** every version of every file of every commit (314) is whitelisted text of at most
  1 MB without long hex, base64 or byte-array runs (but the three key-table files above), and
  holds no run copied from the ROMs. The ROM search ran four times, against Metal Slug 4's folder
  (the GOG copy, the rebuilt `mslug4h` set, MAME's decrypted regions, the BIOS), Metal Slug 5's,
  Metal Slug 3's and Metal Slug X's: no match.
- **Personal data:** every commit's author and committer is Alan Jair Zavala Martinez; no user
  name, other mail or profile path in any version of any file.
- **The icon:** the user's icon (Metal Slug 4's logo) is only used by personal builds, from
  `assets\mslug4.png` outside the repository; it is in no commit and not in the release.

## Stage 3: packaging and CI

- **`tools/package_release.py`** (Metal Slug 4's texts) builds
  `release/metal-slug-4-recomp-v1.0.0-win64.zip` (2 781 434 bytes, 13 files) from the
  interpreter-only build: `mslug4.exe` (no icon), `SDL3.dll`, `LICENSE.txt`, `THIRD_PARTY.md`,
  `README.txt`, the licenses and an empty `game/` folder with instructions for both copies. The
  release audit is clean against the four games' ROMs.
- **Unpacked** in an empty folder, with a fresh preferences folder: with only `neogeo.zip` in
  `game/` it finds the user's GOG install and reaches the start screen; with `mslug4h.zip` and
  `neogeo.zip` in `game/` it loads the MAME set from there and reaches the start screen.
- **GitHub Actions** (`.github/workflows/build.yml`, unchanged since Phase 1): builds and uploads
  `mslug4.exe` with the pinned toolchain.
- **Clean clone:** without ROMs, analysis or the environment's variables, with only the toolchain
  (CMake, Ninja, llvm-mingw, SDL3) and Python in the PATH, it configures and builds with no
  warnings; `--version` says 1.0.0; the Metal Slug 5, 3 and X targets, the tests and the icon are
  left out.

## Stage 4: publishing (each step with the user's OK)

**Repository:** https://github.com/AlmazProud/metal-slug-4-recomp (public, branch `main`)

1. With the user's OK (2026-10-24): `gh repo create AlmazProud/metal-slug-4-recomp --public
   --source . --remote origin --push`: the whole history (28 commits), `main` the same commit as
   the local one (`d7d6e0c`). The push started the CI build.
2. CI: that build (GitHub Actions, the pinned toolchain) passed in 44 s, artifact `mslug4-win64`.
3. With the user's OK (2026-10-24): the documentation commit pushed (CI passed in 54 s) and
   `gh release create v1.0.0` on `main` (`8d128cf`) with `metal-slug-4-recomp-v1.0.0-win64.zip`
   (2 781 434 bytes) and `release/notes-v1.0.0.md` (outside the repository): public, not a draft.
   The zip downloaded back from GitHub has the same SHA-256 as the local one
   (`60faf3fd...c2c127`).

**Release:** https://github.com/AlmazProud/metal-slug-4-recomp/releases/tag/v1.0.0
