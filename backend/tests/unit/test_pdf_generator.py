from src.services.pdf_generator import generate_script_pdf
import pytest

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


@pytest.mark.parametrize("orientation,writing_direction", [
    ("landscape", "vertical"),
    ("portrait", "vertical"),
    ("landscape", "horizontal"),
    ("portrait", "horizontal"),
])
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

