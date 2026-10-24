# Boss health bar and Boss Rush (Metal Slug 4)

Metal Slug 3's and 5's quality-of-life features, for Metal Slug 4 (Phase 4, part B). Worked in
stages, each one closed with a report:

| Stage | Content | Status |
|---|---|---|
| 0 | How to reach every boss without playing the whole game | **Closed**, pending approval (2026-10-24) |
| 1 | Identify the bosses (code, life, death), the middle bosses too | **Closed**, pending approval (2026-10-24) |
| 2 | Boss health bar | **Closed**, pending approval (2026-10-24) |
| 3 | Boss Rush | - |

Official names (the user allowed a web search; [Arcade Quartermaster](https://www.arcadequartermaster.com/mslug4_bosses.html),
[Wikipedia](https://en.wikipedia.org/wiki/Metal_Slug_4)): Mission 1 Bura Gariae, Mission 2
Toschka Dalanue (with Allen O'Neil in the middle of the bridge), Mission 3 The Iron, Mission 4
Big John, Mission 5 Sea Satan, final mission: the Morden android, the Allen android and Amadeus.

## Stage 0: the developers' stage table

As in Metal Slug 3 and 5, the game starts a mission at a section of the developers' stage table,
read by the mission controller (`0xB9FB4`): the mission byte `0x10ED62` picks the group (a table
of 20 pointers at `0xB9CAE`) and the byte `0x10ED63` the record within it (0-based; `0xB9CFE` walks
the records). Writing both during the soldier select (frame 4600 of the scripted start,
`PD_POKE`) starts the game there; the developer mode is not needed (the mission runs of
`docs/PHASE4_PROFILE.md` use no other change). The records: `[length: word] [2 bytes] [routine:
long] [data: long] [word] [area: word] [start X: word] [2 bytes] [name]`, the name in half-width
katakana with `\ch` switches (`analysis/phase4/stage_table.txt`).

The developers numbered the missions in another order than the final game: mission byte 0 (the
city) is their `5-x`, 1 (the bridge) `2-x`, 2 (the snow) `1-x`, 3 (the mummies and zombies)
`3-x`, 4 (the ship) `4-x`, 5 (the final base) `6-x`. The records are not always in their
numbering's order (Mission 3's record 4 is `1-2`). Group 6 is the endings (`MISSION ALL OVER`,
`GOOD END`, `BAD END`, `STAFF ROLL`), 7-8 the attract demos, 9 "How to play", 0x0A-0x0D one per
soldier.

### The boss sections (checked in the port: started there, invincible, screenshots)

| Mission | Mission byte | Record | Name in the table | What loads |
|---|---|---|---|---|
| 1 | 0 | 3 | `5-4 ﾎﾞｽ` | the city's overpass: the airship (Bura Gariae) |
| 2 | 1 | 2 | `2-3 ﾎﾞｽ` | the pillbox tower (Toschka Dalanue) |
| 3 | 2 | 3 | `1-6 ﾎﾞｽ` | the snow: The Iron |
| 4 | 3 | 6 | `3-7 ﾎﾞｽ` | the ruins: Big John's giant head |
| 5 | 4 | 5 | `4-6 ﾎﾞｽ` | the ship's deck: Sea Satan |
| 6 | 5 | 9 | `6-9 ｱﾚﾝ` | the factory catwalks: the Allen android |
| 6 | 5 | 10 | `6-A ﾎﾞｽ` | the round hall: the final machine (Amadeus) |

Mission 6's other sections, all checked the same way: `6-0` the entrance, `6-1` a vertical shaft,
`6-2` and `6-4` corridors, `6-3`, `6-5` and `6-7` engine rooms (`ﾄﾞｳﾘｮｸﾌﾞ`) with two big tanks
each, `6-8` a slope with one, `6-B` corridor 5, `6-C` the escape, `6-D` the bad ending. Mission 2's
`2-2` (the path) shows tanks on a hill; where Allen fights on the bridge and where the Morden
android is (the final mission's "area 2") is for stage 1, by the objects' life.

Script: `analysis\boss_rush\stage0` (outside the repo): `PD_DEVMODE=1 PD_DIPS=8000
PD_POKE=4600,10ED62,<mission>;4600,10ED63,<record>` with the scripted start; `bot_d.txt` is the
scripted start with D every 100 frames (the "D kills every enemy" dip), which ends Mission 1's
boss section (Mission 2 unlocked at frame 11 090, `docs/PHASE4_PROFILE.md`).

### Objects' life and death

The damage routine `0x7E26` is Metal Slug 5's `0x4AD18` with Metal Slug 3's offsets: **the life is
the word at `+0x4E`, the dead bit is bit 7 of `+0x5B`**. The stage's object root is `0x100C0C`
(the stage object records' parent, `docs/PHASE4_PROFILE.md`). Stage 1 identifies the bosses with
these.

### A section ends

At the end of a mission the controller writes the next mission to `0x10ED62` and clears the
section (`0xBA5E2`, `0xBA5E8`), as Metal Slug 5's next-mission step: Metal Slug 5's Boss Rush hook
on the start bytes applies. Inside a mission the start bytes are not written (the only other
writes are the new game's and the setter `0xBA8DC`); the controller presumably advances its own
section byte (`$71`): to be checked in stage 3 (the Allen android's section `6-9` and the final
machine's `6-A` are consecutive).

## Stage 1: the bosses

Found with `analysis\boss_rush\stage1` (outside the repo):

- `run_section.ps1 MISSION RECORD [FRAMES] [DIPS] [SCRIPT]`: a section started as in stage 0, the
  developer mode with debug dips (`8000` invincible; `8009` also "D kills every enemy" with
  `bot_d.txt`), RAM every 60 VBlanks.
- `survey.py`: walks the object list (`0x100C0C`, next at `+4`, parent at `+0xC`) and lists, per
  object, the VBlanks, the routines, the largest and smallest life, the dead bit and the parent.
- `routines.py`: one object's routines and life in time order (alive, phases, defeat).
- `make_bot_left.py`: a bot that crosses the screen firing up (the final boss: the scripted bot
  stays on the right, where the Mother Computer is not hit).
- Every mission walked from its first section with the D bot, then the sections it did not reach
  one by one (the ship's and the final base's), objects with 300 or more life.

| Boss | Life | Object | Code (alive -> defeat) | How it ends |
|---|---|---|---|---|
| Mission 1: Bura Gariae (the airship) | three phases: 850, 1000, 1500-1600 (life 1 between them) | top level; the cages (350) are its children | `0x16516`-`0x16794`: phases `0x165CE`, `0x16672`, `0x16706`, defeat `0x16794` | the life goes below 0 (no dead bit); mission 0 -> 1 |
| Mission 2: Toschka Dalanue (the pillbox tower, piloted by Allen) | four floors: 2700, 2700, 2400, 2100 | four objects (children of the tower's controller) | `0x6DFF8`-`0x6EC78` | each floor: dead bit; mission 1 -> 2 |
| Mission 3: The Iron | 5000 | top level | `0x6B60E`-`0x6BD04` | dead bit; mission 2 -> 3 |
| Mission 4: Big John | 3000 | top level; two parts (`0x1D45A`, the generic part that copies its parent's life) | `0x110E2`-`0x111C2` (defeat `0x111C2`, life below 0 and dead bit) | mission 3 -> 4 |
| Mission 5: Sea Satan | 750, refilled between phases (750 -> 1, 450 -> 1, ...) | top level and a part (`0x1D45A`) | `0x13C46`-`0x13F3A` (defeat `0x13F3A`) | mission 4 -> 5 (it already appears in `4-5`, the bow) |
| Mission 6: the Allen android | 500, twice (two "deaths": `0x60D22`, `0x60D64`) | top level | `0x60814`-`0x60EB6` | section 9 -> 10 (start bytes `5 10`) |
| Mission 6: Amadeus's robot | 2800 | top level | `0x70D70`-`0x71144` | dead bit; its second form follows |
| Mission 6: the robot's second form | 2800 | a child of the Mother Computer | `0x72028`-`0x72440` | dead bit; the Mother Computer follows |
| Mission 6: the Mother Computer (Amadeus) | 6400 | top level | `0x7307E`-`0x73950` (defeat `0x735BE`-`0x73606`) | dead bit; sections 11 (the escape) and 13, then the endings: mission 5 -> 6 |

- **No other middle boss:** the whole missions and the remaining sections have only ordinary
  enemies (500-600 life: the tanks of the final base's engine rooms, soldiers). Allen's Mission 2
  appearance is the tower itself ([Wikipedia](https://en.wikipedia.org/wiki/Metal_Slug_4): he
  pilots the second boss). The Morden androids of the final base are objects with life 32767
  (`0x4829C`, in sections `6-2` to `6-7`): invulnerable, not bosses.
- **A section ends** when the game writes the start bytes: at a mission's end the next mission and
  section 0 (`0xBA5E2`), and inside a mission the next section's record, then `0xFF` once loaded
  (seen in every run: Mission 3's `2 4`, `2 5`, `2 3`; the final base's `5 10` after the Allen
  android). The Boss Rush hook on the start bytes sees both.
- **The "D kills every enemy" dip** kills the Amadeus robot at once and the fight then stops: the
  Mother Computer never takes damage. Without the dip (invincible, `bot_left.txt`) the robot, its
  second form and the Mother Computer come in turn; with its life set to 10 the Mother Computer
  dies and the game goes on to the endings.
- **The airship's last phase** had 1500 in one run and 1600 in another (the section started at
  `5-4` and reached from `5-1`).

**Against MAME** (`analysis\boss_rush\stage1\boss_*`: the scripted start with the start bytes
written at frame 4600, invincible, `PD_DIPS=8000 PD_DEVMODE=1`): images identical on every frame of
the seven boss sections; RAM identical except in Mission 1's and 4's runs, where MAME takes the
VBlank one instruction apart (`boss_m1_known_vblank.txt`, `boss_m4_known_vblank.txt`, checked byte
by byte: the stack and `0x100094`, the line the game measures after its wait loop). Tests
`mslug4_boss_m1_vs_mame` ... `_m6_vs_mame`, `mslug4_boss_m6_allen_vs_mame`.

## Stage 2: the health bar

Metal Slug 3's bar (`src/port/bossbar.c`, Settings > Game > "Boss health bar") with Metal Slug 4's
profile: the object list `0x100C0C` (next at `+4`, parent at `+0xC`), the life at `+0x4E`, the
dead bit at `+0x5B`, and stage 1's bosses by their code, with their official names
(`BURA GARIAE`, `TOSCHKA DALANUE`, `THE IRON`, `BIG JOHN`, `SEA SATAN`, `ALLEN O'NEIL`,
`AMADEUS` for the robot and its second form, `MOTHER COMPUTER`). The airship and the tower have no
fixed full life (their phases and floors differ): the bar takes the largest life it sees, so a
new phase fills it again.

Shared code (Metal Slug 3 and 5 unchanged, their bar and Boss Rush tests pass):

- `boss_min_life`: the smallest life a boss is followed from (default 1000; Metal Slug 4: 400, for
  the Allen android's 500, Sea Satan's 750 and the airship's first phase, 850). Only objects
  running a known boss's code are followed, as before.
- `boss_life_signed`: a life of 0x8000 or more is below 0 (the defeated airship and Big John:
  `0xFF9C`, `0xFFEC`), shown as 0, not taken as indestructible.

**Checked** (`analysis\boss_rush\stage2\bar.ps1`, `PD_BOSSBAR=1`): the bar follows every boss from
its first hit: the airship's three phases (850, 1000, then 1500 or 1600) to 0, the tower floor by
floor, The Iron, Big John (2900/3000 at frame 5602 to 0 and dead at 6921), Sea Satan's phases
(750, refilled, 1, dead), the Allen android, Amadeus's robot and its second form, the Mother
Computer. Tests `mslug4_bossbar_m4`, `_m1` (the phases) and `_final` (the Mother Computer, its life
set to 10 at frame 30000: `10/6400`, then `0/6400 dead`). In the window, a state saved in the Big
John fight shows the bar at the right edge with `BIG JOHN`.