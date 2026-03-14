"""
svg_export.py — Generate an animated SVG bubble chart for embedding in README.

GitHub renders SVGs inline, including CSS animations, so this gives us
a live-looking visualization directly in the README without any JS.
"""

import math
import random
import textwrap
from typing import List, Dict


# ── Layout ────────────────────────────────────────────────────────────────────

WIDTH  = 860
HEIGHT = 360
PAD    = 14
MIN_R  = 28
MAX_R  = 90


def _bubble_radius(usage: int, max_usage: int) -> int:
    if max_usage == 0:
        return MIN_R
    ratio = math.log1p(usage) / math.log1p(max(max_usage, 1))
    return int(MIN_R + ratio * (MAX_R - MIN_R))


def _pack_bubbles(bubbles: List[Dict]) -> List[Dict]:
    """Simple iterative circle packing — keeps bubbles inside the canvas."""
    placed = []
    random.seed(42)  # deterministic layout

    for b in bubbles:
        r = b["r"]
        # Try random positions, keep the first that doesn't overlap too much
        best = None
        best_score = float("inf")
        for _ in range(300):
            x = random.uniform(r + PAD, WIDTH - r - PAD)
            y = random.uniform(r + PAD, HEIGHT - r - PAD)
            # Penalise overlap
            score = 0
            for p in placed:
                dist = math.hypot(p["cx"] - x, p["cy"] - y)
                overlap = (p["r"] + r + 10) - dist
                if overlap > 0:
                    score += overlap ** 2
            if score < best_score:
                best_score = score
                best = (x, y)
            if score == 0:
                break
        b["cx"], b["cy"] = best
        placed.append(b)

    return placed


def _truncate(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[:max_chars - 1] + "…"


# ── SVG building ──────────────────────────────────────────────────────────────

def generate_svg(skills: List[Dict]) -> str:
    if not skills:
        return _empty_svg()

    max_usage = max(s.get("usage_count", 0) for s in skills)

    bubbles = []
    for s in skills:
        usage = s.get("usage_count", 0)
        loaded = bool(s.get("loaded"))
        bubbles.append({
            "name":        s["name"],
            "description": s.get("description", ""),
            "usage":       usage,
            "loaded":      loaded,
            "r":           _bubble_radius(usage, max_usage),
            "tags":        s.get("tags", []),
        })

    # Sort biggest first so they get placed center-ish
    bubbles.sort(key=lambda b: -b["r"])
    bubbles = _pack_bubbles(bubbles)

    parts = [_svg_header()]
    parts.append(_svg_defs(bubbles))
    parts.append(_svg_background())

    # Connection lines between loaded bubbles
    loaded = [b for b in bubbles if b["loaded"]]
    for i in range(len(loaded)):
        for j in range(i + 1, len(loaded)):
            a, b_ = loaded[i], loaded[j]
            dist = math.hypot(a["cx"] - b_["cx"], a["cy"] - b_["cy"])
            if dist < 260:
                opacity = max(0.04, 0.18 * (1 - dist / 260))
                parts.append(
                    f'  <line x1="{a["cx"]:.1f}" y1="{a["cy"]:.1f}" '
                    f'x2="{b_["cx"]:.1f}" y2="{b_["cy"]:.1f}" '
                    f'stroke="#4ecdc4" stroke-width="1" opacity="{opacity:.2f}"/>'
                )

    # Bubbles
    for i, b in enumerate(bubbles):
        parts.append(_svg_bubble(b, i))

    # Legend + stats
    parts.append(_svg_legend(bubbles))
    parts.append("</svg>")

    return "\n".join(parts)


def _svg_header() -> str:
    return textwrap.dedent(f"""\
        <svg xmlns="http://www.w3.org/2000/svg"
             viewBox="0 0 {WIDTH} {HEIGHT}"
             width="{WIDTH}" height="{HEIGHT}"
             role="img" aria-label="Skill Bubble visualization">""")


def _svg_defs(bubbles: List[Dict]) -> str:
    defs = ['  <defs>']

    # Radial gradients per bubble
    for i, b in enumerate(bubbles):
        if b["loaded"]:
            c0, c1, c2 = "#4ecdc4cc", "#7c6af788", "#4ecdc433"
        else:
            c0, c1, c2 = "#3a3a58cc", "#2e2e4688", "#3a3a5833"
        ox = -0.3 * b["r"]
        oy = -0.3 * b["r"]
        # Normalised focal point inside 0..1
        fx = (b["cx"] + ox) / b["cx"] if b["cx"] else 0.4
        fy = (b["cy"] + oy) / b["cy"] if b["cy"] else 0.35
        defs.append(
            f'    <radialGradient id="g{i}" cx="{fx:.2f}" cy="{fy:.2f}" r="0.8">'
            f'<stop offset="0%" stop-color="{c0}"/>'
            f'<stop offset="60%" stop-color="{c1}"/>'
            f'<stop offset="100%" stop-color="{c2}"/>'
            f'</radialGradient>'
        )

    # Glow filters
    defs.append(
        '    <filter id="glow-loaded" x="-40%" y="-40%" width="180%" height="180%">'
        '<feGaussianBlur stdDeviation="5" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
    )
    defs.append(
        '    <filter id="glow-idle" x="-20%" y="-20%" width="140%" height="140%">'
        '<feGaussianBlur stdDeviation="2" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
    )

    # CSS animations
    defs.append("    <style>")
    defs.append("      .bubble-loaded { animation: pulse 3s ease-in-out infinite; }")
    for i, b in enumerate(bubbles):
        if b["loaded"]:
            delay = i * 0.4
            defs.append(f"      #bubble-{i} {{ animation-delay: {delay:.1f}s; }}")
    defs.append(textwrap.dedent("""\
          @keyframes pulse {
            0%, 100% { opacity: 0.92; transform-origin: center; transform: scale(1); }
            50%       { opacity: 1.00; transform: scale(1.035); }
          }
          .label { font-family: 'SF Mono', 'Fira Code', monospace; }
    """))
    defs.append("    </style>")
    defs.append("  </defs>")
    return "\n".join(defs)


def _svg_background() -> str:
    return f'  <rect width="{WIDTH}" height="{HEIGHT}" rx="12" fill="#0d0d14"/>'


def _svg_bubble(b: Dict, i: int) -> str:
    cx, cy, r = b["cx"], b["cy"], b["r"]
    glow_filter = "glow-loaded" if b["loaded"] else "glow-idle"
    cls = "bubble-loaded" if b["loaded"] else ""
    rim_color = "#4ecdc4" if b["loaded"] else "#4a4a6a"

    parts = [f'  <g id="bubble-{i}" class="{cls}">']

    # Main circle
    parts.append(
        f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" '
        f'fill="url(#g{i})" stroke="{rim_color}88" stroke-width="1" '
        f'filter="url(#{glow_filter})"/>'
    )

    # Shine
    sx, sy, sr = cx - r * 0.28, cy - r * 0.28, r * 0.18
    parts.append(
        f'    <circle cx="{sx:.1f}" cy="{sy:.1f}" r="{sr:.1f}" fill="#ffffff22"/>'
    )

    # Label
    font_size = max(9, min(13, int(r * 0.38)))
    label_color = "#e8fffe" if b["loaded"] else "#8888aa"
    label = _truncate(b["name"], max(4, int(r * 0.22)))
    parts.append(
        f'    <text x="{cx:.1f}" y="{cy:.1f}" '
        f'text-anchor="middle" dominant-baseline="middle" '
        f'class="label" font-size="{font_size}" font-weight="600" '
        f'fill="{label_color}">'
        f'<title>{b["name"]} — {b["description"] or "no description"} (uses: {b["usage"]})</title>'
        f'{label}</text>'
    )

    # Usage badge
    if b["usage"] > 0:
        bx, by = cx + r * 0.65, cy - r * 0.65
        badge_text = str(b["usage"]) if b["usage"] <= 99 else "99+"
        parts.append(
            f'    <circle cx="{bx:.1f}" cy="{by:.1f}" r="9" fill="#7c6af7"/>'
        )
        parts.append(
            f'    <text x="{bx:.1f}" y="{by:.1f}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'class="label" font-size="8" font-weight="700" fill="#fff">'
            f'{badge_text}</text>'
        )

    parts.append("  </g>")
    return "\n".join(parts)


def _svg_legend(bubbles: List[Dict]) -> str:
    total   = len(bubbles)
    loaded  = sum(1 for b in bubbles if b["loaded"])
    uses    = sum(b["usage"] for b in bubbles)
    lx, ly  = 16, HEIGHT - 52

    return textwrap.dedent(f"""\
      <g font-family="SF Mono, Fira Code, monospace" font-size="11" fill="#6b6b88">
        <circle cx="{lx+5}" cy="{ly+5}" r="5" fill="#4ecdc4" opacity=".8"/>
        <text x="{lx+16}" y="{ly+9}">active</text>
        <circle cx="{lx+65}" cy="{ly+5}" r="5" fill="#3a3a52"/>
        <text x="{lx+76}" y="{ly+9}">idle</text>
        <text x="{lx}" y="{ly+26}" fill="#3a3a66">─────────────────</text>
        <text x="{lx}" y="{ly+42}">
          <tspan fill="#e8e8f0">{total}</tspan> skills ·
          <tspan fill="#4ecdc4">{loaded}</tspan> loaded ·
          <tspan fill="#f9c74f">{uses}</tspan> total uses
        </text>
      </g>""")


def _empty_svg() -> str:
    return textwrap.dedent(f"""\
        <svg xmlns="http://www.w3.org/2000/svg"
             viewBox="0 0 {WIDTH} 120" width="{WIDTH}" height="120">
          <rect width="{WIDTH}" height="120" rx="12" fill="#0d0d14"/>
          <text x="{WIDTH//2}" y="55" text-anchor="middle"
                font-family="monospace" font-size="28" fill="#3a3a52">◎</text>
          <text x="{WIDTH//2}" y="82" text-anchor="middle"
                font-family="monospace" font-size="12" fill="#6b6b88">
            No skills yet — run sb add &lt;path&gt;
          </text>
        </svg>""")
