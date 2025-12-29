from playscript.conv import fountain, pdf
import io
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# フォント登録
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.abspath(os.path.join(current_dir, "../assets/fonts/ShipporiMincho-Regular.ttf"))
    print(f"DEBUG: Font path calculated as: {font_path}")
    
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('ShipporiMincho', font_path))
            print("DEBUG: Registered font 'ShipporiMincho'")
            # FIXME: Using 'ShipporiMincho' causes KeyError in playscript/reportlab interaction.
            # Reverting to default font 'HeiseiMin-W3' to ensure PDF generation works.
            DEFAULT_FONT = 'HeiseiMin-W3' 
        except Exception as e:
            print(f"DEBUG: Failed to register font: {e}")
            # フォールバック用にCIDフォントを登録
            try:
                pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
            except Exception as cid_e:
                print(f"DEBUG: Failed to register CID font: {cid_e}")
            DEFAULT_FONT = 'HeiseiMin-W3'
    else:
        print(f"DEBUG: Font file not found at {font_path}")
        # フォールバック用にCIDフォントを登録
        try:
            pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
        except Exception as cid_e:
            print(f"DEBUG: Failed to register CID font: {cid_e}")
            
        # Try to list directory to see where we are
        assets_dir = os.path.join(current_dir, "../assets/fonts")
        print(f"DEBUG: Contents of {os.path.abspath(assets_dir)}:")
        try:
            print(os.listdir(assets_dir))
        except:
            print("Could not list directory")
            
        DEFAULT_FONT = 'HeiseiMin-W3'
except Exception as e:
    print(f"DEBUG: Error in font setup: {e}")
    try:
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
    except:
        pass
    DEFAULT_FONT = 'HeiseiMin-W3'

def generate_script_pdf(fountain_content: str) -> bytes:
    """Fountain形式のテキストから縦書きPDFを生成する.
    
    Args:
        fountain_content (str): Fountain形式の脚本テキスト
        
    Returns:
        bytes: 生成されたPDFのバイナリデータ
    """
    # Playscriptライブラリを使用してFountainをパース
    script = fountain.psc_from_fountain(fountain_content)
    
    # PDFストリームを生成
    # 縦書き・明朝体を使用
    pdf_stream = pdf.psc_to_pdf(script, font_name=DEFAULT_FONT)
    
    # バイト列として返す
    return pdf_stream.getvalue()
