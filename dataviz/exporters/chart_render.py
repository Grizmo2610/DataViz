from __future__ import annotations

import base64
import io
import json
from typing import Any


def chart_to_svg(vega_spec: dict[str, Any]) -> str | None:
    """Convert a Vega-Lite spec to an SVG string.

    Tries, in order:
    1. Altair's built-in image renderer (``Chart.to_image``) -- requires a
       Vega renderer backend (vl-convert / node+deno) to be installed.
    2. ``vl_convert`` directly.
    3. A best-effort Matplotlib re-plot of the embedded ``datasets`` /
       ``encoding`` -- needs only ``matplotlib``.
    4. A pure-Python SVG renderer with **no external dependencies at all**
       -- covers the same chart types (histogram/scatter/line/bar) plus the
       layered correlation-heatmap spec this project produces, drawing
       directly from the numbers embedded in the spec. This is the
       guaranteed-to-work path when neither Altair's image backend nor
       matplotlib is installed.

    Shared by exporters that cannot embed an interactive Vega-Embed widget
    (Markdown, PDF) and instead need a static image.

    Returns:
        SVG markup, or None if no renderer backend could produce one.
    """
    svg = _svg_via_altair(vega_spec)
    if svg is not None:
        return svg
    svg = _svg_via_vl_convert(vega_spec)
    if svg is not None:
        return svg
    svg = _svg_via_matplotlib(vega_spec)
    if svg is not None:
        return svg
    return _svg_via_pure_python(vega_spec)


def chart_to_data_uri(vega_spec: dict[str, Any]) -> str | None:
    """Convert a Vega-Lite spec to a base64 SVG data URI for embedding in
    Markdown/notebook image syntax (``![]()`` or an inline ``<img>`` tag).

    Returns:
        A ``data:image/svg+xml;base64,...`` string, or None on failure.
    """
    svg = chart_to_svg(vega_spec)
    if svg is None:
        return None
    encoded = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"


# --------------------------------------------------------------------------- #
# Backends
# --------------------------------------------------------------------------- #

def _svg_via_altair(vega_spec: dict[str, Any]) -> str | None:
    try:
        import altair as alt
        chart = alt.Chart.from_dict(vega_spec)
        result = chart.to_image(format="svg")
        return result.decode() if isinstance(result, (bytes, bytearray)) else result
    except Exception:  # noqa: BLE001
        return None


def _svg_via_vl_convert(vega_spec: dict[str, Any]) -> str | None:
    try:
        import vl_convert as vlc  # type: ignore[import]
        result = vlc.vegalite_to_svg(json.dumps(vega_spec))
        return result.decode() if isinstance(result, (bytes, bytearray)) else result
    except Exception:  # noqa: BLE001
        return None


def _extract_rows(vega_spec: dict[str, Any]) -> list[dict[str, Any]]:
    data_ref = vega_spec.get("data", {})
    if "values" in data_ref:
        return data_ref["values"]
    name = data_ref.get("name")
    datasets = vega_spec.get("datasets", {})
    return datasets.get(name, []) if name else []


def _svg_via_matplotlib(vega_spec: dict[str, Any]) -> str | None:
    """Best-effort re-plot from the spec's embedded data, for the chart
    types ``viz_tools.py`` actually produces (histogram/scatter/line/bar).
    Returns None for chart types it doesn't know how to reconstruct
    (e.g. the layered heatmap spec), leaving the caller to show a text
    fallback instead of a wrong picture.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:  # noqa: BLE001
        return None

    if "layer" in vega_spec:
        return None  # e.g. heatmap -- too spec-specific for a generic fallback

    rows = _extract_rows(vega_spec)
    encoding = vega_spec.get("encoding", {})
    mark = vega_spec.get("mark", {})
    mark_type = mark.get("type") if isinstance(mark, dict) else mark
    title = vega_spec.get("title", "")
    x_field = encoding.get("x", {}).get("field")
    y_field = encoding.get("y", {}).get("field")
    color = "#4361ee"

    if not rows or not x_field:
        return None

    try:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        if mark_type == "bar" and encoding.get("y", {}).get("aggregate") == "count":
            values = [r[x_field] for r in rows if x_field in r]
            ax.hist(values, bins=min(20, max(5, len(set(values)))), color=color)
            ax.set_ylabel("Count")
        elif mark_type in ("circle", "point") and y_field:
            xs = [r.get(x_field) for r in rows]
            ys = [r.get(y_field) for r in rows]
            ax.scatter(xs, ys, alpha=0.65, color=color)
            ax.set_ylabel(y_field)
        elif mark_type == "line" and y_field:
            pts = sorted(
                ((r.get(x_field), r.get(y_field)) for r in rows if x_field in r and y_field in r),
                key=lambda p: p[0],
            )
            if pts:
                xs, ys = zip(*pts)
                ax.plot(xs, ys, color=color)
            ax.set_ylabel(y_field)
        elif mark_type == "bar" and y_field:
            xs = [r.get(x_field) for r in rows]
            ys = [r.get(y_field) for r in rows]
            ax.bar(xs, ys, color=color)
            ax.set_ylabel(y_field)
        else:
            plt.close(fig)
            return None

        ax.set_xlabel(x_field)
        if isinstance(title, str) and title:
            ax.set_title(title)
        fig.tight_layout()
        buf = io.StringIO()
        fig.savefig(buf, format="svg")
        plt.close(fig)
        return buf.getvalue()
    except Exception:  # noqa: BLE001
        return None


# --------------------------------------------------------------------------- #
# Zero-dependency fallback (pure Python, no matplotlib/altair/vl-convert)
# --------------------------------------------------------------------------- #

_SVG_W, _SVG_H = 640, 400
_MARGIN = {"l": 65, "r": 20, "t": 40, "b": 55}
_COLOR = "#4361ee"


def _lerp(v: float, vmin: float, vmax: float, out_min: float, out_max: float) -> float:
    if vmax == vmin:
        return (out_min + out_max) / 2
    return out_min + (v - vmin) / (vmax - vmin) * (out_max - out_min)


def _svg_header(title: str, w: int = _SVG_W, h: int = _SVG_H) -> list[str]:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'font-family="Inter, \'IBM Plex Sans\', system-ui, sans-serif">',
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
    ]
    if title:
        parts.append(
            f'<text x="{w/2:.1f}" y="20" text-anchor="middle" font-size="14" '
            f'font-weight="600" fill="#1a1a2e">{title}</text>'
        )
    return parts


def _svg_axes(plot_w: float, plot_h: float, x_label: str, y_label: str) -> list[str]:
    l, t = _MARGIN["l"], _MARGIN["t"]
    parts = [
        f'<line x1="{l}" y1="{t+plot_h:.1f}" x2="{l+plot_w:.1f}" y2="{t+plot_h:.1f}" stroke="#c8c8d8"/>',
        f'<line x1="{l}" y1="{t}" x2="{l}" y2="{t+plot_h:.1f}" stroke="#c8c8d8"/>',
    ]
    if x_label:
        parts.append(
            f'<text x="{l+plot_w/2:.1f}" y="{t+plot_h+35:.1f}" text-anchor="middle" '
            f'font-size="11" fill="#555770">{x_label}</text>'
        )
    if y_label:
        cy = t + plot_h / 2
        parts.append(
            f'<text x="16" y="{cy:.1f}" text-anchor="middle" font-size="11" fill="#555770" '
            f'transform="rotate(-90 16 {cy:.1f})">{y_label}</text>'
        )
    return parts


def _svg_via_pure_python(vega_spec: dict[str, Any]) -> str | None:
    """Zero-dependency SVG renderer, drawing directly from the numbers
    embedded in the spec. Covers histogram/scatter/line/bar and the
    layered correlation-heatmap spec this project's ``plot_heatmap``
    produces. Returns None only for chart shapes it doesn't recognise.
    """
    if "layer" in vega_spec:
        return _svg_heatmap_pure_python(vega_spec)

    rows = _extract_rows(vega_spec)
    encoding = vega_spec.get("encoding", {})
    mark = vega_spec.get("mark", {})
    mark_type = mark.get("type") if isinstance(mark, dict) else mark
    title = vega_spec.get("title", "")
    title = title if isinstance(title, str) else ""
    x_field = encoding.get("x", {}).get("field")
    y_field = encoding.get("y", {}).get("field")

    if not rows or not x_field:
        return None

    l, t = _MARGIN["l"], _MARGIN["t"]
    plot_w = _SVG_W - _MARGIN["l"] - _MARGIN["r"]
    plot_h = _SVG_H - _MARGIN["t"] - _MARGIN["b"]
    parts = _svg_header(title)
    body: list[str] = []

    if mark_type == "bar" and encoding.get("y", {}).get("aggregate") == "count":
        values = [r[x_field] for r in rows if x_field in r and r[x_field] is not None]
        if not values:
            return None
        vmin, vmax = min(values), max(values)
        nbins = min(20, max(5, len(set(values))))
        bin_w = (vmax - vmin) / nbins if vmax > vmin else 1
        bins = [0] * nbins
        for v in values:
            idx = min(nbins - 1, int((v - vmin) / bin_w)) if bin_w > 0 else 0
            bins[idx] += 1
        max_count = max(bins) or 1
        bar_w = plot_w / nbins
        for i, c in enumerate(bins):
            bar_h = _lerp(c, 0, max_count, 0, plot_h)
            x = l + i * bar_w
            y = t + (plot_h - bar_h)
            body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(bar_w-1,0):.1f}" '
                        f'height="{bar_h:.1f}" fill="{_COLOR}" opacity="0.8"/>')
        body += _svg_axes(plot_w, plot_h, x_field, "Count")

    elif mark_type in ("circle", "point") and y_field:
        pairs = [(r.get(x_field), r.get(y_field)) for r in rows
                 if r.get(x_field) is not None and r.get(y_field) is not None]
        if not pairs:
            return None
        xs, ys = zip(*pairs)
        xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
        for x, y in pairs:
            px = l + _lerp(x, xmin, xmax, 0, plot_w)
            py = t + plot_h - _lerp(y, ymin, ymax, 0, plot_h)
            body.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{_COLOR}" opacity="0.65"/>')
        body += _svg_axes(plot_w, plot_h, x_field, y_field)

    elif mark_type == "line" and y_field:
        pairs = sorted(
            ((r.get(x_field), r.get(y_field)) for r in rows
             if r.get(x_field) is not None and r.get(y_field) is not None),
            key=lambda p: p[0],
        )
        if not pairs:
            return None
        xs, ys = zip(*pairs)
        xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
        pts = [f"{l+_lerp(x,xmin,xmax,0,plot_w):.1f},{t+plot_h-_lerp(y,ymin,ymax,0,plot_h):.1f}"
               for x, y in pairs]
        body.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{_COLOR}" stroke-width="2"/>')
        body += _svg_axes(plot_w, plot_h, x_field, y_field)

    elif mark_type == "bar" and y_field:
        xs = [str(r.get(x_field)) for r in rows]
        ys = [r.get(y_field, 0) or 0 for r in rows]
        max_y = max(ys) if ys else 1
        bar_w = plot_w / len(xs) if xs else plot_w
        for i, yv in enumerate(ys):
            bar_h = _lerp(yv, 0, max_y, 0, plot_h)
            x = l + i * bar_w
            y = t + (plot_h - bar_h)
            body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(bar_w-2,0):.1f}" '
                        f'height="{bar_h:.1f}" fill="{_COLOR}"/>')
        body += _svg_axes(plot_w, plot_h, x_field, y_field)
    else:
        return None

    parts += body
    parts.append("</svg>")
    return "".join(parts)


def _diverging_color(v: float) -> str:
    """Approximate the 'blueorange' Vega color scheme used by plot_heatmap,
    for a correlation value in [-1, 1]."""
    v = max(-1.0, min(1.0, v))
    if v >= 0:
        t = v
        r, g, b = 255 - t * (255 - 230), 255 - t * (255 - 126), 255 - t * (255 - 34)
    else:
        t = -v
        r, g, b = 255 - t * (255 - 49), 255 - t * (255 - 104), 255 - t * (255 - 142)
    return f"rgb({int(r)},{int(g)},{int(b)})"


def _svg_heatmap_pure_python(vega_spec: dict[str, Any]) -> str | None:
    """Zero-dependency renderer for the layered correlation-heatmap spec
    produced by ``plot_heatmap`` (rect layer + text layer)."""
    layers = vega_spec.get("layer", [])
    if not layers:
        return None
    encoding = layers[0].get("encoding", {})
    x_field = encoding.get("x", {}).get("field")
    y_field = encoding.get("y", {}).get("field")
    color_field = encoding.get("color", {}).get("field")
    rows = _extract_rows(vega_spec)
    if not rows or not x_field or not y_field or not color_field:
        return None

    xs = sorted({r[x_field] for r in rows if x_field in r})
    ys = sorted({r[y_field] for r in rows if y_field in r})
    if not xs or not ys:
        return None

    w, h = 520, 520
    margin = {"l": 110, "t": 40, "r": 20, "b": 90}
    cell_w = (w - margin["l"] - margin["r"]) / len(xs)
    cell_h = (h - margin["t"] - margin["b"]) / len(ys)
    title = vega_spec.get("title")
    title = title if isinstance(title, str) else (layers[0].get("title") or "")

    parts = _svg_header(title, w, h)
    grid = {(r[x_field], r[y_field]): r[color_field] for r in rows if color_field in r}

    for i, xv in enumerate(xs):
        for j, yv in enumerate(ys):
            val = grid.get((xv, yv))
            if val is None:
                continue
            cx = margin["l"] + i * cell_w
            cy = margin["t"] + j * cell_h
            parts.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" '
                         f'fill="{_diverging_color(val)}"/>')
            text_color = "#ffffff" if abs(val) > 0.5 else "#1a1a2e"
            parts.append(f'<text x="{cx+cell_w/2:.1f}" y="{cy+cell_h/2+4:.1f}" text-anchor="middle" '
                         f'font-size="10" fill="{text_color}">{val:.2f}</text>')

    for i, xv in enumerate(xs):
        cx = margin["l"] + i * cell_w + cell_w / 2
        ty = margin["t"] + len(ys) * cell_h + 14
        parts.append(f'<text x="{cx:.1f}" y="{ty:.1f}" text-anchor="end" font-size="10" fill="#555770" '
                     f'transform="rotate(-30 {cx:.1f} {ty:.1f})">{xv}</text>')
    for j, yv in enumerate(ys):
        cy = margin["t"] + j * cell_h + cell_h / 2 + 4
        parts.append(f'<text x="{margin["l"]-8}" y="{cy:.1f}" text-anchor="end" '
                     f'font-size="10" fill="#555770">{yv}</text>')

    parts.append("</svg>")
    return "".join(parts)
