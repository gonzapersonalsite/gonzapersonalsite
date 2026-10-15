"""Render the animated pixel goblin shown at the top of the profile README.

Story (one loop): the goblin strolls in, pulls a laptop out, opens it and types,
looks left and right, closes and stashes the laptop, then runs off.

Usage: python scripts/render_goblin.py assets
Writes goblin.svg (light) and goblin-dark.svg (dark) into the given directory.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

U = 3  # sprite pixel size (px)
DURATION = 16  # seconds per loop
WIDTH = 560
GROUND = 15  # sprite row the feet stand on (in sprite pixels, from the top of the canvas)
HEIGHT = (GROUND + 2) * U

EASE_OUT = "0 0 0.58 1"
EASE_IN = "0.42 0 1 1"
EASE_IN_OUT = "0.42 0 0.58 1"
LINEAR = "0 0 1 1"

# Timeline (fractions of DURATION)
WALK_END = 0.22
SLIDE_OUT = (0.26, 0.31)
LID_OPEN = (0.31, 0.35)
HANDS_OUT = (0.35, 0.38)
LOOK = (0.64, 0.76)
HANDS_IN = (0.76, 0.78)
LID_CLOSE = (0.78, 0.82)
SLIDE_IN = (0.82, 0.87)
RUN = (0.88, 0.97)

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
SPRITE_W = 24
TOP = GROUND - 13  # sprite top row so legs end on the ground


@dataclass(frozen=True)
class Theme:
    body: str
    highlight: str
    ear: str
    shade: str
    blush: str
    ink: str
    lid: str
    lid_edge: str
    lid_shadow: str
    keys: str
    base: str
    logo: str
    glyph: str
    shadow_opacity: float


DARK = Theme(
    body="#82a353", highlight="#9cbf63", ear="#b3d47a", shade="#5f7d3a", blush="#e69a80",
    ink="#0b0b0b", lid="#8a8580", lid_edge="#d1ccc7", lid_shadow="#5e5955", keys="#3d3936",
    base="#b9b3ad", logo="#e8e3de", glyph="#d4a373", shadow_opacity=0.55,
)
LIGHT = Theme(
    body="#82a353", highlight="#9cbf63", ear="#b3d47a", shade="#5f7d3a", blush="#e69a80",
    ink="#1f2328", lid="#8a8580", lid_edge="#c9c3bd", lid_shadow="#5e5955", keys="#3d3936",
    base="#a39d97", logo="#e8e3de", glyph="#9a6b2f", shadow_opacity=0.18,
)


def kt(*values: float) -> str:
    return ";".join(f"{v:.4f}" for v in values)


def px(x: float, y: float, w: float, h: float, fill: str) -> str:
    return f'<rect x="{x * U:g}" y="{y * U:g}" width="{w * U:g}" height="{h * U:g}" fill="{fill}"/>'


def on_timeline(kind: str, attribute: str, values: list[str], times: list[float], splines: list[str] | None = None) -> str:
    """One animation driven by the main loop. kind is 'animate' or a transform type."""
    tag = "animate" if kind == "animate" else "animateTransform"
    type_attr = "" if kind == "animate" else f' type="{kind}"'
    mode = f' calcMode="spline" keySplines="{";".join(splines)}"' if splines else ""
    return (
        f'<{tag} attributeName="{attribute}"{type_attr} dur="{DURATION}s" repeatCount="indefinite"'
        f'{mode} values="{";".join(values)}" keyTimes="{kt(*times)}"/>'
    )


def opacity_window(start: float, end: float, fade: float = 0.0) -> str:
    """Visible inside [start, end]; fade > 0 cross-fades at both ends."""
    if fade:
        return on_timeline("animate", "opacity", ["0", "0", "1", "1", "0", "0"],
                           [0, start, start + fade, end - fade, end, 1])
    return (
        f'<animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" calcMode="discrete" '
        f'values="0;1;0" keyTimes="{kt(0, start, end)}"/>'
    )


def loop(kind: str, values: str, seconds: float, begin: float = 0) -> str:
    return (
        f'<animateTransform attributeName="transform" type="{kind}" values="{values}" '
        f'dur="{seconds}s" begin="{begin}s" repeatCount="indefinite"/>'
    )


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
    hide_closed = (
        f'<animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" calcMode="discrete" '
        f'values="1;0;1" keyTimes="{kt(0, start, end)}"/>'
    )
    return f'<g>{closed}{hide_closed}</g><g opacity="0">{opened}{glance}{opacity_window(start, end)}</g>'


def legs(t: Theme, moving_windows: list[tuple[float, float]]) -> str:
    left, right = px(6, 11, 2, 2, t.body), px(16, 11, 2, 2, t.body)
    left_shadow, right_shadow = px(6, 12, 2, 1, t.shade), px(16, 12, 2, 1, t.shade)
    stride = (
        f'<g>{left}{left_shadow}{loop("translate", f"0 0;0 {-U};0 0", 0.32)}</g>'
        f'<g>{right}{right_shadow}{loop("translate", f"0 {-U};0 0;0 {-U}", 0.32)}</g>'
    )
    (w0, w1), (r0, r1) = moving_windows
    walking_vis = (
        f'<animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" calcMode="discrete" '
        f'values="1;0;1;0" keyTimes="{kt(0, w1, r0, r1)}"/>'
    )
    standing_vis = (
        f'<animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" calcMode="discrete" '
        f'values="0;1;0;1" keyTimes="{kt(0, w1, r0, r1)}"/>'
    )
    return f'<g>{stride}{walking_vis}</g><g opacity="0">{left}{right}{left_shadow}{right_shadow}{standing_vis}</g>'


def laptop(t: Theme) -> str:
    """Drawn behind the goblin so it slides out from its side, then the lid swings open."""
    hinge_x, hinge_y = 33 * U, 12 * U
    lid = (
        px(28, 5, 6, 7, t.lid) + px(28, 5, 6, 1, t.lid_edge) + px(33, 6, 1, 6, t.lid_shadow)
        + px(30, 7, 1, 1, t.logo) + px(29, 8, 1, 1, t.logo) + px(31, 8, 1, 1, t.logo) + px(30, 9, 1, 1, t.logo)
    )
    lid_swing = on_timeline(
        "scale", "transform",
        ["1 0", "1 0", "1 1", "1 1", "1 0", "1 0"],
        [0, LID_OPEN[0], LID_OPEN[1], LID_CLOSE[0], LID_CLOSE[1], 1],
        [LINEAR, EASE_OUT, LINEAR, EASE_IN, LINEAR],
    )
    hinged_lid = (
        f'<g transform="translate({hinge_x} {hinge_y})"><g>{lid_swing}'
        f'<g transform="translate({-hinge_x} {-hinge_y})">{lid}</g></g></g>'
    )
    base = px(22, 11, 12, 1, t.base) + px(23, 11, 9, 1, t.keys) + px(22, 12, 12, 1, t.lid_shadow)
    slide = on_timeline(
        "translate", "transform",
        [f"{-10 * U} 0", f"{-10 * U} 0", "0 0", "0 0", f"{-10 * U} 0", f"{-10 * U} 0"],
        [0, SLIDE_OUT[0], SLIDE_OUT[1], SLIDE_IN[0], SLIDE_IN[1], 1],
        [LINEAR, EASE_OUT, LINEAR, EASE_IN, LINEAR],
    )
    visible = opacity_window(SLIDE_OUT[0], SLIDE_IN[1], fade=0.01)
    return f'<g opacity="0">{base}{hinged_lid}{slide}{visible}</g>'


def hands(t: Theme) -> str:
    """Arms reach from the goblin's side onto the keyboard; the two hands tap alternately."""
    hinge_x = 21 * U
    arm = px(21, 9, 4, 1, t.shade) + px(21, 10, 7, 1, t.body)
    hand_a = f'<g>{px(24, 10, 2, 1, t.highlight)}{loop("translate", f"0 0;0 {U};0 0", 0.2)}</g>'
    hand_b = f'<g>{px(27, 10, 2, 1, t.highlight)}{loop("translate", f"0 {U};0 0;0 {U}", 0.2)}</g>'
    reach = on_timeline(
        "scale", "transform",
        ["0 1", "0 1", "1 1", "1 1", "0 1", "0 1"],
        [0, HANDS_OUT[0], HANDS_OUT[1], HANDS_IN[0], HANDS_IN[1], 1],
        [LINEAR, EASE_OUT, LINEAR, EASE_IN, LINEAR],
    )
    return (
        f'<g opacity="0"><g transform="translate({hinge_x} 0)"><g>{reach}'
        f'<g transform="translate({-hinge_x} 0)">{arm}{hand_a}{hand_b}</g></g></g>'
        f'{opacity_window(HANDS_OUT[0], HANDS_IN[1])}</g>'
    )


def glyphs(t: Theme) -> str:
    items = "".join(
        f'<text x="{(26 + i * 3) * U}" y="{4 * U}" font-family="ui-monospace, Menlo, Consolas, monospace" '
        f'font-size="8" fill="{t.glyph}" opacity="0">{text}'
        f'<animate attributeName="opacity" values="0;1;0" dur="1.2s" begin="{i * 0.4}s" repeatCount="indefinite"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 4;0 -6" dur="1.2s" '
        f'begin="{i * 0.4}s" repeatCount="indefinite"/></text>'
        for i, text in enumerate(("{}", "&lt;/&gt;", ";"))
    )
    return f'<g opacity="0">{items}{opacity_window(HANDS_OUT[1], LOOK[0])}</g>'


def shadow(t: Theme) -> str:
    """Soft ground shadow; stretches under the laptop while it is out."""
    stretch = on_timeline(
        "animate", "rx",
        [f"{13 * U}", f"{13 * U}", f"{19 * U}", f"{19 * U}", f"{13 * U}", f"{13 * U}"],
        [0, SLIDE_OUT[0], SLIDE_OUT[1], SLIDE_IN[0], SLIDE_IN[1], 1],
    )
    shift = on_timeline(
        "animate", "cx",
        [f"{12 * U}", f"{12 * U}", f"{17 * U}", f"{17 * U}", f"{12 * U}", f"{12 * U}"],
        [0, SLIDE_OUT[0], SLIDE_OUT[1], SLIDE_IN[0], SLIDE_IN[1], 1],
    )
    return (
        f'<ellipse cx="{12 * U}" cy="{13 * U}" rx="{13 * U}" ry="{U}" fill="#000" '
        f'opacity="{t.shadow_opacity}">{stretch}{shift}</ellipse>'
    )


def render(t: Theme) -> str:
    start_x = -40 * U
    stop_x = WIDTH // 2 - 16 * U
    exit_x = WIDTH + 10 * U
    y = TOP * U
    travel = on_timeline(
        "translate", "transform",
        [f"{start_x} {y}", f"{stop_x} {y}", f"{stop_x} {y}", f"{exit_x} {y}", f"{exit_x} {y}"],
        [0, WALK_END, RUN[0], RUN[1], 1],
        [EASE_OUT, LINEAR, EASE_IN, LINEAR],
    )
    bob = loop("translate", f"0 0;0 {-U / 2:g};0 0", 0.32)
    goblin = (
        f'{shadow(t)}{laptop(t)}'
        f'<g>{body_pixels(t)}{eyes(t)}{bob}</g>'
        f'{legs(t, [(0, WALK_END), RUN])}{hands(t)}{glyphs(t)}'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" shape-rendering="crispEdges" role="img" '
        f'aria-label="A pixel goblin pulls out a laptop, codes for a while, looks around and runs off">'
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
