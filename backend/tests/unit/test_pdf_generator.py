import pytest

from src.services.pdf_generator import (
    _get_h2_number,
    _scene_headings_to_sections,
    generate_script_pdf,
)

SAMPLE_FOUNTAIN = """Title: Test Script
Author: Me

INT. ROOM - DAY

CHARACTER
Hello world.
"""


def test_generate_script_pdf() -> None:
    """PDF生成のシンプルなテスト（デフォルト: 横置き＋縦書き）."""
    pdf_bytes = generate_script_pdf(SAMPLE_FOUNTAIN)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # PDFヘッダーチェック
    # 通常PDFは %PDF-1.x で始まる
    assert pdf_bytes.startswith(b"%PDF")


@pytest.mark.parametrize(
    "orientation,writing_direction",
    [
        ("landscape", "vertical"),
        ("portrait", "vertical"),
        ("landscape", "horizontal"),
        ("portrait", "horizontal"),
    ],
)
def test_generate_script_pdf_all_patterns(orientation: str, writing_direction: str) -> None:
    """4パターン全てのPDF生成テスト."""
    pdf_bytes = generate_script_pdf(
        SAMPLE_FOUNTAIN,
        orientation=orientation,
        writing_direction=writing_direction,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


class TestSceneHeadingsToSections:
    """playscript が捨てる Scene Heading を Section Heading に寄せる変換."""

    def test_forced_heading_becomes_h2(self) -> None:
        src = "# ブロックⅠ\n\n.オフィス - 昼\n\n!ト書き"
        assert _scene_headings_to_sections(src) == "# ブロックⅠ\n\n## オフィス - 昼\n\n!ト書き"

    def test_standard_heading_becomes_h2(self) -> None:
        assert _scene_headings_to_sections("INT. ROOM - DAY") == "## INT. ROOM - DAY"
        assert _scene_headings_to_sections("EXT. PARK - NIGHT") == "## EXT. PARK - NIGHT"

    def test_dot1_is_act_and_dot2_is_scene(self) -> None:
        assert _scene_headings_to_sections(".1 第一幕") == "# 第一幕"
        assert _scene_headings_to_sections(".2 教室") == "## 教室"

    def test_merges_into_preceding_h2(self) -> None:
        src = "## シーン1\n\n.教室 - 朝\n\n!ト書き"
        # 結合で消えた行の空行はそのまま残る（Fountain 上は無害）
        assert _scene_headings_to_sections(src) == "## シーン1 (教室 - 朝)\n\n\n!ト書き"

    def test_does_not_merge_into_h1_or_h3(self) -> None:
        assert _scene_headings_to_sections("# 幕\n\n.教室") == "# 幕\n\n## 教室"
        assert _scene_headings_to_sections("### 小見出し\n\n.教室") == "### 小見出し\n\n## 教室"

    def test_leaves_non_headings_alone(self) -> None:
        src = "!……そうか。\n...続く\n@犬山\nセリフ。"
        assert _scene_headings_to_sections(src) == src


def test_get_h2_number() -> None:
    assert _get_h2_number(1, 1) == "1A"
    assert _get_h2_number(2, 3) == "2C"
    # 幕見出しが無い場合は "0A" にしない
    assert _get_h2_number(0, 1) == "A"


FORCED_HEADING_FOUNTAIN = """Title: Test
Author: Me

# ブロックⅠ

.オフィス - 昼

三つのスチール机。

@上司
犬山。
"""


@pytest.mark.parametrize("writing_direction", ["vertical", "horizontal"])
def test_forced_scene_heading_is_rendered(writing_direction: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """先頭 "." の強制シーン見出しが H2 として playscript に渡り、PDF が生成される."""
    from playscript import PScLineType
    from playscript.conv import fountain as psc_fountain

    captured: list = []
    original = psc_fountain.psc_from_fountain

    def spy(content: str):
        psc = original(content)
        captured.append(psc)
        return psc

    monkeypatch.setattr(psc_fountain, "psc_from_fountain", spy)

    pdf_bytes = generate_script_pdf(FORCED_HEADING_FOUNTAIN, writing_direction=writing_direction)
    assert pdf_bytes.startswith(b"%PDF")

    h2_texts = [line.text for line in captured[0].lines if line.type == PScLineType.H2]
    assert h2_texts == ["オフィス - 昼"]
