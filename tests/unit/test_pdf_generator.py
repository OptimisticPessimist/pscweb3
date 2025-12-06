from src.services.pdf_generator import generate_script_pdf

def test_generate_script_pdf() -> None:
    """PDF生成のシンプルなテスト."""
    fountain_content = """Title: Test Script
Author: Me

INT. ROOM - DAY

CHARACTER
Hello world.
"""
    pdf_bytes = generate_script_pdf(fountain_content)
    
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # PDFヘッダーチェック
    # 通常PDFは %PDF-1.x で始まる
    assert pdf_bytes.startswith(b"%PDF")
