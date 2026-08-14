"""
Generates the Habit Tracker Home Screen icons.

Solid background with "HT" drawn as hard-edged pixel-art letterforms on a 24x24
cell grid -- H in neon pink, T in neon cyan, with a soft neon bloom behind them.

Pure standard library (zlib + struct) -- no Pillow, no network.

    python make_icon.py

Writes icon-180.png (apple-touch-icon), icon-192.png and icon-512.png (manifest).
"""

import math
import struct
import zlib

SUPER = 1008        # render resolution (divisible by 24), downsampled per target
GRID = 24           # logical pixel-art cells across the icon

BG = (13, 10, 26)           # solid background
PINK = (255, 46, 151)
CYAN = (0, 229, 255)
FIELD = 224                 # resolution of the glow distance field
SEAM = 0.10                 # seam inset around each lit cell, in cell units
SEAM_DARK = 0.80            # how far that seam blends back toward the background


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
# 8 cells wide, 12 tall, 2-cell strokes throughout.
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

# "HT" block is 18 x 12 cells -> centred in the 24 x 24 grid with 3/6 padding.
H_ORIGIN = (3, 6)
T_ORIGIN = (13, 6)


def cells(rows, origin):
    ox, oy = origin
    return {(ox + x, oy + y)
            for y, row in enumerate(rows)
            for x, ch in enumerate(row) if ch == "X"}


H_CELLS = cells(H_ROWS, H_ORIGIN)
T_CELLS = cells(T_ROWS, T_ORIGIN)


def distance_field(cell_set):
    """Distance (in grid units) from each sample point to the nearest lit cell."""
    rects = [(cx, cy, cx + 1, cy + 1) for cx, cy in cell_set]
    field = []
    for j in range(FIELD):
        gy = (j + 0.5) / FIELD * GRID
        for i in range(FIELD):
            gx = (i + 0.5) / FIELD * GRID
            best = 1e9
            for x0, y0, x1, y1 in rects:
                dx = x0 - gx if gx < x0 else (gx - x1 if gx > x1 else 0.0)
                dy = y0 - gy if gy < y0 else (gy - y1 if gy > y1 else 0.0)
                d = dx * dx + dy * dy
                if d < best:
                    best = d
                    if d == 0.0:
                        break
            field.append(math.sqrt(best))
    return field


def sample(field, u, v):
    """Bilinear sample of a FIELD x FIELD distance map at u, v in 0..1."""
    fx = min(FIELD - 1.001, max(0.0, u * FIELD - 0.5))
    fy = min(FIELD - 1.001, max(0.0, v * FIELD - 0.5))
    i, j = int(fx), int(fy)
    tx, ty = fx - i, fy - j
    a = field[j * FIELD + i]
    b = field[j * FIELD + i + 1]
    c = field[(j + 1) * FIELD + i]
    d = field[(j + 1) * FIELD + i + 1]
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def render(size, fh, ft):
    px = []
    for y in range(size):
        v = (y + 0.5) / size
        gy = int(v * GRID)
        for x in range(size):
            u = (x + 0.5) / size
            gx = int(u * GRID)
            cell = (gx, gy)

            lit = PINK if cell in H_CELLS else CYAN if cell in T_CELLS else None
            if lit:
                # Darken a seam around every cell so the individual pixels of the
                # letterform stay visible -- this is what reads as "pixel art"
                # rather than just a bold sans-serif H and T.
                fx, fy = u * GRID - gx, v * GRID - gy
                edge = min(fx, 1.0 - fx, fy, 1.0 - fy)
                if edge < SEAM:
                    k = (1.0 - edge / SEAM) * SEAM_DARK
                    lit = tuple(lit[i] + (BG[i] - lit[i]) * k for i in range(3))
                px.append(lit)
                continue

            # solid background plus the bloom shed by each letter
            gh = math.exp(-sample(fh, u, v) * 2.6)
            gt = math.exp(-sample(ft, u, v) * 2.6)
            r = BG[0] + PINK[0] * gh * 0.55 + CYAN[0] * gt * 0.55
            g = BG[1] + PINK[1] * gh * 0.55 + CYAN[1] * gt * 0.55
            b = BG[2] + PINK[2] * gh * 0.55 + CYAN[2] * gt * 0.55
            px.append((min(255.0, r), min(255.0, g), min(255.0, b)))
    return px


def box_resize(src, src_size, dst_size):
    """Area-average resize. Handles non-integer ratios (1008 -> 180)."""
    if src_size == dst_size:
        return [(int(c[0] + .5), int(c[1] + .5), int(c[2] + .5)) for c in src]
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
    print("building glow fields ...")
    fh, ft = distance_field(H_CELLS), distance_field(T_CELLS)
    print(f"rendering {SUPER}x{SUPER} ...")
    big = render(SUPER, fh, ft)
    for target in (512, 192, 180):
        name = f"icon-{target}.png"
        write_png(name, box_resize(big, SUPER, target), target, target)
        print("wrote", name)
