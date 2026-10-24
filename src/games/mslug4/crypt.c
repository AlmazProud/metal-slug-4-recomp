/* Metal Slug 4: decryption of the MAME set's cartridge files (mslug4h). Learned as a black box:
 * tools/probe_decryption.py fed MAME synthetic patterns (no game data, no MAME code) and
 * tools/learn_crypt4.py reduced the maps to the tables of crypt_tables.h, checked on the user's
 * MAME set against the regions MAME built from it: program, sprites, fix, M1 and samples identical
 * (docs/PHASE5_LOADER.md). The output has the runtime's layout, the same bytes as the GOG copy's.
 */
#include <stdlib.h>
#include <string.h>

#include "crypt_tables.h"
#include "neogeo.h"

/* ------------------------------------------------------------------ program */
/* 263-ph1.p1 + 263-ph2.sp2: not encrypted, MAME's region is the files in order. */
static void program(const uint8_t *p, uint32_t p_size, const uint8_t *chip, uint8_t *out)
{
    (void)chip;
    memcpy(out, p, p_size);
}

/* ------------------------------------------------------------------ sprites and fix (CMC50) */
/* Metal Slug 3's CMC42 form with Metal Slug 4's tables (src/games/mslug5/crypt.c). The region is
   48 MB, not a power of 2: an output address byte b2 at or past CMC_TOP goes back by
   0x100 - CMC_TOP; the next step uses it before that. */
static void sprites(const uint8_t *image, uint32_t size, uint8_t *region)
{
    static const uint8_t *const X[4] = {CMC_X0, CMC_X1, CMC_X2, CMC_X3};
    static const uint8_t *const Y[4] = {CMC_Y0, CMC_Y1, CMC_Y2, CMC_Y3};
    const uint8_t *base = CMC_BASE_ORDER;
    for (uint32_t v = 0; v < size / 4; v++) {
        uint8_t a0 = (uint8_t)v, a1 = (uint8_t)(v >> 8), a2 = (uint8_t)(v >> 16);
        uint8_t b0 = a0 ^ CMC_T1[a1];
        uint32_t b2 = a2 ^ CMC_T2[a1] ^ CMC_T3[b0];
        uint8_t b1 = a1 ^ CMC_T4[b0] ^ CMC_T5[b2];
        if (b2 >= CMC_TOP) b2 -= 0x100 - CMC_TOP;
        uint32_t out = ((uint32_t)b0 | (uint32_t)b1 << 8 | b2 << 16) * 4;
        int mid = CMC_M1[a1] ^ CMC_M2[a2], end = CMC_E1[a1] ^ CMC_E2[a2];
        for (int p = 0; p < 4; p++) {
            int q = base[p];
            if (mid && q == base[1]) q = base[2];
            else if (mid && q == base[2]) q = base[1];
            if (end && q == base[0]) q = base[3];
            else if (end && q == base[3]) q = base[0];
            region[out + (uint32_t)q] = image[v * 4 + (uint32_t)p] ^ X[q][b0] ^ Y[q][a1];
        }
    }
}

/* The fix layer (S format, 512 KB): byte k is sprite byte CMC_FIX_BASE ^ (a linear map of k). */
static void fix(const uint8_t *region, uint8_t *s)
{
    const int bits = (int)(sizeof CMC_FIX_COLS / sizeof CMC_FIX_COLS[0]);
    for (uint32_t k = 0; k < (1u << bits); k++) {
        uint32_t at = CMC_FIX_BASE;
        for (int b = 0; b < bits; b++) if (k >> b & 1) at ^= CMC_FIX_COLS[b];
        s[k] = region[at];
    }
}

/* ------------------------------------------------------------------ samples (PCM2) */
/* Output byte i: input byte PCM2_BASE ^ (a linear map of i's bits; Metal Slug 4: bit 2 flipped),
   XORed by i's low 3 bits. */
static void adpcm(uint8_t *v, uint32_t size)
{
    uint8_t *in = malloc(size);
    if (!in) return;
    memcpy(in, v, size);
    const int bits = (int)(sizeof PCM2_COLS / sizeof PCM2_COLS[0]);
    for (uint32_t i = 0; i < size; i++) {
        uint32_t src = PCM2_BASE;
        for (int b = 0; b < bits; b++) if (i >> b & 1) src ^= PCM2_COLS[b];
        v[i] = in[src % size] ^ PCM2_XOR[i & 7];
    }
    free(in);
}

/* ------------------------------------------------------------------ the M1 (CMC50, keyed) */
static uint32_t gather(uint32_t v, const uint8_t *bits)
{
    uint32_t o = 0;
    for (int k = 0; k < 8; k++) o |= ((v >> bits[k]) & 1) << k;
    return o;
}

/* Metal Slug 5's keyed byte permutation (src/games/mslug5/crypt.c) for Metal Slug 4's key: two
   64 KB banks, each in place. */
static int z80(uint8_t *m, uint32_t size)
{
    const uint32_t banks = (uint32_t)(sizeof M1_PA / sizeof M1_PA[0]);
    uint32_t sum = 0;
    for (uint32_t i = 0; i < 0x10000 && i < size; i++) sum += m[i];
    if ((sum & 0xFFFF) != M1_KEY || size != banks << 16) return -1;
    uint8_t *in = malloc(size);
    if (!in) return -1;
    memcpy(in, m, size);
    for (uint32_t k = 0; k < banks; k++)
        for (uint32_t x = 0; x < 0x10000; x++) {
            uint32_t a = gather(x, M1_A_BITS), b = gather(x, M1_B_BITS);
            uint32_t X = M1_PA[k][a] ^ M1_T1[k][b];
            uint32_t Y = M1_PB[k][b] ^ M1_T2[k][X];
            uint32_t r = 0;
            for (int i = 0; i < 8; i++) r |= ((X >> i) & 1) << M1_XPOS[k][i] | ((Y >> i) & 1) << M1_YPOS[k][i];
            m[k << 16 | r] = in[k << 16 | x];
        }
    free(in);
    return 0;
}

const NgMameCrypt MSLUG4_CRYPT = {
    .program_size = 5 * 1024 * 1024,
    .program = program,
    .sprites = sprites,
    .fix_size = 512 * 1024,
    .fix = fix,
    .z80 = z80,
    .adpcm = adpcm,
};
