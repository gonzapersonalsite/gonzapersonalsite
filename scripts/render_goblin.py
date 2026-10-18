"""Render the animated pixel goblin shown at the top of the profile README.

Story (one loop): a side-view 2D portal opens on the left and the goblin strolls
out of it, leans and pulls a laptop out from behind its back, sets it down in
front of itself, opens it and types with its two stubby hands, looks left and
right, closes the laptop, tucks it behind its back again and runs into a portal
that opens on the right.

Usage: python scripts/render_goblin.py assets
Writes goblin.svg (light) and goblin-dark.svg (dark) into the given directory.

All sprite coordinates are in sprite pixels (U screen pixels each), relative to
the goblin's top-left corner.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

U = 3  # screen pixels per sprite pixel
DURATION = 16  # seconds per loop
WIDTH = 560
TOP_MARGIN = 5  # sprite pixels above the goblin, room for the floating code glyphs
SPRITE_ROWS = 13
HEIGHT = (TOP_MARGIN + SPRITE_ROWS + 2) * U

EASE_OUT = "0 0 0.58 1"
EASE_IN = "0.42 0 1 1"
EASE_IN_OUT = "0.42 0 0.58 1"
LINEAR = "0 0 1 1"

# Timeline (fractions of DURATION)
WALK_END = 0.20
REACH = (0.21, 0.24)  # leans and reaches behind its back
PULL = (0.24, 0.28, 0.32)  # behind the back -> out at its side -> down in front of it
LID_OPEN = (0.32, 0.36)
TYPING = (0.36, 0.62)
LOOK = (0.62, 0.74)
LID_CLOSE = (0.76, 0.80)
STASH = (0.80, 0.84, 0.88)  # in front -> out at its side -> behind the back
RUN = (0.89, 0.97)
STEP_SECONDS = 0.08  # a quarter of a stride: lift, plant, lift the other foot, plant
TAP_SECONDS = 0.14  # half a typing beat
GAIT_WINDOWS = [(0.0, WALK_END, STEP_SECONDS), (RUN[0], RUN[1], STEP_SECONDS)]

# Laptop offsets (sprite pixels) relative to its resting place in front of the goblin.
LAPTOP_X = 14  # left edge of the deck when resting in front of the goblin
BEHIND = (-11, -2)  # tucked behind the goblin's back
BESIDE = (7, -2)  # held out at its right side, clear of the body
RESTING = (0, 0)

# Goblin body, left half (mirrored). g body, h highlight, e inner ear, s shade
HALF_SPRITE = [
    "........gggg",
    "gg....gggggg",
    ".eeh.ggggggg",
    "..eehggggggg",
    "...eeggggggg",
    "....gggggggg",
    "....gggggggg",
    "....gggggggg",
    "....sggggggg",
    "....sggggggg",
    ".....sgggggg",
]


@dataclass(frozen=True)
class Theme:
    body: str
    highlight: str
    ear: str
    shade: str
    blush: str
    ink: str
    lid: str
    lid_light: str
    lid_dark: str
    deck: str
    keys: str
    base: str
    logo: str
    glyph: str
    shadow_opacity: float
    portal_glow: str
    portal_rim: str
    portal_core: str


DARK = Theme(
    body="#82a353", highlight="#9cbf63", ear="#b3d47a", shade="#5f7d3a", blush="#e69a80",
    ink="#0b0b0b", lid="#7d7873", lid_light="#cfc9c3", lid_dark="#55504c", deck="#b4aea8",
    keys="#45413e", base="#5e5955", logo="#efeae5", glyph="#d4a373", shadow_opacity=0.55,
    portal_glow="#4b35b8", portal_rim="#5de0e6", portal_core="#e0f7fa",
)
LIGHT = Theme(
    body="#82a353", highlight="#9cbf63", ear="#b3d47a", shade="#5f7d3a", blush="#e69a80",
    ink="#1f2328", lid="#7d7873", lid_light="#c4beb8", lid_dark="#55504c", deck="#a8a29c",
    keys="#45413e", base="#5e5955", logo="#efeae5", glyph="#9a6b2f", shadow_opacity=0.18,
    portal_glow="#90caf9", portal_rim="#1976d2", portal_core="#fff8e1",
)


# --- SVG helpers -----------------------------------------------------------------------------

def kt(*values: float) -> str:
    return ";".join(f"{v:.4f}" for v in values)


def px(x: float, y: float, w: float, h: float, fill: str) -> str:
    return f'<rect x="{x * U:g}" y="{y * U:g}" width="{w * U:g}" height="{h * U:g}" fill="{fill}"/>'


def on_timeline(kind: str, attribute: str, values: list[str], times: list[float],
                splines: list[str] | None = None) -> str:
    """One animation on the main loop. kind is 'animate' or a transform type (translate, scale)."""
    tag = "animate" if kind == "animate" else "animateTransform"
    type_attr = "" if kind == "animate" else f' type="{kind}"'
    mode = f' calcMode="spline" keySplines="{";".join(splines)}"' if splines else ""
    return (
        f'<{tag} attributeName="{attribute}"{type_attr} dur="{DURATION}s" repeatCount="indefinite"'
        f'{mode} values="{";".join(values)}" keyTimes="{kt(*times)}"/>'
    )


def visible(windows: list[tuple[float, float]]) -> str:
    """Discrete opacity: 1 inside any of the windows, 0 elsewhere."""
    values, times = ["0"], [0.0]
    for start, end in windows:
        values.append("1")
        times.append(start)
        if end < 1:
            values.append("0")
            times.append(end)
    return (
        f'<animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" calcMode="discrete" '
        f'values="{";".join(values)}" keyTimes="{kt(*times)}"/>'
    )


def pivot(x: float, y: float, inner: str, animation: str) -> str:
    """Apply a scale animation around the sprite point (x, y)."""
    return (
        f'<g transform="translate({x * U:g} {y * U:g})"><g>{animation}'
        f'<g transform="translate({-x * U:g} {-y * U:g})">{inner}</g></g></g>'
    )


def beat_motion(windows: list[tuple[float, float, float]], pattern: list[int]) -> str:
    """Vertical offsets on the main loop, one pattern step per beat inside each (start, end, beat) window.

    Body and legs share the same windows and beats, so they always stay in step with each other.
    pattern holds offsets in sprite pixels (negative = up) and repeats; outside the windows it is 0.
    """
    values, times = ["0 0"], [0.0]
    for start, end, beat_seconds in windows:
        if start > times[-1]:
            values.append("0 0")
            times.append(start)
        step = beat_seconds / DURATION
        t, k = start, 0
        while t + step <= end:
            t += step
            values.append(f"0 {pattern[k % len(pattern)] * U}")
            times.append(t)
            k += 1
        if values[-1] != "0 0":
            values.append("0 0")
            times.append(min(t + step / 2, end))
    if times[-1] < 1:
        values.append("0 0")
        times.append(1.0)
    return on_timeline("translate", "transform", values, times)


# --- Goblin parts ----------------------------------------------------------------------------

def body_pixels(t: Theme) -> str:
    colors = {"g": t.body, "h": t.highlight, "e": t.ear, "s": t.shade}
    parts = []
    for y, half in enumerate(HALF_SPRITE):
        row = half + half[::-1]
        x = 0
        while x < len(row):
            char, run = row[x], 1
            while x + run < len(row) and row[x + run] == char:
                run += 1
            if char in colors:
                parts.append(px(x, y, run, 1, colors[char]))
            x += run
    parts += [px(6, 7, 1, 1, t.blush), px(17, 7, 1, 1, t.blush), px(11, 7, 2, 1, t.ink)]
    return "".join(parts)


def eyes(t: Theme) -> str:
    """Happy closed eyes; open eyes glancing left and right while looking around."""
    closed = (
        px(6, 6, 1, 1, t.ink) + px(7, 5, 2, 1, t.ink) + px(9, 6, 1, 1, t.ink)
        + px(14, 6, 1, 1, t.ink) + px(15, 5, 2, 1, t.ink) + px(17, 6, 1, 1, t.ink)
    )
    opened = px(7, 5, 2, 2, t.ink) + px(15, 5, 2, 2, t.ink)
    start, end = LOOK
    step = (end - start) / 4
    glance = on_timeline(
        "translate", "transform",
        ["0 0", "0 0", f"{-U} 0", f"{U} 0", f"{-U} 0", "0 0", "0 0"],
        [0, start, start + step, start + 2 * step, start + 3 * step, end, 1],
        [LINEAR, EASE_IN_OUT, EASE_IN_OUT, EASE_IN_OUT, EASE_IN_OUT, LINEAR],
    )
    return (
        f'<g>{closed}{visible([(0, start), (end, 1)])}</g>'
        f'<g opacity="0">{opened}{glance}{visible([(start, end)])}</g>'
    )


def lean() -> str:
    """The body leans towards its back while reaching for the laptop and while tucking it away."""
    values = ["0 0", "0 0", f"{U} 0", f"{U} 0", "0 0", "0 0", f"{U} 0", "0 0", "0 0"]
    times = [0, REACH[0], REACH[1], PULL[1], PULL[2], STASH[1], STASH[1] + 0.02, STASH[2], 1]
    splines = [LINEAR, EASE_OUT, LINEAR, EASE_IN_OUT, LINEAR, EASE_OUT, EASE_IN_OUT, LINEAR]
    return on_timeline("translate", "transform", values, times, splines)


def feet(t: Theme) -> tuple[str, str]:
    # The top row tucks under the body so a planted foot stays attached while the body rises.
    left = px(6, 10, 2, 3, t.body) + px(6, 12, 2, 1, t.shade)
    right = px(16, 10, 2, 3, t.body) + px(16, 12, 2, 1, t.shade)
    return left, right


def legs(t: Theme) -> str:
    """Both feet take turns lifting while walking and running; the body rises on every lift."""
    left, right = feet(t)
    left_step = beat_motion(GAIT_WINDOWS, [-1, 0, 0, 0])
    right_step = beat_motion(GAIT_WINDOWS, [0, 0, -1, 0])
    return f'<g>{left}{left_step}</g><g>{right}{right_step}</g>'


def stub_hand(t: Theme, x: int, y: int) -> str:
    """A hand drawn exactly like a foot: a 2x2 stub with a shaded bottom row."""
    return px(x, y, 2, 2, t.body) + px(x, y + 1, 2, 1, t.shade)


def laptop_motion() -> str:
    points = [BEHIND, BEHIND, BESIDE, RESTING, RESTING, BESIDE, BEHIND, BEHIND]
    times = [0, PULL[0], PULL[1], PULL[2], STASH[0], STASH[1], STASH[2], 1]
    splines = [LINEAR, EASE_OUT, EASE_IN_OUT, LINEAR, EASE_IN_OUT, EASE_IN, LINEAR]
    return on_timeline("translate", "transform", [f"{dx * U} {dy * U}" for dx, dy in points], times, splines)


def laptop_pixels(t: Theme) -> str:
    """A laptop in three-quarter view, the lid's back facing us and leaning back."""
    x = LAPTOP_X
    deck = (
        px(x, 11, 16, 1, t.deck)
        + "".join(px(k, 11, 1, 1, t.keys) for k in range(x + 1, x + 7, 2))
        + px(x - 1, 12, 17, 1, t.base)
    )
    closed_lid = px(x + 1, 10, 15, 1, t.lid) + px(x + 1, 10, 1, 1, t.lid_light)
    lid_rows = []
    for row in range(3, 11):
        x0 = x + 7 + (10 - row) // 2  # every two rows up the lid shifts one pixel back
        if row == 3:
            lid_rows.append(px(x0, row, 8, 1, t.lid_light))
        else:
            lid_rows.append(px(x0, row, 1, 1, t.lid_light) + px(x0 + 1, row, 6, 1, t.lid)
                            + px(x0 + 7, row, 1, 1, t.lid_dark))
    cx = x + 13
    logo = px(cx, 5, 1, 1, t.logo) + px(cx - 1, 6, 3, 1, t.logo) + px(cx, 7, 1, 1, t.logo)
    swing = on_timeline(
        "scale", "transform",
        ["1 0", "1 0", "1 1", "1 1", "1 0", "1 0"],
        [0, LID_OPEN[0], LID_OPEN[1], LID_CLOSE[0], LID_CLOSE[1], 1],
        [LINEAR, EASE_OUT, LINEAR, EASE_IN, LINEAR],
    )
    lid = pivot(0, 11, "".join(lid_rows) + logo, swing)
    closed = f'<g>{closed_lid}{visible([(0, LID_OPEN[0] + 0.01), (LID_CLOSE[1] - 0.01, 1)])}</g>'
    # The hand holding the laptop's left end while it is carried.
    holding = f'<g>{stub_hand(t, x - 2, 9)}{visible([(PULL[0], PULL[2]), (STASH[0], STASH[2])])}</g>'
    return deck + closed + lid + holding


def laptop(t: Theme, windows: list[tuple[float, float]]) -> str:
    """The laptop and the hand carrying it, shown only during the given windows.

    It is drawn twice: behind the body (while it comes from / goes to the goblin's back)
    and in front of the body (once it is clear of it), switching layers at its side.
    """
    return f'<g opacity="0"><g>{laptop_motion()}{laptop_pixels(t)}</g>{visible(windows)}</g>'


def typing_hands(t: Theme) -> str:
    """Two stubby hands, just like its feet, tapping the keys in turn."""
    taps = []
    for i, x in enumerate((LAPTOP_X + 1, LAPTOP_X + 4)):
        begin = i * TAP_SECONDS
        taps.append(
            f'<g>{stub_hand(t, x, 10)}<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 {U};0 0" keyTimes="0;0.5;1" calcMode="spline" '
            f'keySplines="{EASE_IN_OUT};{EASE_IN_OUT}" dur="{2 * TAP_SECONDS}s" begin="{begin}s" '
            f'repeatCount="indefinite"/></g>'
        )
    return f'<g opacity="0">{"".join(taps)}{visible([(LID_OPEN[1] - 0.01, LID_CLOSE[0])])}</g>'


def glyphs(t: Theme) -> str:
    items = "".join(
        f'<text x="{(LAPTOP_X + 6 + i * 4) * U}" y="{-1 * U}" font-family="ui-monospace, Menlo, Consolas, monospace" '
        f'font-size="9" fill="{t.glyph}" opacity="0">{text}'
        f'<animate attributeName="opacity" values="0;1;0" dur="1.2s" begin="{i * 0.4}s" repeatCount="indefinite"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 6;0 -6" dur="1.2s" '
        f'begin="{i * 0.4}s" repeatCount="indefinite"/></text>'
        for i, text in enumerate(("{}", "&lt;/&gt;", ";"))
    )
    return f'<g opacity="0">{items}{visible([TYPING])}</g>'


def shadow(t: Theme) -> str:
    """Soft ground shadow that stretches under the laptop while it rests in front of the goblin."""
    times = [0, PULL[1], PULL[2], STASH[0], STASH[1], 1]
    rx = on_timeline("animate", "rx", [f"{v * U}" for v in (13, 13, 17, 17, 13, 13)], times)
    cx = on_timeline("animate", "cx", [f"{v * U}" for v in (12, 12, 16, 16, 12, 12)], times)
    return (
        f'<ellipse cx="{12 * U}" cy="{13 * U}" rx="{13 * U}" ry="{U}" fill="#000" '
        f'opacity="{t.shadow_opacity}">{rx}{cx}</ellipse>'
    )


def portal_particle(x: float, y: float, w: float, h: float, fill: str,
                    dx1: float, dy1: float, dx2: float, dy2: float,
                    open_start: float, close_end: float, phase: float) -> str:
    span = close_end - open_start
    t1 = round(open_start + span * (0.18 + phase), 4)
    t2 = round(open_start + span * (0.44 + phase), 4)
    t3 = round(open_start + span * (0.70 + phase), 4)
    p1 = f"{dx1 * U:g} {dy1 * U:g}"
    p2 = f"{dx2 * U:g} {dy2 * U:g}"
    times = [0, open_start, t1, t2, t3, close_end, 1]
    splines = [LINEAR, EASE_IN_OUT, EASE_IN_OUT, EASE_IN_OUT, EASE_IN_OUT, LINEAR]
    motion = on_timeline("translate", "transform", ["0 0", "0 0", p1, p2, p1, "0 0", "0 0"], times, splines)
    opacity = on_timeline("animate", "opacity", ["0.72", "0.72", "1", "0.72", "1", "0.72", "0.72"], times, splines)
    return (
        f'<g>{motion}<rect x="{x * U:g}" y="{y * U:g}" width="{w * U:g}" height="{h * U:g}" '
        f'fill="{fill}">{opacity}</rect></g>'
    )


def ring_scale(open_start: float, open_end: float, close_start: float, close_end: float) -> str:
    return on_timeline(
        "scale", "transform",
        ["0 0", "0 0", "1 1", "1 1", "0 0", "0 0"],
        [0, open_start, open_end, close_start, close_end, 1],
        [LINEAR, EASE_OUT, LINEAR, EASE_IN, LINEAR],
    )


def portal(side: str, portal_x: int, portal_y: int, t: Theme,
           open_start: float, open_full: float, close_start: float, close_end: float) -> str:
    inward = 1 if side == "entry" else -1
    glow = "".join([
        px(0, -8, 1, 1, t.portal_glow),
        px(-1, -7, 3, 1, t.portal_glow),
        px(-2, -6, 5, 2, t.portal_glow),
        px(-3, -4, 7, 9, t.portal_glow),
        px(-2, 5, 5, 2, t.portal_glow),
        px(-1, 7, 3, 1, t.portal_glow),
        px(-2, 8, 5, 1, t.portal_glow),
    ])
    rim = "".join([
        px(0, -7, 1, 1, t.portal_rim),
        px(-1, -6, 3, 2, t.portal_rim),
        px(-2, -4, 5, 9, t.portal_rim),
        px(-1, 5, 3, 2, t.portal_rim),
        px(-1, 7, 3, 2, t.portal_rim),
    ])
    core = "".join([
        px(0, -6, 1, 2, t.portal_core),
        px(-1, -4, 3, 9, t.portal_core),
        px(0, 5, 1, 3, t.portal_core),
        px(-1, -3, 1, 2, t.portal_glow),
        px(1, -1, 1, 2, t.portal_glow),
        px(-1, 1, 1, 2, t.portal_glow),
        px(1, 3, 1, 1, t.portal_glow),
        px(0, 8, 1, 1, t.portal_core),
    ])
    particles = "".join([
        portal_particle(inward * 3, -6, 1, 1, t.portal_core, inward * 1, -0.5, -inward * 0.5, 0.5, open_start, close_end, 0.00),
        portal_particle(inward * 4, -3, 1, 2, t.portal_rim, inward * 1, 0.5, -inward * 0.5, -0.5, open_start, close_end, 0.03),
        portal_particle(-inward * 3, -5, 1, 1, t.portal_core, -inward * 0.5, -0.5, inward * 0.5, 0.5, open_start, close_end, 0.06),
        portal_particle(inward * 4, 0, 2, 1, t.portal_core, inward * 1, -0.5, -inward * 0.5, 0.5, open_start, close_end, 0.02),
        portal_particle(inward * 3, 3, 1, 2, t.portal_rim, inward * 1, 0.5, -inward * 0.5, -0.5, open_start, close_end, 0.05),
        portal_particle(-inward * 3, 3, 1, 1, t.portal_glow, -inward * 0.5, 0.5, inward * 0.5, -0.5, open_start, close_end, 0.08),
        portal_particle(inward * 4, 6, 1, 1, t.portal_core, inward * 1, -0.5, -inward * 0.5, 0.5, open_start, close_end, 0.04),
        portal_particle(inward * 1, -8, 1, 1, t.portal_core, inward * 0.5, -0.5, -inward * 0.5, 0.5, open_start, close_end, 0.07),
    ])
    open_span = open_full - open_start
    close_span = close_end - close_start
    core_s = ring_scale(
        open_start,
        round(open_start + open_span * 0.64, 4),
        round(close_start + close_span * 0.36, 4),
        close_end,
    )
    rim_s = ring_scale(
        round(open_start + open_span * 0.18, 4),
        round(open_start + open_span * 0.82, 4),
        round(close_start + close_span * 0.18, 4),
        round(close_end - close_span * 0.18, 4),
    )
    outer_s = ring_scale(
        round(open_start + open_span * 0.36, 4),
        open_full,
        close_start,
        round(close_end - close_span * 0.36, 4),
    )
    pt1 = round(open_start + (close_end - open_start) * 0.25, 4)
    pt2 = round(open_start + (close_end - open_start) * 0.50, 4)
    pt3 = round(open_start + (close_end - open_start) * 0.75, 4)
    core_pulse = on_timeline(
        "animate", "opacity",
        ["1", "1", "0.86", "1", "0.86", "1", "1"],
        [0, open_start, pt1, pt2, pt3, close_end, 1],
        [LINEAR, EASE_IN_OUT, EASE_IN_OUT, EASE_IN_OUT, EASE_IN_OUT, LINEAR],
    )
    outer_layer = pivot(0.5, 0.5, glow + particles, outer_s)
    rim_layer = pivot(0.5, 0.5, rim, rim_s)
    core_layer = pivot(0.5, 0.5, f"<g>{core}{core_pulse}</g>", core_s)
    return (
        f'<g transform="translate({portal_x} {portal_y})" opacity="0">'
        f'{visible([(open_start, close_end)])}{outer_layer}{rim_layer}{core_layer}</g>'
    )


def render(t: Theme) -> str:
    start_x, stop_x, exit_x = -45 * U, WIDTH // 2 - 15 * U, WIDTH + 10 * U
    y = TOP_MARGIN * U
    portal_margin = 6 * U
    entry_portal_x = portal_margin
    exit_portal_x = WIDTH - portal_margin
    portal_center_y = 9 * U

    entry_span = stop_x - start_x
    t_entry_clear = WALK_END * ((entry_portal_x + 3 - start_x) / entry_span)
    entry_p = portal(
        "entry", entry_portal_x, portal_center_y, t,
        0.002, 0.044, round(t_entry_clear + 0.075, 4), round(t_entry_clear + 0.123, 4),
    )

    exit_span = exit_x - stop_x
    t_exit_touch = RUN[0] + (RUN[1] - RUN[0]) * ((exit_portal_x - 66 - stop_x) / exit_span)
    t_exit_clear = round(RUN[0] + (RUN[1] - RUN[0]) * 0.925, 4)
    exit_p = portal(
        "exit", exit_portal_x, portal_center_y, t,
        round(t_exit_touch - 0.135, 4), round(t_exit_touch - 0.087, 4), t_exit_clear, 0.998,
    )

    travel = on_timeline(
        "translate", "transform",
        [f"{start_x} {y}", f"{stop_x} {y}", f"{stop_x} {y}", f"{exit_x} {y}", f"{exit_x} {y}"],
        [0, WALK_END, RUN[0], RUN[1], 1],
        [EASE_OUT, LINEAR, EASE_IN, LINEAR],
    )
    body_bounce = beat_motion(GAIT_WINDOWS[:1] + [(TYPING[0], TYPING[1], TAP_SECONDS)] + GAIT_WINDOWS[1:], [-1, 0])
    body = f'<g>{lean()}<g>{body_pixels(t)}{eyes(t)}{body_bounce}</g></g>'
    behind = laptop(t, [(PULL[0], PULL[1]), (STASH[1], STASH[2])])
    in_front = laptop(t, [(PULL[1], STASH[1])])
    goblin = f'{shadow(t)}{behind}{body}{legs(t)}{in_front}{typing_hands(t)}{glyphs(t)}'
    clip_width = exit_portal_x - entry_portal_x
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" shape-rendering="crispEdges" role="img" '
        f'aria-label="A pixel goblin emerges from a portal, pulls a laptop from behind its back, '
        f'codes for a while, looks around and leaps into another portal">'
        f'<defs><clipPath id="portal-clip"><rect x="{entry_portal_x}" y="0" width="{clip_width}" height="{HEIGHT}"/></clipPath></defs>'
        f'<g clip-path="url(#portal-clip)"><g transform="translate({start_x} {y})">{travel}{goblin}</g></g>'
        f'{entry_p}{exit_p}</svg>'
    )


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: render_goblin.py <output_dir>")
    output_dir = Path(sys.argv[1])
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "goblin.svg").write_text(render(LIGHT), encoding="utf-8")
    (output_dir / "goblin-dark.svg").write_text(render(DARK), encoding="utf-8")


if __name__ == "__main__":
    main()
