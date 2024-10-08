# -*- coding: utf-8 -*-

# ripemd.py - pure Python implementation of the RIPEMD-160 algorithm.
# Bjorn Edstrom <be@bjrn.se> 16 december 2007.
#
# Copyrights
# ==========
#
# This code is a derived from an implementation by Markus Friedl which is
# subject to the following license. This Python implementation is not
# subject to any other license.
#
# /*
#  * Copyright (c) 2001 Markus Friedl.  All rights reserved.
#  *
#  * Redistribution and use in source and binary forms, with or without
#  * modification, are permitted provided that the following conditions
#  * are met:
#  * 1. Redistributions of source code must retain the above copyright
#  *    notice, this list of conditions and the following disclaimer.
#  * 2. Redistributions in binary form must reproduce the above copyright
#  *    notice, this list of conditions and the following disclaimer in the
#  *    documentation and/or other materials provided with the distribution.
#  *
#  * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
#  * IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
#  * OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#  * IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
#  * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
#  * NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES LOSS OF USE,
#  * DATA, OR PROFITS OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
#  * THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#  */
# /*
#  * Preneel, Bosselaers, Dobbertin, "The Cryptographic Hash Function RIPEMD-160",
#  * RSA Laboratories, CryptoBytes, Volume 3, Number 2, Autumn 1997,
#  * ftp://ftp.rsasecurity.com/pub/cryptobytes/crypto3n2.pdf
#  */

import sys
import struct

# -----------------------------------------------------------------------------
# public interface


def ripemd160(b: bytes) -> bytes:
    """Calculates the RIPEMD160 hash of binary data"""
    ctx = RMDContext()
    rmd160_update(ctx, b, len(b))
    digest = rmd160_final(ctx)
    return digest


# -----------------------------------------------------------------------------


class RMDContext:
    def __init__(self):
        self.state = [
            0x67452301,
            0xEFCDAB89,
            0x98BADCFE,
            0x10325476,
            0xC3D2E1F0,
        ]  # uint32
        self.count = 0  # uint64
        self.buffer = [0] * 64  # uchar


def rmd160_update(ctx, inp, inplen):
    have = int((ctx.count // 8) % 64)
    inplen = int(inplen)
    need = 64 - have
    ctx.count += 8 * inplen
    off = 0
    if inplen >= need:
        if have:
            for i in range(need):
                ctx.buffer[have + i] = inp[i]
            rmd160_transform(ctx.state, ctx.buffer)
            off = need
            have = 0
        while off + 64 <= inplen:
            rmd160_transform(ctx.state, inp[off:])  # <---
            off += 64
    if off < inplen:
        for i in range(inplen - off):
            ctx.buffer[have + i] = inp[off + i]


def rmd160_final(ctx):
    size = struct.pack("<Q", ctx.count)
    padlen = 64 - ((ctx.count // 8) % 64)
    if padlen < 1 + 8:
        padlen += 64
    rmd160_update(ctx, PADDING, padlen - 8)
    rmd160_update(ctx, size, 8)
    return struct.pack("<5L", *ctx.state)


# -----------------------------------------------------------------------------

K0 = 0x00000000
K1 = 0x5A827999
K2 = 0x6ED9EBA1
K3 = 0x8F1BBCDC
K4 = 0xA953FD4E
KK0 = 0x50A28BE6
KK1 = 0x5C4DD124
KK2 = 0x6D703EF3
KK3 = 0x7A6D76E9
KK4 = 0x00000000

PADDING = [0x80] + [0] * 63


def rol(n, x):
    return ((x << n) & 0xFFFFFFFF) | (x >> (32 - n))


def f0(x, y, z):
    return x ^ y ^ z


def f1(x, y, z):
    return (x & y) | (((~x) % 0x100000000) & z)


def f2(x, y, z):
    return (x | ((~y) % 0x100000000)) ^ z


def f3(x, y, z):
    return (x & z) | (((~z) % 0x100000000) & y)


def f4(x, y, z):
    return x ^ (y | ((~z) % 0x100000000))


def r(a, b, c, d, e, fj, kj, sj, rj, x):
    a = rol(sj, (a + fj(b, c, d) + x[rj] + kj) % 0x100000000) + e
    c = rol(10, c)
    return a % 0x100000000, c


def rmd160_transform(state, block):  # uint32 state[5], uchar block[64]
    assert (
        sys.byteorder == "little"
    ), "Only little endian is supported atm for RIPEMD160"
    x = struct.unpack("<16L", bytes(block[0:64]))

    a = state[0]
    b = state[1]
    c = state[2]
    d = state[3]
    e = state[4]

    # /* Round 1 */
    a, c = r(a, b, c, d, e, f0, K0, 11, 0, x)
    e, b = r(e, a, b, c, d, f0, K0, 14, 1, x)
    d, a = r(d, e, a, b, c, f0, K0, 15, 2, x)
    c, e = r(c, d, e, a, b, f0, K0, 12, 3, x)
    b, d = r(b, c, d, e, a, f0, K0, 5, 4, x)
    a, c = r(a, b, c, d, e, f0, K0, 8, 5, x)
    e, b = r(e, a, b, c, d, f0, K0, 7, 6, x)
    d, a = r(d, e, a, b, c, f0, K0, 9, 7, x)
    c, e = r(c, d, e, a, b, f0, K0, 11, 8, x)
    b, d = r(b, c, d, e, a, f0, K0, 13, 9, x)
    a, c = r(a, b, c, d, e, f0, K0, 14, 10, x)
    e, b = r(e, a, b, c, d, f0, K0, 15, 11, x)
    d, a = r(d, e, a, b, c, f0, K0, 6, 12, x)
    c, e = r(c, d, e, a, b, f0, K0, 7, 13, x)
    b, d = r(b, c, d, e, a, f0, K0, 9, 14, x)
    a, c = r(a, b, c, d, e, f0, K0, 8, 15, x)  # /* #15 */
    # /* Round 2 */
    e, b = r(e, a, b, c, d, f1, K1, 7, 7, x)
    d, a = r(d, e, a, b, c, f1, K1, 6, 4, x)
    c, e = r(c, d, e, a, b, f1, K1, 8, 13, x)
    b, d = r(b, c, d, e, a, f1, K1, 13, 1, x)
    a, c = r(a, b, c, d, e, f1, K1, 11, 10, x)
    e, b = r(e, a, b, c, d, f1, K1, 9, 6, x)
    d, a = r(d, e, a, b, c, f1, K1, 7, 15, x)
    c, e = r(c, d, e, a, b, f1, K1, 15, 3, x)
    b, d = r(b, c, d, e, a, f1, K1, 7, 12, x)
    a, c = r(a, b, c, d, e, f1, K1, 12, 0, x)
    e, b = r(e, a, b, c, d, f1, K1, 15, 9, x)
    d, a = r(d, e, a, b, c, f1, K1, 9, 5, x)
    c, e = r(c, d, e, a, b, f1, K1, 11, 2, x)
    b, d = r(b, c, d, e, a, f1, K1, 7, 14, x)
    a, c = r(a, b, c, d, e, f1, K1, 13, 11, x)
    e, b = r(e, a, b, c, d, f1, K1, 12, 8, x)  # /* #31 */
    # /* Round 3 */
    d, a = r(d, e, a, b, c, f2, K2, 11, 3, x)
    c, e = r(c, d, e, a, b, f2, K2, 13, 10, x)
    b, d = r(b, c, d, e, a, f2, K2, 6, 14, x)
    a, c = r(a, b, c, d, e, f2, K2, 7, 4, x)
    e, b = r(e, a, b, c, d, f2, K2, 14, 9, x)
    d, a = r(d, e, a, b, c, f2, K2, 9, 15, x)
    c, e = r(c, d, e, a, b, f2, K2, 13, 8, x)
    b, d = r(b, c, d, e, a, f2, K2, 15, 1, x)
    a, c = r(a, b, c, d, e, f2, K2, 14, 2, x)
    e, b = r(e, a, b, c, d, f2, K2, 8, 7, x)
    d, a = r(d, e, a, b, c, f2, K2, 13, 0, x)
    c, e = r(c, d, e, a, b, f2, K2, 6, 6, x)
    b, d = r(b, c, d, e, a, f2, K2, 5, 13, x)
    a, c = r(a, b, c, d, e, f2, K2, 12, 11, x)
    e, b = r(e, a, b, c, d, f2, K2, 7, 5, x)
    d, a = r(d, e, a, b, c, f2, K2, 5, 12, x)  # /* #47 */
    # /* Round 4 */
    c, e = r(c, d, e, a, b, f3, K3, 11, 1, x)
    b, d = r(b, c, d, e, a, f3, K3, 12, 9, x)
    a, c = r(a, b, c, d, e, f3, K3, 14, 11, x)
    e, b = r(e, a, b, c, d, f3, K3, 15, 10, x)
    d, a = r(d, e, a, b, c, f3, K3, 14, 0, x)
    c, e = r(c, d, e, a, b, f3, K3, 15, 8, x)
    b, d = r(b, c, d, e, a, f3, K3, 9, 12, x)
    a, c = r(a, b, c, d, e, f3, K3, 8, 4, x)
    e, b = r(e, a, b, c, d, f3, K3, 9, 13, x)
    d, a = r(d, e, a, b, c, f3, K3, 14, 3, x)
    c, e = r(c, d, e, a, b, f3, K3, 5, 7, x)
    b, d = r(b, c, d, e, a, f3, K3, 6, 15, x)
    a, c = r(a, b, c, d, e, f3, K3, 8, 14, x)
    e, b = r(e, a, b, c, d, f3, K3, 6, 5, x)
    d, a = r(d, e, a, b, c, f3, K3, 5, 6, x)
    c, e = r(c, d, e, a, b, f3, K3, 12, 2, x)  # /* #63 */
    # /* Round 5 */
    b, d = r(b, c, d, e, a, f4, K4, 9, 4, x)
    a, c = r(a, b, c, d, e, f4, K4, 15, 0, x)
    e, b = r(e, a, b, c, d, f4, K4, 5, 5, x)
    d, a = r(d, e, a, b, c, f4, K4, 11, 9, x)
    c, e = r(c, d, e, a, b, f4, K4, 6, 7, x)
    b, d = r(b, c, d, e, a, f4, K4, 8, 12, x)
    a, c = r(a, b, c, d, e, f4, K4, 13, 2, x)
    e, b = r(e, a, b, c, d, f4, K4, 12, 10, x)
    d, a = r(d, e, a, b, c, f4, K4, 5, 14, x)
    c, e = r(c, d, e, a, b, f4, K4, 12, 1, x)
    b, d = r(b, c, d, e, a, f4, K4, 13, 3, x)
    a, c = r(a, b, c, d, e, f4, K4, 14, 8, x)
    e, b = r(e, a, b, c, d, f4, K4, 11, 11, x)
    d, a = r(d, e, a, b, c, f4, K4, 8, 6, x)
    c, e = r(c, d, e, a, b, f4, K4, 5, 15, x)
    b, d = r(b, c, d, e, a, f4, K4, 6, 13, x)  # /* #79 */

    aa = a
    bb = b
    cc = c
    dd = d
    ee = e

    a = state[0]
    b = state[1]
    c = state[2]
    d = state[3]
    e = state[4]

    # /* Parallel round 1 */
    a, c = r(a, b, c, d, e, f4, KK0, 8, 5, x)
    e, b = r(e, a, b, c, d, f4, KK0, 9, 14, x)
    d, a = r(d, e, a, b, c, f4, KK0, 9, 7, x)
    c, e = r(c, d, e, a, b, f4, KK0, 11, 0, x)
    b, d = r(b, c, d, e, a, f4, KK0, 13, 9, x)
    a, c = r(a, b, c, d, e, f4, KK0, 15, 2, x)
    e, b = r(e, a, b, c, d, f4, KK0, 15, 11, x)
    d, a = r(d, e, a, b, c, f4, KK0, 5, 4, x)
    c, e = r(c, d, e, a, b, f4, KK0, 7, 13, x)
    b, d = r(b, c, d, e, a, f4, KK0, 7, 6, x)
    a, c = r(a, b, c, d, e, f4, KK0, 8, 15, x)
    e, b = r(e, a, b, c, d, f4, KK0, 11, 8, x)
    d, a = r(d, e, a, b, c, f4, KK0, 14, 1, x)
    c, e = r(c, d, e, a, b, f4, KK0, 14, 10, x)
    b, d = r(b, c, d, e, a, f4, KK0, 12, 3, x)
    a, c = r(a, b, c, d, e, f4, KK0, 6, 12, x)  # /* #15 */
    # /* Parallel round 2 */
    e, b = r(e, a, b, c, d, f3, KK1, 9, 6, x)
    d, a = r(d, e, a, b, c, f3, KK1, 13, 11, x)
    c, e = r(c, d, e, a, b, f3, KK1, 15, 3, x)
    b, d = r(b, c, d, e, a, f3, KK1, 7, 7, x)
    a, c = r(a, b, c, d, e, f3, KK1, 12, 0, x)
    e, b = r(e, a, b, c, d, f3, KK1, 8, 13, x)
    d, a = r(d, e, a, b, c, f3, KK1, 9, 5, x)
    c, e = r(c, d, e, a, b, f3, KK1, 11, 10, x)
    b, d = r(b, c, d, e, a, f3, KK1, 7, 14, x)
    a, c = r(a, b, c, d, e, f3, KK1, 7, 15, x)
    e, b = r(e, a, b, c, d, f3, KK1, 12, 8, x)
    d, a = r(d, e, a, b, c, f3, KK1, 7, 12, x)
    c, e = r(c, d, e, a, b, f3, KK1, 6, 4, x)
    b, d = r(b, c, d, e, a, f3, KK1, 15, 9, x)
    a, c = r(a, b, c, d, e, f3, KK1, 13, 1, x)
    e, b = r(e, a, b, c, d, f3, KK1, 11, 2, x)  # /* #31 */
    # /* Parallel round 3 */
    d, a = r(d, e, a, b, c, f2, KK2, 9, 15, x)
    c, e = r(c, d, e, a, b, f2, KK2, 7, 5, x)
    b, d = r(b, c, d, e, a, f2, KK2, 15, 1, x)
    a, c = r(a, b, c, d, e, f2, KK2, 11, 3, x)
    e, b = r(e, a, b, c, d, f2, KK2, 8, 7, x)
    d, a = r(d, e, a, b, c, f2, KK2, 6, 14, x)
    c, e = r(c, d, e, a, b, f2, KK2, 6, 6, x)
    b, d = r(b, c, d, e, a, f2, KK2, 14, 9, x)
    a, c = r(a, b, c, d, e, f2, KK2, 12, 11, x)
    e, b = r(e, a, b, c, d, f2, KK2, 13, 8, x)
    d, a = r(d, e, a, b, c, f2, KK2, 5, 12, x)
    c, e = r(c, d, e, a, b, f2, KK2, 14, 2, x)
    b, d = r(b, c, d, e, a, f2, KK2, 13, 10, x)
    a, c = r(a, b, c, d, e, f2, KK2, 13, 0, x)
    e, b = r(e, a, b, c, d, f2, KK2, 7, 4, x)
    d, a = r(d, e, a, b, c, f2, KK2, 5, 13, x)  # /* #47 */
    # /* Parallel round 4 */
    c, e = r(c, d, e, a, b, f1, KK3, 15, 8, x)
    b, d = r(b, c, d, e, a, f1, KK3, 5, 6, x)
    a, c = r(a, b, c, d, e, f1, KK3, 8, 4, x)
    e, b = r(e, a, b, c, d, f1, KK3, 11, 1, x)
    d, a = r(d, e, a, b, c, f1, KK3, 14, 3, x)
    c, e = r(c, d, e, a, b, f1, KK3, 14, 11, x)
    b, d = r(b, c, d, e, a, f1, KK3, 6, 15, x)
    a, c = r(a, b, c, d, e, f1, KK3, 14, 0, x)
    e, b = r(e, a, b, c, d, f1, KK3, 6, 5, x)
    d, a = r(d, e, a, b, c, f1, KK3, 9, 12, x)
    c, e = r(c, d, e, a, b, f1, KK3, 12, 2, x)
    b, d = r(b, c, d, e, a, f1, KK3, 9, 13, x)
    a, c = r(a, b, c, d, e, f1, KK3, 12, 9, x)
    e, b = r(e, a, b, c, d, f1, KK3, 5, 7, x)
    d, a = r(d, e, a, b, c, f1, KK3, 15, 10, x)
    c, e = r(c, d, e, a, b, f1, KK3, 8, 14, x)  # /* #63 */
    # /* Parallel round 5 */
    b, d = r(b, c, d, e, a, f0, KK4, 8, 12, x)
    a, c = r(a, b, c, d, e, f0, KK4, 5, 15, x)
    e, b = r(e, a, b, c, d, f0, KK4, 12, 10, x)
    d, a = r(d, e, a, b, c, f0, KK4, 9, 4, x)
    c, e = r(c, d, e, a, b, f0, KK4, 12, 1, x)
    b, d = r(b, c, d, e, a, f0, KK4, 5, 5, x)
    a, c = r(a, b, c, d, e, f0, KK4, 14, 8, x)
    e, b = r(e, a, b, c, d, f0, KK4, 6, 7, x)
    d, a = r(d, e, a, b, c, f0, KK4, 8, 6, x)
    c, e = r(c, d, e, a, b, f0, KK4, 13, 2, x)
    b, d = r(b, c, d, e, a, f0, KK4, 6, 13, x)
    a, c = r(a, b, c, d, e, f0, KK4, 5, 14, x)
    e, b = r(e, a, b, c, d, f0, KK4, 15, 0, x)
    d, a = r(d, e, a, b, c, f0, KK4, 13, 3, x)
    c, e = r(c, d, e, a, b, f0, KK4, 11, 9, x)
    b, d = r(b, c, d, e, a, f0, KK4, 11, 11, x)  # /* #79 */

    t = (state[1] + cc + d) % 0x100000000
    state[1] = (state[2] + dd + e) % 0x100000000
    state[2] = (state[3] + ee + a) % 0x100000000
    state[3] = (state[4] + aa + b) % 0x100000000
    state[4] = (state[0] + bb + c) % 0x100000000
    state[0] = t % 0x100000000
