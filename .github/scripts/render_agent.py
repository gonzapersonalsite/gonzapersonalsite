"""Render an animated SVG of Gonzalo's pixel goblin coding over the contribution graph.

Story (one loop): the goblin strolls in, pulls out a laptop and types while the
contribution graph fills in, looks left and right, stashes the laptop and runs off.

Usage: python render_agent.py <github_user> <output_dir>
Requires GITHUB_TOKEN in the environment to read the contribution calendar.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

GRAPHQL_URL = "https://api.github.com/graphql"
REQUEST_TIMEOUT_SECONDS = 30

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { contributionLevel weekday } }
      }
    }
  }
}
"""

LEVELS = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}

# Layout (px)
CELL = 10
GAP = 3
STEP = CELL + GAP
MARGIN = 12
U = 4  # sprite pixel size
DURATION = 14  # seconds per loop

# Timeline (fractions of DURATION)
WALK_END = 0.28
LAPTOP_OUT = 0.31
TYPE_END = 0.62
LOOK_END = 0.74
LAPTOP_AWAY = 0.77
RUN_END = 0.88
GRAPH_FADE = 0.96

# Goblin sprite, left half (mirrored to build the full 24px-wide body).
# g body, h highlight, e inner ear, s shade
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
LEGS_LEFT_X = 6  # leg columns 6-7 (mirrored to 16-17)
LEG_ROWS = (11, 12)
SPRITE_W = 24
SPRITE_H = 13


@dataclass(frozen=True)
class Theme:
    name: str
    cells: tuple[str, str, str, str, str]
    body: str
    highlight: str
    ear: str
    shade: str
    blush: str
    ink: str
    laptop: str
    laptop_light: str
    floor: str
    glyph: str


DARK = Theme(
    name="dark",
    cells=("#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"),
    body="#82a353",
    highlight="#9cbf63",
    ear="#b3d47a",
    shade="#5f7d3a",
    blush="#e69a80",
    ink="#0b0b0b",
    laptop="#88827f",
    laptop_light="#d1ccc7",
    floor="#222222",
    glyph="#d4a373",
)

LIGHT = Theme(
    name="light",
    cells=("#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"),
    body="#82a353",
    highlight="#9cbf63",
    ear="#b3d47a",
    shade="#5f7d3a",
    blush="#e69a80",
    ink="#1f2328",
    laptop="#6e7781",
    laptop_light="#afb8c1",
    floor="#d0d7de",
    glyph="#9a6b2f",
)


def fetch_levels(login: str, token: str) -> list[list[int]]:
    """Return weeks as lists of 7 contribution levels (index = weekday)."""
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    result = []
    for week in weeks:
        column = [0] * 7
        for day in week["contributionDays"]:
            column[day["weekday"]] = LEVELS[day["contributionLevel"]]
        result.append(column)
    return result


def kt(*values: float) -> str:
    return ";".join(f"{v:.4f}" for v in values)


def px(x: float, y: float, w: float, h: float, fill: str) -> str:
    return f'<rect x="{x * U:g}" y="{y * U:g}" width="{w * U:g}" height="{h * U:g}" fill="{fill}"/>'


def timeline(attribute: str, values: str, key_times: str, discrete: bool = False) -> str:
    mode = ' calcMode="discrete"' if discrete else ""
    return (
        f'<animate attributeName="{attribute}" dur="{DURATION}s" repeatCount="indefinite"'
        f'{mode} values="{values}" keyTimes="{key_times}"/>'
    )


def loop_translate(values: str, seconds: float) -> str:
    return (
        f'<animateTransform attributeName="transform" type="translate" values="{values}" '
        f'dur="{seconds}s" repeatCount="indefinite"/>'
    )


def render_body(t: Theme) -> str:
    colors = {"g": t.body, "h": t.highlight, "e": t.ear, "s": t.shade}
    parts = []
    for y, half in enumerate(HALF_SPRITE):
        row = half + half[::-1]
        x = 0
        while x < len(row):
            char = row[x]
            run = 1
            while x + run < len(row) and row[x + run] == char:
                run += 1
            if char in colors:
                parts.append(px(x, y, run, 1, colors[char]))
            x += run
    # Face: blush and mouth are fixed, eyes are animated separately.
    parts.append(px(6, 7, 1, 1, t.blush))
    parts.append(px(17, 7, 1, 1, t.blush))
    parts.append(px(11, 7, 2, 1, t.ink))
    return "".join(parts)


def render_eyes(t: Theme) -> str:
    """Happy closed eyes while strolling and typing; open eyes glancing sideways when looking around."""
    closed = (
        px(6, 6, 1, 1, t.ink) + px(7, 5, 2, 1, t.ink) + px(9, 6, 1, 1, t.ink)
        + px(14, 6, 1, 1, t.ink) + px(15, 5, 2, 1, t.ink) + px(17, 6, 1, 1, t.ink)
    )
    open_eyes = px(7, 5, 2, 2, t.ink) + px(15, 5, 2, 2, t.ink)
    look = (
        f'<animateTransform attributeName="transform" type="translate" dur="{DURATION}s" '
        f'repeatCount="indefinite" calcMode="discrete" '
        f'values="0 0;{-U} 0;{U} 0;{-U} 0;{U} 0;0 0" '
        f'keyTimes="{kt(0, TYPE_END, 0.65, 0.68, 0.71, LOOK_END)}"/>'
    )
    return (
        f'<g>{closed}{timeline("opacity", "1;0;1", kt(0, TYPE_END, LOOK_END), discrete=True)}</g>'
        f'<g opacity="0">{open_eyes}{look}'
        f'{timeline("opacity", "0;1;0", kt(0, TYPE_END, LOOK_END), discrete=True)}</g>'
    )


def render_legs(t: Theme) -> str:
    right_x = SPRITE_W - LEGS_LEFT_X - 2
    left = px(LEGS_LEFT_X, LEG_ROWS[0], 2, 2, t.body)
    right = px(right_x, LEG_ROWS[0], 2, 2, t.body)
    moving = (
        f'<g>{left}{loop_translate(f"0 0;0 {-U};0 0", 0.3)}</g>'
        f'<g>{right}{loop_translate(f"0 {-U};0 0;0 {-U}", 0.3)}</g>'
    )
    walking = f'<g>{moving}{timeline("opacity", "1;0;1", kt(0, WALK_END, LAPTOP_AWAY), discrete=True)}</g>'
    standing = (
        f'<g opacity="0">{left}{right}'
        f'{timeline("opacity", "0;1;0", kt(0, WALK_END, LAPTOP_AWAY), discrete=True)}</g>'
    )
    return walking + standing


def render_laptop(t: Theme) -> str:
    """Open laptop to the goblin's right, lid facing the viewer with a small logo."""
    lid = px(27, 4, 7, 7, t.laptop) + px(27, 4, 7, 1, t.laptop_light) + px(26, 5, 1, 6, t.laptop_light)
    logo = px(30, 6, 1, 1, t.laptop_light) + px(29, 7, 1, 1, t.laptop_light) + px(31, 7, 1, 1, t.laptop_light) + px(30, 8, 1, 1, t.laptop_light)
    base = px(21, 11, 13, 1, t.laptop_light) + px(21, 12, 13, 1, t.laptop)
    glyphs = "".join(
        f'<text x="{(23 + i * 3) * U}" y="{3 * U}" font-family="ui-monospace, Menlo, Consolas, monospace" '
        f'font-size="10" fill="{t.glyph}" opacity="0">{text}'
        f'<animate attributeName="opacity" values="0;1;0" dur="0.9s" begin="{i * 0.3}s" repeatCount="indefinite"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 6;0 -6" dur="0.9s" '
        f'begin="{i * 0.3}s" repeatCount="indefinite"/></text>'
        for i, text in enumerate(("{}", "&lt;/&gt;", ";"))
    )
    typing_fx = f'<g opacity="0">{glyphs}{timeline("opacity", "0;1;0", kt(0, LAPTOP_OUT, TYPE_END), discrete=True)}</g>'
    return (
        f'<g opacity="0">{lid}{logo}{base}'
        f'{timeline("opacity", "0;1;0", kt(0, LAPTOP_OUT, LAPTOP_AWAY), discrete=True)}</g>'
        f'{typing_fx}'
    )


def render_goblin(t: Theme) -> str:
    bob = loop_translate(f"0 0;0 {-U // 2};0 0", 0.3)
    typing_bounce = (
        f'<g>{render_body(t)}{render_eyes(t)}{bob}</g>'
    )
    return typing_bounce + render_legs(t) + render_laptop(t)


def render(weeks: list[list[int]], t: Theme) -> str:
    grid_w = len(weeks) * STEP - GAP
    grid_h = 7 * STEP - GAP
    width = grid_w + 2 * MARGIN
    sprite_top = MARGIN + grid_h + 22
    floor_y = sprite_top + SPRITE_H * U
    height = floor_y + U + MARGIN

    base = []
    fills = []
    span = TYPE_END - LAPTOP_OUT
    for col, week in enumerate(weeks):
        x = MARGIN + col * STEP
        lit = []
        for row, level in enumerate(week):
            y = MARGIN + row * STEP
            base.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{t.cells[0]}"/>')
            if level:
                lit.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{t.cells[level]}"/>')
        if lit:
            on = LAPTOP_OUT + span * col / max(len(weeks) - 1, 1)
            fills.append(
                f'<g opacity="0">{"".join(lit)}'
                f'{timeline("opacity", "0;0;1;1;0", kt(0, on, min(on + 0.02, GRAPH_FADE), GRAPH_FADE, 1))}</g>'
            )

    start_x = -40 * U
    stop_x = MARGIN + grid_w * 0.4
    exit_x = width + 10 * U
    goblin = (
        f'<g transform="translate({start_x} {sprite_top})">'
        f'<animateTransform attributeName="transform" type="translate" dur="{DURATION}s" repeatCount="indefinite" '
        f'values="{start_x} {sprite_top};{stop_x:.0f} {sprite_top};{stop_x:.0f} {sprite_top};'
        f'{exit_x} {sprite_top};{exit_x} {sprite_top}" '
        f'keyTimes="{kt(0, WALK_END, LAPTOP_AWAY, RUN_END, 1)}"/>'
        f'{render_goblin(t)}</g>'
    )
    floor = f'<rect x="0" y="{floor_y}" width="{width}" height="{U}" fill="{t.floor}"/>'

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges" role="img" '
        f'aria-label="A pixel goblin codes on a laptop while the contribution graph fills in">'
        f'{"".join(base)}{"".join(fills)}{floor}{goblin}</svg>'
    )


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("Usage: render_agent.py <github_user> <output_dir>")
    login, output_dir = sys.argv[1], Path(sys.argv[2])
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is required")
    weeks = fetch_levels(login, token)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "goblin.svg").write_text(render(weeks, LIGHT), encoding="utf-8")
    (output_dir / "goblin-dark.svg").write_text(render(weeks, DARK), encoding="utf-8")


if __name__ == "__main__":
    main()
