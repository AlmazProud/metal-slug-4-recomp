/* Metal Slug 4 (SNK / Playmore, 2002): game descriptor (hashes, addresses and chip facts; never
 * game data).
 *
 * The target is MAME's `mslug4h` (the NGH program). The user's copy is GOG's release by Code
 * Mystics (Data\rom\*.bin): MAME's regions after MAME's own transformations, the sprites in packed
 * pixels; the `mslug4h` set rebuilt from it matches `mame -listxml mslug4h` (MAME 0.289) by CRC-32
 * and SHA-1 (docs/ROM_MAP.md). The MAME set's program is not encrypted; its sprites and fix
 * (CMC50), M1 (CMC50, keyed by the data) and V ROMs (PCM2) are: crypt.c decrypts them at load
 * (docs/PHASE5_LOADER.md). Both copies load, with the same bytes.
 */
#include "neogeo.h"

extern const NgMameCrypt MSLUG4_CRYPT;     /* crypt.c */

static const NgMameFile MAME[] = {
    {NG_MAME_P, 0, "263-ph1.p1", 1048576, 0xc67f5c8d, "12af74964843f103520d9f0825069ea2f67eeb2f", "gog"},
    {NG_MAME_P, 1, "263-ph2.sp2", 4194304, 0xbc3ec89e, "2cb0626bc4fa57e1d25f208e04532b570d87b3fb", NULL},
    {NG_MAME_M, 0, "263-m1.m1", 131072, 0x46ac8228, "5aeea221050c98e4bb0f16489ce772bf1c80f787", NULL},
    {NG_MAME_V, 0, "263-v1.v1", 8388608, 0x01e9b9cd, "0b045c2999449f7dab5ae8a42e957d5b6650431e", NULL},
    {NG_MAME_V, 1, "263-v2.v2", 8388608, 0x4ab2bf81, "77ccfa48f7e3daddef5fe5229a0093eb2f803742", NULL},
    {NG_MAME_C, 0, "263-c1.c1", 8388608, 0x84865f8a, "34467ada896eb7c7ca58658bf2a932936d8b632c", NULL},
    {NG_MAME_C, 1, "263-c2.c2", 8388608, 0x81df97f2, "2b74493b8ec8fd49216a627aeb3db493f76124e3", NULL},
    {NG_MAME_C, 2, "263-c3.c3", 8388608, 0x1a343323, "bbbb5232bba538c277ce2ee02e2956ca2243b787", NULL},
    {NG_MAME_C, 3, "263-c4.c4", 8388608, 0x942cfb44, "d9b46c71726383c4581fb042e63897e5a3c92d1b", NULL},
    {NG_MAME_C, 4, "263-c5.c5", 8388608, 0xa748854f, "2611bbedf9b5d8e82c6b2c99b88f842c46434d41", NULL},
    {NG_MAME_C, 5, "263-c6.c6", 8388608, 0x5c8ba116, "6034db09c8706d4ddbcefc053efbc47a0953eb92", NULL},
};

static const NgGame GAME = {
    .id = "mslug4",
    .title = "Metal Slug 4",
    .project = "metal-slug-4-recomp",
    .gog_id = "1773574593",
    /* GOG's files (SHA-256 of the user's copy): p1.bin = maincpu, c1.bin = the sprites in packed
       pixels, s2.bin = the 512 KB fix, m1.bin = audiocpu, v1.bin = adpcma. */
    .codemystics = {
        [NG_CM_P] = {"p1.bin", 5242880, "89efce026ce9ed938914cc3c5b78bbfc8d341b38877bc02a688f46fc53f364e2"},
        [NG_CM_TILES] = {"c1.bin", 50331648, "c4e824787b11d934e87550d6ad2935d47860c1589dbc6ee79fc29717356e0818"},
        [NG_CM_FIX_GAME] = {"s2.bin", 524288, "2f0d88562d9a052504c3b034bd118c454c80464ef7f8abe42b2da86e816a7054"},
        [NG_CM_Z80] = {"m1.bin", 589824, "7548486641b9ded055bcb8dbcd82b46f302ac67d69eef75d0ccbd6571b77cac0"},
        [NG_CM_ADPCM] = {"v1.bin", 16777216, "caaf8b1fde035c6102c5a4a7f5a20b8e34e294ef86b55e4cb88f0a64c6f07415"},
    },
    /* First MB of p1.bin: 263-ph1.p1, the GOG copy's program (= mslug4h's). */
    .gog_p1_sha256 = "94f28c85d0909a6d04f5428b7bc0758d24dc55b236b88c19f933b8c23d219d1a",
    .mame = MAME,
    .n_mame = (int)(sizeof MAME / sizeof MAME[0]),
    .crypt = &MSLUG4_CRYPT,               /* decrypted at load (docs/PHASE5_LOADER.md) */
    .mame_encrypted = 1,
    .cart = NG_CART_STANDARD,           /* P2 banking at 0x2FFFF0-0x2FFFFF, no protection chip */
    .fix_bank = NG_FIX_BANK_ROWS,
};

const NgGame *const ng_game = &GAME;
