"""Render the animated pixel goblin shown at the top of the profile README.

Story (one loop): the goblin strolls in, reaches behind its back and pulls out a
laptop, sets it down, opens it and types with both hands, looks left and right,
closes the laptop, stashes it behind its back again and runs off.

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
CARRY_OUT = (0.23, 0.28, 0.31)  # starts behind the back -> held out at its side -> set on the ground
LID_OPEN = (0.31, 0.35)
ARMS_OUT = (0.35, 0.38)
LOOK = (0.62, 0.74)
ARMS_IN = (0.74, 0.76)
LID_CLOSE = (0.76, 0.80)
CARRY_BACK = (0.80, 0.83, 0.88)  # lift -> back behind the back
RUN = (0.89, 0.97)
STEP_SECONDS = 0.16  # half a stride

# Carry offsets of the laptop (sprite pixels) while it is behind the back / held at the side.
HIDDEN_DX, HELD_DY = -19, -3
LAPTOP_X = 23  # left edge of the laptop deck on the ground

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


DARK = Theme(
    body="#82a353", highlight="#9cbf63", ear="#b3d47a", shade="#5f7d3a", blush="#e69a80",
    ink="#0b0b0b", lid="#7d7873", lid_light="#cfc9c3", lid_dark="#55504c", deck="#b4aea8",
    keys="#45413e", base="#5e5955", logo="#efeae5", glyph="#d4a373", shadow_opacity=0.55,
)
LIGHT = Theme(
    body="#82a353", highlight="#9cbf63", ear="#b3d47a", shade="#5f7d3a", blush="#e69a80",
    ink="#1f2328", lid="#7d7873", lid_light="#c4beb8", lid_dark="#55504c", deck="#a8a29c",
    keys="#45413e", base="#5e5955", logo="#efeae5", glyph="#9a6b2f", shadow_opacity=0.18,
)


# --- SVG helpers -----------------------------------------------------------------------------

def kt(*values: float) -> str:
    return ";".join(f"{v:.4f}" for v in values)


def px(x: float, y: float, w: float, h: float, fill: str, inner: str = "") -> str:
    attrs = f'x="{x * U:g}" y="{y * U:g}" width="{w * U:g}" height="{h * U:g}" fill="{fill}"'
    return f"<rect {attrs}>{inner}</rect>" if inner else f"<rect {attrs}/>"


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


def press(seconds: float, begin: float, rest: int, pressed: int) -> str:
    """Looping height change so a forearm reaches down to the keys and back."""
    return (
        f'<animate attributeName="height" values="{rest * U};{pressed * U};{rest * U}" '
        f'keyTimes="0;0.5;1" calcMode="spline" keySplines="{EASE_IN_OUT};{EASE_IN_OUT}" '
        f'dur="{seconds}s" begin="{begin}s" repeatCount="indefinite"/>'
    )


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


def stride_bob() -> str:
    """Body bob synced to footsteps while walking and running, still otherwise."""
    values, times = ["0 0"], [0.0]
    step = STEP_SECONDS / DURATION
    for start, end in ((0.0, WALK_END), RUN):
        if start > times[-1]:
            values.append("0 0")
            times.append(start)
        t, up = start, True
        while t + step <= end:
            t += step
            values.append(f"0 {-U}" if up else "0 0")
            times.append(t)
            up = not up
        if values[-1] != "0 0":
            values.append("0 0")
            times.append(min(t + step / 2, end))
    if times[-1] < 1:
        values.append("0 0")
        times.append(1.0)
    return on_timeline("translate", "transform", values, times)


def legs(t: Theme) -> str:
    left = px(6, 11, 2, 2, t.body) + px(6, 12, 2, 1, t.shade)
    right = px(16, 11, 2, 2, t.body) + px(16, 12, 2, 1, t.shade)
    cycle = f"{2 * STEP_SECONDS}s"
    stride = (
        f'<g>{left}<animateTransform attributeName="transform" type="translate" '
        f'values="0 0;0 {-U};0 0" dur="{cycle}" repeatCount="indefinite"/></g>'
        f'<g>{right}<animateTransform attributeName="transform" type="translate" '
        f'values="0 {-U};0 0;0 {-U}" dur="{cycle}" repeatCount="indefinite"/></g>'
    )
    moving = [(0, WALK_END), RUN]
    still = [(WALK_END, RUN[0]), (RUN[1], 1)]
    return f'<g>{stride}{visible(moving)}</g><g opacity="0">{left}{right}{visible(still)}</g>'


def carry_motion() -> tuple[list[str], list[float], list[str]]:
    """Laptop offset keyframes: behind the back -> held at the side -> on the ground, and back."""
    hidden, held, ground = (HIDDEN_DX, HELD_DY), (0, HELD_DY), (0, 0)
    points = [hidden, hidden, held, ground, ground, held, hidden, hidden]
    times = [0, CARRY_OUT[0], CARRY_OUT[1], CARRY_OUT[2], CARRY_BACK[0], CARRY_BACK[1], CARRY_BACK[2], 1]
    splines = [LINEAR, EASE_OUT, EASE_IN_OUT, LINEAR, EASE_IN_OUT, EASE_IN, LINEAR]
    return [f"{dx} {dy}" for dx, dy in points], times, splines


def laptop(t: Theme) -> str:
    """A laptop in three-quarter view: slanted lid (back facing us) and a deck with keys.

    Drawn behind the body, so while it is behind the goblin's back it is hidden.
    """
    deck = (
        px(LAPTOP_X, 11, 17, 1, t.deck)
        + "".join(px(x, 11, 1, 1, t.keys) for x in range(LAPTOP_X + 1, LAPTOP_X + 9, 2))
        + px(LAPTOP_X - 1, 12, 18, 1, t.base)
    )
    closed_lid = px(LAPTOP_X + 1, 10, 16, 1, t.lid) + px(LAPTOP_X + 1, 10, 1, 1, t.lid_light)
    # Lid leans back: every two rows up it shifts one pixel right.
    lid_rows = []
    for row in range(2, 11):
        shift = (10 - row) // 2
        x0 = LAPTOP_X + 8 + shift
        if row == 2:
            lid_rows.append(px(x0, row, 9, 1, t.lid_light))
            continue
        lid_rows.append(px(x0, row, 1, 1, t.lid_light) + px(x0 + 1, row, 7, 1, t.lid) + px(x0 + 8, row, 1, 1, t.lid_dark))
    cx = LAPTOP_X + 14  # logo centre column on the slanted lid
    logo = px(cx, 5, 1, 1, t.logo) + px(cx - 1, 6, 3, 1, t.logo) + px(cx, 7, 1, 1, t.logo)
    swing = on_timeline(
        "scale", "transform",
        ["1 0", "1 0", "1 1", "1 1", "1 0", "1 0"],
        [0, LID_OPEN[0], LID_OPEN[1], LID_CLOSE[0], LID_CLOSE[1], 1],
        [LINEAR, EASE_OUT, LINEAR, EASE_IN, LINEAR],
    )
    lid = pivot(0, 11, "".join(lid_rows) + logo, swing)
    closed_vis = visible([(0, LID_OPEN[0] + 0.01), (LID_CLOSE[1] - 0.01, 1)])
    values, times, splines = carry_motion()
    move = on_timeline("translate", "transform", [_scaled(v) for v in values], times, splines)
    fade = 0.008
    shown = on_timeline(
        "animate", "opacity", ["0", "0", "1", "1", "0", "0"],
        [0, CARRY_OUT[0], CARRY_OUT[0] + fade, CARRY_BACK[2] - fade, CARRY_BACK[2], 1],
    )
    return f'<g opacity="0"><g>{move}{deck}<g>{closed_lid}{closed_vis}</g>{lid}</g>{shown}</g>'


def _scaled(pair: str) -> str:
    dx, dy = (int(v) for v in pair.split())
    return f"{dx * U} {dy * U}"


def carrying_arm(t: Theme) -> str:
    """The back arm that holds the laptop: from inside the body to the laptop's left edge.

    Its width and height track the laptop offset so the hand stays on the laptop.
    """
    values, times, splines = carry_motion()
    offsets = [tuple(int(v) for v in value.split()) for value in values]
    hand_x = LAPTOP_X  # the hand grips the closed laptop's left end
    widths = [f"{(hand_x - 4 + 1 + dx) * U}" for dx, _ in offsets]  # arm starts inside the body at column 4
    ys = [f"{(10 + dy) * U}" for _, dy in offsets]
    arm = px(4, 10, hand_x - 4 + 1 + HIDDEN_DX, 1, t.body,
             on_timeline("animate", "width", widths, times, splines)
             + on_timeline("animate", "y", ys, times, splines))
    return f'<g opacity="0">{arm}{visible([(CARRY_OUT[0], LID_OPEN[1]), (LID_CLOSE[0], CARRY_BACK[2])])}</g>'


def typing_arm(t: Theme, color: str, shoulder_x: int, row: int, hand_x: int, begin: float) -> str:
    """A stick arm reaching from the body to the keyboard; its forearm presses the keys."""
    upper = px(shoulder_x, row, hand_x - shoulder_x, 1, color)
    forearm = px(hand_x, row, 1, 11 - row, color, press(0.28, begin, 11 - row, 12 - row))
    reach = on_timeline(
        "scale", "transform",
        ["0 1", "0 1", "1 1", "1 1", "0 1", "0 1"],
        [0, ARMS_OUT[0], ARMS_OUT[1], ARMS_IN[0], ARMS_IN[1], 1],
        [LINEAR, EASE_OUT, LINEAR, EASE_IN, LINEAR],
    )
    return f'<g opacity="0">{pivot(shoulder_x, row, upper + forearm, reach)}{visible([(ARMS_OUT[0], ARMS_IN[1])])}</g>'


def glyphs(t: Theme) -> str:
    items = "".join(
        f'<text x="{(LAPTOP_X + 2 + i * 4) * U}" y="{-1 * U}" font-family="ui-monospace, Menlo, Consolas, monospace" '
        f'font-size="9" fill="{t.glyph}" opacity="0">{text}'
        f'<animate attributeName="opacity" values="0;1;0" dur="1.2s" begin="{i * 0.4}s" repeatCount="indefinite"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 6;0 -6" dur="1.2s" '
        f'begin="{i * 0.4}s" repeatCount="indefinite"/></text>'
        for i, text in enumerate(("{}", "&lt;/&gt;", ";"))
    )
    return f'<g opacity="0">{items}{visible([(ARMS_OUT[1], LOOK[0])])}</g>'


def shadow(t: Theme) -> str:
    """Soft ground shadow that stretches under the laptop while it is on the ground."""
    times = [0, CARRY_OUT[1], CARRY_OUT[2], CARRY_BACK[0], CARRY_BACK[1], 1]
    rx = on_timeline("animate", "rx", [f"{v * U}" for v in (13, 13, 21, 21, 13, 13)], times)
    cx = on_timeline("animate", "cx", [f"{v * U}" for v in (12, 12, 21, 21, 12, 12)], times)
    return (
        f'<ellipse cx="{12 * U}" cy="{13 * U}" rx="{13 * U}" ry="{U}" fill="#000" '
        f'opacity="{t.shadow_opacity}">{rx}{cx}</ellipse>'
    )


def render(t: Theme) -> str:
    start_x, stop_x, exit_x = -45 * U, WIDTH // 2 - 20 * U, WIDTH + 10 * U
    y = TOP_MARGIN * U
    travel = on_timeline(
        "translate", "transform",
        [f"{start_x} {y}", f"{stop_x} {y}", f"{stop_x} {y}", f"{exit_x} {y}", f"{exit_x} {y}"],
        [0, WALK_END, RUN[0], RUN[1], 1],
        [EASE_OUT, LINEAR, EASE_IN, LINEAR],
    )
    behind = (
        shadow(t) + laptop(t) + carrying_arm(t)
        + typing_arm(t, t.shade, shoulder_x=18, row=8, hand_x=LAPTOP_X + 3, begin=0.14)
    )
    front = typing_arm(t, t.highlight, shoulder_x=17, row=9, hand_x=LAPTOP_X + 6, begin=0.0) + glyphs(t)
    goblin = f'{behind}<g>{body_pixels(t)}{eyes(t)}{stride_bob()}</g>{legs(t)}{front}'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" shape-rendering="crispEdges" role="img" '
        f'aria-label="A pixel goblin pulls a laptop from behind its back, codes for a while, '
        f'looks around and runs off">'
        f'<g transform="translate({start_x} {y})">{travel}{goblin}</g></svg>'
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
