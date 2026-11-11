"""Classic PKO 1.38 CHAP and packet codecs; not modern RSA/AES."""
import hashlib
from functools import lru_cache
from des_tables import IP, FP, EXPAND, PERMUTE, PC1, PC2, SHIFTS, SBOX


def permute(value, table, width):
    out = 0
    for bit in table:
        out = (out << 1) | ((value >> (width - bit)) & 1)
    return out


@lru_cache(maxsize=32)
def subkeys(key):
    bits = permute(int.from_bytes(key, 'big'), PC1, 64)
    c, d = bits >> 28, bits & 0xfffffff
    result = []
    for shift in SHIFTS:
        c = ((c << shift) | (c >> (28 - shift))) & 0xfffffff
        d = ((d << shift) | (d >> (28 - shift))) & 0xfffffff
        result.append(permute((c << 28) | d, PC2, 56))
    return result


def des(block, key, decrypt=False):
    if len(block) != 8 or len(key) != 8:
        raise ValueError('DES requires an 8-byte key and block')
    bits = permute(int.from_bytes(block, 'big'), IP, 64)
    left, right = bits >> 32, bits & 0xffffffff
    keys = subkeys(key)
    for k in reversed(keys) if decrypt else keys:
        expanded = permute(right, EXPAND, 32) ^ k
        combined = 0
        for i in range(8):
            x = (expanded >> (42 - i * 6)) & 63
            row, column = ((x >> 4) & 2) | (x & 1), (x >> 1) & 15
            combined = (combined << 4) | SBOX[i * 64 + row * 16 + column]
        left, right = right, left ^ permute(combined, PERMUTE, 32)
    return permute((right << 32) | left, FP, 64).to_bytes(8, 'big')


def triple_des(data, key, decrypt=False):
    if len(data) % 8 or len(key) < 24:
        raise ValueError('Expected whole DES blocks and at least 24 key bytes')
    keys = [key[:8], key[8:16], key[16:24]]
    if decrypt:
        keys.reverse()
    result = bytearray()
    for offset in range(0, len(data), 8):
        b = des(data[offset:offset+8], keys[0], decrypt)
        b = des(b, keys[1], not decrypt)
        result.extend(des(b, keys[2], decrypt))
    return bytes(result)


def password_key(password):
    return hashlib.md5(password.encode('ascii')).hexdigest().upper().encode('ascii')


def login_proof(challenge, password):
    # CDES::RunPad(ZERO) always adds a block, including aligned messages.
    padded = challenge + bytes(8 - len(challenge) % 8)
    return triple_des(padded, password_key(password))


def session_key(encrypted, password):
    if len(encrypted) < 8:
        raise ValueError('Missing session key')
    return triple_des(encrypted, password_key(password), True)[:6]


def noise_seed(challenge, version=136):
    if len(challenge) < 4:
        raise ValueError('Challenge is too short')
    multiplier = (version * version * 0x1111 * 2) & 0xffff
    if multiplier & 0x8000:
        multiplier -= 0x10000
    seed = (int.from_bytes(challenge[-4:], 'little') * multiplier) & 0xffffffff
    return bytearray(seed & mask for mask in (1, 2, 4, 8))


class Noise:
    def __init__(self, seed):
        self.key = bytearray(seed)
        if len(self.key) != 4:
            raise ValueError('Noise key must have four bytes')

    def transform(self, packet, decrypt=False):
        data = bytearray(packet)
        before = bytes(data)
        for i in range(min(len(data) // 4, 8) * 4):
            data[i] ^= self.key[3 - i % 4]
        encrypted = before if decrypt else data
        if len(data) >= 8:
            self.key[:] = bytes(encrypted[7-i] ^ encrypted[3-i] ^ (i+1) for i in range(4))
        return bytes(data)


def packet_b(packet, key, decrypt=False):
    if not key:
        raise ValueError('Missing B cipher key')
    result = bytearray()
    for i, b in enumerate(packet):
        k = key[i % len(key)]
        # VC2003 converts signed char to uint32 before unsigned remainder.
        rotation = ((k if k < 128 else k - 256) & 0xffffffff) % len(key) + 1
        rotation &= 7
        if decrypt:
            b = ((b >> rotation) | (b << (8-rotation))) & 255
            result.append(b ^ k)
        else:
            b ^= k
            result.append(((b << rotation) | (b >> (8-rotation))) & 255)
    return bytes(result)


class PacketCipher:
    def __init__(self, seed, key):
        self.noise = Noise(seed)
        self.key = bytes(key)

    def encrypt(self, body):
        return packet_b(self.noise.transform(body), self.key)

    def decrypt(self, body):
        return self.noise.transform(packet_b(body, self.key, True), True)
