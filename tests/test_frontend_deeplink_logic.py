import re
from pathlib import Path


def test_deep_link_logic_present_in_frontend_bundle():
    app_js_path = Path("src/normen_tool/static/app.js")
    content = app_js_path.read_text(encoding="utf-8")

    assert "parseDeepLinkParams" in content
    assert "updateDeepLinkUrl" in content
    assert "drawBlockHighlights" in content
    assert "focusBlockById" in content
    assert "getHighlightBlockIdsForPage" in content
