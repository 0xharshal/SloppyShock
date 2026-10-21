#!/usr/bin/env python3
"""Generate watchface.xml and strings.xml for the round negative-LCD face.

WFF has no loops or variables, so the repeated parts (seconds-ring tick gaps,
the complication slots) are generated here. Edit this file,
not the generated XML, then run:

    python3 tools/gen_watchface.py

Writes one face per build flavor (src/compact, src/detailed); shared resources
stay in src/main.
"""
import math
import os

SRC = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "watchface", "src"))
RES = os.path.join(SRC, "main", "res")     # shared: font, digit PNGs, watch_face_info

SIZE = 450
C = SIZE / 2

# Palette
BG = "#000000"
PANEL = "#121417"
FRAME = "#2B3238"
RED = "#C62828"
LCD = "#EEF3EC"
GHOST = "#1D2226"
LABEL = "#4DD0E1"
ACCENT = "#FFE082"
# Always-on: dimmer colours (fewer lit/bright pixels). AOD_LCD must match
# DIGIT_COLOR in tools/gen_segment_font.py (the always-on digits are PNGs).
AOD_LCD = "#8C918B"
AOD_ACCENT = "#A8925A"

# Level ring: a thick arc split into 60 segments by gap lines in BG colour.
# What it shows is chosen in the editor ("ring" list): (option id, label, lit angle).
RING_R = 214       # centre-line radius of the ring
RING_W = 14        # ring thickness
TICK_GAP = 3       # gap width between segments
PANEL_R = 198      # LCD panel radius (ring inner edge is at 207)
AOD_RING_W = 3     # always-on: thin segments

# ---- Layout. Designed for a panel of radius 184 (red inner ring at 177) and
# scaled about the centre by K, so a bigger panel keeps every alignment.
# Content stays inside the red inner ring (r = PANEL_R - 7).
K = (PANEL_R - 7) / 177


def pos(v):
    """A design-space coordinate (x or y), scaled about the centre."""
    return round(C + (v - C) * K)


def sz(v):
    """A design-space size (width, height, font size), scaled."""
    return round(v * K)


# Segment-font widths: every char advances 0.765 em, ':' 0.3 em.
def seg_w(chars, size, colons=0):
    return math.ceil(chars * 0.765 * size + colons * 0.3 * size)


# Top row: day + date, centred.
DATE_Y, DATE_SIZE = pos(72), sz(26)
DAY_W, DATE_W, DATE_GAP = seg_w(3, DATE_SIZE), seg_w(5, DATE_SIZE), sz(10)
DAY_X = round(C - (DAY_W + DATE_GAP + DATE_W) / 2)
DATE_X = DAY_X + DAY_W + DATE_GAP
DIVIDER_YS = (pos(110), pos(214))

# Main time ("88:88"), right-aligned to MAIN_RIGHT; AM/PM and seconds beside it.
MAIN_Y, MAIN_SIZE, MAIN_RIGHT = pos(126), sz(76), pos(323)
MAIN_W = seg_w(4, MAIN_SIZE, colons=1)
MAIN_X = MAIN_RIGHT - MAIN_W
SIDE_X = MAIN_RIGHT + sz(4)
AMPM_SIZE = sz(20)
SEC_SIZE = sz(34)
SEC_W = seg_w(2, SEC_SIZE)
SEC_Y = MAIN_Y + MAIN_SIZE - SEC_SIZE    # bottom-aligned with the main digits

# Always-on clock digits: PNGs rendered by tools/gen_segment_font.py at MAIN_SIZE
# (its DIGIT_PX must equal MAIN_SIZE; checked in check_digit_pngs()).
DIGIT_H = MAIN_SIZE
DIGIT_W = round(0.765 * DIGIT_H)
COLON_W = round(0.3 * DIGIT_H)


def box(x, y, w, h):
    """A design-space rectangle, scaled. Edges are scaled (not sizes) so that
    shared edges between neighbouring boxes stay shared."""
    x0, y0, x1, y1 = pos(x), pos(y), pos(x + w), pos(y + h)
    return x0, y0, x1 - x0, y1 - y0


# Lower area, design space: column edges 74..222 and 228..376, rows A/B/C.
ROW_A = (222, 32)
ROW_B = (262, 44)
ROW_C = (314, 32)
COL_L, COL_R = (74, 148), (228, 148)

# Lit ring angle: whole segments only (60 segments, 6 degrees each).
SECONDS_ANGLE = "([SECOND] + 1) * 6"
RING_MODES = [
    ("complication", "Complication (battery, steps, …)"),
    ("seconds", "Seconds"),
]
RING_SLOT_ID = 2
RING_DEFAULT = ("WATCH_BATTERY", "RANGED_VALUE")
# Second ring complication: lights only the segment at its value, in ACCENT.
POINTER_SLOT_ID = 5
POINTER_DEFAULT = ("STEP_COUNT", "GOAL_PROGRESS")

# Complication slots: (slot id, (x, y, w, h), default provider, default type, kind)
# kind: "short" (title + value), "long" (also LONG_TEXT), "large" (big detail
# panel). Ids 0/1 keep their earlier meaning so existing picks survive updates.
SLOTS_COMPACT = [
    (3, box(*COL_L[:1], ROW_A[0], COL_L[1], ROW_A[1]), "UNREAD_NOTIFICATION_COUNT", "SHORT_TEXT", "short"),
    (6, box(*COL_R[:1], ROW_A[0], COL_R[1], ROW_A[1]), "WATCH_BATTERY", "SHORT_TEXT", "short"),
    (0, box(*COL_L[:1], ROW_B[0], COL_L[1], ROW_B[1]), "STEP_COUNT", "SHORT_TEXT", "short"),
    (1, box(*COL_R[:1], ROW_B[0], COL_R[1], ROW_B[1]), "WORLD_CLOCK", "SHORT_TEXT", "short"),
    (4, box(135, ROW_C[0], 180, ROW_C[1]), "NEXT_EVENT", "LONG_TEXT", "long"),
]

# Detailed dial: one large panel over rows A+B (calendar, weather, …) and one
# small slot at the bottom.
# Detail layouts: the panels fill rows A+B and reach down to PANEL_BOTTOM; the
# single small slot sits lower (ROW_C_LOW) than in the compact layout.
ROW_C_LOW = (324, 32)
PANEL_TOP, PANEL_BOTTOM = ROW_A[0], ROW_C_LOW[0] - 8
BOTTOM_SLOT = (4, box(135, ROW_C_LOW[0], 180, ROW_C_LOW[1]), "STEP_COUNT", "SHORT_TEXT", "long")

SLOTS_DETAILED = [
    (10, box(COL_L[0], PANEL_TOP, COL_R[0] + COL_R[1] - COL_L[0], PANEL_BOTTOM - PANEL_TOP),
     "NEXT_EVENT", "LONG_TEXT", "large"),
    BOTTOM_SLOT,
]

# Dual detail: two half-width panels side by side (same columns as compact).
SLOTS_DUAL = [
    (11, box(COL_L[0], PANEL_TOP, COL_L[1], PANEL_BOTTOM - PANEL_TOP), "NEXT_EVENT", "LONG_TEXT", "large"),
    (12, box(COL_R[0], PANEL_TOP, COL_R[1], PANEL_BOTTOM - PANEL_TOP), "SUNRISE_SUNSET", "SHORT_TEXT", "large"),
    BOTTOM_SLOT,
]

# Build flavors: one watch face (and APK) per layout. compact keeps the
# original package name so existing installs keep their settings.
# (face name, slots, has ring marker). WFF allows at most 8 ComplicationSlots
# per face (schema maxOccurs, enforced by the Watch Face Push validator); compact
# has 5 small + ring + 2 tap areas, so it goes without the ring marker.
MAX_SLOTS = 8
VARIANTS = {
    "compact": ("SloppyShock", SLOTS_COMPACT, False),
    "detailed": ("SloppyShock Detailed", SLOTS_DETAILED, True),
    "dual": ("SloppyShock Dual", SLOTS_DUAL, True),
}
SLOTS = SLOTS_COMPACT                     # the variant being generated
HAS_POINTER = False
SLOT_NAMES = {3: "Upper left", 6: "Upper right", 0: "Left", 1: "Right", 4: "Bottom", 10: "Detail panel",
              11: "Left detail panel", 12: "Right detail panel"}

# Invisible tap areas over fixed parts of the face. Each is a complication slot
# that draws nothing: pick any provider / app shortcut in the editor and tapping
# the area opens it. (slot id, string name, label, (x, y, w, h), default provider)
TAP_PAD = sz(4)
TAP_AREAS = [
    (7, "tap_time", "Tap on time",
     (MAIN_X - TAP_PAD, MAIN_Y - TAP_PAD, SIDE_X + SEC_W - MAIN_X + 2 * TAP_PAD, MAIN_SIZE + 2 * TAP_PAD),
     "EMPTY"),
    (8, "tap_date", "Tap on date",
     (DAY_X - TAP_PAD, DATE_Y - TAP_PAD, DATE_X + DATE_W - DAY_X + 2 * TAP_PAD, DATE_SIZE + 2 * TAP_PAD),
     "DATE"),
]
TAP_TYPES = "SMALL_IMAGE MONOCHROMATIC_IMAGE SHORT_TEXT LONG_TEXT RANGED_VALUE EMPTY"


def seg_text(x, y, w, size, text=None, template=None, color=LCD, align="END"):
    """A PartText in the segment font. Ghosts pass `text`, live values `template`."""
    body = f"<![CDATA[{text}]]>" if text is not None else f"<Template>{template}</Template>"
    return f'''<PartText x="{x}" y="{y}" width="{w}" height="{size}">
                <Text align="{align}">
                    <Font family="lcd_segments" size="{size}" color="{color}">{body}</Font>
                </Text>
            </PartText>'''


def label(x, y, w, h, size, text, color, align="START"):
    return f'''<PartText x="{x}" y="{y}" width="{w}" height="{h}">
                <Text align="{align}">
                    <Font family="SYNC_TO_DEVICE" size="{size}" color="{color}" weight="BOLD"><![CDATA[{text}]]></Font>
                </Text>
            </PartText>'''


def ring_gaps():
    r0, r1 = RING_R - RING_W / 2 - 1, RING_R + RING_W / 2 + 1
    lines = []
    for i in range(60):
        a = math.radians(i * 6)
        sx, sy = C + r0 * math.sin(a), C - r0 * math.cos(a)
        ex, ey = C + r1 * math.sin(a), C - r1 * math.cos(a)
        lines.append(f'<Line startX="{sx:.1f}" startY="{sy:.1f}" endX="{ex:.1f}" endY="{ey:.1f}">'
                     f'<Stroke color="{BG}" thickness="{TICK_GAP}" /></Line>')
    return "\n            ".join(lines)


def ring_arc(color, end_expr=None, thickness=RING_W):
    d = 2 * RING_R
    transform = (f'\n                <Transform target="endAngle" value="{end_expr}" />'
                 if end_expr else "")
    return f'''<Arc centerX="{C}" centerY="{C}" width="{d}" height="{d}" startAngle="0" endAngle="360">{transform}
                <Stroke color="{color}" thickness="{thickness}" cap="BUTT" />
            </Arc>'''


def mode_variant(ambient):
    """Show a part only in interactive mode (ambient=False) or only in always-on."""
    if ambient:
        return 'alpha="0">\n            <Variant mode="AMBIENT" target="alpha" value="255" />'
    return '>\n            <Variant mode="AMBIENT" target="alpha" value="0" />'


def ring_draw(angle, ambient=False):
    """Track + lit arc + segment gaps. Always-on uses the thin, dim variant."""
    w, lit = (AOD_RING_W, AOD_LCD) if ambient else (RING_W, LCD)
    return f'''<PartDraw x="0" y="0" width="{SIZE}" height="{SIZE}" {mode_variant(ambient)}
            {ring_arc(GHOST, thickness=w)}
            {ring_arc(lit, angle, thickness=w)}
            {ring_gaps()}
            </PartDraw>'''


def ring_both(angle):
    return f"{ring_draw(angle)}\n            {ring_draw(angle, ambient=True)}"


# Fraction (0..1) of a ranged / goal complication.
RANGED_FRAC = ("clamp(([COMPLICATION.RANGED_VALUE_VALUE] - [COMPLICATION.RANGED_VALUE_MIN]) / "
               "([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN]), 0, 1)")
GOAL_FRAC = "clamp([COMPLICATION.GOAL_PROGRESS_VALUE] / [COMPLICATION.GOAL_PROGRESS_TARGET_VALUE], 0, 1)"


def ring_bounds():
    """Ring slots must use a full-screen BoundingBox: Samsung's runtime clips a
    complication's drawing to its bounds, and with a ring-shaped BoundingArc
    (fine on the emulator) the ring was clipped away completely."""
    return f'<BoundingBox x="0" y="0" width="{SIZE}" height="{SIZE}" />'


def ring_slot():
    """The ring as a complication: any RANGED_VALUE or GOAL_PROGRESS provider
    fills it (whole segments only). Thick when interactive, thin and dim in
    always-on."""
    seg = lambda frac: f"floor({frac} * 60) * 6"
    return f'''<ComplicationSlot x="0" y="0" width="{SIZE}" height="{SIZE}" slotId="{RING_SLOT_ID}"
            displayName="slot_ring" isCustomizable="TRUE" supportedTypes="RANGED_VALUE GOAL_PROGRESS EMPTY">
            <DefaultProviderPolicy defaultSystemProvider="{RING_DEFAULT[0]}" defaultSystemProviderType="{RING_DEFAULT[1]}" />
            {ring_bounds()}
            <Complication type="RANGED_VALUE">
            {ring_both(seg(RANGED_FRAC))}
            </Complication>
            <Complication type="GOAL_PROGRESS">
            {ring_both(seg(GOAL_FRAC))}
            </Complication>
            <Complication type="EMPTY">
            {ring_both("0")}
            </Complication>
        </ComplicationSlot>'''


def pointer_draw(frac, ambient=False):
    """One ACCENT segment at the value's position (segment n = round(frac * 60),
    1-based), drawn over the ring so the white fill stays visible around it."""
    n = f"round({frac} * 60)"
    d = 2 * RING_R
    w, color = (AOD_RING_W, AOD_ACCENT) if ambient else (RING_W, ACCENT)
    return f'''<PartDraw x="0" y="0" width="{SIZE}" height="{SIZE}" {mode_variant(ambient)}
                <Transform target="alpha" value="({n} &gt; 0) ? 255 : 0" />
                <Arc centerX="{C}" centerY="{C}" width="{d}" height="{d}" startAngle="0" endAngle="6">
                    <Transform target="startAngle" value="({n} - 1) * 6" />
                    <Transform target="endAngle" value="{n} * 6" />
                    <Stroke color="{color}" thickness="{w}" cap="BUTT" />
                </Arc>
            {ring_gaps()}
            </PartDraw>'''


def pointer_both(frac):
    return f"{pointer_draw(frac)}\n            {pointer_draw(frac, ambient=True)}"


def pointer_slot():
    """Second ring complication: a single yellow segment marks its value.
    """
    return f'''<ComplicationSlot x="0" y="0" width="{SIZE}" height="{SIZE}" slotId="{POINTER_SLOT_ID}"
            displayName="slot_pointer" isCustomizable="TRUE" supportedTypes="RANGED_VALUE GOAL_PROGRESS EMPTY">
            <DefaultProviderPolicy defaultSystemProvider="{POINTER_DEFAULT[0]}" defaultSystemProviderType="{POINTER_DEFAULT[1]}" />
            {ring_bounds()}
            <Complication type="RANGED_VALUE">
            {pointer_both(RANGED_FRAC)}
            </Complication>
            <Complication type="GOAL_PROGRESS">
            {pointer_both(GOAL_FRAC)}
            </Complication>
        </ComplicationSlot>'''


def ring_options():
    # Complication slots only work as direct children of <Scene>, so the ring
    # slot is always there and "seconds" paints an opaque seconds ring over it.
    # 1px placeholder so the option is not empty (untested whether WFF needs it).
    return f'''<ListOption id="complication">
            <PartDraw x="0" y="0" width="1" height="1" alpha="0"><Rectangle x="0" y="0" width="1" height="1"><Fill color="{BG}" /></Rectangle></PartDraw>
            </ListOption>
            <ListOption id="seconds">
            {ring_draw(SECONDS_ANGLE)}
            </ListOption>'''


def complication_slot(slot_id, rect, provider, ptype, kind):
    """A rounded LCD sub-window.
    short/long: tall slots show title above value, compact ones icon + value.
    large: a detail panel - icon + title (segment font, accent colour) on top,
    a full-width value line below, progress bar for ranged values, full-size
    images. All text uses the narrow segment font (fits ~40% more chars).
    Panel values wrap onto two lines (maxLines="2"; wrapping only works
    without ellipsis); single-line slot text ends in an ellipsis."""
    x, y, w, h = rect
    large = kind == "large"
    half = large and w <= sz(200)
    tall = large or h >= sz(40)
    pad = sz(8 if large else 8)
    icon_s = sz(20 if large else 18 if tall else 16)
    # half panel: 14 chars ("MEDIA CONTROLS"); full panel: ~23 chars
    # Panel titles carry key values (e.g. the weather temperature): same size as the value.
    title_size = sz(21 if half else 23) if large else sz(10)
    # Panel values: large enough to read; wrap onto a second line when longer.
    text_size = sz(21 if half else 23) if large else sz(22 if tall else 20)
    text_lines = 2 if large else 1
    if large:
        icon_x, icon_y = pad, sz(8)
        title_x, title_y = pad + icon_s + sz(5), icon_y + min(0, (icon_s - title_size) // 2)
        title_row = max(icon_s, title_size)
        text_x = pad
        text_y = icon_y + icon_s + (h - icon_y - icon_s - text_size) // 2 - sz(3)
    else:
        text_x = pad + icon_s + sz(4)
        text_y = sz(16) if tall else (h - text_size) // 2
        icon_x, icon_y = pad, text_y + (text_size - icon_s) // 2
        title_x, title_y = text_x, sz(3)
    text_w = w - text_x - (pad if large else sz(6))
    title_w = w - title_x - (pad if large else sz(6))
    # Providers send either a monochrome icon (tinted to match) or a colour
    # "small image" (e.g. media, weather); draw whichever is present.
    icon = f'''<PartImage x="{icon_x}" y="{icon_y}" width="{icon_s}" height="{icon_s}">
                    <Image resource="[COMPLICATION.SMALL_IMAGE]" />
                </PartImage>
                <PartImage x="{icon_x}" y="{icon_y}" width="{icon_s}" height="{icon_s}" tintColor="{LABEL}">
                    <Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]" />
                </PartImage>'''
    title_font = (f'<Font family="lcd_segments_narrow" size="{title_size}" color="{ACCENT}">' if large else
                  f'<Font family="SYNC_TO_DEVICE" size="{title_size}" color="{LABEL}" weight="BOLD">')
    title = f'''<PartText x="{title_x}" y="{title_y}" width="{title_w}" height="{title_size + sz(2)}">
                    <Text align="START" ellipsis="TRUE">{title_font}
                        <Template>%s<Parameter expression="[COMPLICATION.TITLE]" /></Template>
                    </Font></Text>
                </PartText>''' if tall else ""
    clip = ' maxLines="2"' if text_lines > 1 else ' ellipsis="TRUE"'
    # The font's line height exceeds its size: give wrapped text 1.3 lines each.
    text_box_h = text_size if text_lines == 1 else round(text_lines * text_size * 1.3)
    if text_lines > 1:
        text_y = icon_y + title_row + sz(4)   # directly under the title, like a card
    text = f'''<PartText x="{text_x}" y="{text_y}" width="{text_w}" height="{text_box_h}">
                    <Text align="START"{clip}><Font family="lcd_segments_narrow" size="{text_size}" color="{LCD}">
                        <Template>%s<Parameter expression="[COMPLICATION.TEXT]" /></Template>
                    </Font></Text>
                </PartText>'''
    bar_h = sz(3 if large else 2)
    bar = f'''<PartDraw x="{text_x}" y="{h - bar_h - sz(4)}" width="{text_w}" height="{bar_h}">
                    <Rectangle x="0" y="0" width="{text_w}" height="{bar_h}"><Fill color="{GHOST}" /></Rectangle>
                    <Rectangle x="0" y="0" width="{text_w}" height="{bar_h}">
                        <Transform target="width" value="{RANGED_FRAC} * {text_w}" />
                        <Fill color="{ACCENT}" />
                    </Rectangle>
                </PartDraw>'''
    img = min(h - 8, sz(40))
    mono = min(h - 10, sz(32))
    types = {"short": "", "long": "LONG_TEXT ", "large": "LONG_TEXT PHOTO_IMAGE "}[kind] + \
        "SHORT_TEXT RANGED_VALUE SMALL_IMAGE MONOCHROMATIC_IMAGE EMPTY"
    extra = ""
    if kind in ("long", "large"):
        extra += f'''
            <Complication type="LONG_TEXT">
                {icon}
                {title if large else ""}
                {text}
            </Complication>'''
    if large:
        extra += f'''
            <Complication type="PHOTO_IMAGE">
                <PartImage x="{sz(4)}" y="{sz(4)}" width="{w - 2 * sz(4)}" height="{h - 2 * sz(4)}">
                    <Image resource="[COMPLICATION.PHOTO_IMAGE]" />
                </PartImage>
            </Complication>'''
    return f'''<ComplicationSlot x="{x}" y="{y}" width="{w}" height="{h}" slotId="{slot_id}"
            displayName="slot_{slot_id}" isCustomizable="TRUE" supportedTypes="{types}">
            <DefaultProviderPolicy defaultSystemProvider="{provider}" defaultSystemProviderType="{ptype}" />
            <BoundingBox x="0" y="0" width="{w}" height="{h}" />{extra}
            <Complication type="SHORT_TEXT">
                {icon}
                {title}
                {text}
            </Complication>
            <Complication type="RANGED_VALUE">
                {icon}
                {title}
                {text}
                {bar}
            </Complication>
            <Complication type="SMALL_IMAGE">
                <PartImage x="{(w - img) // 2}" y="{(h - img) // 2}" width="{img}" height="{img}">
                    <Image resource="[COMPLICATION.SMALL_IMAGE]" />
                </PartImage>
            </Complication>
            <Complication type="MONOCHROMATIC_IMAGE">
                <PartImage x="{(w - mono) // 2}" y="{(h - mono) // 2}" width="{mono}" height="{mono}" tintColor="{LCD}">
                    <Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]" />
                </PartImage>
            </Complication>
        </ComplicationSlot>'''


def slot_frames():
    """Faint rounded outlines marking the complication slots (interactive only)."""
    return "\n            ".join(
        f'<RoundRectangle x="{x}" y="{y}" width="{w}" height="{h}" cornerRadiusX="{sz(10)}" cornerRadiusY="{sz(10)}">'
        f'<Stroke color="{FRAME}" thickness="1" /></RoundRectangle>'
        for _, (x, y, w, h), *_ in SLOTS)


def aod_clock(right, y):
    """The only clock visible in ambient, built to the display-offload rules:
    one DigitalClock, leading-zero hh/mm, bitmap font of same-width 0-9 only,
    no Transform/Localization/seconds. The colon is static text."""
    mm_x = right - 2 * DIGIT_W
    colon_x = mm_x - COLON_W
    hh_x = colon_x - 2 * DIGIT_W
    return f'''<Group x="0" y="0" width="{SIZE}" height="{SIZE}" alpha="0" name="aod_clock">
            <Variant mode="AMBIENT" target="alpha" value="255" />
            <PartText x="{colon_x}" y="{y}" width="{COLON_W}" height="{DIGIT_H}">
                <Text align="CENTER">
                    <Font family="lcd_segments" size="{DIGIT_H}" color="{AOD_LCD}"><![CDATA[:]]></Font>
                </Text>
            </PartText>
            <DigitalClock x="{hh_x}" y="{y}" width="{right - hh_x}" height="{DIGIT_H}">
                <TimeText x="0" y="0" width="{2 * DIGIT_W}" height="{DIGIT_H}" format="hh" align="START">
                    <BitmapFont family="lcd_digits" size="{DIGIT_H}" />
                </TimeText>
                <TimeText x="{mm_x - hh_x}" y="0" width="{2 * DIGIT_W}" height="{DIGIT_H}" format="mm" align="START">
                    <BitmapFont family="lcd_digits" size="{DIGIT_H}" />
                </TimeText>
            </DigitalClock>
        </Group>'''


def dividers():
    """Horizontal rules between rows, inset to the panel circle."""
    out = []
    for y in DIVIDER_YS:
        half = math.sqrt((PANEL_R - 7) ** 2 - (y - C) ** 2) - 14
        out.append(f'<Line startX="{C - half:.0f}" startY="{y}" endX="{C + half:.0f}" endY="{y}">'
                   f'<Stroke color="{FRAME}" thickness="1" /></Line>')
    return "\n            ".join(out)


def tap_slot(slot_id, name, _label, box, provider):
    """Invisible complication slot: only its tap action matters."""
    x, y, w, h = box
    nothing = ('<PartDraw x="0" y="0" width="1" height="1" alpha="0">'
               f'<Rectangle x="0" y="0" width="1" height="1"><Fill color="{BG}" /></Rectangle></PartDraw>')
    bodies = "\n            ".join(f'<Complication type="{t}">{nothing}</Complication>' for t in TAP_TYPES.split())
    default = (f'\n            <DefaultProviderPolicy defaultSystemProvider="{provider}" defaultSystemProviderType="SHORT_TEXT" />'
               if provider != "EMPTY" else "")
    return f'''<ComplicationSlot x="{x}" y="{y}" width="{w}" height="{h}" slotId="{slot_id}"
            displayName="{name}" isCustomizable="TRUE" supportedTypes="{TAP_TYPES}">{default}
            <BoundingBox x="0" y="0" width="{w}" height="{h}" />
            {bodies}
        </ComplicationSlot>'''


def check_digit_pngs():
    """The always-on BitmapFont uses PNGs from gen_segment_font.py; they must be
    rendered at this layout's digit size or the clock would be misaligned."""
    import struct
    path = os.path.join(RES, "drawable-nodpi", "lcd_digit_0.png")
    with open(path, "rb") as f:
        w, h = struct.unpack(">II", f.read(24)[16:24])
    if (w, h) != (DIGIT_W, DIGIT_H):
        raise SystemExit(f"lcd_digit_*.png are {w}x{h}, layout needs {DIGIT_W}x{DIGIT_H}: "
                         f"set DIGIT_PX = {DIGIT_H} in tools/gen_segment_font.py and rerun it")


def tap_slots():
    return "\n        ".join(tap_slot(*t) for t in TAP_AREAS)


def slots():
    return "\n        ".join(complication_slot(*slot) for slot in SLOTS)


def build():

    ring_config_options = "\n            ".join(
        f'<ListOption id="{rid}" displayName="ring_{rid}" screenReaderText="ring_{rid}" />'
        for rid, _ in RING_MODES)

    bitmap_chars = "\n            ".join(
        f'<Character name="{d}" resource="lcd_digit_{d}" width="{DIGIT_W}" height="{DIGIT_H}" />'
        for d in "0123456789")

    return f'''<?xml version="1.0" encoding="utf-8"?>
<!-- GENERATED by tools/gen_watchface.py - edit the generator, not this file. -->
<!--
  SloppyShock: round negative-LCD watch face (Watch Face Format v2).
  Digits use res/font/lcd_segments.ttf (tools/gen_segment_font.py). Each segment
  readout has a dim "8" ghost underneath so unlit segments show, like a real
  LCD; ghost and value share box, size and END alignment, and the font is
  monospaced, so they line up.

  Always-on: only the "aod_clock" group's clock is visible, so the face
  qualifies for low-power display offload (a coprocessor draws the digits;
  everything else visible in ambient becomes a static, periodically refreshed
  layer). Seconds are hidden in ambient for the same reason. Samsung's runtime
  also refuses offload if anything visible in ambient uses a second/minute/hour
  data source (dates, AM/PM, battery and complications are fine).
-->
<WatchFace width="{SIZE}" height="{SIZE}">
    <Metadata key="CLOCK_TYPE" value="DIGITAL" />
    <Metadata key="PREVIEW_TIME" value="10:08:32" />

    <UserConfigurations>
        <ListConfiguration id="ring_mode" displayName="ring_label" screenReaderText="ring_label" defaultValue="{RING_MODES[0][0]}">
            {ring_config_options}
        </ListConfiguration>
    </UserConfigurations>

    <BitmapFonts>
        <BitmapFont name="lcd_digits">
            {bitmap_chars}
        </BitmapFont>
    </BitmapFonts>

    <Scene backgroundColor="{BG}">
        <!-- Level ring, chosen in the editor: a complication (any ranged/goal
             provider; battery by default) or seconds. Dim full ring, lit arc,
             then gap lines cut it into 60 segments. Hidden in ambient.
             The unlit track is also drawn on its own underneath, so the ring
             stays visible while a provider has no data (or none is picked). -->
        <PartDraw x="0" y="0" width="{SIZE}" height="{SIZE}" name="ring_track">
            <Variant mode="AMBIENT" target="alpha" value="0" />
            {ring_arc(GHOST)}
            {ring_gaps()}
        </PartDraw>
        <PartDraw x="0" y="0" width="{SIZE}" height="{SIZE}" alpha="0" name="ring_track_aod">
            <Variant mode="AMBIENT" target="alpha" value="255" />
            {ring_arc(GHOST, thickness=AOD_RING_W)}
            {ring_gaps()}
        </PartDraw>
        {ring_slot()}
        <Group x="0" y="0" width="{SIZE}" height="{SIZE}" name="seconds_ring">
            <Variant mode="AMBIENT" target="alpha" value="0" />
            <ListConfiguration id="ring_mode">
            {ring_options()}
            </ListConfiguration>
        </Group>
        {pointer_slot() if HAS_POINTER else ""}

        <!-- Quarter markers on the ring -->
        <PartDraw x="0" y="0" width="{SIZE}" height="{SIZE}" name="quarter_marks">
            <Variant mode="AMBIENT" target="alpha" value="0" />
            <Rectangle x="{C - 3}" y="{C - RING_R - RING_W / 2}" width="6" height="{RING_W}"><Fill color="{RED}" /></Rectangle>
        </PartDraw>

        <!-- Circular LCD panel -->
        <PartDraw x="0" y="0" width="{SIZE}" height="{SIZE}" name="lcd_panel">
            <Variant mode="AMBIENT" target="alpha" value="0" />
            <Ellipse x="{C - PANEL_R}" y="{C - PANEL_R}" width="{2 * PANEL_R}" height="{2 * PANEL_R}">
                <Fill color="{PANEL}" />
                <Stroke color="{FRAME}" thickness="2" />
            </Ellipse>
            <Ellipse x="{C - PANEL_R + 7}" y="{C - PANEL_R + 7}" width="{2 * PANEL_R - 14}" height="{2 * PANEL_R - 14}">
                <Stroke color="{RED}" thickness="1.5" />
            </Ellipse>
            {dividers()}
            {slot_frames()}
        </PartDraw>


        <!-- Unlit LCD segments, hidden in ambient mode -->
        <Group x="0" y="0" width="{SIZE}" height="{SIZE}" name="ghost_segments">
            <Variant mode="AMBIENT" target="alpha" value="0" />
            {seg_text(DAY_X, DATE_Y, DAY_W, DATE_SIZE, "###", color=GHOST)}
            {seg_text(DATE_X, DATE_Y, DATE_W, DATE_SIZE, "88-88", color=GHOST)}
            {seg_text(MAIN_X, MAIN_Y, MAIN_W, MAIN_SIZE, "88:88", color=GHOST)}
            {seg_text(SIDE_X, SEC_Y, SEC_W, SEC_SIZE, "88", color=GHOST)}
        </Group>

        <Group x="0" y="0" width="{SIZE}" height="{SIZE}" name="lcd_content">
            <!-- TOP: day of week (14-segment letters) + date (DD-MM), centred -->
            {seg_text(DAY_X, DATE_Y, DAY_W, DATE_SIZE, template='%s<Parameter expression="[DAY_OF_WEEK_S]" />', color=ACCENT)}
            {seg_text(DATE_X, DATE_Y, DATE_W, DATE_SIZE, template='%s-%s<Parameter expression="[DAY_Z]" /><Parameter expression="[MONTH_Z]" />')}

            <!-- MIDDLE: local time (interactive only; see aod_clock), AM/PM and seconds -->
            <DigitalClock x="{MAIN_X}" y="{MAIN_Y}" width="{MAIN_W}" height="{MAIN_SIZE}">
                <Variant mode="AMBIENT" target="alpha" value="0" />
                <TimeText x="0" y="0" width="{MAIN_W}" height="{MAIN_SIZE}" format="h:mm" align="END">
                    <Font family="lcd_segments" size="{MAIN_SIZE}" color="{LCD}" />
                </TimeText>
            </DigitalClock>
            <!-- AM/PM in 14-segment letters; TimeText has no "a" format. Hidden in 24h mode. -->
            <PartText x="{SIDE_X}" y="{MAIN_Y + 2}" width="{SEC_W}" height="{AMPM_SIZE}">
                <Transform target="alpha" value="[IS_24_HOUR_MODE] ? 0 : 255" />
                <Text align="START">
                    <Font family="lcd_segments" size="{AMPM_SIZE}" color="{ACCENT}">
                        <Template>%s<Parameter expression="[AMPM_STRING]" /></Template>
                    </Font>
                </Text>
            </PartText>
            <DigitalClock x="{SIDE_X}" y="{SEC_Y}" width="{SEC_W}" height="{SEC_SIZE}">
                <Variant mode="AMBIENT" target="alpha" value="0" />
                <TimeText x="0" y="0" width="{SEC_W}" height="{SEC_SIZE}" format="ss" align="END">
                    <Font family="lcd_segments" size="{SEC_SIZE}" color="{LCD}" />
                </TimeText>
            </DigitalClock>

        </Group>

        <!-- Complication slots: row A pair, row B pair (world clock by default on
             the right), row C wide (long text) -->
        {slots()}

        <!-- Invisible tap areas (configurable shortcuts) over the time and date -->
        {tap_slots()}

        {aod_clock(MAIN_RIGHT, MAIN_Y)}
    </Scene>
</WatchFace>
'''


def strings(face_name):
    lines = ['<resources>',
             f'    <string name="watch_face_name">{face_name}</string>',
             '    <string name="ring_label">Ring</string>']
    lines += [f'    <string name="ring_{rid}">{name}</string>' for rid, name in RING_MODES]
    lines += [f'    <string name="slot_{sid}">{SLOT_NAMES[sid]} complication</string>' for sid, *_ in SLOTS]
    lines += ['    <string name="slot_ring">Ring</string>',
              ] + (['    <string name="slot_pointer">Ring marker (yellow)</string>'] if HAS_POINTER else [])
    lines += [f'    <string name="{name}">{label}</string>' for _, name, label, *_ in TAP_AREAS]
    return "\n".join(lines + ['</resources>', ''])


if __name__ == "__main__":
    check_digit_pngs()
    for variant, (face_name, variant_slots, HAS_POINTER) in VARIANTS.items():
        SLOTS = variant_slots
        count = len(SLOTS) + len(TAP_AREAS) + 1 + HAS_POINTER   # + ring (+ marker)
        if count > MAX_SLOTS:
            raise SystemExit(f"{variant}: {count} complication slots, WFF allows {MAX_SLOTS}")
        res = os.path.join(SRC, variant, "res")
        for sub in ("raw", "values"):
            os.makedirs(os.path.join(res, sub), exist_ok=True)
        with open(os.path.join(res, "raw", "watchface.xml"), "w") as f:
            f.write(build())
        with open(os.path.join(res, "values", "strings.xml"), "w") as f:
            f.write(strings(face_name))
        print(f"wrote {variant}: watchface.xml and strings.xml")
