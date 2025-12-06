from playscript.conv import fountain, pdf
import io

def generate_script_pdf(fountain_content: str) -> bytes:
    """Fountain形式のテキストから縦書きPDFを生成する.
    
    Args:
        fountain_content (str): Fountain形式の脚本テキスト
        
    Returns:
        bytes: 生成されたPDFのバイナリデータ
    """
    # Playscriptライブラリを使用してFountainをパース
    # psc_from_fountain は playscript.script.Script オブジェクトを返す（はず）
    script = fountain.psc_from_fountain(fountain_content)
    
    # PDFストリームを生成
    # psc_to_pdf は io.BytesIO オブジェクトを返す
    pdf_stream = pdf.psc_to_pdf(script)
    
    # バイト列として返す
    return pdf_stream.getvalue()
