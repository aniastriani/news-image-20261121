"""The World in One Image - Saturday 21 November 2026.

A newspaper front page drawn entirely in code: a hand-built 5x7 pixel
font, a tiny RGB canvas, and a from-scratch PNG writer. Pure Python
standard library, no network, no clock, no randomness, no files read
at run time. The output is a deterministic 1024x1024 PNG.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

PAPER = (250, 246, 236)
INK = (22, 22, 22)
PANEL = (255, 255, 255)
RULE = (30, 30, 30)
RED = (158, 28, 28)

# ---------------------------------------------------------------------------
# Hand-drawn 5x7 bitmap font. Each glyph is seven rows of five cells;
# "#" is ink, "." is empty. Drawn by hand for this page.
# ---------------------------------------------------------------------------

FONT = {
    "A": (
        ".###.",
        "#...#",
        "#...#",
        "#####",
        "#...#",
        "#...#",
        "#...#",
    ),
    "B": (
        "####.",
        "#...#",
        "#...#",
        "####.",
        "#...#",
        "#...#",
        "####.",
    ),
    "C": (
        ".####",
        "#....",
        "#....",
        "#....",
        "#....",
        "#....",
        ".####",
    ),
    "D": (
        "####.",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "####.",
    ),
    "E": (
        "#####",
        "#....",
        "#....",
        "####.",
        "#....",
        "#....",
        "#####",
    ),
    "F": (
        "#####",
        "#....",
        "#....",
        "####.",
        "#....",
        "#....",
        "#....",
    ),
    "G": (
        ".####",
        "#....",
        "#....",
        "#.###",
        "#...#",
        "#...#",
        ".###.",
    ),
    "H": (
        "#...#",
        "#...#",
        "#...#",
        "#####",
        "#...#",
        "#...#",
        "#...#",
    ),
    "I": (
        "#####",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "#####",
    ),
    "J": (
        "..###",
        "...#.",
        "...#.",
        "...#.",
        "...#.",
        "#..#.",
        ".##..",
    ),
    "K": (
        "#...#",
        "#..#.",
        "#.#..",
        "##...",
        "#.#..",
        "#..#.",
        "#...#",
    ),
    "L": (
        "#....",
        "#....",
        "#....",
        "#....",
        "#....",
        "#....",
        "#####",
    ),
    "M": (
        "#...#",
        "##.##",
        "#.#.#",
        "#.#.#",
        "#...#",
        "#...#",
        "#...#",
    ),
    "N": (
        "#...#",
        "##..#",
        "##..#",
        "#.#.#",
        "#..##",
        "#..##",
        "#...#",
    ),
    "O": (
        ".###.",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        ".###.",
    ),
    "P": (
        "####.",
        "#...#",
        "#...#",
        "####.",
        "#....",
        "#....",
        "#....",
    ),
    "Q": (
        ".###.",
        "#...#",
        "#...#",
        "#...#",
        "#.#.#",
        "#..#.",
        ".##.#",
    ),
    "R": (
        "####.",
        "#...#",
        "#...#",
        "####.",
        "#.#..",
        "#..#.",
        "#...#",
    ),
    "S": (
        ".####",
        "#....",
        "#....",
        ".###.",
        "....#",
        "....#",
        "####.",
    ),
    "T": (
        "#####",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
    ),
    "U": (
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        ".###.",
    ),
    "V": (
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        ".#.#.",
        "..#..",
    ),
    "W": (
        "#...#",
        "#...#",
        "#...#",
        "#.#.#",
        "#.#.#",
        "##.##",
        "#...#",
    ),
    "X": (
        "#...#",
        "#...#",
        ".#.#.",
        "..#..",
        ".#.#.",
        "#...#",
        "#...#",
    ),
    "Y": (
        "#...#",
        "#...#",
        ".#.#.",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
    ),
    "Z": (
        "#####",
        "....#",
        "...#.",
        "..#..",
        ".#...",
        "#....",
        "#####",
    ),
}

FONT.update({
    "0": (
        ".###.",
        "#..##",
        "#.#.#",
        "##..#",
        "#...#",
        "#...#",
        ".###.",
    ),
    "1": (
        "..#..",
        ".##..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        ".###.",
    ),
    "2": (
        ".###.",
        "#...#",
        "....#",
        "...#.",
        "..#..",
        ".#...",
        "#####",
    ),
    "3": (
        "####.",
        "....#",
        "....#",
        ".###.",
        "....#",
        "....#",
        "####.",
    ),
    "4": (
        "...#.",
        "..##.",
        ".#.#.",
        "#..#.",
        "#####",
        "...#.",
        "...#.",
    ),
    "5": (
        "#####",
        "#....",
        "####.",
        "....#",
        "....#",
        "#...#",
        ".###.",
    ),
    "6": (
        ".###.",
        "#....",
        "#....",
        "####.",
        "#...#",
        "#...#",
        ".###.",
    ),
    "7": (
        "#####",
        "....#",
        "...#.",
        "...#.",
        "..#..",
        "..#..",
        "..#..",
    ),
    "8": (
        ".###.",
        "#...#",
        "#...#",
        ".###.",
        "#...#",
        "#...#",
        ".###.",
    ),
    "9": (
        ".###.",
        "#...#",
        "#...#",
        ".####",
        "....#",
        "....#",
        ".###.",
    ),
    " ": (
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
    ),
    ".": (
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
        "..#..",
    ),
    ",": (
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
        "..#..",
        "..#..",
        ".#...",
    ),
    ":": (
        ".....",
        "..#..",
        ".....",
        ".....",
        ".....",
        "..#..",
        ".....",
    ),
    ";": (
        ".....",
        "..#..",
        ".....",
        ".....",
        ".....",
        "..#..",
        "..#..",
        ".#...",
    ),
    "'": (
        "..#..",
        "..#..",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
    ),
    "-": (
        ".....",
        ".....",
        ".....",
        ".###.",
        ".....",
        ".....",
        ".....",
    ),
    "!": (
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        ".....",
        "..#..",
    ),
    "?": (
        ".###.",
        "#...#",
        "....#",
        "...#.",
        "..#..",
        ".....",
        "..#..",
    ),
    "(": (
        "...#.",
        "..#..",
        ".#...",
        ".#...",
        ".#...",
        "..#..",
        "...#.",
    ),
    ")": (
        ".#...",
        "..#..",
        "...#.",
        "...#.",
        "...#.",
        "..#..",
        ".#...",
    ),
    "/": (
        "....#",
        "....#",
        "...#.",
        "...#.",
        "..#..",
        ".#...",
        "#....",
    ),
    "&": (
        ".##..",
        "#..#.",
        "#.#..",
        ".#...",
        "#.#.#",
        "#..#.",
        ".##.#",
    ),
    "%": (
        "##..#",
        "##.#.",
        "...#.",
        "..#..",
        ".#...",
        "#.##.",
        "#..##",
    ),
    "+": (
        ".....",
        "..#..",
        "..#..",
        ".###.",
        "..#..",
        "..#..",
        ".....",
    ),
    "=": (
        ".....",
        ".....",
        ".###.",
        ".....",
        ".###.",
        ".....",
        ".....",
    ),
    '"': (
        ".#.#.",
        ".#.#.",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
    ),
    "*": (
        ".....",
        ".#.#.",
        "..#..",
        ".###.",
        "..#..",
        ".#.#.",
        ".....",
    ),
})


# ---------------------------------------------------------------------------
# Canvas: a plain RGB pixel buffer with rectangle and text drawing.
# ---------------------------------------------------------------------------

class Canvas:
    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(colour * (width * height))

    def set_pixel(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i] = colour[0]
            self.pixels[i + 1] = colour[1]
            self.pixels[i + 2] = colour[2]

    def fill_rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        for yy in range(y0, y1):
            base = (yy * self.width + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.pixels[i] = colour[0]
                self.pixels[i + 1] = colour[1]
                self.pixels[i + 2] = colour[2]

    def frame_rect(self, x, y, w, h, colour, thick=2):
        self.fill_rect(x, y, w, thick, colour)
        self.fill_rect(x, y + h - thick, w, thick, colour)
        self.fill_rect(x, y, thick, h, colour)
        self.fill_rect(x + w - thick, y, thick, h, colour)

    def disc(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                    self.set_pixel(xx, yy, colour)

    def line(self, x0, y0, x1, y1, colour):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.set_pixel(x, y, colour)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy


def text_width(text, scale):
    return len(text) * 6 * scale


def draw_text(canvas, x, y, text, scale, colour):
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "#":
                    canvas.fill_rect(
                        cx + col * scale, y + row * scale, scale, scale, colour
                    )
        cx += 6 * scale


def draw_text_centred(canvas, cx, y, text, scale, colour):
    draw_text(canvas, cx - text_width(text, scale) // 2, y, text, scale, colour)


def wrap_text(text, max_chars):
    """Greedy word wrap into lines of at most max_chars characters."""
    lines = []
    for chunk in text.split("\n"):
        words = chunk.split(" ")
        current = ""
        for word in words:
            if not current:
                current = word
            elif len(current) + 1 + len(word) <= max_chars:
                current += " " + word
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# PNG writer: raw RGB rows, filter byte 0 per row, zlib, CRC-checked chunks.
# ---------------------------------------------------------------------------

def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)
        start = y * stride
        raw += canvas.pixels[start:start + stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(
        b"IHDR",
        struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0),
    )
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


# ---------------------------------------------------------------------------
# Small drawn illustrations, one per story, along the bottom of each panel.
# Each gets the panel's inner box (x, y, width, height) to draw inside.
# ---------------------------------------------------------------------------

SKY = (214, 230, 240)
SEA = (52, 110, 150)
DARK = (40, 40, 44)
FLAME = (232, 120, 24)
SMOKE = (120, 120, 118)
LEAF = (46, 130, 80)
GOLD = (214, 164, 32)


def scene_missiles(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, SKY)
    cv.fill_rect(x, y + h - 22, w, 22, (96, 110, 96))
    cv.disc(x + w - 52, y + 20, 13, GOLD)
    for sx, sy, ln in ((x + 30, y + 14, 60), (x + 130, y + 8, 74), (x + 250, y + 18, 56)):
        cv.line(sx, sy, sx + ln, sy + 26, FLAME)
        cv.disc(sx + ln, sy + 26, 5, FLAME)
        cv.disc(sx + ln + 4, sy + 30, 3, SMOKE)
    cv.fill_rect(x + 40, y + h - 40, 26, 18, DARK)
    cv.fill_rect(x + 44, y + h - 48, 18, 8, DARK)


def scene_climate(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (222, 238, 226))
    cv.disc(x + w // 2, y + h // 2 + 4, 26, LEAF)
    cv.fill_rect(x + w // 2 - 26, y + h // 2 - 4, 52, 8, (222, 238, 226))
    cv.fill_rect(x + w // 2 - 4, y + h // 2 - 26, 8, 52, (222, 238, 226))
    cv.disc(x + 46, y + 18, 12, GOLD)
    for dx in (-8, 0, 8):
        cv.line(x + w - 46 + dx, y + h - 12, x + w - 46 + dx, y + h - 34, LEAF)
    cv.disc(x + w - 46, y + h - 40, 7, LEAF)


def scene_talks(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (224, 230, 242))
    cv.fill_rect(x + 30, y + h - 30, w - 60, 8, (120, 84, 50))
    cv.fill_rect(x + 30, y + h - 38, w - 60, 8, (150, 108, 62))
    for i, col in enumerate(((28, 64, 140), (158, 28, 28), (34, 120, 70))):
        fx = x + 60 + i * 130
        cv.fill_rect(fx, y + 12, 54, 34, col)
        cv.fill_rect(fx, y + 12, 54, 6, (255, 255, 255))
        cv.line(fx + 27, y + 12, fx + 27, y + h - 38, DARK)
    cv.disc(x + w // 2, y + 22, 9, GOLD)


def scene_court(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (232, 228, 240))
    cv.fill_rect(x + w // 2 - 3, y + 10, 6, h - 26, DARK)
    cv.fill_rect(x + w // 2 - 40, y + h - 16, 80, 6, DARK)
    cv.line(x + w // 2 - 70, y + 16, x + w // 2 - 70, y + 44, DARK)
    cv.line(x + w // 2 + 70, y + 16, x + w // 2 + 70, y + 44, DARK)
    cv.line(x + w // 2 - 70, y + 16, x + w // 2, y + 10, DARK)
    cv.line(x + w // 2 + 70, y + 16, x + w // 2, y + 10, DARK)
    cv.disc(x + w // 2 - 70, y + 48, 14, GOLD)
    cv.disc(x + w // 2 + 70, y + 48, 14, GOLD)
    cv.fill_rect(x + w // 2 - 84, y + 34, 28, 4, GOLD)
    cv.fill_rect(x + w // 2 + 56, y + 34, 28, 4, GOLD)


def scene_deal(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (222, 238, 236))
    cv.fill_rect(x, y + h - 20, w, 20, (140, 170, 190))
    # Arched bridge: deck, arch, and suspension ticks.
    cv.fill_rect(x + 16, y + h - 34, w - 32, 6, DARK)
    for i in range(9):
        t = i / 8.0
        bx = x + 24 + int(t * (w - 48))
        arch_y = y + h - 34 - int(26 * (1 - (2 * t - 1) ** 2))
        cv.line(bx, arch_y, bx, y + h - 34, DARK)
    cv.disc(x + w // 2, y + 16, 10, GOLD)
    for dx, dy in ((-46, 8), (46, 8), (-70, 26), (70, 26)):
        cv.disc(x + w // 2 + dx, y + 26 + dy, 4, (28, 64, 140))


def scene_tanker(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (238, 226, 204))
    cv.fill_rect(x, y + h - 30, w, 30, SEA)
    cv.fill_rect(x + 40, y + h - 52, w - 120, 22, DARK)
    cv.fill_rect(x + w - 110, y + h - 74, 30, 22, (200, 200, 200))
    cv.line(x + w - 95, y + h - 74, x + w - 95, y + h - 96, DARK)
    for fx, fy, fr in ((x + 90, y + h - 58, 12), (x + 130, y + h - 66, 9), (x + 160, y + h - 56, 7)):
        cv.disc(fx, fy, fr, FLAME)
        cv.disc(fx, fy - fr - 6, fr // 2, SMOKE)
    cv.fill_rect(x + 20, y + h - 18, 60, 4, (255, 255, 255))
    cv.fill_rect(x + w - 90, y + h - 12, 70, 4, (255, 255, 255))


# ---------------------------------------------------------------------------
# The six stories, written for Saturday 21 November 2026.
# ---------------------------------------------------------------------------

STORIES = [
    {
        "kicker": "WARSAW / WAR",
        "colour": (158, 28, 28),
        "headline": "MISSILES CRASH IN POLAND AS RUSSIA POUNDS UKRAINE",
        "body": "TWO RUSSIAN MISSILES AND A DRONE CAME DOWN IN SOUTH-EAST POLAND "
                "DURING A HUGE OVERNIGHT BARRAGE ON UKRAINE. MORE THAN 400 DRONES "
                "AND 110 MISSILES WERE FIRED, AT LEAST EIGHT PEOPLE WERE KILLED, "
                "AND POWER WAS CUT IN ELEVEN REGIONS. WARSAW CALLED IT A DELIBERATE "
                "PROVOCATION, AND NATO CHIEF MARK RUTTE HEADS TO WARSAW TODAY.",
        "scene": scene_missiles,
    },
    {
        "kicker": "ANTALYA / CLIMATE",
        "colour": (34, 120, 70),
        "headline": "CLIMATE TALKS STALL IN ANTALYA AS FOSSIL FUELS VANISH FROM DRAFT",
        "body": "THE COP31 CLIMATE TALKS IN ANTALYA HAVE SLIPPED INTO OVERTIME WITH "
                "NO DEAL IN SIGHT. THE LATEST DRAFT MAKES NO MENTION OF FOSSIL "
                "FUELS AT ALL, AND NEGOTIATORS FROM NEARLY 200 COUNTRIES REMAIN "
                "DEADLOCKED. A NEW TEXT IS PROMISED FOR SATURDAY MORNING.",
        "scene": scene_climate,
    },
    {
        "kicker": "WASHINGTON / DIPLOMACY",
        "colour": (28, 64, 140),
        "headline": "PEACE TALKS EDGE FORWARD AS MOSCOW AGREES TO A WIDER TABLE",
        "body": "UNITED STATES ENVOYS SAY TALKS TO END THE WAR IN UKRAINE ARE "
                "EDGING FORWARD. MOSCOW HAS AGREED TO A MULTILATERAL FORMAT WITH "
                "EUROPE AT THE TABLE, AND PRESIDENT ZELENSKYY IS PRESSING FOR "
                "NEGOTIATIONS TO START SOON.",
        "scene": scene_talks,
    },
    {
        "kicker": "YANGON / JUSTICE",
        "colour": (96, 50, 140),
        "headline": "MYANMAR REJECTS WORLD COURT GENOCIDE RULING AS UNFAIR",
        "body": "MYANMAR HAS REJECTED THE WORLD COURT RULING THAT FOUND IT "
                "RESPONSIBLE FOR GENOCIDE AGAINST THE ROHINGYA, CALLING THE "
                "DECISION UNFAIR. THE COURT RULED BY NINE VOTES TO SIX OVER THE "
                "2017 CRACKDOWN IN RAKHINE STATE.",
        "scene": scene_court,
    },
    {
        "kicker": "LONDON / EUROPE",
        "colour": (14, 110, 120),
        "headline": "UK AND EU SEAL LANDMARK POST-BREXIT RESET DEAL",
        "body": "BRITAIN AND THE EUROPEAN UNION HAVE STRUCK A LANDMARK POST-BREXIT "
                "DEAL AT A SUMMIT IN BRUSSELS. IT OPENS YOUTH MOBILITY FOR 100,000 "
                "YOUNG PEOPLE, EASES FARM TRADE, AND LINKS THE TWO CARBON MARKETS.",
        "scene": scene_deal,
    },
    {
        "kicker": "HORMUZ / ENERGY",
        "colour": (176, 84, 16),
        "headline": "TANKER STRUCK AND LEFT BURNING IN THE STRAIT OF HORMUZ",
        "body": "A TANKER WAS STRUCK BY A PROJECTILE AND CAUGHT FIRE WHILE SAILING "
                "THROUGH THE STRAIT OF HORMUZ, THE WORLD'S BUSIEST OIL CHOKEPOINT. "
                "NO CASUALTIES WERE REPORTED, BUT THE ATTACK ADDS TO A WAVE OF "
                "STRIKES ON SHIPPING IN THE WATERWAY.",
        "scene": scene_tanker,
    },
]


# ---------------------------------------------------------------------------
# Page layout.
# ---------------------------------------------------------------------------

def draw_panel(cv, story, px, py, pw, ph):
    cv.fill_rect(px, py, pw, ph, PANEL)
    cv.frame_rect(px, py, pw, ph, RULE, 2)
    # Kicker band.
    cv.fill_rect(px + 2, py + 2, pw - 4, 30, story["colour"])
    draw_text(cv, px + 14, py + 10, story["kicker"], 2, (255, 255, 255))
    # Headline, two lines at scale 2.
    inner_w = pw - 28
    head_lines = wrap_text(story["headline"], inner_w // 12)
    hy = py + 42
    for line in head_lines[:2]:
        draw_text(cv, px + 14, hy, line, 2, INK)
        hy += 17
    cv.fill_rect(px + 14, hy + 2, inner_w, 2, story["colour"])
    # Body at scale 1.
    body_lines = wrap_text(story["body"], inner_w // 6)
    by = hy + 12
    for line in body_lines[:6]:
        draw_text(cv, px + 14, by, line, 1, INK)
        by += 10
    # Illustration along the bottom, taller so panels feel full.
    ix = px + 14
    iy = py + ph - 100
    iw = pw - 28
    ih = 86
    story["scene"](cv, ix, iy, iw, ih)
    cv.frame_rect(ix, iy, iw, ih, RULE, 1)


def draw_page():
    cv = Canvas(WIDTH, HEIGHT, PAPER)
    # Masthead.
    draw_text_centred(cv, WIDTH // 2, 30, "THE WORLD IN ONE IMAGE", 5, INK)
    cv.fill_rect(24, 74, WIDTH - 48, 3, RED)
    draw_text_centred(cv, WIDTH // 2, 86, "SATURDAY 21 NOVEMBER 2026", 2, RED)
    draw_text_centred(
        cv, WIDTH // 2, 112, "SIX STORIES THAT SHAPED THE WORLD TODAY", 1, INK
    )
    cv.fill_rect(24, 128, WIDTH - 48, 3, RULE)
    cv.fill_rect(24, 134, WIDTH - 48, 1, RULE)
    # Story grid: 2 columns x 3 rows.
    grid_x, grid_y = 24, 146
    gap = 10
    pw = (WIDTH - 2 * grid_x - gap) // 2
    ph = (968 - grid_y - 2 * gap) // 3
    for i, story in enumerate(STORIES):
        col = i % 2
        row = i // 2
        px = grid_x + col * (pw + gap)
        py = grid_y + row * (ph + gap)
        draw_panel(cv, story, px, py, pw, ph)
    # Footer.
    cv.fill_rect(24, 978, WIDTH - 48, 2, RULE)
    draw_text_centred(
        cv,
        WIDTH // 2,
        988,
        "THE WORLD IN ONE IMAGE - SATURDAY 21 NOVEMBER 2026 - SIX STORIES, ONE PAGE",
        1,
        INK,
    )
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    page = draw_page()
    write_png(page, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
