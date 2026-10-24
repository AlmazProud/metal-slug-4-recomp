# Boss health bar and Boss Rush (Metal Slug 4)

Metal Slug 3's and 5's quality-of-life features, for Metal Slug 4 (Phase 4, part B). Worked in
stages, each one closed with a report:

| Stage | Content | Status |
|---|---|---|
| 0 | How to reach every boss without playing the whole game | **Closed**, pending approval (2026-10-24) |
| 1 | Identify the bosses (code, life, death), the middle bosses too | - |
| 2 | Boss health bar | - |
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
