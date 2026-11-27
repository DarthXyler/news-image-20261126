"""Build entry.png: Thursday 26 November 2026's world news on one 1024x1024 poster.

Usage (from the repository root):
    python tools/make_poster.py            # writes entry.png
    python tools/make_poster.py --preview  # also writes preview-300.png (300 px wide check)

Inputs: art/1.png .. art/15.png, text-free illustrations (1-10 for the illustrated stories,
11-15 for five picture tiles). Every icon, the map and all text are drawn here in code.
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
# Section A: ten illustrated stories (number, region, tag, headline <= 7 words, detail or "")
# Row 1 holds four large cards, row 2 six smaller ones (headline only).
BIG = [
    (1, "AMERICAS", "USA · TRADE", "US proposes tariffs on 14 trading partners",
     "Vietnam faces up to 35%; comment open until 5 Jan"),
    (7, "MIDDLE EAST", "KUWAIT", "Kuwait drone attack kills two Italians",
     "Air-defence technicians. Iranian-made drones blamed; Iran denies"),
    (3, "MIDDLE EAST", "SAUDI ARABIA", "Houthis claim strikes on Saudi Arabia",
     "Ras Tanura refinery and Riyadh's financial district"),
    (2, "AFRICA", "EGYPT", "Cairo highway tanker fire kills at least 31",
     "21 injured in Warraq after a fallen power cable"),
]
SMALL = [
    (4, "SPACE", "SPACE", "SpaceX cleared for up to 1M satellites"),
    (8, "ASIA", "THAILAND", "Huge blast at Bangkok oil depot"),
    (10, "MIDDLE EAST", "HORMUZ", "Iran: two tankers hit mines, catch fire"),
    (5, "MIDDLE EAST", "ISRAEL", "Drop Netanyahu Case 4000, judges urge"),
    (6, "OCEANIA", "SOLOMON IS.", "Australia, Solomons sign security treaty"),
    (9, "AMERICAS", "USA", "Thanksgiving storm pummels US East Coast"),
]

# Section B: fifteen tiles (number, region, tag, headline <= 6-7 words, icon name or art file)
PIC_TILES = [
    (11, "ASIA", "CHINA", "Xi ousts Shanghai's party chief", "15.png"),
    (13, "ASIA", "N. KOREA", "Kim: deploy tactical nukes more widely", "11.png"),
    (21, "AMERICAS", "COLOMBIA", "17-hour siege ends, 76 hostages freed", "12.png"),
    (25, "ASIA", "INDONESIA", "Java mine flood: 8 dead, 18 trapped", "14.png"),
    (26, "ASIA", "HONG KONG", "A year since deadly Wang Fuk Court fire", "13.png"),
]
TILES = [
    (12, "ASIA", "N. KOREA", "Swiss top diplomat given 48h to leave", "hourglass"),
    (14, "EUROPE", "POLAND", "No-fly zone planned on eastern border", "noplane"),
    (15, "EUROPE", "UKRAINE", "30+ nations: Russia, stop CS gas", "gas"),
    (16, "EUROPE", "RUSSIA", "Record military budget; Merz warns", "bars"),
    (17, "EUROPE", "UKRAINE", "Ukraine hits Russian air base: 5 planes", "plane_hit"),
    (18, "MIDDLE EAST", "YEMEN · SAUDI", "Coalition: 50 Houthi targets destroyed", "target"),
    (19, "MIDDLE EAST", "LEBANON", "Israel hits Hezbollah launchers in Beqaa", "missile"),
    (20, "EUROPE", "GERMANY", "2 Iraqis held in alleged synagogue plot", "cuffs"),
    (22, "AFRICA", "NIGERIA", "Meth lab raid: 1.5 t; 5 Mexicans held", "flask"),
    (23, "AFRICA", "S. AFRICA", "Ramaphosa wins Phala Phala case", "gavel"),
]

# Section C: "Also today" (number, one line); story 24 moved here when story 26 got a picture
ALSO = [
    (24, "EU proposes €50bn tech fund and Quantum Act"),
    (27, "New York judge upholds Mamdani's rent freeze"),
    (28, "Spain: feminists march against violence"),
    (29, "Asian markets recover; China urges tariff talks"),
    (30, "Musk: every US child to get two SpaceX shares"),
    (31, "Iraq jails 8 French nationals for life over ISIS"),
    (32, "Putin fires Murmansk governor amid probe"),
    (33, "Novaya Gazeta leaves Moscow, works from Riga"),
    (34, "Trump, NATO's Rutte discuss Ukraine and Iran"),
    (35, "Israel says it is ready to strike Iran without US"),
    (36, "Iowa: lead azide detonated, zero airborne lead"),
    (37, "Puerto Rico top court scraps Luma power deal"),
    (38, "Australia braces for hotter El Niño summer"),
    (39, "ESA's Hera images crater on asteroid Dimorphos"),
    (40, "Duran Duran guitarist Andy Taylor dies at 65"),
]

N_STORIES = len(BIG) + len(SMALL) + len(PIC_TILES) + len(TILES) + len(ALSO)

# Map pins: number -> (lon, lat). Badges are spread apart automatically (see draw_map).
PINS = {
    1: (-77.0, 38.9), 9: (-75.5, 36.5), 27: (-74.0, 40.7), 34: (-80.0, 26.7), 36: (-93.5, 42.0),
    30: (-100.0, 39.0), 37: (-66.1, 18.4), 21: (-75.5, 10.4),
    28: (-3.7, 40.4), 40: (-1.9, 52.5), 24: (4.4, 50.8), 20: (10.4, 51.2), 14: (23.5, 52.0),
    33: (24.1, 56.9), 15: (31.0, 49.5), 16: (37.6, 55.8), 17: (41.0, 52.5), 32: (33.1, 68.9),
    2: (31.2, 30.0), 5: (35.2, 31.8), 35: (34.8, 32.1), 19: (36.0, 33.8), 31: (44.4, 33.3),
    7: (47.9, 29.4), 3: (50.1, 26.6), 10: (56.2, 26.2), 18: (47.0, 15.5),
    22: (8.0, 9.5), 23: (28.0, -26.0),
    29: (116.4, 39.9), 11: (121.4, 31.2), 26: (114.2, 22.3), 12: (125.7, 39.0), 13: (127.0, 40.4),
    8: (100.5, 13.7), 25: (107.6, -6.9), 38: (134.0, -25.0), 6: (160.0, -9.4),
}
IN_SPACE = [4, 39]  # shown beside a satellite symbol in the map's corner

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
        elif kind == "target":
            d.ellipse(box(5, 5, 35, 35), outline=RED, width=int(3 * u))
            d.ellipse(box(12, 12, 28, 28), outline=RED, width=int(3 * u))
            d.ellipse(box(17.5, 17.5, 22.5, 22.5), fill=RED)
            for x0, y0, x1, y1 in ((20, 1, 20, 9), (20, 31, 20, 39), (1, 20, 9, 20), (31, 20, 39, 20)):
                d.line(P(x0, y0, x1, y1), fill=NAVY, width=int(2.5 * u))
        elif kind == "cuffs":
            d.ellipse(box(3, 14, 19, 30), outline=NAVY, width=int(3.5 * u))
            d.ellipse(box(21, 14, 37, 30), outline=NAVY, width=int(3.5 * u))
            for cx in (15.5, 20, 24.5):
                d.ellipse(box(cx - 2.6, 9, cx + 2.6, 15), outline=GREY, width=int(1.6 * u))
            d.rectangle(box(9, 12, 13, 16), fill=NAVY2)
            d.rectangle(box(27, 12, 31, 16), fill=NAVY2)
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
     (142, 59), (135, 54), (141, 46), (130, 42), (129.5, 36), (127, 34.5), (126.3, 37.5), (125, 39.5),
     (121.5, 39), (122.5, 37), (119, 35), (122, 30.8), (121, 28), (120, 24), (110, 20), (108, 16),
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

LON0, LON1, LAT0, LAT1 = -128.0, 170.0, 72.0, -42.0
PIN_R = 6.5  # badge radius in map pixels


def spread_badges(anchors: dict[int, tuple[float, float]], w: float, h: float) -> dict[int, tuple[float, float]]:
    """Deterministic relaxation: push overlapping badges apart, pull each gently back to its pin."""
    pos = {n: [x, y] for n, (x, y) in anchors.items()}
    keys = sorted(pos)
    gap = 2 * PIN_R + 1.0
    for _ in range(400):
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                dx = pos[b][0] - pos[a][0]
                dy = pos[b][1] - pos[a][1]
                dist = math.hypot(dx, dy)
                if dist < gap:
                    if dist < 1e-6:  # identical spots: split along a fixed direction
                        dx, dy, dist = 1.0, 0.3 * ((a + b) % 3 - 1), 1.0
                    push = (gap - dist) / 2
                    ux, uy = dx / dist, dy / dist
                    pos[a][0] -= ux * push
                    pos[a][1] -= uy * push
                    pos[b][0] += ux * push
                    pos[b][1] += uy * push
        for n in keys:
            ax, ay = anchors[n]
            pos[n][0] += (ax - pos[n][0]) * 0.02
            pos[n][1] += (ay - pos[n][1]) * 0.02
            pos[n][0] = min(max(pos[n][0], PIN_R + 1), w - PIN_R - 1)
            pos[n][1] = min(max(pos[n][1], PIN_R + 1), h - PIN_R - 1)
    return {n: (x, y) for n, (x, y) in pos.items()}


def pin_colour(n: int):
    if n in {s[0] for s in BIG + SMALL}:
        return RED
    if n in {s[0] for s in PIC_TILES + TILES}:
        return NAVY
    return TEAL_D


def draw_map(w: int, h: int) -> Image.Image:
    sx = w / (LON1 - LON0)
    sy = h / (LAT0 - LAT1)

    def proj(lon, lat):
        return ((lon - LON0) * sx, (LAT0 - lat) * sy)

    anchors = {n: proj(lo, la) for n, (lo, la) in PINS.items()}
    for n, (x, y) in anchors.items():
        assert 0 <= x <= w and 0 <= y <= h, f"pin {n} is off the map"
    badges = spread_badges(anchors, w, h)
    # space corner (lower left, open Pacific): satellite symbol and its badges
    sat_x, sat_y = 20, h - 22
    space_badges = {n: (sat_x + 22 + i * (2 * PIN_R + 2), sat_y) for i, n in enumerate(IN_SPACE)}
    for n, (bx, by) in badges.items():
        for sx_, sy_ in space_badges.values():
            assert math.hypot(bx - sx_, by - sy_) > 2 * PIN_R, f"badge {n} hits the space corner"
    MAP_INFO["max_shift"] = max(math.hypot(badges[n][0] - anchors[n][0], badges[n][1] - anchors[n][1])
                                for n in badges)

    def paint(d: ImageDraw.ImageDraw, k: int, big):
        d.rounded_rectangle((0, 0, w * k, h * k), radius=8 * k, fill=(214, 233, 232))
        for poly in LAND:
            d.polygon([(proj(lo, la)[0] * k, proj(lo, la)[1] * k) for lo, la in poly],
                      fill=(199, 186, 158), outline=(170, 155, 125))
        f = font(int(8.5 * k))
        for n in sorted(badges):  # leader lines and pin dots first, badges on top
            (x, y), (bx, by) = anchors[n], badges[n]
            if math.hypot(bx - x, by - y) > PIN_R:
                d.line((x * k, y * k, bx * k, by * k), fill=NAVY, width=k)
            d.ellipse(((x - 1.8) * k, (y - 1.8) * k, (x + 1.8) * k, (y + 1.8) * k), fill=NAVY)
        # satellite symbol: body, two solar panels, a short antenna
        cx, cy = sat_x * k, sat_y * k
        d.rectangle((cx - 4 * k, cy - 4 * k, cx + 4 * k, cy + 4 * k), fill=GOLD, outline=NAVY, width=k)
        d.rectangle((cx - 15 * k, cy - 3 * k, cx - 6 * k, cy + 3 * k), fill=NAVY2)
        d.rectangle((cx + 6 * k, cy - 3 * k, cx + 15 * k, cy + 3 * k), fill=NAVY2)
        d.line((cx, cy - 4 * k, cx, cy - 9 * k), fill=NAVY, width=k)
        d.text((cx, cy + 7 * k), "SPACE", font=font(int(7 * k)), fill=NAVY, anchor="ma")
        for n, (bx, by) in list(badges.items()) + list(space_badges.items()):
            r = PIN_R * k
            d.ellipse((bx * k - r, by * k - r, bx * k + r, by * k + r), fill=pin_colour(n), outline=PAPER, width=k)
            d.text((bx * k, by * k + 0.5 * k), str(n), font=f, fill=(255, 255, 255), anchor="mm")

    return supersampled(w, h, paint, scale=3)


MAP_INFO: dict[str, float] = {}


# ---------------------------------------------------------------- poster


FOCUS = {1: 0.55, 2: 0.55, 3: 0.55, 4: 0.5, 5: 0.6, 6: 0.45, 7: 0.6, 8: 0.45, 9: 0.55, 10: 0.5,
         11: 0.55, 12: 0.7, 13: 0.72, 14: 0.6, 15: 0.5}
CARD_LINE = (222, 210, 186)


def place_art(im, art_dir, name, x, y, w, h, focus):
    art = cover(Image.open(os.path.join(art_dir, name)).convert("RGB"), w, h, focus)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h + 10), radius=7, fill=255)
    im.paste(art, (int(x), int(y)), mask)


def headline(d, text, x, y, max_w, lines_max, size, min_size, gap=3, colour=INK, bold=True):
    f, lines = fit(text, max_w, lines_max, size, min_size, bold=bold)
    for ln in lines:
        d.text((x, y), ln, font=f, fill=colour)
        y += f.size + gap
    return y


def build(art_dir: str) -> Image.Image:
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)

    # Masthead
    d.rectangle((0, 0, W, 86), fill=NAVY)
    d.text((M + 2, 10), "THE WORLD IN ONE POSTER", font=font(15), fill=GOLD)
    f_date = font(50)
    d.text((M, 30), "THURSDAY 26 NOVEMBER 2026", font=f_date, fill=PAPER)
    count = f"{N_STORIES} STORIES"
    d.text((W - M, 30), count, font=font(22), fill=GOLD, anchor="ra")
    d.text((W - M, 56), "8 REGIONS · SPACE", font=font(15), fill=CREAM, anchor="ra")
    LAYOUT.append(("masthead", M + text_w(f_date, "THURSDAY 26 NOVEMBER 2026") + 14, W - M - text_w(font(22), count)))
    d.rectangle((0, 86, W, 90), fill=RED)

    # Row 1: four large picture cards
    y0, gap = 96, 8
    cw = (W - 2 * M - 3 * gap) / 4
    img_h, card_h = 126, 224
    for i, (n, region, tag, head, detail) in enumerate(BIG):
        x = M + i * (cw + gap)
        d.rounded_rectangle((x, y0, x + cw, y0 + card_h), radius=8, fill=PAPER, outline=CARD_LINE)
        place_art(im, art_dir, f"{n}.png", x, y0, int(cw), img_h, FOCUS[n])
        badge(d, x + 16, y0 + 16, n, r=12, size=14)
        pill(d, x + 32, y0 + 8, tag, REGION_COL[region], size=12)
        yy = headline(d, head, x + 9, y0 + img_h + 6, cw - 16, 2, 22, 21)
        yy = headline(d, detail, x + 9, yy + 2, cw - 16, 2, 13, 13, gap=2, colour=(70, 74, 84), bold=False)
        LAYOUT.append((f"big {n} text", yy, y0 + card_h - 2))

    # Row 2: six smaller picture cards
    y0 = 96 + card_h + gap
    cw = (W - 2 * M - 5 * gap) / 6
    img_h, card_h = 86, 158
    for i, (n, region, tag, head) in enumerate(SMALL):
        x = M + i * (cw + gap)
        d.rounded_rectangle((x, y0, x + cw, y0 + card_h), radius=8, fill=PAPER, outline=CARD_LINE)
        place_art(im, art_dir, f"{n}.png", x, y0, int(cw), img_h, FOCUS[n])
        badge(d, x + 14, y0 + 14, n, r=11, size=13)
        pill(d, x + 28, y0 + 6, tag, REGION_COL[region], size=11, pad=5)
        yy = headline(d, head, x + 8, y0 + img_h + 5, cw - 14, 3, 18, 17)
        LAYOUT.append((f"small {n} text", yy, y0 + card_h - 1))
    y0 += card_h + gap

    # Picture tiles (5 across)
    tw = (W - 2 * M - 4 * 6) / 5
    img_h, th = 66, 112
    for i, (n, region, tag, head, art_name) in enumerate(PIC_TILES):
        x = M + i * (tw + 6)
        d.rounded_rectangle((x, y0, x + tw, y0 + th), radius=7, fill=PAPER, outline=CARD_LINE)
        place_art(im, art_dir, art_name, x, y0, int(tw), img_h, FOCUS[int(art_name.split(".")[0])])
        badge(d, x + 13, y0 + 13, n, r=10, size=12)
        pill(d, x + 26, y0 + 5, tag, REGION_COL[region], size=11, pad=5)
        yy = headline(d, head, x + 8, y0 + img_h + 5, tw - 14, 2, 17, 16)
        LAYOUT.append((f"pic tile {n} text", yy, y0 + th - 1))
    y0 += th + 6

    # Icon tiles (2 rows of 5)
    th = 64
    for i, (n, region, tag, head, icon) in enumerate(TILES):
        r_, c_ = divmod(i, 5)
        x = M + c_ * (tw + 6)
        y = y0 + r_ * (th + 6)
        d.rounded_rectangle((x, y, x + tw, y + th), radius=7, fill=PAPER, outline=CARD_LINE)
        d.rectangle((x, y + 6, x + 4, y + th - 6), fill=REGION_COL[region])
        ic = draw_icon(icon, 26, None)
        icon_x = int(x + tw - 30)
        im.paste(ic, (icon_x, int(y + 4)), ic)
        badge(d, x + 17, y + 14, n, r=10, size=12)
        ft = font(12)
        d.text((x + 31, y + 8), tag, font=ft, fill=REGION_COL[region])
        LAYOUT.append((f"tile {n} tag", x + 31 + text_w(ft, tag), icon_x - 2))
        yy = headline(d, head, x + 10, y + 27, tw - 18, 2, 16, 15, gap=2)
        LAYOUT.append((f"tile {n} text", yy, y + th - 1))
    y0 += 2 * th + 6 + 8

    # Bottom: map + also-today
    by = y0
    d.text((M, by), "WHERE IT HAPPENED", font=font(14), fill=NAVY)
    lg = font(11, False)
    lx0 = M + 160
    for colour, label in ((RED, "picture stories"), (NAVY, "tiles"), (TEAL_D, "also today")):
        d.ellipse((lx0, by + 3, lx0 + 10, by + 13), fill=colour)
        d.text((lx0 + 14, by + 1), label, font=lg, fill=NAVY)
        lx0 += 22 + text_w(lg, label)
    mw = 404
    mh = H - 28 - (by + 20) - 4
    mp = draw_map(mw, mh)
    im.paste(mp, (M, by + 20), mp)
    LAYOUT.append(("map legend", lx0, M + mw))

    lx = M + mw + 14
    d.text((lx, by), "ALSO TODAY", font=font(14), fill=NAVY)
    col_w = (W - M - lx - 12) / 2
    per_col = math.ceil(len(ALSO) / 2)
    row_h = (H - 30 - (by + 22)) / per_col
    for i, (n, text) in enumerate(ALSO):
        c, rr = divmod(i, per_col)
        x = lx + c * (col_w + 12)
        y = by + 22 + rr * row_h
        if rr:
            d.line((x, y - 3, x + col_w, y - 3), fill=CARD_LINE)
        badge(d, x + 10, y + row_h / 2 - 2, n, r=10, fill=TEAL_D, size=11)
        f, lines = fit(text, col_w - 26, 1, 14, 14, bold="narrow")
        d.text((x + 25, y + row_h / 2 - 2), lines[0], font=f, fill=INK, anchor="lm")
    LAYOUT.append(("also-today rows", row_h, 999))
    LAYOUT.append(("also-today min row height", 22, row_h))

    # Footer
    d.rectangle((0, H - 26, W, H), fill=NAVY)
    foot = (f"All {N_STORIES} stories happened or were first reported on Thursday 26 November 2026"
            " · sources include Reuters, NPR, Anadolu, Euronews, Times of Israel, PBS")
    ff = font(12)
    d.text((W / 2, H - 13), foot, font=ff, fill=CREAM, anchor="mm")
    LAYOUT.append(("footer width", text_w(ff, foot), W - 2 * M))
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
    print(f"  layout ok: {len(LAYOUT)} boxes checked; smallest text {min(s for _, s, _ in FIT_LOG)}px;"
          f" {N_STORIES} stories; furthest map badge {MAP_INFO['max_shift']:.0f}px from its pin")
    shrunk = [(t, s, want) for t, s, want in FIT_LOG if s < want]
    for t, s, want in shrunk:
        print(f"  shrunk {want}->{s}px: {t}")
    if a.preview:
        p = os.path.join(ROOT, "preview-300.png")
        im.resize((300, 300), Image.LANCZOS).save(p)
        print(f"wrote {p}")


if __name__ == "__main__":
    sys.exit(main())
