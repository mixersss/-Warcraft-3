"""Native terrain safety apron; source-world coordinates and walkability stay fixed.

The 1.26 crash dump is consistent with an invalid terrain-cell pointer near
the southeast village corner. This is a diagnostic mitigation, not a proven
identification of the engine function. Keep a full 16-tile (2048-unit) apron
outside the old world, without opening any new playable ground.
"""
import struct

TILES = 16
UNITS = TILES * 128


def environment(data):
    assert data[:4] == b'W3E!'
    grounds = struct.unpack_from('<I', data, 13)[0]
    offset = 17 + grounds * 4
    cliffs = struct.unpack_from('<I', data, offset)[0]
    offset += 4 + cliffs * 4
    width, height, x, y = struct.unpack_from('<IIff', data, offset)
    assert (width, height, x, y) == (257, 257, -16384., -16384.)
    cells = data[offset + 16:]
    assert len(cells) == width * height * 7
    new_width, new_height = width + 2*TILES, height + 2*TILES
    out = bytearray(data[:offset])
    out += struct.pack('<IIff', new_width, new_height, x-UNITS, y-UNITS)
    # Clamp to source edge vertices, preserving all seven source bytes in the
    # interior. No object/camera/unit coordinates are translated.
    for row in range(new_height):
        source_row = min(height-1, max(0, row-TILES))
        line = cells[source_row*width*7:(source_row+1)*width*7]
        out += line[:7]*TILES + line + line[-7:]*TILES
    return bytes(out)


def raster(data, *, shadow=False):
    margin = TILES*4
    if shadow:
        width = height = 1024
        header = b''
        cells = data
    else:
        assert data[:4] == b'MP3W'
        width, height = struct.unpack_from('<II', data, 8)
        header = data[:8] + struct.pack('<II', width+margin*2, height+margin*2)
        cells = data[16:]
    assert (width, height) == (1024, 1024) and len(cells) == width*height
    new_width = width+margin*2
    # 0xFF blocks ground, flying, build and other pathing in the new apron.
    # Original pathing (including the Hokage barricade) is copied byte-exact.
    fill = b'\xff'
    out = bytearray(header + fill*(new_width*margin))
    for row in range(height):
        out += fill*margin + cells[row*width:(row+1)*width] + fill*margin
    out += fill*(new_width*margin)
    return bytes(out)
