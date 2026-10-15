"""Render an animated SVG of a pixel robot typing commits into the contribution graph.

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
U = 5  # robot pixel size
DURATION = 12  # seconds per loop

# Timeline (fractions of DURATION)
WALK_END = 0.22
LAPTOP_IN = 0.27
FILL_START = 0.29
FILL_END = 0.84
BUBBLE_START = 0.30
BUBBLE_END = 0.46
HOLD_END = 0.94


@dataclass(frozen=True)
class Theme:
    name: str
    cells: tuple[str, str, str, str, str]
    robot_outline: str
    robot_body: str
    robot_shade: str
    visor: str
    eyes: str
    accent: str
    laptop: str
    laptop_base: str
    bubble_bg: str
    bubble_fg: str


LIGHT = Theme(
    name="light",
    cells=("#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"),
    robot_outline="#3b4a5e",
    robot_body="#8fa3bf",
    robot_shade="#6f84a3",
    visor="#1b2430",
    eyes="#2ee6d6",
    accent="#d4a373",
    laptop="#c9d1d9",
    laptop_base="#57606a",
    bubble_bg="#24292f",
    bubble_fg="#e6edf3",
)

DARK = Theme(
    name="dark",
    cells=("#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"),
    robot_outline="#4a5d78",
    robot_body="#9fb3cf",
    robot_shade="#7a90b0",
    visor="#0d1117",
    eyes="#2ee6d6",
    accent="#d4a373",
    laptop="#d0d7de",
    laptop_base="#6e7781",
    bubble_bg="#e6edf3",
    bubble_fg="#0d1117",
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


def rect(x: float, y: float, w: float, h: float, fill: str, extra: str = "") -> str:
    return f'<rect x="{x * U}" y="{y * U}" width="{w * U}" height="{h * U}" fill="{fill}"{extra}/>'


def render_robot(t: Theme) -> str:
    """Pixel robot facing the viewer, 14x21 robot-pixels, origin at its top-left."""
    head = "".join([
        rect(6, 1, 1, 2, t.robot_outline),
        f'<g>{rect(5, -1, 3, 2, t.accent)}'
        f'<animate attributeName="opacity" values="1;0.25;1" dur="1.2s" repeatCount="indefinite"/></g>',
        rect(1, 3, 12, 8, t.robot_outline),
        rect(2, 4, 10, 6, t.robot_body),
        rect(2, 8, 10, 2, t.robot_shade),
        rect(3, 5, 8, 3, t.visor),
        f'<g>{rect(4, 6, 2, 1, t.eyes)}{rect(8, 6, 2, 1, t.eyes)}'
        f'<animate attributeName="opacity" values="1;1;0;1" keyTimes="0;0.92;0.96;1" '
        f'dur="3.5s" repeatCount="indefinite"/></g>',
        rect(6, 11, 2, 1, t.robot_outline),
    ])
    body = "".join([
        rect(2, 12, 10, 6, t.robot_outline),
        rect(3, 13, 8, 4, t.robot_body),
        rect(3, 16, 8, 1, t.robot_shade),
        rect(6, 14, 2, 1, t.accent),
    ])
    side_arms = rect(1, 13, 1, 4, t.robot_outline) + rect(12, 13, 1, 4, t.robot_outline)
    walking_legs = (
        f'<g>{rect(4, 18, 2, 3, t.robot_outline)}'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -{U};0 0" '
        f'dur="0.36s" repeatCount="indefinite"/></g>'
        f'<g>{rect(8, 18, 2, 3, t.robot_outline)}'
        f'<animateTransform attributeName="transform" type="translate" values="0 -{U};0 0;0 -{U}" '
        f'dur="0.36s" repeatCount="indefinite"/></g>'
    )
    standing_legs = rect(4, 18, 2, 3, t.robot_outline) + rect(8, 18, 2, 3, t.robot_outline)
    laptop = (
        rect(1, 13, 12, 6, t.laptop)
        + rect(1, 13, 12, 1, t.laptop_base)
        + rect(6, 15, 2, 2, t.accent)
        + rect(0, 19, 14, 1, t.laptop_base)
    )
    typing_hands = (
        f'<g>{rect(0, 18, 2, 1, t.robot_outline)}'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;0 {U};0 0" '
        f'dur="0.24s" repeatCount="indefinite"/></g>'
        f'<g>{rect(12, 18, 2, 1, t.robot_outline)}'
        f'<animateTransform attributeName="transform" type="translate" values="0 {U};0 0;0 {U}" '
        f'dur="0.24s" repeatCount="indefinite"/></g>'
    )
    walking_phase = (
        f'<g>{side_arms}{walking_legs}'
        f'<animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" '
        f'calcMode="discrete" values="1;0" keyTimes="{kt(0, WALK_END)}"/></g>'
    )
    typing_phase = (
        f'<g opacity="0">{standing_legs}{laptop}{typing_hands}'
        f'<animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" '
        f'values="0;0;1;1;0" keyTimes="{kt(0, WALK_END, LAPTOP_IN, HOLD_END, 1)}"/></g>'
    )
    bob = (
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="0 0;0 -{U};0 0" dur="0.36s" repeatCount="indefinite"/>'
    )
    return f'<g>{head}{body}{bob}</g>{walking_phase}{typing_phase}'


def render(weeks: list[list[int]], t: Theme) -> str:
    grid_w = len(weeks) * STEP - GAP
    grid_h = 7 * STEP - GAP
    width = grid_w + 2 * MARGIN
    robot_top = MARGIN + grid_h + 14
    height = robot_top + 22 * U + MARGIN

    base = []
    fills = []
    span = FILL_END - FILL_START
    for col, week in enumerate(weeks):
        x = MARGIN + col * STEP
        lit = []
        for row, level in enumerate(week):
            y = MARGIN + row * STEP
            base.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{t.cells[0]}"/>')
            if level:
                lit.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{t.cells[level]}"/>')
        if lit:
            on = FILL_START + span * col / max(len(weeks) - 1, 1)
            fills.append(
                f'<g opacity="0">{"".join(lit)}'
                f'<animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" '
                f'values="0;0;1;1;0" keyTimes="{kt(0, on, min(on + 0.02, HOLD_END), HOLD_END, 1)}"/></g>'
            )

    stop_x = MARGIN + grid_w * 0.38
    robot = (
        f'<g transform="translate({-20 * U} {robot_top})">'
        f'<animateTransform attributeName="transform" type="translate" dur="{DURATION}s" '
        f'repeatCount="indefinite" values="{-20 * U} {robot_top};{stop_x:.0f} {robot_top};{stop_x:.0f} {robot_top}" '
        f'keyTimes="{kt(0, WALK_END, 1)}"/>'
        f'{render_robot(t)}</g>'
    )

    message = 'git commit -m "ship it" ✓'
    bubble_x = stop_x + 17 * U
    bubble_y = robot_top + 2 * U
    bubble_w = 7.2 * len(message) + 16
    bubble = (
        f'<g opacity="0">'
        f'<rect x="{bubble_x:.0f}" y="{bubble_y}" width="{bubble_w:.0f}" height="24" rx="6" fill="{t.bubble_bg}"/>'
        f'<path d="M{bubble_x:.0f} {bubble_y + 14} l-8 4 l8 -10 z" fill="{t.bubble_bg}"/>'
        f'<clipPath id="type-{t.name}"><rect x="{bubble_x + 8:.0f}" y="{bubble_y}" width="0" height="24">'
        f'<animate attributeName="width" dur="{DURATION}s" repeatCount="indefinite" '
        f'values="0;0;{bubble_w - 16:.0f};{bubble_w - 16:.0f}" keyTimes="{kt(0, BUBBLE_START, BUBBLE_END, 1)}"/>'
        f'</rect></clipPath>'
        f'<text x="{bubble_x + 8:.0f}" y="{bubble_y + 16}" clip-path="url(#type-{t.name})" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="12" '
        f'fill="{t.bubble_fg}">{message.replace(chr(34), "&quot;")}</text>'
        f'<animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" '
        f'calcMode="discrete" values="0;1;0" keyTimes="{kt(0, BUBBLE_START, HOLD_END)}"/>'
        f'</g>'
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" shape-rendering="crispEdges" role="img" '
        f'aria-label="A pixel robot types on a laptop while the contribution graph fills in">'
        f'{"".join(base)}{"".join(fills)}{robot}{bubble}</svg>'
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
    (output_dir / "agent.svg").write_text(render(weeks, LIGHT), encoding="utf-8")
    (output_dir / "agent-dark.svg").write_text(render(weeks, DARK), encoding="utf-8")


if __name__ == "__main__":
    main()
