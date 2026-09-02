"""Static guards on the sidebar panel's stylesheet (custom panel height).

The panel is registered with ``component_name="custom"`` and
``embed_iframe: False``. HA does not give ``<ha-panel-custom>`` a definite
height in that configuration, so a percentage height on ``:host`` resolves to
``auto``: the host shrinks to content height and the iframe collapses with it.
A reporter measured the whole chain at 1344x150 in a 1600x1000 viewport —
nav bar, one card, then empty page background for the rest of the screen.

The fix is a viewport-relative height. These tests parse the stylesheet text
rather than render it; they exist to stop ``height: 100%`` from creeping back
onto ``:host``, which is the exact regression that produced the collapse.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PANEL_JS = (
    Path(__file__).resolve().parents[1]
    / "custom_components/culiplan/frontend/culiplan-panel.js"
)


@pytest.fixture(scope="module")
def styles() -> str:
    """Return the STYLES template literal, comments stripped."""
    source = PANEL_JS.read_text(encoding="utf-8")
    start = source.index("const STYLES = `")
    end = source.index("`;", start)
    css = source[start + len("const STYLES = `") : end]
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def _rule(styles: str, selector: str) -> str:
    """Return the declaration block for a top-level selector."""
    match = re.search(
        rf"(?:^|\}}|\n)\s*{re.escape(selector)}\s*\{{(.*?)\}}", styles, re.DOTALL
    )
    assert match, f"{selector} rule not found"
    return match.group(1)


def test_host_height_is_viewport_relative(styles: str) -> None:
    """:host must not depend on an ancestor's height."""
    host = _rule(styles, ":host")
    heights = re.findall(r"height:\s*([^;]+);", host)
    assert heights, ":host declares no height"
    for value in heights:
        assert "%" not in value, (
            f":host height {value.strip()!r} is ancestor-relative; HA gives "
            "<ha-panel-custom> no definite height, so this resolves to auto and "
            "the panel collapses to content height (~150px)."
        )
    assert any("vh" in v for v in heights), ":host needs a vh-based height"


def test_host_is_a_flex_column(styles: str) -> None:
    """The iframe grows via flex, so the host must establish the column."""
    host = _rule(styles, ":host")
    assert re.search(r"display:\s*flex", host), ":host must be display: flex"
    assert re.search(r"flex-direction:\s*column", host)


def test_fill_grows_to_consume_remaining_space(styles: str) -> None:
    """.fill is the iframe — it must flex, not inherit a percentage height."""
    fill = _rule(styles, ".fill")
    assert re.search(r"flex:\s*1", fill), ".fill must grow to fill the host"
    assert not re.search(r"height:\s*\d+%", fill), (
        ".fill must not use a percentage height — it collapses with the host"
    )
    assert re.search(r"min-height:\s*0", fill), (
        ".fill needs min-height: 0 so the flex item can shrink below content size"
    )


def test_dynamic_viewport_height_is_offered(styles: str) -> None:
    """100dvh keeps mobile browser chrome from clipping the app."""
    host = _rule(styles, ":host")
    assert "100dvh" in host
    # Must come after the 100vh fallback so older browsers keep a usable value.
    assert host.index("100vh") < host.index("100dvh")
