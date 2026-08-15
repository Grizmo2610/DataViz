from __future__ import annotations

import base64
import json
from typing import Any


def chart_to_svg(vega_spec: dict[str, Any]) -> str | None:
    """Convert a Vega-Lite spec to an SVG string using Altair's renderer.

    Shared by exporters that cannot embed an interactive Vega-Embed widget
    (Markdown, Jupyter Notebook, PDF) and instead need a static image.

    Returns:
        SVG markup, or None if no renderer backend is available.
    """
    try:
        import altair as alt
        chart = alt.Chart.from_dict(vega_spec)
        result = chart.to_image(format="svg")
        return result.decode() if isinstance(result, (bytes, bytearray)) else result
    except Exception:  # noqa: BLE001
        try:
            import vl_convert as vlc  # type: ignore[import]
            result = vlc.vegalite_to_svg(json.dumps(vega_spec))
            return result.decode() if isinstance(result, (bytes, bytearray)) else result
        except Exception:  # noqa: BLE001
            return None


def chart_to_data_uri(vega_spec: dict[str, Any]) -> str | None:
    """Convert a Vega-Lite spec to a base64 SVG data URI for embedding in
    Markdown/notebook image syntax (``![]()``).

    Returns:
        A ``data:image/svg+xml;base64,...`` string, or None on failure.
    """
    svg = chart_to_svg(vega_spec)
    if svg is None:
        return None
    encoded = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"
