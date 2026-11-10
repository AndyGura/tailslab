from io import BufferedReader, BytesIO

from resources.eac.compressions.base import BaseCompressionAlgorithm

# COMP: LZ77 compression of NFS Hot Pursuit 2 PS2 (Black Box, *.LZC files: compressed chunk bundles), ported from
# SLUS_203.62 ("..\indep\src\lzcompress.cpp": decompressor 0x1b41c8, compressor 0x1b3de0).
# Header (16 bytes): "COMP", 0x01, 0x10, u16 stored flag (1: the data follows uncompressed), uncompressed length (u32),
# compressed length incl. header (u32).
# The stream is groups of 16 tokens, each after a 16-bit little-endian flag word, LSB first: 0 = literal byte,
# 1 = match of 2 bytes: distance high 4 bits in the high nibble of byte 0, length - 3 (3..18) in its low nibble,
# distance low 8 bits in byte 1. Distance 1..4095.
# The compressor finds matches by a hash of the next 3 bytes (one candidate position per hash, 0x8000 entries), the
# last 18 bytes of the input are literals. When the output would not be smaller than the input, the data is stored.

_HEADER_LENGTH = 16
_MAX_DISTANCE = 0xFFF
_MAX_LENGTH = 18


class CompCompression(BaseCompressionAlgorithm):
    def uncompress(self, buffer: [BufferedReader, BytesIO], input_length: int):
        inp = buffer.read(input_length)
        if inp[:4] != b'COMP':
            raise ValueError('Invalid COMP header')
        output_length = int.from_bytes(inp[8:12], 'little')
        input_end = min(int.from_bytes(inp[12:16], 'little'), len(inp))
        if int.from_bytes(inp[6:8], 'little') == 1:
            return bytes(inp[_HEADER_LENGTH:input_end])
        out = bytearray(output_length)
        ip = _HEADER_LENGTH
        op = 0
        flags = 1
        while ip < input_end:
            if flags == 1:
                flags = inp[ip] | (inp[ip + 1] << 8) | 0x10000
                ip += 2
            # as the game: near the end, the input end is checked after every token
            for _ in range(16 if ip <= input_end - 0x20 else 1):
                if flags & 1:
                    b0 = inp[ip]
                    distance = ((b0 & 0xF0) << 4) | inp[ip + 1]
                    length = (b0 & 0x0F) + 3
                    ip += 2
                    if distance >= length:
                        out[op : op + length] = out[op - distance : op - distance + length]
                    else:
                        for i in range(length):
                            out[op + i] = out[op + i - distance]
                    op += length
                else:
                    out[op] = inp[ip]
                    ip += 1
                    op += 1
                flags >>= 1
        if op != output_length:
            raise ValueError(f'Error while unpacking COMP: expected length {output_length}, actual length: {op}')
        return bytes(out)

    def compress(self, buffer: [BufferedReader, BytesIO], input_length: int):
        data = buffer.read(input_length)
        n = len(data)
        header = bytearray(b'COMP\x01\x10\x00\x00' + n.to_bytes(4, 'little') + b'\x00\x00\x00\x00')
        out = bytearray(header)
        # the game's table comes uninitialized from the allocator: zeroes are positions before the input
        table = [-1] * 0x8000
        # the game hashes 16 tokens at once while 0x120 bytes are left, then one at a time: the same choices
        hash_end = n - 0x12
        flags_pos = len(out)
        out += b'\0\0'
        flags = 0
        tokens = 0
        pos = 0
        # checked by the game after every 16 tokens, the output only grows: the same result
        stored = len(out) > n
        while not stored and pos < n:
            if pos <= hash_end:
                h = ((((data[pos] << 4) ^ data[pos + 1]) << 4) ^ data[pos + 2]) * 0x9E5F
                slot = (h >> 4) & 0x7FFF
                candidate = table[slot]
                table[slot] = pos
                distance = pos - candidate
                length = 0
                if candidate >= 0 and 0 < distance <= _MAX_DISTANCE:
                    while length < _MAX_LENGTH and data[candidate + length] == data[pos + length]:
                        length += 1
            else:
                length = 0
            if length >= 3:
                flags |= 1 << tokens
                out.append(((distance & 0xF00) >> 4) | (length - 3))
                out.append(distance & 0xFF)
                pos += length
            else:
                out.append(data[pos])
                pos += 1
            tokens += 1
            if tokens == 16:
                out[flags_pos] = flags & 0xFF
                out[flags_pos + 1] = flags >> 8
                flags_pos = len(out)
                out += b'\0\0'
                flags = 0
                tokens = 0
            stored = len(out) > n
        if stored:
            header[6] = 1
            out = header + data
        else:
            # the bits of the last word after its tokens are ones (the game's flag register starts as 0xFFFF0000)
            flags |= (0xFFFF << tokens) & 0xFFFF
            out[flags_pos] = flags & 0xFF
            out[flags_pos + 1] = flags >> 8
            if tokens == 0:
                del out[flags_pos:]
        out[12:16] = len(out).to_bytes(4, 'little')
        return bytes(out)
