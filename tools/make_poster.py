"""Build entry.png: Thursday 26 November 2026's world news on one 1024x1024 poster.

Usage (from the repository root):
    python tools/make_poster.py            # writes entry.png
    python tools/make_poster.py --preview  # also writes preview-300.png (300 px wide check)

Inputs: art/1.png .. art/5.png (text-free illustrations for lead stories 1-5).
Lead story 6 and every icon, map and all text are drawn here in code.
Needs Pillow and Arial Bold (C:\\Windows\\Fonts\\arialbd.ttf on Windows).
"""

from __future__ import annotations

import argparse
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_BOLD = os.environ.get("POSTER_FONT", r"C:\Windows\Fonts\arialbd.ttf")
FONT_REG = os.environ.get("POSTER_FONT_REG", r"C:\Windows\Fonts\arial.ttf")

W = H = 1024
M = 12  # outer margin

# Palette (matches the ChatGPT art: navy, red, cream, gold, teal)
NAVY = (19, 34, 63)
NAVY2 = (36, 56, 96)
RED = (200, 55, 45)
CREAM = (246, 238, 220)
PAPER = (252, 248, 238)
GOLD = (224, 165, 38)
TEAL = (42, 157, 143)
TEAL_D = (24, 104, 96)
GREY = (120, 128, 140)
INK = (24, 28, 36)

REGION_COL = {
    "AMERICAS": RED,
    "EUROPE": NAVY2,
    "MIDDLE EAST": GOLD,
    "AFRICA": (176, 98, 40),
    "ASIA": TEAL_D,
    "OCEANIA": TEAL,
    "SPACE": (90, 70, 150),
}

# ---------------------------------------------------------------- stories
# Section A: six lead stories (number, region, tag, headline <= 7 words, detail line)
LEADS = [
    (1, "AMERICAS", "USA · TRADE", "US proposes tariffs on 14 trading partners",
     "Vietnam up to 35% · open to comment until 5 Jan"),
    (2, "AFRICA", "EGYPT", "Cairo fuel tanker fire kills at least 31",
     "21 injured in Warraq after a power cable fell"),
    (3, "MIDDLE EAST", "SAUDI ARABIA · GULF", "Houthis claim strikes on Saudi refinery, Riyadh",
     "Ras Tanura · 2+ ships hit mines in Hormuz"),
    (4, "SPACE", "SPACE · TECH", "US lets SpaceX launch up to 1M satellites",
     "As AI data centres in space · scientists sceptical"),
    (5, "MIDDLE EAST", "ISRAEL", "Judges urge dropping Netanyahu bribery case",
     "Case 4000 against Israel's prime minister"),
    (6, "OCEANIA", "AUSTRALIA · SOLOMON IS.", "Australia, Solomon Islands sign security treaty",
     "About $490m over 10 years"),
]

# Section B: thirteen tiles (number, region, tag, headline <= 6 words, icon)
TILES = [
    (7, "ASIA", "CHINA", "Xi ousts Shanghai party chief", "star_down"),
    (8, "ASIA", "N. KOREA", "Swiss top diplomat given 48h to leave", "hourglass"),
    (9, "ASIA", "N. KOREA", "Kim calls for wider tactical nukes", "missile"),
    (10, "EUROPE", "POLAND", "No-fly zone planned on eastern border", "noplane"),
    (11, "EUROPE", "UKRAINE", "30+ nations: Russia, stop CS gas", "gas"),
    (12, "EUROPE", "RUSSIA", "Record military budget; Merz warns", "bars"),
    (13, "EUROPE", "UKRAINE", "Ukraine hits Russian air base: 5 planes", "plane_hit"),
    (14, "AMERICAS", "COLOMBIA", "17-hour siege ends, 76 hostages freed", "cart"),
    (15, "AFRICA", "NIGERIA", "Meth lab raid: 1.5 tonnes, 5 Mexicans held", "flask"),
    (16, "AFRICA", "S. AFRICA", "Ramaphosa wins Phala Phala court case", "gavel"),
    (17, "EUROPE", "EU", "€50bn tech fund, Quantum Act proposed", "chip"),
    (18, "ASIA", "INDONESIA", "Java mine flood: 8 dead, 18 trapped", "helmet"),
    (19, "AMERICAS", "USA", "Storms hit US Thanksgiving travel", "storm"),
]

# Section C: "Also today" (number, one line)
ALSO = [
    (20, "Iraq jails 8 French nationals for life over ISIS"),
    (21, "Putin fires Murmansk governor amid probe"),
    (22, "Novaya Gazeta leaves Moscow, works from Riga"),
    (23, "Trump, NATO's Rutte discuss Ukraine and Iran"),
    (24, "Israel says it is ready to strike Iran without US"),
    (25, "Iowa: US Army blows up all its lead azide"),
    (26, "Puerto Rico top court scraps Luma power deal"),
    (27, "Australia braces for hotter El Niño summer"),
    (28, "ESA's Hera images crater on asteroid Dimorphos"),
    (29, "Stocks rebound, Stoxx 600 +1.4%; US closed"),
    (30, "Duran Duran guitarist Andy Taylor dies at 65"),
    (31, "NFL: Steelers cut quarterback Aaron Rodgers"),
]

# Map pins: number -> (lon, lat, badge dx, badge dy) in map pixels
PINS = {
    1: (-77.0, 38.9, -14, -12),
    19: (-96.0, 37.0, -6, 10),
    14: (-75.5, 10.4, 0, 10),
    17: (4.4, 50.8, -16, -10),
    10: (21.0, 52.2, -6, -16),
    11: (31.0, 49.5, 2, -14),
    12: (37.6, 55.8, 12, -12),
    2: (31.2, 30.0, -16, 4),
    5: (35.2, 31.8, 4, 12),
    3: (50.1, 26.6, 14, 4),
    15: (8.0, 9.5, -4, 12),
    16: (28.0, -26.0, 0, 12),
    7: (121.5, 31.2, 4, 12),
    8: (125.7, 39.0, -14, -12),
    9: (125.7, 39.0, 8, -14),
    18: (107.6, -6.9, -10, 10),
    6: (160.0, -9.4, 10, -10),
}

# ---------------------------------------------------------------- helpers


FONT_NARROW = os.environ.get("POSTER_FONT_NARROW", r"C:\Windows\Fonts\ARIALNB.TTF")


def font(size: int, bold=True) -> ImageFont.FreeTypeFont:
    """bold=True: Arial Bold, False: Arial, "narrow": Arial Narrow Bold."""
    path = FONT_NARROW if bold == "narrow" else (FONT_BOLD if bold else FONT_REG)
    return ImageFont.truetype(path, size)


def text_w(f: ImageFont.FreeTypeFont, s: str) -> float:
    return f.getlength(s)


def wrap(f, text: str, max_w: float) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(f, trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


FIT_LOG: list[tuple[str, int, int]] = []
# (what, where it ends, where the next thing starts): checked after build
LAYOUT: list[tuple[str, float, float]] = []


def fit(text: str, max_w: float, max_lines: int, size: int, min_size: int, bold=True):
    """Largest font size <= size whose wrap fits max_lines lines of max_w."""
    for s in range(size, min_size - 1, -1):
        f = font(s, bold)
        lines = wrap(f, text, max_w)
        if len(lines) <= max_lines and all(text_w(f, l) <= max_w for l in lines):
            FIT_LOG.append((text, s, size))
            return f, lines
    raise SystemExit(f"text does not fit at {min_size}px: {text!r}")


def supersampled(w: int, h: int, painter, scale: int = 4, bg=(0, 0, 0, 0)) -> Image.Image:
    """Paint at `scale`x on an RGBA canvas and downsample (anti-aliased shapes)."""
    big = Image.new("RGBA", (w * scale, h * scale), bg)
    painter(ImageDraw.Draw(big), scale, big)
    return big.resize((w, h), Image.LANCZOS)


def cover(img: Image.Image, w: int, h: int, focus_y: float = 0.5) -> Image.Image:
    """Resize to cover w x h, then crop; focus_y picks the vertical band kept."""
    s = max(w / img.width, h / img.height)
    r = img.resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.LANCZOS)
    x = (r.width - w) // 2
    y = int((r.height - h) * focus_y)
    return r.crop((x, y, x + w, y + h))


def badge(d: ImageDraw.ImageDraw, cx, cy, n: int, r=11, fill=RED, size=13):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill, outline=PAPER, width=2)
    f = font(size)
    d.text((cx, cy + 0.5), str(n), font=f, fill=(255, 255, 255), anchor="mm")


def pill(d, x, y, text, fill, size=12, pad=6, fg=(255, 255, 255)):
    f = font(size)
    tw = text_w(f, text)
    h = size + 6
    d.rounded_rectangle((x, y, x + tw + 2 * pad, y + h), radius=h // 2, fill=fill)
    d.text((x + pad, y + h / 2 + 0.5), text, font=f, fill=fg, anchor="lm")
    return x + tw + 2 * pad


# ---------------------------------------------------------------- story 6 art


def draw_story6(w: int, h: int) -> Image.Image:
    """Flat illustration: turquoise sea, islands, a grey patrol ship beside a small
    coastguard boat, and a dotted line from a landmass at the bottom edge."""

    def paint(d: ImageDraw.ImageDraw, k: int, big: Image.Image):
        W2, H2 = w * k, h * k
        d.rectangle((0, 0, W2, H2), fill=(38, 170, 170))
        # soft wave dashes
        for row in range(14):
            y = (row + 0.5) * H2 / 14
            off = (row % 2) * 60 * k
            for x in range(-80 * k + off, W2, 120 * k):
                d.arc((x, y - 6 * k, x + 40 * k, y + 6 * k), 200, 340, fill=(92, 200, 196), width=2 * k)

        def E(cx, cy, rx, ry, fill):
            d.ellipse(((cx - rx) * k, (cy - ry) * k, (cx + rx) * k, (cy + ry) * k), fill=fill)

        def island(blobs, palms):
            # blobs: (cx, cy, rx, ry) pieces of one irregular island
            for cx, cy, rx, ry in blobs:  # shallow-water ring
                E(cx, cy, rx + 6, ry + 5, (118, 212, 202))
            for cx, cy, rx, ry in blobs:  # sand
                E(cx, cy, rx, ry, CREAM)
            for cx, cy, rx, ry in blobs:  # forest, set off-centre so it never reads as an eye
                E(cx - rx * 0.15, cy - ry * 0.25, rx * 0.72, ry * 0.6, TEAL_D)
            for px, py in palms:
                E(px, py, 4.5, 4.5, (14, 78, 70))
                E(px + 3, py - 2, 3, 3, (30, 120, 100))

        island([(222, 46, 26, 11), (248, 52, 18, 9), (206, 54, 12, 6)], [(218, 43), (238, 47)])
        island([(286, 84, 20, 9), (304, 78, 12, 7)], [(286, 81)])
        island([(176, 40, 12, 5)], [(174, 38)])
        island([(300, 28, 10, 5)], [])

        # landmass along the bottom edge
        land = [(0, h), (0, h - 20), (30, h - 25), (70, h - 22), (110, h - 28), (150, h - 24), (190, h - 21),
                (230, h - 27), (275, h - 22), (w, h - 25), (w, h)]
        d.polygon([(x * k, y * k) for x, y in land], fill=GOLD)
        inner = [(0, h), (0, h - 9), (60, h - 13), (130, h - 15), (200, h - 11), (260, h - 9), (w, h - 12), (w, h)]
        d.polygon([(x * k, y * k) for x, y in inner], fill=(198, 132, 30))

        # dotted route from the landmass up to the islands
        def dots(p0, p1, n):
            for i in range(n + 1):
                t = i / n
                x = (p0[0] + (p1[0] - p0[0]) * t) * k
                y = (p0[1] + (p1[1] - p0[1]) * t) * k
                d.ellipse((x - 2 * k, y - 2 * k, x + 2 * k, y + 2 * k), fill=PAPER)

        dots((200, h - 24), (278, 96), 10)
        dots((270, 78), (248, 62), 4)

        # ships, seen from above, side by side heading right
        def hull(x, y, L, B, col, deck):
            pts = [(x, y - B / 2), (x + L * 0.78, y - B / 2), (x + L, y), (x + L * 0.78, y + B / 2), (x, y + B / 2)]
            d.polygon([((x + 4) * k, (y - B / 2) * k), ((x - L * 0.45) * k, (y - B * 1.3) * k),
                       ((x - L * 0.45) * k, (y + B * 1.3) * k), ((x + 4) * k, (y + B / 2) * k)],
                      fill=(150, 222, 214))  # wake
            d.polygon([(px * k, py * k) for px, py in pts], fill=col, outline=NAVY, width=k)
            d.rounded_rectangle(((x + L * 0.22) * k, (y - B * 0.3) * k, (x + L * 0.58) * k, (y + B * 0.3) * k),
                                radius=2 * k, fill=deck)

        # grey naval patrol vessel
        hull(70, 66, 118, 20, (150, 158, 166), NAVY)
        E(160, 66, 4, 4, NAVY)
        E(84, 66, 3, 3, NAVY)
        # small coastguard boat alongside (cream hull, red stripe)
        hull(92, 92, 58, 13, PAPER, (60, 80, 110))
        d.line((101 * k, 86 * k, 101 * k, 98 * k), fill=RED, width=3 * k)

    return supersampled(w, h, paint, scale=4, bg=(38, 170, 170, 255)).convert("RGB")


# ---------------------------------------------------------------- icons


def draw_icon(kind: str, s: int, col) -> Image.Image:
    def paint(d: ImageDraw.ImageDraw, k: int, big):
        S = s * k
        u = S / 40.0  # design grid 40x40

        def P(*xy):
            return [(xy[i] * u, xy[i + 1] * u) for i in range(0, len(xy), 2)]

        def box(x0, y0, x1, y1):
            return (x0 * u, y0 * u, x1 * u, y1 * u)

        if kind == "star_down":
            pts = []
            for i in range(10):
                a = -math.pi / 2 + i * math.pi / 5
                r = 13 if i % 2 == 0 else 5.5
                pts += [17 + r * math.cos(a), 16 + r * math.sin(a)]
            d.polygon(P(*pts), fill=RED)
            d.line(P(32, 8, 32, 32), fill=NAVY, width=int(4 * u))
            d.polygon(P(26, 28, 38, 28, 32, 37), fill=NAVY)
        elif kind == "hourglass":
            d.rectangle(box(9, 4, 31, 8), fill=NAVY)
            d.rectangle(box(9, 32, 31, 36), fill=NAVY)
            d.polygon(P(11, 8, 29, 8, 20, 20, 29, 32, 11, 32, 20, 20), fill=CREAM, outline=NAVY, width=int(2 * u))
            d.polygon(P(14, 11, 26, 11, 20, 18), fill=GOLD)
            d.polygon(P(20, 24, 27, 31, 13, 31), fill=GOLD)
        elif kind == "missile":
            d.polygon(P(17, 10, 23, 10, 23, 32, 17, 32), fill=NAVY)
            d.polygon(P(17, 10, 20, 2, 23, 10), fill=RED)
            d.polygon(P(17, 24, 11, 34, 17, 32), fill=RED)
            d.polygon(P(23, 24, 29, 34, 23, 32), fill=RED)
            d.polygon(P(18, 32, 22, 32, 20, 39), fill=GOLD)
        elif kind == "noplane":
            d.polygon(P(6, 22, 16, 19, 22, 8, 26, 8, 23, 19, 34, 18, 36, 14, 38, 14, 37, 22, 23, 24, 26, 34, 22, 34,
                        15, 25, 6, 25), fill=NAVY)
            d.ellipse(box(3, 3, 37, 37), outline=RED, width=int(4 * u))
            d.line(P(9, 9, 31, 31), fill=RED, width=int(4 * u))
        elif kind == "gas":
            for cx, cy, r in ((13, 22, 8), (22, 16, 10), (29, 23, 8), (20, 26, 8)):
                d.ellipse(box(cx - r, cy - r, cx + r, cy + r), fill=(170, 180, 186))
            d.line(P(8, 33, 32, 33), fill=GREY, width=int(2 * u))
            d.ellipse(box(14, 14, 26, 26), outline=RED, width=int(3 * u))
            d.line(P(16, 16, 24, 24), fill=RED, width=int(3 * u))
        elif kind == "bars":
            d.rectangle(box(6, 24, 13, 36), fill=NAVY2)
            d.rectangle(box(16, 16, 23, 36), fill=NAVY2)
            d.rectangle(box(26, 6, 33, 36), fill=RED)
            d.line(P(4, 37, 36, 37), fill=NAVY, width=int(2 * u))
        elif kind == "plane_hit":
            for i in range(12):
                a = i * math.pi / 6
                r = 12 if i % 2 == 0 else 6
                pass
            pts = []
            for i in range(16):
                a = i * math.pi / 8
                r = 13 if i % 2 == 0 else 7
                pts += [26 + r * math.cos(a), 14 + r * math.sin(a)]
            d.polygon(P(*pts), fill=GOLD)
            d.ellipse(box(21, 9, 31, 19), fill=RED)
            d.polygon(P(4, 30, 14, 27, 19, 18, 22, 18, 20, 27, 30, 26, 32, 23, 34, 23, 33, 30, 20, 31, 22, 38, 19, 38,
                        13, 32, 4, 33), fill=NAVY)
        elif kind == "cart":
            d.line(P(3, 7, 9, 7, 13, 27, 32, 27), fill=NAVY, width=int(3 * u))
            d.polygon(P(10, 11, 36, 11, 33, 23, 12, 23), fill=RED)
            d.ellipse(box(12, 29, 18, 35), fill=NAVY)
            d.ellipse(box(26, 29, 32, 35), fill=NAVY)
        elif kind == "flask":
            d.polygon(P(16, 4, 24, 4, 24, 16, 34, 34, 6, 34, 16, 16), fill=CREAM, outline=NAVY, width=int(2.5 * u))
            d.polygon(P(11.5, 25, 28.5, 25, 32.5, 32.5, 7.5, 32.5), fill=TEAL)
            d.rectangle(box(14, 2, 26, 6), fill=NAVY)
        elif kind == "gavel":
            hd = [(-9, -5), (9, -5), (9, 5), (-9, 5)]
            a = -math.pi / 4

            def rot(pts, cx, cy):
                return [(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)) for x, y in pts]

            hp = rot(hd, 15, 14)
            d.polygon([(x * u, y * u) for x, y in hp], fill=(150, 90, 40))
            hand = rot([(-2, 0), (2, 0), (2, 20), (-2, 20)], 15, 14)
            d.polygon([(x * u, y * u) for x, y in hand], fill=(120, 70, 30))
            d.rounded_rectangle(box(18, 31, 38, 37), radius=2 * u, fill=NAVY)
        elif kind == "chip":
            d.rounded_rectangle(box(9, 9, 31, 31), radius=3 * u, fill=NAVY)
            for i in range(4):
                p = 12 + i * 5.3
                d.line(P(p, 3, p, 9), fill=GOLD, width=int(2 * u))
                d.line(P(p, 31, p, 37), fill=GOLD, width=int(2 * u))
                d.line(P(3, p, 9, p), fill=GOLD, width=int(2 * u))
                d.line(P(31, p, 37, p), fill=GOLD, width=int(2 * u))
            f = font(int(15 * u))
            d.text((20 * u, 20.5 * u), "€", font=f, fill=GOLD, anchor="mm")
        elif kind == "helmet":
            d.pieslice(box(7, 10, 33, 36), 180, 360, fill=GOLD)
            d.rounded_rectangle(box(4, 22, 36, 26), radius=2 * u, fill=(190, 130, 20))
            d.ellipse(box(16, 12, 24, 20), fill=CREAM, outline=NAVY, width=int(1.5 * u))
            for x in (8, 18, 28):
                d.arc(box(x - 4, 29, x + 4, 35), 200, 340, fill=TEAL, width=int(2.5 * u))
        elif kind == "storm":
            for cx, cy, r in ((14, 15, 8), (23, 11, 10), (30, 17, 7)):
                d.ellipse(box(cx - r, cy - r, cx + r, cy + r), fill=NAVY2)
            d.rounded_rectangle(box(6, 15, 37, 24), radius=4 * u, fill=NAVY2)
            d.polygon(P(21, 23, 15, 32, 20, 32, 17, 39, 26, 28, 21, 28, 24, 23), fill=GOLD)
            for x in (10, 30):
                d.line(P(x, 27, x - 2, 33), fill=TEAL, width=int(2 * u))

    return supersampled(s, s, paint, scale=4)


# ---------------------------------------------------------------- world map

LAND = [
    # North America
    [(-168, 65), (-160, 71), (-140, 70), (-120, 72), (-95, 74), (-82, 72), (-64, 60), (-56, 52), (-66, 44),
     (-71, 41), (-76, 35), (-81, 31), (-80, 25), (-82, 26), (-84, 30), (-90, 30), (-97, 27), (-97, 21), (-91, 19),
     (-88, 21), (-87, 16), (-83, 10), (-77, 8), (-80, 8), (-85, 11), (-92, 14), (-105, 20), (-110, 24), (-115, 30),
     (-118, 34), (-123, 39), (-124, 46), (-127, 51), (-135, 57), (-145, 60), (-155, 58), (-165, 60)],
    # Greenland
    [(-55, 60), (-44, 60), (-22, 70), (-20, 80), (-40, 83), (-65, 80), (-70, 77), (-56, 70)],
    # South America
    [(-77, 8), (-72, 12), (-62, 10), (-50, 1), (-35, -5), (-38, -13), (-48, -26), (-58, -38), (-65, -42),
     (-68, -52), (-74, -50), (-72, -35), (-71, -18), (-81, -5), (-80, 0)],
    # Eurasia
    [(-10, 36), (-9, 43), (-1, 46), (-4, 48), (2, 51), (8, 54), (10, 58), (5, 62), (15, 69), (28, 71), (40, 67),
     (60, 70), (80, 73), (100, 77), (120, 73), (140, 72), (160, 70), (180, 68), (180, 64), (165, 60), (160, 55),
     (142, 59), (135, 54), (141, 46), (130, 42), (127, 38), (126, 35), (121, 31), (120, 24), (110, 20), (108, 16),
     (109, 12), (104, 9), (100, 13), (99, 7), (103, 1), (98, 8), (97, 16), (92, 21), (88, 22), (80, 15), (77, 8),
     (73, 20), (67, 25), (57, 25), (56, 27), (50, 30), (48, 29), (51, 24), (56, 25), (59, 22), (55, 17), (44, 13),
     (43, 17), (39, 22), (35, 28), (34, 32), (36, 36), (30, 37), (27, 40), (23, 38), (22, 40), (19, 42), (13, 45),
     (16, 40), (12, 38), (8, 44), (3, 43), (-1, 37), (-6, 36)],
    # Africa
    [(-17, 21), (-16, 13), (-8, 4), (5, 5), (9, 4), (9, -1), (13, -6), (12, -17), (15, -27), (18, -34), (25, -34),
     (32, -28), (35, -22), (40, -15), (40, -5), (44, 0), (51, 11), (43, 12), (38, 18), (33, 28), (32, 31), (20, 32),
     (10, 37), (-6, 36), (-10, 30)],
    [(-5, 50), (1, 51), (0, 54), (-2, 57), (-5, 58), (-6, 55), (-3, 54), (-5, 52)],  # Britain
    [(114, -22), (122, -18), (130, -12), (137, -12), (142, -11), (146, -19), (153, -26), (150, -37), (144, -39),
     (138, -35), (130, -32), (116, -35), (114, -28)],  # Australia
    [(95, 5), (100, 1), (106, -6), (102, -4), (95, 3)],  # Sumatra
    [(106, -6), (114, -7), (114, -8.5), (106, -7.5)],  # Java
    [(109, 1), (117, 7), (119, 1), (116, -4), (110, -3)],  # Borneo
    [(131, -1), (141, -3), (150, -10), (141, -9), (134, -4)],  # New Guinea
    [(130, 31), (135, 34), (140, 36), (142, 41), (140, 41), (136, 36), (131, 34)],  # Japan
    [(44, -25), (47, -25), (50, -15), (49, -12), (44, -17)],  # Madagascar
    [(172, -35), (178, -38), (174, -41), (167, -46), (171, -44)],  # New Zealand
    [(156, -7), (161, -9), (162, -11), (157, -9)],  # Solomon Islands (enlarged)
]

LON0, LON1, LAT0, LAT1 = -170.0, 182.0, 76.0, -52.0


def draw_map(w: int, h: int) -> Image.Image:
    sx = w / (LON1 - LON0)
    sy = h / (LAT0 - LAT1)

    def proj(lon, lat, k):
        return ((lon - LON0) * sx * k, (LAT0 - lat) * sy * k)

    def paint(d: ImageDraw.ImageDraw, k: int, big):
        d.rounded_rectangle((0, 0, w * k, h * k), radius=8 * k, fill=(214, 233, 232))
        for poly in LAND:
            d.polygon([proj(lo, la, k) for lo, la in poly], fill=(199, 186, 158), outline=(170, 155, 125))
        lead = {n for n, *_ in LEADS}
        for n, (lo, la, dx, dy) in PINS.items():
            x, y = proj(lo, la, k)
            bx, by = x + dx * k, y + dy * k
            d.line((x, y, bx, by), fill=NAVY, width=k)
            d.ellipse((x - 2 * k, y - 2 * k, x + 2 * k, y + 2 * k), fill=NAVY)
            r = 7 * k
            d.ellipse((bx - r, by - r, bx + r, by + r), fill=RED if n in lead else NAVY, outline=PAPER, width=k)
            f = font(int(9 * k))
            d.text((bx, by + 0.5 * k), str(n), font=f, fill=(255, 255, 255), anchor="mm")

    return supersampled(w, h, paint, scale=3)


# ---------------------------------------------------------------- poster


def build(art_dir: str) -> Image.Image:
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)

    # Masthead
    d.rectangle((0, 0, W, 86), fill=NAVY)
    d.text((M + 2, 10), "THE WORLD IN ONE POSTER", font=font(15), fill=GOLD)
    f_date = font(50)
    d.text((M, 30), "THURSDAY 26 NOVEMBER 2026", font=f_date, fill=PAPER)
    dw = text_w(f_date, "THURSDAY 26 NOVEMBER 2026")
    rx = M + dw + 18
    d.text((W - M, 30), "31 STORIES", font=font(22), fill=GOLD, anchor="ra")
    d.text((W - M, 56), "7 REGIONS · SPACE", font=font(15), fill=CREAM, anchor="ra")
    assert rx < W - M - text_w(font(22), "31 STORIES"), "masthead collision"
    d.rectangle((0, 86, W, 90), fill=RED)

    # Lead cards (3 x 2)
    cw, gap = 326, 11
    img_h, card_h = 146, 232
    focus = {1: 0.55, 2: 0.55, 3: 0.55, 4: 0.5, 5: 0.6}
    for i, (n, region, tag, head, detail) in enumerate(LEADS):
        col, row = i % 3, i // 3
        x = M + col * (cw + gap)
        y = 98 + row * (card_h + 8)
        d.rounded_rectangle((x, y, x + cw, y + card_h), radius=8, fill=PAPER, outline=(222, 210, 186))
        if n <= 5:
            art = cover(Image.open(os.path.join(art_dir, f"{n}.png")).convert("RGB"), cw, img_h, focus[n])
        else:
            art = draw_story6(cw, img_h)
        mask = Image.new("L", (cw, img_h), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw, img_h + 10), radius=8, fill=255)
        im.paste(art, (x, y), mask)
        badge(d, x + 18, y + 18, n, r=13, size=15)
        pill(d, x + 36, y + 9, tag, REGION_COL[region], size=12)
        f, lines = fit(head, cw - 20, 2, 25, 23)
        ty = y + img_h + 7
        for ln in lines:
            d.text((x + 10, ty), ln, font=f, fill=INK)
            ty += f.size + 3
        fd, dl = fit(detail, cw - 20, 1, 14, 13, bold=False)
        d.text((x + 10, y + card_h - 21), dl[0], font=fd, fill=(70, 74, 84))
        LAYOUT.append((f"lead {n} text", ty, y + card_h - 21))

    # Tiles: 7 on the first row, 6 on the second
    ty0 = 574
    th = 108
    rows = [TILES[:7], TILES[7:]]
    for r, items in enumerate(rows):
        n_items = len(items)
        tw = (W - 2 * M - (n_items - 1) * 6) / n_items
        for j, (n, region, tag, head, icon) in enumerate(items):
            x = M + j * (tw + 6)
            y = ty0 + r * (th + 6)
            d.rounded_rectangle((x, y, x + tw, y + th), radius=7, fill=PAPER, outline=(222, 210, 186))
            d.rectangle((x, y + 6, x + 4, y + th - 6), fill=REGION_COL[region])
            ic = draw_icon(icon, 32, None)
            icon_x = int(x + tw - 37)
            im.paste(ic, (icon_x, int(y + 5)), ic)
            badge(d, x + 18, y + 16, n, r=10, size=12)
            ft = font(12)
            d.text((x + 32, y + 10), tag, font=ft, fill=REGION_COL[region])
            LAYOUT.append((f"tile {n} tag", x + 32 + text_w(ft, tag), icon_x))
            f, lines = fit(head, tw - 18, 3, 17, 16)
            yy = y + 40
            for ln in lines:
                d.text((x + 10, yy), ln, font=f, fill=INK)
                yy += f.size + 3
            LAYOUT.append((f"tile {n} text", yy, y + th - 2))

    # Bottom: map + also-today
    by = 806
    d.text((M, by), "WHERE IT HAPPENED", font=font(14), fill=NAVY)
    mw, mh = 404, 164
    mp = draw_map(mw, mh)
    im.paste(mp, (M, by + 22), mp)
    d.text((M + 6, by + 22 + mh - 16), "No pin: 4 (in orbit), 13 (air base not named)",
           font=font(11, False), fill=NAVY)

    lx = M + mw + 14
    d.text((lx, by), "ALSO TODAY", font=font(14), fill=NAVY)
    col_w = (W - M - lx - 12) / 2
    row_h = 27.5
    for i, (n, text) in enumerate(ALSO):
        c, rr = i // 6, i % 6
        x = lx + c * (col_w + 12)
        y = by + 24 + rr * row_h
        if rr:
            d.line((x, y - 4, x + col_w, y - 4), fill=(222, 210, 186))
        badge(d, x + 10, y + 10, n, r=10, fill=NAVY, size=11)
        f, lines = fit(text, col_w - 26, 1, 14, 14, bold="narrow")
        d.text((x + 25, y + 10), lines[0], font=f, fill=INK, anchor="lm")
    LAYOUT.append(("also-today bottom", by + 24 + 5 * row_h + 20, H - 26))

    # Footer
    d.rectangle((0, H - 26, W, H), fill=NAVY)
    d.text((W / 2, H - 13), "All 31 stories happened or were first reported on Thursday 26 November 2026"
           " · sources include Reuters, AP, NPR, Anadolu, DW, Bloomberg",
           font=font(12), fill=CREAM, anchor="mm")
    return im


def save_under_limit(im: Image.Image, path: str, limit: int = 1048576) -> int:
    im.save(path, "PNG", optimize=True)
    size = os.path.getsize(path)
    if size > limit:
        q = im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
        q.save(path, "PNG", optimize=True)
        size = os.path.getsize(path)
    if size > limit:
        raise SystemExit(f"{path} is {size} bytes, over {limit}")
    return size


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", default=os.path.join(ROOT, "art"))
    ap.add_argument("--out", default=os.path.join(ROOT, "entry.png"))
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    im = build(a.art)
    size = save_under_limit(im, a.out)
    print(f"wrote {a.out}: {im.width}x{im.height}, {size} bytes")
    clashes = [(what, end, limit) for what, end, limit in LAYOUT if end > limit]
    for what, end, limit in clashes:
        print(f"  OVERLAP {what}: ends at {end:.0f}, limit {limit:.0f}")
    if clashes:
        raise SystemExit("layout overlaps, see above")
    print(f"  layout ok: {len(LAYOUT)} boxes checked; smallest text {min(s for _, s, _ in FIT_LOG)}px")
    shrunk = [(t, s, want) for t, s, want in FIT_LOG if s < want]
    for t, s, want in shrunk:
        print(f"  shrunk {want}->{s}px: {t}")
    if a.preview:
        p = os.path.join(ROOT, "preview-300.png")
        im.resize((300, 300), Image.LANCZOS).save(p)
        print(f"wrote {p}")


if __name__ == "__main__":
    sys.exit(main())
