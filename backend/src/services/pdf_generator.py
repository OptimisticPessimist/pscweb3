from playscript.conv import fountain, pdf
import io
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.pagesizes import landscape, A4

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
    from fountain.fountain import Fountain
    
    # メタデータを抽出してAuthorフィールドに追記するなどの処理を行う
    # Playscriptは標準でTitle, Author以外の一部メタデータを無視するため
    f_parser = Fountain(fountain_content)
    metadata = f_parser.metadata
    
    extra_info_parts = []
    
    
    if "draft date" in metadata:
        extra_info_parts.append(f"Draft: {', '.join(metadata['draft date'])}")
    elif "date" in metadata:
        extra_info_parts.append(f"Date: {', '.join(metadata['date'])}")
        
    if "contact" in metadata:
        extra_info_parts.append(f"Contact:\n{'\n'.join(metadata['contact'])}")
        
    if "copyright" in metadata:
        extra_info_parts.append(f"Copyright: {', '.join(metadata['copyright'])}")
        
    if "revision" in metadata:
        extra_info_parts.append(f"Revision: {', '.join(metadata['revision'])}")
        
    if "notes" in metadata:
        extra_info_parts.append(f"\nNotes:\n{'\n'.join(metadata['notes'])}")

    if "author" in metadata:
        # User requested explicit "Author: ..." labeling
        # adding it to the top of our metadata block
        extra_info_parts.insert(0, f"Author: {', '.join(metadata['author'])}")

    script = fountain.psc_from_fountain(fountain_content)
    
    if extra_info_parts:
        extra_info_str = "\n".join(extra_info_parts)
        # playscriptはscript.linesの内容を使用してPDFを生成するため、
        # メタデータを表示するにはTITLE行のテキストを直接書き換える必要がある
        # script.titleを変更しても反映されない
        from playscript import PScLineType
        
        # TITLE行を更新し、AUTHOR行は削除する（重複防止＆複数行表示対応のため）
        new_lines = []
        found_title = False
        
        for line in script.lines:
            if line.type == PScLineType.TITLE:
                line.text += "\n\n" + extra_info_str
                found_title = True
                new_lines.append(line)
            elif line.type == PScLineType.AUTHOR:
                # 既にTitle行にAuthorを含めたので、元のAuthor行は除外する
                continue
            else:
                new_lines.append(line)
        
        script.lines = new_lines
        
        # デバッグ用：script.titleも更新しておく
        if hasattr(script, 'title'):
             script.title += "\n\n" + extra_info_str

    # PDFストリームを生成
    # 縦書き・明朝体を使用
    # 演劇台本の標準的な書式である「縦書き・横置き」にするため、用紙サイズを横向き(landscape)に設定
    # 用紙サイズはA4とする
    pdf_stream = pdf.psc_to_pdf(script, font_name=DEFAULT_FONT, size=landscape(A4))
    
    # バイト列として返す
    return pdf_stream.getvalue()
