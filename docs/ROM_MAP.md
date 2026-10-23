# ROM_MAP: the GOG copy and MAME's `mslug4h` set (Phase 0)

Source: the user's GOG install (`K:\METAL SLUG 4`, id 1773574593, Code Mystics' `NeoGeo.exe`),
copied to `roms\gog\`, with the Neo Geo BIOS files of the Metal Slug 3 workspace in `roms\neogeo\`.
Oracle: MAME 0.289, `mame mslug4h -bios us -rompath roms`.

**Main result:** the GOG files are MAME's `mslug4h` regions after MAME's own transformations
(sprites in a packed-pixel layout of Code Mystics'). Every transformation was learned from MAME as
a black box (synthetic patterns; no MAME code read) and inverted on the GOG files: **all 11 game
ROMs of `mslug4h` are rebuilt with the CRC-32 and SHA-1 of `mame -listxml`**, the encrypted M1
included (`tools/rebuild_set.py`, `tools/verify_set.py`). The rebuilt set (`roms\mslug4h\`) is the
oracle's input; MAME's regions dumped from it (`roms\decrypted\`) equal the GOG files byte for
byte. Both stay outside the repository (the audit and the pre-commit hook search them).

## The GOG files

| File | Bytes | What it is |
|---|---|---|
| `p1.bin` | 5 MB | `cslot1:maincpu` as is: `263-ph1.p1` (1 MB) + `263-ph2.sp2` (4 MB), the `mslug4h` (NGH) program; not `mslug4`'s `263-p1.p1` / `263-p2.sp2` |
| `c1.bin` | 48 MB | `cslot1:sprites` (the six C ROMs after CMC50), in **packed pixels** (below) |
| `s2.bin` | 512 KB | `cslot1:fixed`, byte for byte: MAME's fix taken from the C ROMs (the sprite region's last 512 KB, rearranged) |
| `s1.bin` | 128 KB | a fix of its own, not used by MAME: 2 613 of its 4 096 tiles are in `s2.bin` (e.g. most of tiles 0x100- are `s2.bin`'s 0x3100-), the rest are not. Not needed; not studied further |
| `m1.bin` | 576 KB | `cslot1:audiocpu`, byte for byte: the decrypted 128 KB M1 at 0x10000 (0-0xFFFF repeats 0x10000-0x1FFFF), zeros from 0x30000 |
| `v1.bin` | 16 MB | `cslot1:ymsnd:adpcma`, byte for byte (the two V ROMs after PCM2) |
| `sp_4j.bin` | 128 KB | `japan-j3.bin` (BIOS `japan-mv1b`, CRC `dff6d41f`), exact |
| `sp_4s.bin` | 128 KB | CRC `142e97cc`: matches no BIOS of MAME 0.289. An MVS system ROM ("COPYRIGHT BY SNK CORPORATION", same vectors as `japan-j3`), 89 489 bytes apart from it; probably another region's BIOS, maybe patched. Not needed (`-bios us`) |

`Options\` holds only `Modes.txt` (two emulator settings, `single:12`, `two:12`); `Data\` holds
the emulator's interface (`ui\`, `fonts\`, `logos\`, `borders\`, `network\`, `strings.txt`...)
and the user's `~*.bin` settings: nothing of the game.

### Code Mystics' sprite layout

Per 128-byte tile, `c1.bin` holds 16 rows of 8 bytes, two 4-bit pixels per byte (low nibble first),
left to right. MAME's region holds bit planes: 4 bytes per 8-pixel line in the order planes 0, 2,
1, 3, bit x = pixel x; the tile's right half in bytes 0-63, the left half in 64-127, rows 8-15
32 bytes after rows 0-7. Learned from the GOG files themselves: the sprite region's last 512 KB
are `s2.bin` rearranged (MAME's fix map, below), and every one of the tile's 1 024 bits matched
exactly one bit of `c1.bin`'s tile over the 3 852 non-uniform tiles there
(`rebuild_set.packed_to_planar`).

## The set

`tools/verify_set.py mslug4h`: every game ROM of `mslug4h` found with matching CRC-32 and SHA-1.
`mame -verifyroms mslug4h`: only the system stand-ins differ (`sfix.sfix`, GOG's Metal Slug 3 one,
28 bytes apart; `sm1.sm1`, the first 128 KB of Metal Slug 3's M1), as in the Metal Slug 3 and 5
workspaces. `mslug4` (other P1/P2) and `ms4plus` (a hack) cannot be rebuilt: their programs are
not in the GOG copy.

| File | Bytes | MAME region | Transformation (learned) |
|---|---|---|---|
| `263-ph1.p1`, `263-ph2.sp2` | 1 MB + 4 MB | `cslot1:maincpu` (5 MB) | **none** (identity) |
| `263-c1.c1`...`263-c6.c6` | 6 x 8 MB | `cslot1:sprites` (48 MB) | CMC50: affine |
| (no S1) | | `cslot1:fixed` (**512 KB**) | the sprite region's last 512 KB, rearranged |
| `263-m1.m1` | 128 KB | `cslot1:audiocpu` (576 KB) | CMC50 M1: a byte permutation **keyed by the data** |
| `263-v1.v1`, `263-v2.v2` | 8 MB + 8 MB | `cslot1:ymsnd:adpcma` (16 MB) | PCM2: an address map only |

## How the transformations were learned

`tools/probe_decryption.py learn TARGET` (`program`, `graphics`, `audio`, `adpcm`), adapted from
Metal Slug 5: MAME loads a `mslug4h` set where the probed files hold synthetic patterns and the
others are zero-filled stand-ins (there is no real set to probe around; MAME warns about their
checksums and loads them); `tools/mame/dump_region.lua` dumps the regions. Model, checked on
every probe: every output unit is a constant or `pi_i(input unit sigma(i)) XOR c(i)`; then a
prediction for a fresh random image. `check TARGET` applies the maps to the rebuilt set and compares
with MAME's dumps of it. Maps in `analysis\phase0\probe\<target>\` (never in the repository).

| Target | Runs | Linearity | Model | Prediction | Rebuilt set vs MAME's dump |
|---|---|---|---|---|---|
| program | 44 | 0 units break it | identity: no address map, no bit permutation, no XOR | 0 words differ | 2 621 440 / 2 621 440 words |
| graphics: sprites | 40 | 0 | each output byte = an input byte XOR k (50 135 040 bytes with k != 0), no bit permutation | 0 | 50 331 648 / 50 331 648 |
| graphics: fix | (same) | 0 | 524 288 bytes of the input, the same XOR as the sprite bytes they come from: the decrypted sprites' bytes 0x2F80000-0x2FFFFFF rearranged | 0 | 524 288 / 524 288 |
| adpcm | 38 | 0 | input byte at the output address XOR 4, no data change | 0 | 16 777 216 / 16 777 216 |
| audio (M1) | 5 + 7 | **breaks** (195 787 bytes) | keyed byte permutation, below | 0 | 589 824 / 589 824 |

### The M1: a permutation keyed by the data

As in Metal Slug 5 (`docs/ROM_MAP.md` there): the affine probes break linearity, and the
permutation depends on the 16-bit sum of the file's first 64 KB. Each 64 KB bank stays in place,
so the key is the sum of the **decrypted** bank 0 too: from `m1.bin`, **0xB5E6**. The permutation
was learned for that key (`learn audio --key 0xb5e6`: synthetic images given that sum by a block of
compensation bytes, three base-256 address digits, two rounds): the 128 KB file fills
`audiocpu` 0x10000-0x2FFFF (and its mirror 0-0xFFFF); 0x30000-0x8FFFF are constant zeros. A fresh
random image with the same key is predicted exactly, and inverting `m1.bin` gives `263-m1.m1`
(CRC `46ac8228`, SHA-1 `5aeea221...`): **the key is consistent with the real file.** The file's
second bank decrypts to all 0xFF.

## The 68000 program (`maincpu`)

| Region offset | Content |
|---|---|
| `0x000000-0x0FFFFF` | P1, the fixed area: vectors SP `0x10F300`, PC `0xC00402`; header `NEO-GEO`, NGH `0x0263`, P size `0x500000`, backup RAM `0x10F000` (`0x88` bytes) |
| `0x100000-0x4FFFFF` | P2: four 1 MB banks, shown at `0x200000` |

Header entry points: USER `0x0806`, PLAYER_START `0x0AA0`, DEMO_END `0x0C6C`, COIN_SOUND `0x0C62`.

### P2 banks

`tools/mame/oracle_phase0.lua` (122 s: boot, attract, a scripted game): 196 793 writes, all to
`0x2FFFF0` (full words): values 1 (138 654), 2 (42 486), 3 (15 565), 0 (85) and 7 (3, at boot,
PC `0x8DE`). The standard Neo Geo P2 bank switch: the window `0x200000-0x2FFFFF` shows the 1 MB bank
`value & 3` of P2 (to be checked in Phase 2, with the value 7). No protection chip.

### Soft dips (header)

Tables at `0x1936` (Japan), `0x1536` (USA), `0x172A` (Europe), title `METAL SLUG 4`: count
setting `HERO` (default 3), then CONTINUE, DIFFICULTY (LEVEL 1-8, default 4), PLAY TIME, DEMO
SOUND, **PLAY MANUAL** (option 4, default ON), CREDIT/LEVEL, NEXT, LANGUAGE (English, Portuguese,
Spanish, Japanese) and **BLOOD** (option 8, default OFF in the USA table). Their RAM bytes: Phase 4.

### Developer menu and debug RAM (for later phases)

- Strings: `SET DEBUG DIP` (`0xA8763`), `TEST STAGE` (`0xA877C`), `COLOR BAR` (`0xA8792`),
  `STAGE SELECT` (`0x95B9`, after `STAGE 1`...`STAGE 6`, `DATA LOAD ?`, `DATA SAVE ?`) and the
  `SOUND TEST` (`0x2968`: `BGM SET`, `S.E SET`, `ALL STOP`...).
- P1 references the BIOS developer mode `0x10FE80` four times (`0x3188`, `0xA746`, `0xA76E`,
  `0xA78A`) and the word `0x10F000` (Metal Slug 3's debug dips) 17 times. To be confirmed in MAME
  (Phase 4); it should reach the six missions and every boss without recording games.
- **Debug symbols:** P1 `0xF0829-0xFFFE9` keeps 1 495 `NAME $ADDRESS` pairs and 58 `$$ task`
  markers from the developers' tools (`BOSS0601_000_HIT $00074F64`, `PLAYER...`, `MARINE...`,
  `HELI...`, `ZOMB...`, `PVEHICLE...`, `bs6_task`, `chrsel`, `eset_610`...): names and addresses of
  hit boxes, sprite patterns and tasks, a guide for the profile and the bosses (Phase 4).

## Z80 (NEO-ZMC)

122 s with a game: only the four default banks (ports `0x08`-`0x0B`, high bytes `0x1E`, `0x0E`,
`0x06`, `0x02`, 37 times each): the driver works in the M1's first 64 KB.

## Fix layer

The cartridge fix is **512 KB** (16 384 tiles), all four 128 KB banks used (`s2.bin`): fix bank
switching, as in Metal Slug 3 (whose runtime has it), unlike Metal Slug 5's 128 KB. How the game
selects the banks: Phase 2.

## The oracle

`mame mslug4h -bios us -rompath roms` (`analysis\phase0\oracle`, `oracle_phase0.lua` with
`PD_PLAY=1`): the first boot with an empty NVRAM, the title, the attract demo, a coin and START,
"MISSION 1 START", the bot playing Mission 1 until game over and the high score table. Audio over
122 s (`-wavwrite`): sound in 95 seconds, from second 15. MAME warns about `sfix.sfix` and
`sm1.sm1`.

## Risks

- **Loader (Phase 5):** the GOG copy needs the packed-pixel conversion and nothing else (its other
  files are MAME's regions); the MAME set needs CMC50 (sprites, fix), the keyed M1 and PCM2's
  address XOR. Key tables, if any, are the user's decision.
- **Fix banking** and the P2 bank value 7: Phase 2.
- `s1.bin` and `sp_4s.bin` stay unexplained (not needed by MAME or the port).
