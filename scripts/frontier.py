#!/usr/bin/env python3
"""Reads data/ramen.json, computes the Pareto frontier (maximize taste,
minimize ease_of_access), and writes a static SVG to output/frontier.svg."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "ramen.json"
OUT_PATH = ROOT / "output" / "frontier.svg"

# axis scale is fixed (not data-driven) so the frame stays stable as points
# are added/removed over time -- frontier changes read as data changes, not
# axis rescaling.
AXIS_MIN, AXIS_MAX = 0, 10

# theme "a" palette
BG = "#0d0c0b"
INK = "#8f877c"
BRIGHT = "#d8d2c6"
ACCENT = "#9b3d2c"
DIM = "#545049"

FONT = '"SFMono-Regular",Menlo,Monaco,"Courier New",monospace'

W, H = 720, 420
PAD_L, PAD_R, PAD_T, PAD_B = 70, 40, 50, 60
PLOT_W = W - PAD_L - PAD_R
PLOT_H = H - PAD_T - PAD_B


def load_points():
    with open(DATA_PATH) as f:
        raw = json.load(f)
    return raw


def pareto_frontier(points):
    """Maximize taste, minimize ease_of_access. Standard skyline scan."""
    ordered = sorted(points, key=lambda p: (-p["taste"], p["ease_of_access"]))
    frontier = []
    best = float("inf")
    for p in ordered:
        if p["ease_of_access"] < best:
            frontier.append(p)
            best = p["ease_of_access"]
    # sort ascending by taste for drawing a left-to-right staircase
    frontier.sort(key=lambda p: p["taste"])
    return frontier


def sx(ease):
    # ease_of_access on the x-axis: low (better) plots to the left
    return PAD_L + (ease - AXIS_MIN) / (AXIS_MAX - AXIS_MIN) * PLOT_W


def sy(taste):
    # taste on the y-axis: high (better) plots near the top
    return PAD_T + (AXIS_MAX - taste) / (AXIS_MAX - AXIS_MIN) * PLOT_H


def place_labels(entries, min_gap=12, char_w=6.0):
    """Greedy vertical de-collision for point labels. entries: list of
    dicts with x, y, name. Returns {name: (label_x, label_y)}."""
    placed = []  # (x_start, x_end, y)
    result = {}
    for e in sorted(entries, key=lambda e: (e["y"], e["x"])):
        label_x = e["x"] + 7
        label_y = e["y"] - 7
        width = len(e["name"]) * char_w
        moved = True
        while moved:
            moved = False
            for x_start, x_end, y in placed:
                if label_x < x_end and label_x + width > x_start and abs(label_y - y) < min_gap:
                    label_y = y + min_gap
                    moved = True
        placed.append((label_x, label_x + width, label_y))
        result[e["name"]] = (label_x, label_y)
    return result


def build_svg(points):
    frontier = pareto_frontier(points)
    frontier_names = {p["name"] for p in frontier}

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" font-family=\'{FONT}\'>'
    )

    # solid background -- kept self-contained (not transparent) so the card
    # reads correctly regardless of the host page's background color.
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{BG}"/>')

    # title
    parts.append(
        f'<text x="{PAD_L}" y="28" fill="{ACCENT}" font-size="11" '
        f'letter-spacing="3.5">RAMEN — PARETO FRONTIER</text>'
    )

    # axes
    parts.append(
        f'<line x1="{PAD_L}" y1="{PAD_T}" x2="{PAD_L}" y2="{H-PAD_B}" '
        f'stroke="{DIM}" stroke-width="1"/>'
    )
    parts.append(
        f'<line x1="{PAD_L}" y1="{H-PAD_B}" x2="{W-PAD_R}" y2="{H-PAD_B}" '
        f'stroke="{DIM}" stroke-width="1"/>'
    )

    # ticks 0..10 step 2
    for v in range(AXIS_MIN, AXIS_MAX + 1, 2):
        x = sx(v)
        y = sy(v)
        parts.append(
            f'<line x1="{x}" y1="{H-PAD_B}" x2="{x}" y2="{H-PAD_B+4}" stroke="{DIM}"/>'
        )
        parts.append(
            f'<text x="{x}" y="{H-PAD_B+16}" fill="{INK}" font-size="9" '
            f'text-anchor="middle">{v}</text>'
        )
        parts.append(
            f'<line x1="{PAD_L-4}" y1="{y}" x2="{PAD_L}" y2="{y}" stroke="{DIM}"/>'
        )
        parts.append(
            f'<text x="{PAD_L-10}" y="{y+3}" fill="{INK}" font-size="9" '
            f'text-anchor="end">{v}</text>'
        )

    # axis titles
    parts.append(
        f'<text x="{PAD_L + PLOT_W/2}" y="{H-16}" fill="{INK}" font-size="10" '
        f'letter-spacing="2" text-anchor="middle">← LOWER IS BETTER — EASE OF ACCESS</text>'
    )
    parts.append(
        f'<text x="16" y="{PAD_T + PLOT_H/2}" fill="{INK}" font-size="10" '
        f'letter-spacing="2" text-anchor="middle" '
        f'transform="rotate(-90 16 {PAD_T + PLOT_H/2})">TASTE — HIGHER IS BETTER →</text>'
    )

    # frontier line: straight dotted segments connecting consecutive
    # frontier points, low->high taste
    if len(frontier) > 1:
        pts = [(sx(p["ease_of_access"]), sy(p["taste"])) for p in frontier]
        path = f"M {pts[0][0]} {pts[0][1]}"
        for x, y in pts[1:]:
            path += f" L {x} {y}"
        parts.append(
            f'<path d="{path}" fill="none" stroke="{ACCENT}" stroke-width="1.5" '
            f'stroke-dasharray="1.5,4" stroke-linecap="round"/>'
        )

    # points
    coords = {p["name"]: (sx(p["ease_of_access"]), sy(p["taste"])) for p in points}
    labels = place_labels([{"name": n, "x": x, "y": y} for n, (x, y) in coords.items()])

    for p in points:
        x, y = coords[p["name"]]
        on_frontier = p["name"] in frontier_names
        r = 4 if on_frontier else 2.5
        color = ACCENT if on_frontier else INK
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')

        label_x, label_y = labels[p["name"]]
        if label_y != y - 7:
            parts.append(
                f'<line x1="{x+2}" y1="{y-3}" x2="{label_x-2}" y2="{label_y-3}" '
                f'stroke="{DIM}" stroke-width="0.5"/>'
            )
        label_color = BRIGHT if on_frontier else INK
        parts.append(
            f'<text x="{label_x}" y="{label_y}" fill="{label_color}" font-size="10">{p["name"]}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    points = load_points()
    svg = build_svg(points)
    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(svg)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
