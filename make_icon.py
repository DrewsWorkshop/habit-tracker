"""
Generates the Habit Tracker Home Screen icons.

Flat two-colour mark: a solid mint background with "HT" in solid purple,
drawn as terminal/bitmap letterforms on a 24x24 cell grid. Uniform square
strokes, no glow, no shadow, no bevel, no gradient -- just the two colours.

Pure standard library (zlib + struct) -- no Pillow, no network.

    python make_icon.py

Writes icon-180.png (apple-touch-icon), icon-192.png and icon-512.png (manifest).
"""

import math
import struct
import zlib

SUPER = 1008        # render resolution (divisible by 24), downsampled per target
GRID = 24           # logical cells across the icon

MINT = (127, 227, 192)      # solid background
PURPLE = (91, 33, 182)      # solid text


# ---------------------------------------------------------------- png writer
def write_png(path, pixels, w, h):
    """pixels: flat list of (r, g, b) int tuples, length w*h."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter type 0 (None)
        for r, g, b in pixels[y * w:(y + 1) * w]:
            raw += bytes((r, g, b))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- letterforms
# 8 cells wide, 12 tall, uniform 2-cell strokes -- console-font proportions.
H_ROWS = [
    "XX....XX",
    "XX....XX",
    "XX....XX",
    "XX....XX",
    "XX....XX",
    "XXXXXXXX",
    "XXXXXXXX",
    "XX....XX",
    "XX....XX",
    "XX....XX",
    "XX....XX",
    "XX....XX",
]
T_ROWS = [
    "XXXXXXXX",
    "XXXXXXXX",
    "...XX...",
    "...XX...",
    "...XX...",
    "...XX...",
    "...XX...",
    "...XX...",
    "...XX...",
    "...XX...",
    "...XX...",
    "...XX...",
]

# The "HT" block is 18 x 12 cells -> centred in the 24 x 24 grid (3 / 6 padding).
H_ORIGIN = (3, 6)
T_ORIGIN = (13, 6)


def cells(rows, origin):
    ox, oy = origin
    return {(ox + x, oy + y)
            for y, row in enumerate(rows)
            for x, ch in enumerate(row) if ch == "X"}


INK = cells(H_ROWS, H_ORIGIN) | cells(T_ROWS, T_ORIGIN)


def render(size):
    px = []
    for y in range(size):
        gy = int((y + 0.5) / size * GRID)
        for x in range(size):
            gx = int((x + 0.5) / size * GRID)
            px.append(PURPLE if (gx, gy) in INK else MINT)
    return px


def box_resize(src, src_size, dst_size):
    """Area-average resize; antialiases the letter edges. Handles 1008 -> 180."""
    if src_size == dst_size:
        return list(src)
    scale = src_size / dst_size
    out = []
    for y in range(dst_size):
        y0, y1 = y * scale, (y + 1) * scale
        ja, jb = int(y0), min(src_size, int(math.ceil(y1)))
        for x in range(dst_size):
            x0, x1 = x * scale, (x + 1) * scale
            ia, ib = int(x0), min(src_size, int(math.ceil(x1)))
            r = g = b = wsum = 0.0
            for j in range(ja, jb):
                wy = min(j + 1, y1) - max(j, y0)
                if wy <= 0:
                    continue
                base = j * src_size
                for i in range(ia, ib):
                    wx = min(i + 1, x1) - max(i, x0)
                    if wx <= 0:
                        continue
                    w = wx * wy
                    c = src[base + i]
                    r += c[0] * w; g += c[1] * w; b += c[2] * w; wsum += w
            out.append((int(r / wsum + .5), int(g / wsum + .5), int(b / wsum + .5)))
    return out


if __name__ == "__main__":
    print(f"rendering {SUPER}x{SUPER} ...")
    big = render(SUPER)
    for target in (512, 192, 180):
        name = f"icon-{target}.png"
        write_png(name, box_resize(big, SUPER, target), target, target)
        print("wrote", name)
