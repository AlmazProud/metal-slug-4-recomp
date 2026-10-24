# Phase 4: Metal Slug 4's profile and frontend

**State:** part A (profile and frontend) closed, pending approval (2026-10-24). Part B (boss
health bar and Boss Rush, in stages with a report each): `docs/BOSS_RUSH.md`.

Goal: Metal Slug 5's frontend working with Metal Slug 4 and verified against MAME (the game
profile `src/games/mslug4/profile.c`; the frontend only offers what the profile supports).

## Plan (part A)

1. The engine's addresses, from Metal Slug 3's and 5's profile windows found in Metal Slug 4's P1
   (`tools/match_windows.py`) and the developers' debug symbols, each checked in the program and
   in MAME.
2. Developer mode, debug dips and the developers' menu.
3. Cheats, forms and vehicles, each with a MAME run that writes the same bytes at the same moments.
4. Mission mode and the "Start mission" option (Metal Slug 5's fix `08fa037` from the start).
5. Red blood, the title logo, the sound catalog, rumble, texts, records.
6. A MAME run per mission and its test; the portable copy.

The audio stays out of the pass criteria (deferred by the user, Phase 2).

## The engine

Metal Slug 4's program shares Metal Slug 3's and 5's engine. `tools/match_windows.py` cuts each
window of a reference profile into 8-byte chunks and votes for the displacement of their exact
occurrences in the target's P1: most of Metal Slug 5's and 3's windows are found, relocated (Metal
Slug 4's mission controller, for one, is Metal Slug 3's 0xED10C at 0xB9FB4). `a5` is `0x108000`
in the game code. Every address below was then read in the listing and checked in the port and
in MAME.

The developers' debug symbols (P1 `0xF0829-0xFFFE9`, `docs/ROM_MAP.md`) are names of data
(hit boxes, sprite patterns, tuning values) rather than code: a guide (`UTAN` the monkey, `ZOMB`
the zombie, `MARINE`, `HELI`...), not a source of addresses. They are extracted to
`analysis/phase4/symbols.txt` (outside the repo).

## Addresses

| What | Address | Notes |
|---|---|---|
| VBlank wait loop | `0x1E26`-`0x1E2E`, exit `0x1E30` | `cmp.b -$7F6D(a5),d0`: the game's threshold; VBlanks per cycle stored at `0x100096` |
| Debug dips | `0x10F000` | cleared on boot at `0x876` (and at `0xA752` without the developer mode) |
| Developer mode (BIOS) / the game's copy | `0x10FE80` / `0x10F002` | checked at `0x3188`; copied at `0xA746` |
| "SET DEBUG DIP" bit table | `0xA8E5A` | Metal Slug 5's, byte for byte: the same 15 switches and bits |
| Developer pause and menu | `0xA8444` | SELECT held + D newly pressed, as in Metal Slug 5 |
| Load meter | `0x1BF4` / `0x1C6A` | dip `0x0010`: shadow on (`0x3A0011`) while the VBlank handler works |
| Soft dips (USA header `0x1536`) | `0x10FD8A`- | PLAY MANUAL `0x10FD8E`, BLOOD `0x10FD92` (read at `0x775A6`) |
| Mission / section to start | `0x10ED62` / `0x10ED63` | a new game sets 0 at `0xB9D44`; setter `0xBA8DC` |
| Mission controller | object `0x100B5C` | loads the start bytes at `0xB9FBE` into `$70` / `$71`; section `0xFF` once running (`0xBA186`); next mission `0xBA5DE` |
| Current mission | `0x100BCC` | the controller's `$70`: 0-5 (checked in each mission run) |
| Player 1's score | `0x1066D8` | 8 BCD digits (checked against the HUD) |
| Player tables (P1 / P2) | `0x10EDEA` / `0x10EDFA` | 0x10 bytes: +2 shots, +3 sub-type, +4 weapon, +5 previous, +7 bombs, +8 food, +0xC ammo |
| Player objects | `0x100CBC` / `0x100D6C` | `$80` their table, `$92` form, `$93` requested form, `$94` cleared on pickup |
| Status objects | `0x1009FC` / `0x100AAC` | `$8C` character, `$8D` lives (from the HERO setting `0x10FD88`) |
| Weapon records | `0xC522E` | 19 x 10 bytes, Metal Slug 5's layout |
| Give a weapon | `0xC52EC` | D0 player, D1 weapon |
| Form table | `0xC508A` | `[(event * 2 + weapon class (0xC5032)) * 10 + form class (0xC5022)]`; requested by `0xC5046` |
| Stage object records | `0x84B32` | command 8 as Metal Slug 3's; type table `0x83F6E`, root `0x100C0C`, scroll layer `0x10ECA2` |
| The developers' stage table | `0xB9CAE` | 20 groups (`analysis/phase4/stage_table.txt`): mission bytes 0-5, 6 the endings, 7-8 the demos, 9 "How to play" |

Missions: mission byte 0 is the city (the developers' `5-x`), 1 the bridge (`2-x`), 2 the snow
(`1-x`), 3 the mummies and zombies (`3-x`), 4 the ship (`4-x`), 5 the final base (`6-x`).

## Soldiers

The soldier select is Marco, Fio, Trevor, Nadia; the internal characters are Marco 0, Trevor 1,
Nadia 2, Fio 3 (Metal Slug 3's numbers with Trevor and Nadia in Tarma's and Eri's places), found
by picking each one. Shared code: the profile's `soldier_names` and `soldier_internal_of` (Metal
Slug X, 3 and 5 keep Marco, Eri, Tarma, Fio).

## Weapons

19 records, Metal Slug 5's layout. 0-15 have Metal Slug 3's classes and ammo (7-11 are the fat
soldier's big versions). 1, 16, 17 and 18 (pistol class, 200, 30 and 200 shots; voices `18 7B`,
`7C`, `8D`) are listed by number: their sprites in the game did not tell them apart reliably
(the Dual Machine Gun, new in Metal Slug 4, is presumably one of them; not confirmed).

## Forms

Player object `$92` current form, `$93` requested. The form table has 2 weapon classes and 10 form
classes (Metal Slug 5's 3 and 4: shared code `form_weapon_classes`, `form_classes`). Found by
requesting each form:

| Form | What | Asked by event / back with |
|---|---|---|
| 0 / 1 | normal (pistol / other weapons) | - |
| 2 | fat (food: `0xC5868`, +0x1F0 to the table's +8, at `0x780`) | 1 / 2 |
| 3 | the mummy | 3 / 4 |
| 6 | the snowman (frozen; ends by itself) | 5 / - |
| 7 | the zombie | 7 / 8 |
| 8 | the monkey | 19 / 20 |
| 4 / 5 | looked normal | 9 |
| 9-11 | the soldier dies | - |
| 12-15 | hang the game | - |

The form cheat offers normal, fat, the mummy, the zombie and the monkey, each requested with the
game's own event (shared code: `form_events`, the event that asks for each form and the one that
brings it back; Metal Slug 5 keeps fat only). From a special form it goes back to normal first.

## Vehicles

The object type table (`0x83F6E`), each type spawned in Mission 1: 0x00-0x0C put the player in the
Metal Slug at once ("CANNON" on the HUD; four variants), 0x18 and 0x1C are a walking machine
(brown, red) with the "IN" marker. 0x10 and 0x14 showed no vehicle and are left out; the
motorcycle, the truck and the other Metal Slug 4 vehicles were not found among the first types.
Names by appearance.

## Sound driver

Metal Slug 5's driver. Every sound is a mode command and a command: music is ADPCM-B in mode `08`
(the game's own: `08 32` the attract intro, `08 24` "How to play", `08 27` the soldier select,
`08 2A` Mission 1, `08 23` Mission 1's boss, `08 25` mission complete, `08 22` Mission 2: names
from the moment they play in the recorded runs); mode `07` gives the same catalog. Effects are
ADPCM-A in `1A` (20-79), voices in `18` (1F-F0); mode `19` plays one sound for every command and
is left out. `0A` sets the music volume (`0A A0` full). The catalog (`tools/sound_catalog.py ...
mslug4`, taken at frame 700, the intro's silent black screen) has 319 sounds; the weapons'
announcer voices are named from the weapon records.

The sound menu silences the driver with `03`, `0A A0`, `08 20`, `07 20` (the game's own sequence
between missions, after `03`). The commands go one per frame and Metal Slug 4's driver stops the
music only when the sequence has arrived (5 frames): shared code, the sound menu test now measures
the silence after the silence sequence has been sent (Metal Slug X, 3 and 5 still pass).

- **Rumble:** no automatic table, as in Metal Slug 5; the user can set it per sound.

## Verified against MAME

All with images identical on every frame; RAM differs only in the VBlanks listed in each run's
`<run>_known_vblank.txt`, checked byte by byte.

| Run (`analysis\phase4`) | What | Known VBlanks |
|---|---|---|
| `debug/devmode` | developer mode | none |
| `debug/devdips` | developer mode and every debug dip (`FB8F`) | none |
| `debug/loadmeter` | the load meter dip | none |
| `debug/blood` | red blood | none |
| `missions/mission2`-`mission6` | the scripted game started at Missions 2-6 (`PD_POKE` at 4600, during the soldier select) | Missions 2, 3, 6: the stack, plus `0x100094` (the line the game measures after its wait loop) and one transient byte (`0x105BD1`); Missions 4 and 5: none |
| `missions/mission4` + `PD_START_MISSION=4` | the "Start mission" option | the start mission byte while the option has written it and the MAME run not yet |
| `cheats/cheats` | the Heavy Machine Gun and the Enemy Chaser through the game's routine, 63 bombs, 7 lives, Fio | none |
| `vehicles/vehicles` | the Metal Slug spawned in front of player 1 | none |
| `forms/forms` | fat, the mummy, the zombie and the monkey, each followed by normal | none |

Also in the port:

- **Mission mode's direct start** (`mslug4_mission_mode_direct`): the coin right after the boot,
  no "How to play" (PLAY MANUAL read as off), Mission 3 written at frame 2608 and loaded.
- **Records** (`mslug4_records_clean`): the user's game completes Missions 1 and 2 cleanly (frames
  16 334 and 46 069) and both are recorded; `mslug4_records_slowdown_off`: a mission completed
  with the slowdown off is not recorded, and says why; `mslug4_progress_mission_unlocked`: from
  Mission 1's boss section with the "D kills every enemy" dip, Mission 2 is unlocked at 11 090.
- **The sound menu** in the middle of the user's game (`mslug4_sound_menu`).
- **The title logo** (sprites 33-52 and the TM, 274, tile `0x1CABF`, about frame 2100 of the
  attract), generated in the window's preferences folder; fast boot to the game's first image
  (frame 301).
- **The portable copy** (`tools/make_portable.py --only mslug4`): GOG's files and the system files
  in `game\`; run from `portable_test`, it found the game and wrote only its `save` folder.

## Changes to shared code (Metal Slug X, 3 and 5 unchanged)

- `cheats.c`, `profile.h`, `menu.c`: the form table's class counts, per-form events, the soldier
  names and select order.
- `headless.c`: the sound menu test measures the silence after the silence sequence.
- `lang.c`: the new names in Spanish.
- `tools/match_windows.py` (new), `tools/sound_catalog.py` (`mslug4`), `tools/make_portable.py`
  (Metal Slug 4, `--only`, Metal Slug 5's default folder).

## Pending

- Part B: the boss health bar and Boss Rush (`docs/BOSS_RUSH.md`).
- Weapons 1, 16, 17, 18 and the other vehicles: not identified.
- The audio (deferred by the user, Phase 2).
