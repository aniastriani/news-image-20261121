#!/usr/bin/env python3
"""The World in One Image - Saturday 21 November 2026.

A newspaper front page that sums up the day's world news in a single
picture. Pure Python 3.13 standard library only: a hand-drawn 5 by 7
pixel font, small vector drawings for each story, and a PNG writer
built by hand (zlib compression, CRCs from binascii). No network, no
clock, no random numbers, no files read at run time, so every run
writes exactly the same bytes.

Run it with:
    python3 main.py
The picture goes to /output/entry.png, or to $MAKEFUN_OUTPUT_DIR
when that variable is set.
"""

import os
import struct
import zlib
from binascii import crc32

# ------------------------------------------------------------------ page

W = 1024
H = 1024

NEWSprint = (247, 243, 234)   # warm paper
CARD = (255, 253, 246)        # lighter panel fill
INK = (26, 26, 26)            # near-black
FAINT = (110, 106, 96)        # secondary ink
CRIMSON = (172, 38, 28)       # war and justice kickers
DEEPBLUE = (28, 64, 116)      # diplomacy kicker
SEAGREEN = (16, 104, 100)     # climate and Europe kickers
EMBER = (150, 74, 22)         # energy kicker
LEAF = (30, 104, 64)          # climate accent
OCHRE = (178, 134, 30)        # chart and flag accents
PALE = (120, 170, 205)        # globe sea
SNOW = (255, 255, 255)


class Canvas:
    """An RGB pixel sheet with a handful of drawing tools."""

    def __init__(self, width, height, colour):
        self.w = width
        self.h = height
        self.buf = bytearray(colour * (width * height))

    def dot(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = colour

    def rect(self, x, y, w, h, colour):
        xa = max(0, x)
        ya = max(0, y)
        xb = min(self.w, x + w)
        yb = min(self.h, y + h)
        for yy in range(ya, yb):
            base = (yy * self.w + xa) * 3
            for xx in range(xa, xb):
                i = base + (xx - xa) * 3
                self.buf[i], self.buf[i + 1], self.buf[i + 2] = colour

    def frame(self, x, y, w, h, colour, thick=1):
        self.rect(x, y, w, thick, colour)
        self.rect(x, y + h - thick, w, thick, colour)
        self.rect(x, y, thick, h, colour)
        self.rect(x + w - thick, y, thick, h, colour)

    def hrule(self, x, y, length, colour, thick=1):
        self.rect(x, y, length, thick, colour)

    def vrule(self, x, y, length, colour, thick=1):
        self.rect(x, y, thick, length, colour)

    def segment(self, x0, y0, x1, y1, colour, thick=1):
        """Bresenham line, thickened by stamping small squares."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.rect(x - thick // 2, y - thick // 2, thick, thick, colour)
            if x == x1 and y == y1:
                break
            step = 2 * err
            if step >= dy:
                err += dy
                x += sx
            if step <= dx:
                err += dx
                y += sy

    def blob(self, cx, cy, r, colour):
        """A filled disc, drawn one row at a time."""
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            half = int((r * r - dy * dy) ** 0.5)
            self.rect(cx - half, yy, half * 2 + 1, 1, colour)

    def halo(self, cx, cy, r, colour, thick=2):
        """A ring: the disc of radius r minus the disc inside it."""
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            outer = int((r * r - dy * dy) ** 0.5)
            inner = int(max(0, (r - thick) ** 2 - dy * dy) ** 0.5)
            self.rect(cx - outer, yy, outer - inner, 1, colour)
            self.rect(cx + inner + 1, yy, outer - inner, 1, colour)


# -------------------------------------------------------------- pixel type
# A 5 by 7 bitmap font, drawn by hand. '#' is ink, '.' is empty. Only
# the characters this front page needs are defined here.

GLYPHS = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "00100", "00100", "00100"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "01100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '%': ("11001", "11010", "00100", "01000", "10011", "10011", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00001", "00010", "00100", "01000", "10000", "10000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    '*': ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
}

GW = 5
GH = 7


def measure(text, scale):
    """Pixel width of a string at a scale, one pixel gap per glyph."""
    return len(text) * (GW * scale + scale) - scale


def put_text(page, x, y, text, scale, colour, align="left"):
    """Draw one line of text; align left, centre or right on x."""
    width = measure(text, scale)
    if align == "center":
        x -= width // 2
    elif align == "right":
        x -= width
    cx = x
    for ch in text:
        glyph = GLYPHS.get(ch, GLYPHS[' '])
        for row in range(GH):
            bits = glyph[row]
            for col in range(GW):
                if bits[col] == '1':
                    page.rect(cx + col * scale, y + row * scale,
                              scale, scale, colour)
        cx += GW * scale + scale
    return width


def flow(text, max_width, scale):
    """Greedy word wrap; returns the lines that fit inside max_width."""
    words = text.split(' ')
    lines = []
    current = ''
    for word in words:
        trial = word if not current else current + ' ' + word
        if measure(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ------------------------------------------------------------ PNG writer

def _piece(kind, data):
    out = struct.pack('>I', len(data)) + kind + data
    out += struct.pack('>I', crc32(kind + data) & 0xFFFFFFFF)
    return out


def png_bytes(page):
    """Encode the page as a PNG: 8-bit RGB, one filter byte per row."""
    raw = bytearray()
    for y in range(page.h):
        raw.append(0)  # filter: none
        start = (y * page.w) * 3
        raw += page.buf[start:start + page.w * 3]
    ihdr = struct.pack('>IIBBBBB', page.w, page.h, 8, 2, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n'
    png += _piece(b'IHDR', ihdr)
    png += _piece(b'IDAT', zlib.compress(bytes(raw), 9))
    png += _piece(b'IEND', b'')
    return png


# ---------------------------------------------------------- illustrations

def art_missile(page, x, y, w, h):
    """A missile streaking down at an angle, bursting at its tip."""
    page.segment(x + 12, y + 8, x + w // 2, y + h - 30, INK, 3)
    page.segment(x + w // 2, y + h - 30, x + w // 2 - 14, y + h - 44, INK, 3)
    page.segment(x + w // 2, y + h - 30, x + w // 2 + 14, y + h - 44, INK, 3)
    bx, by = x + w // 2, y + h - 22
    for dx, dy in ((0, -12), (10, -8), (13, 0), (10, 8), (0, 12),
                   (-10, 8), (-13, 0), (-10, -8)):
        page.segment(bx, by, bx + dx, by + dy, CRIMSON, 3)
    page.blob(bx, by, 5, CRIMSON)
    page.blob(x + w - 26, y + 12, 4, OCHRE)
    page.blob(x + w - 46, y + 26, 3, OCHRE)


def art_clock(page, x, y, w, h):
    """A clock running past the hour: talks in overtime."""
    cx, cy = x + w // 2 - 60, y + h // 2
    r = h // 2 - 10
    page.blob(cx, cy, r, SNOW)
    page.halo(cx, cy, r, INK, 2)
    page.blob(cx, cy, 3, INK)
    page.segment(cx, cy, cx, cy - r + 8, INK, 3)
    page.segment(cx, cy, cx + r - 12, cy + 6, INK, 3)
    page.segment(cx - r + 6, cy - 6, cx - r + 14, cy - 6, CRIMSON, 2)
    page.segment(cx + r - 14, cy + 6, cx + r - 6, cy + 6, CRIMSON, 2)
    sx = x + w - 90
    page.rect(sx, cy - 20, 30, 40, LEAF)
    page.rect(sx + 34, cy - 20, 30, 40, SEAGREEN)
    page.vrule(sx + 15, cy - 26, 6, FAINT, 2)
    page.vrule(sx + 49, cy - 26, 6, FAINT, 2)
    page.segment(sx - 8, cy + 28, sx + 72, cy - 32, CRIMSON, 4)


def art_table(page, x, y, w, h):
    """Four flags on poles above a round negotiating table."""
    cols = [DEEPBLUE, CRIMSON, OCHRE, LEAF]
    for i, col in enumerate(cols):
        px = x + 30 + i * (w - 60) // 3
        page.vrule(px, y + 6, h - 40, INK, 3)
        page.rect(px + 3, y + 6, 30, 18, col)
        page.rect(px + 3, y + 24, 30, 3, SNOW)
    page.hrule(x + 8, y + h - 26, w - 16, INK, 3)
    page.rect(x + w // 2 - 30, y + h - 22, 60, 4, INK)
    page.blob(x + w // 2, y + h - 14, 4, INK)


def art_scales(page, x, y, w, h):
    """Scales of justice: post, beam, two pans, base."""
    cx = x + w // 2
    page.vrule(cx, y + 6, h - 26, INK, 3)
    page.hrule(x + 14, y + 12, w - 28, INK, 3)
    page.blob(cx, y + 10, 4, INK)
    for side in (-1, 1):
        px = cx + side * (w // 2 - 20)
        page.segment(px, y + 12, px - 16, y + 40, INK, 2)
        page.segment(px, y + 12, px + 16, y + 40, INK, 2)
        page.hrule(px - 16, y + 40, 32, INK, 2)
        page.segment(px - 14, y + 40, px - 8, y + 52, INK, 2)
        page.segment(px + 14, y + 40, px + 8, y + 52, INK, 2)
        page.hrule(px - 8, y + 52, 16, INK, 2)
    page.hrule(cx - 26, y + h - 16, 52, INK, 3)
    page.hrule(cx - 34, y + h - 10, 68, INK, 3)


def art_bridge(page, x, y, w, h):
    """A bridge arc between two towers, stars above it."""
    x0, x1 = x + 20, x + w - 20
    base = y + h - 14
    for i in range(25):
        t = i / 24
        px = int(x0 + (x1 - x0) * t)
        py = int(base - 26 * (1 - (2 * t - 1) ** 2))
        page.blob(px, py, 3, DEEPBLUE)
    page.vrule(x + 26, base - 34, 34, INK, 3)
    page.vrule(x + w - 29, base - 34, 34, INK, 3)
    page.hrule(x + 8, base, w - 16, INK, 3)
    for sx, sy in ((x + w // 2 - 70, y + 6), (x + w // 2, y + 2),
                   (x + w // 2 + 70, y + 6)):
        page.blob(sx, sy, 3, OCHRE)
        page.segment(sx - 6, sy, sx + 6, sy, OCHRE, 2)
        page.segment(sx, sy - 6, sx, sy + 6, OCHRE, 2)


def art_tanker(page, x, y, w, h):
    """An oil tanker with flames at its stack, on a wavy sea."""
    cx = x + w // 2
    page.rect(cx - 70, y + 26, 140, 24, EMBER)
    page.rect(cx - 70, y + 26, 140, 4, INK)
    page.rect(cx + 44, y + 6, 20, 20, INK)
    page.rect(cx + 48, y + 10, 12, 12, SNOW)
    bx, by = cx + 54, y + 2
    for dx, dy in ((0, -10), (8, -6), (10, 2), (4, 8), (-4, 8),
                   (-10, 2), (-8, -6)):
        page.segment(bx, by, bx + dx, by + dy, CRIMSON, 3)
    page.blob(bx, by, 4, CRIMSON)
    page.hrule(x + 10, y + h - 18, w - 20, PALE, 3)
    page.hrule(x + 30, y + h - 10, w - 60, PALE, 3)
    page.blob(x + 24, y + 12, 4, OCHRE)
    page.blob(x + w - 24, y + 20, 3, OCHRE)


ART = {
    'missile': art_missile,
    'clock': art_clock,
    'table': art_table,
    'scales': art_scales,
    'bridge': art_bridge,
    'tanker': art_tanker,
}


# ------------------------------------------------------------ the stories

# kicker, kicker colour, headline, body, illustration key
STORIES = [
    ("WARSAW - WAR", CRIMSON,
     "RUSSIAN MISSILES CRASH IN POLAND",
     "Moscow fires 400 drones and 110 missiles at Ukraine. At least 8 "
     "are killed, Kyiv bridges are hit. Warsaw calls it provocation.",
     'missile'),
    ("ANTALYA - CLIMATE", LEAF,
     "COP31 TALKS STALL IN OVERTIME",
     "The Antalya climate summit runs past its deadline with no deal. "
     "The draft drops any call to phase out fossil fuels.",
     'clock'),
    ("WASHINGTON - DIPLOMACY", DEEPBLUE,
     "PEACE TALKS EDGE FORWARD",
     "US envoys say Moscow has agreed to a multilateral format with "
     "Europe at the table. Zelenskyy presses for talks to start soon.",
     'table'),
    ("YANGON - JUSTICE", CRIMSON,
     "MYANMAR REJECTS GENOCIDE RULING",
     "Myanmar calls the world court verdict biased after the court "
     "found it committed genocide against the Rohingya.",
     'scales'),
    ("LONDON - EUROPE", SEAGREEN,
     "UK AND EU STRIKE LANDMARK DEAL",
     "Britain and the EU agree youth mobility, farm trade and carbon "
     "market deals in a landmark post-Brexit reset.",
     'bridge'),
    ("HORMUZ - ENERGY", EMBER,
     "TANKER STRUCK IN STRAIT OF HORMUZ",
     "A tanker is hit and left burning in the Strait of Hormuz, the "
     "world's busiest oil chokepoint. No crew are reported hurt.",
     'tanker'),
]


# ------------------------------------------------------------------ layout

MARGIN = 24
PW = 472
PH = 268
GAP = 16
TOP = 152


def masthead(page):
    page.hrule(MARGIN, 22, W - 2 * MARGIN, INK, 2)
    put_text(page, W // 2, 38, "THE WORLD IN ONE IMAGE", 7, INK,
             align="center")
    put_text(page, W // 2, 100, "SATURDAY 21 NOVEMBER 2026", 3, CRIMSON,
             align="center")
    put_text(page, W // 2, 126, "SIX STORIES FROM AROUND THE WORLD",
             2, FAINT, align="center")
    page.hrule(MARGIN, 146, W - 2 * MARGIN, INK, 4)


def panel(page, story, px, py):
    kicker, colour, headline, body, art = story
    page.rect(px, py, PW, PH, CARD)
    page.frame(px, py, PW, PH, INK, 2)
    # Kicker band.
    page.rect(px + 2, py + 2, PW - 4, 28, colour)
    put_text(page, px + 14, py + 10, kicker, 2, SNOW)
    # Headline, wrapped to two lines at most.
    inner = PW - 28
    lines = flow(headline, inner, 3)
    hy = py + 44
    for line in lines[:2]:
        put_text(page, px + 14, hy, line, 3, INK)
        hy += 24
    # Body copy (the font is capitals only, so the copy is set in caps).
    by = hy + 6
    for line in flow(body.upper(), inner, 2)[:4]:
        put_text(page, px + 14, by, line, 2, INK)
        by += 17
    # Illustration strip along the bottom of the panel.
    art_top = py + PH - 78
    page.hrule(px + 14, art_top - 8, PW - 28, FAINT, 1)
    ART[art](page, px + 14, art_top, PW - 28, 70)


def footer(page):
    page.hrule(MARGIN, 994, W - 2 * MARGIN, INK, 2)
    put_text(page, W // 2, 1000,
             "THE WORLD IN ONE IMAGE - SATURDAY 21 NOVEMBER 2026",
             1, FAINT, align="center")


def build():
    page = Canvas(W, H, NEWSprint)
    page.frame(8, 8, W - 16, H - 16, INK, 2)
    masthead(page)
    for i, story in enumerate(STORIES):
        col = i % 2
        row = i // 2
        px = MARGIN + col * (PW + GAP)
        py = TOP + row * (PH + GAP)
        panel(page, story, px, py)
    footer(page)
    return page


def main():
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(build())
    path = os.path.join(out_dir, 'entry.png')
    with open(path, 'wb') as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes)")


if __name__ == '__main__':
    main()
