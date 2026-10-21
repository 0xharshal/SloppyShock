#!/usr/bin/env python3
"""Generate the 7-segment LCD font used by the watch face.

Writes watchface/src/main/res/font/lcd_segments.ttf. Requires fontTools.
Digits are 7-segment; letters (A-Z, lowercase maps to the same glyphs) are
14-segment, like the day-of-week field on classic digital watches. Every digit, letter and
the space share one advance width, so a "88:88" ghost (digits) or "###" ghost
(letters, all 14 segments on) drawn underneath lines up segment-for-segment.

    python3 tools/gen_segment_font.py

It also renders digits 0-9 as PNGs (res/drawable-nodpi/lcd_digit_N.png) for the
always-on clock: low-power display offload only accepts a bitmap font made of
same-width 0-9 images. Requires Pillow for that step.
"""
import math
import os

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

UPM = 1000
H = 1000           # digit height
W = 520            # digit body width (before slant)
T = 110            # segment thickness
TI = 66            # thickness of the inner 14-segment strokes
GAP = 14           # gap between neighbouring segments
SLANT = math.tan(math.radians(6))
SIDE = 70          # side bearing on each side
ADVANCE = int(W + H * SLANT + 2 * SIDE)
COLON_ADVANCE = 300

# Bitmap digits for the always-on clock, pre-coloured (BitmapFont isn't tinted).
DIGIT_PX = 82                 # glyph height in px == BitmapFont size == MAIN_SIZE in gen_watchface.py
DIGIT_COLOR = "#8C918B"            # == AOD_LCD in gen_watchface.py (always-on only)

# Segment layout:  aaa
#                 f   b
#                  ggg
#                 e   c
#                  ddd
SEGMENTS_FOR = {
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc",
    "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg",
    "-": "g",
}

# 14-segment letters. Outer segments a-f as above, g1/g2 = left/right half of
# the middle bar, i/l = upper/lower centre bar, h/j = upper diagonals
# (left/right), k/m = lower diagonals (left/right).
LETTERS = {
    "A": "a b c e f g1 g2", "B": "a b c d g2 i l", "C": "a d e f",
    "D": "a b c d i l", "E": "a d e f g1 g2", "F": "a e f g1",
    "G": "a c d e f g2", "H": "b c e f g1 g2", "I": "a d i l",
    "J": "b c d e", "K": "e f g1 j m", "L": "d e f",
    "M": "b c e f h j", "N": "b c e f h m", "O": "a b c d e f",
    "P": "a b e f g1 g2", "Q": "a b c d e f m", "R": "a b e f g1 g2 m",
    "S": "a c d f g1 g2", "T": "a i l", "U": "b c d e f",
    "V": "e f k j", "W": "b c e f k m", "X": "h j k m",
    "Y": "h j l", "Z": "a d j k",
    "#": "a b c d e f g1 g2 h i j k l m",
    "+": "g1 g2 i l",
    "/": "j k",
    "%": "f c j k",
}


def hseg(x0, x1, yc, t=T):
    h = t / 2
    return [(x0, yc), (x0 + h, yc + h), (x1 - h, yc + h),
            (x1, yc), (x1 - h, yc - h), (x0 + h, yc - h)]


def vseg(xc, y0, y1, t=T):
    h = t / 2
    return [(xc, y0), (xc - h, y0 + h), (xc - h, y1 - h),
            (xc, y1), (xc + h, y1 - h), (xc + h, y0 + h)]


def segment_polys():
    l, r = T / 2, W - T / 2
    top, mid, bot = H - T / 2, H / 2, T / 2
    return {
        "a": hseg(l + GAP, r - GAP, top),
        "g": hseg(l + GAP, r - GAP, mid),
        "d": hseg(l + GAP, r - GAP, bot),
        "f": vseg(l, mid + GAP, top - GAP),
        "b": vseg(r, mid + GAP, top - GAP),
        "e": vseg(l, bot + GAP, mid - GAP),
        "c": vseg(r, bot + GAP, mid - GAP),
    }


def bar(p0, p1, t):
    """A straight stroke of thickness t from p0 to p1, with pointed ends."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    px, py = -uy * t / 2, ux * t / 2
    tip = t / 2
    return [(x0, y0), (x0 + ux * tip + px, y0 + uy * tip + py),
            (x1 - ux * tip + px, y1 - uy * tip + py), (x1, y1),
            (x1 - ux * tip - px, y1 - uy * tip - py), (x0 + ux * tip - px, y0 + uy * tip - py)]


def segment14_polys():
    segs = segment_polys()
    del segs["g"]
    l, r, cx = T / 2, W - T / 2, W / 2
    top, mid, bot = H - T / 2, H / 2, T / 2
    segs["g1"] = hseg(l + GAP, cx - GAP / 2, mid)
    segs["g2"] = hseg(cx + GAP / 2, r - GAP, mid)
    segs["i"] = vseg(cx, mid + T / 2 + GAP, top - T / 2 - GAP, TI)
    segs["l"] = vseg(cx, bot + T / 2 + GAP, mid - T / 2 - GAP, TI)
    # Diagonals run from the inner corners of the outer frame to the centre.
    ix0, ix1 = T + GAP + 4, W - T - GAP - 4
    iy_top, iy_bot = H - T - GAP - 4, T + GAP + 4
    jm_top, jm_bot = mid + T / 2 + GAP, mid - T / 2 - GAP
    off = TI / 2 + GAP
    segs["h"] = bar((ix0, iy_top), (cx - off, jm_top), TI)
    segs["j"] = bar((ix1, iy_top), (cx + off, jm_top), TI)
    segs["k"] = bar((ix0, iy_bot), (cx - off, jm_bot), TI)
    segs["m"] = bar((ix1, iy_bot), (cx + off, jm_bot), TI)
    return segs


def square(cx, cy, s):
    h = s / 2
    return [(cx - h, cy - h), (cx - h, cy + h), (cx + h, cy + h), (cx + h, cy - h)]


def draw(polys, x_offset):
    pen = TTGlyphPen(None)
    for poly in polys:
        pts = [(round(x + x_offset + y * SLANT), round(y)) for x, y in poly]
        # TrueType outer contours run clockwise (negative signed area, y-up).
        area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
        if area > 0:
            pts.reverse()
        pen.moveTo(pts[0])
        for p in pts[1:]:
            pen.lineTo(p)
        pen.closePath()
    return pen.glyph()


# Font variants: (file name, family, body width, thickness, inner thickness, side bearing).
# Add narrower variants here if needed (e.g. body width 360 fits ~40% more chars).
VARIANTS = [
    ("lcd_segments", "Segment7", 520, 110, 66, 70),
]


def main():
    for name, family, w, t, ti, side in VARIANTS:
        path = build_font(name, family, w, t, ti, side)
        if name == "lcd_segments":
            render_digit_pngs(path)


def build_font(file_name, family, w, t, ti, side):
    """Builds one variant; the glyph helpers read these module-level proportions."""
    global W, T, TI, SIDE, ADVANCE
    W, T, TI, SIDE = w, t, ti, side
    ADVANCE = int(W + H * SLANT + 2 * SIDE)
    segs = segment_polys()
    segs14 = segment14_polys()
    glyphs, metrics, cmap = {}, {}, {}

    def add(name, char, polys, advance, x_offset):
        glyphs[name] = draw(polys, x_offset)
        metrics[name] = (advance, 0)
        if char:
            cmap[ord(char)] = name

    add(".notdef", None, [], ADVANCE, 0)
    add("space", " ", [], ADVANCE, 0)
    for ch, on in SEGMENTS_FOR.items():
        name = {"-": "hyphen"}.get(ch, f"digit{ch}")
        add(name, ch, [segs[s] for s in on], ADVANCE, SIDE)
    for ch, on in LETTERS.items():
        name = {"#": "numbersign", "+": "plus", "/": "slash", "%": "percent"}.get(ch, ch)
        add(name, ch, [segs14[s] for s in on.split()], ADVANCE, SIDE)
        if ch.isalpha():
            cmap[ord(ch.lower())] = name

    dot = T * 1.05
    colon_x = (COLON_ADVANCE - H * SLANT) / 2
    add("colon", ":", [square(0, H * 0.28, dot), square(0, H * 0.72, dot)],
        COLON_ADVANCE, colon_x)
    add("period", ".", [square(0, T / 2, dot)], COLON_ADVANCE, colon_x)

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(list(glyphs))
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    lsb = {n: glyphs[n].xMin if hasattr(glyphs[n], "xMin") else 0 for n in glyphs}
    fb.setupHorizontalMetrics({n: (metrics[n][0], lsb[n]) for n in glyphs})
    fb.setupHorizontalHeader(ascent=H, descent=0)
    fb.setupNameTable({"familyName": family, "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=H, sTypoDescender=0, sTypoLineGap=0,
                usWinAscent=H, usWinDescent=0, sCapHeight=H, sxHeight=H)
    fb.setupPost()
    # Fixed timestamps: identical glyphs give an identical file (no churn).
    fb.updateHead(created=0x80000000, modified=0x80000000)

    out = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "watchface", "src",
                                        "main", "res", "font", f"{file_name}.ttf"))
    fb.save(out)
    print(f"wrote {out} (advance {ADVANCE / UPM:.3f} em)")
    return out


def digit_png_width():
    return round(ADVANCE * DIGIT_PX / UPM)


def render_digit_pngs(font_path):
    from PIL import Image, ImageDraw, ImageFont

    res = os.path.dirname(os.path.dirname(font_path))
    out_dir = os.path.join(res, "drawable-nodpi")
    os.makedirs(out_dir, exist_ok=True)
    font = ImageFont.truetype(font_path, DIGIT_PX)
    w = digit_png_width()
    for d in "0123456789":
        im = Image.new("RGBA", (w, DIGIT_PX), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 0), d, font=font, fill=DIGIT_COLOR)
        im.save(os.path.join(out_dir, f"lcd_digit_{d}.png"), optimize=True)
    print(f"wrote 10 digit PNGs ({w}x{DIGIT_PX}) to", out_dir)


if __name__ == "__main__":
    main()
