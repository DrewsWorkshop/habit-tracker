"""
Generates the Neon Habits Home Screen icons.

Pure standard library (zlib + struct) -- no Pillow, no network.
Renders a synthwave scene at 4x then box-downsamples for antialiasing.

    python make_icon.py

Writes icon-180.png (apple-touch-icon), icon-192.png and icon-512.png (manifest).
"""

import math
import struct
import zlib

SUPER = 1024  # render resolution, downsampled to each target size


# ---------------------------------------------------------------- png writer
def write_png(path, pixels, w, h):
    """pixels: flat list of (r, g, b) tuples, length w*h."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter type 0 (None)
        row = pixels[y * w:(y + 1) * w]
        for r, g, b in row:
            raw += bytes((r, g, b))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- colour math
def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(lerp(c1[i], c2[i], t) for i in range(3))


def ramp(stops, t):
    """stops: [(pos, (r,g,b)), ...] sorted by pos."""
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if p0 <= t <= p1:
            return mix(c0, c1, (t - p0) / (p1 - p0) if p1 > p0 else 0.0)
    return stops[-1][1]


def screen(base, add, amount):
    """Additive-ish blend that never clips ugly."""
    return tuple(min(255.0, base[i] + add[i] * amount) for i in range(3))


def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


# ---------------------------------------------------------------- the scene
BG_TOP = (7, 6, 14)
BG_BOT = (37, 15, 67)
PINK = (255, 46, 151)
CYAN = (0, 229, 255)
PURPLE = (176, 108, 255)
WHITE = (255, 255, 255)

SUN_STOPS = [
    (0.00, (255, 224, 102)),
    (0.34, (255, 154, 60)),
    (0.72, (255, 46, 151)),
    (1.00, (176, 108, 255)),
]

HORIZON = 0.615   # y of the horizon, in 0..1
SUN_CY = 0.435
SUN_R = 0.255


def shade(u, v):
    """u, v in 0..1 -> (r, g, b) float tuple."""
    # backdrop gradient
    col = ramp([(0.0, BG_TOP), (0.45, (11, 7, 24)), (0.70, (21, 11, 46)), (1.0, BG_BOT)], v)

    # sun glow halo
    d = math.hypot(u - 0.5, v - SUN_CY)
    halo = max(0.0, 1.0 - d / (SUN_R * 2.25))
    col = screen(col, PINK, halo ** 2.4 * 0.55)

    # the sun disc, with retro scanline gaps in its lower half
    if d < SUN_R:
        t = (v - (SUN_CY - SUN_R)) / (2 * SUN_R)
        sun = ramp(SUN_STOPS, t)
        band = 1.0
        if t > 0.42:
            cyc = (v * 34.0) % 1.0                    # bands tied to absolute v
            gap = 0.30 + 0.32 * ((t - 0.42) / 0.58)   # gaps widen toward the bottom
            band = 0.0 if cyc < gap else 1.0
        edge = min(1.0, (SUN_R - d) / (SUN_R * 0.035))  # antialias the rim
        col = mix(col, sun, band * edge)

    # horizon beam
    hd = abs(v - HORIZON)
    beam = max(0.0, 1.0 - hd / 0.016)
    if beam > 0:
        tint = mix(CYAN, PINK, abs(u - 0.5) * 2 if u > 0.5 else 0.0)
        tint = mix(CYAN, tint, 1.0)
        centre = max(0.0, 1.0 - abs(u - 0.5) * 1.6)
        col = screen(col, mix(tint, WHITE, centre ** 2), beam ** 1.5 * 0.95)
    col = screen(col, PINK, max(0.0, 1.0 - hd / 0.09) ** 3 * 0.30)

    # perspective grid below the horizon
    if v > HORIZON:
        t = (v - HORIZON) / (1.0 - HORIZON)     # 0 at horizon, 1 at bottom
        lw = 0.0016 + 0.0060 * t                 # lines thicken toward the viewer

        # converging verticals
        best = 9.0
        for k in range(-13, 14):
            if k == 0:
                continue
            x = 0.5 + k * 0.052 * t
            best = min(best, abs(u - x))
        gv = max(0.0, 1.0 - best / lw)

        # receding horizontals, bunched near the horizon
        gh = 0.0
        for n in range(1, 16):
            tn = 1.0 - 1.0 / (1.0 + n * 0.30)
            gh = max(gh, max(0.0, 1.0 - abs(t - tn) / (lw * 1.3)))

        g = max(gv, gh) * (0.30 + 0.70 * t)
        col = screen(col, mix(PURPLE, PINK, t), g * 0.85)

    # neon check mark, front and centre
    cd = min(
        seg_dist(u, v, 0.325, 0.470, 0.445, 0.585),
        seg_dist(u, v, 0.445, 0.585, 0.690, 0.315),
    )
    stroke, soft = 0.037, 0.020
    if cd < stroke + soft * 3:
        col = screen(col, CYAN, max(0.0, 1.0 - cd / (stroke + soft * 3)) ** 2.2 * 0.75)
        if cd < stroke:
            aa = min(1.0, (stroke - cd) / 0.006)
            col = mix(col, mix(WHITE, CYAN, min(1.0, cd / stroke)), aa)

    # corner vignette
    vg = math.hypot((u - 0.5) * 1.05, (v - 0.46) * 1.05)
    col = mix(col, (4, 2, 10), max(0.0, (vg - 0.52)) * 1.5)
    return col


def render(size):
    px = []
    for y in range(size):
        v = (y + 0.5) / size
        for x in range(size):
            u = (x + 0.5) / size
            px.append(shade(u, v))
    return px


def box_resize(src, src_size, dst_size):
    """Area-average resize. Handles non-integer ratios (1024 -> 180)."""
    if src_size == dst_size:
        return [(int(c[0] + 0.5), int(c[1] + 0.5), int(c[2] + 0.5)) for c in src]
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
            out.append((int(r / wsum + 0.5), int(g / wsum + 0.5), int(b / wsum + 0.5)))
    return out


if __name__ == "__main__":
    print(f"rendering {SUPER}x{SUPER} ...")
    big = render(SUPER)
    for target in (512, 192, 180):
        name = f"icon-{target}.png"
        write_png(name, box_resize(big, SUPER, target), target, target)
        print("wrote", name)
