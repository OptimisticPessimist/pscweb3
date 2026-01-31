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
    
    
    # Synopsis (あらすじ) handling
    synopsis = metadata.get("synopsis", metadata.get("あらすじ", []))
    if synopsis:
        extra_info_parts.append(f"\n【あらすじ】\n{'\n'.join(synopsis)}")

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

    script = fountain.psc_from_fountain(fountain_content)
    
    # メタデータをAuthor行に集約する（Title行のスタイル維持のため）
    # Author行がない場合はTitle行の後に作成して挿入する
    
    # まずAuthor情報を取得（Fountainパーサーが取得していない可能性があるためmetadataから再取得）
    authors = metadata.get("author", [])
    author_str = ", ".join(authors) if authors else ""
    
    # 表示用のメタデータ文字列を作成
    # Authorが一番上に来るようにする
    if author_str:
        final_metadata_parts = [author_str]
    else:
        final_metadata_parts = []
        
    if extra_info_parts:
        final_metadata_parts.extend(extra_info_parts)
    
    final_metadata_str = "\n".join(final_metadata_parts)

    if final_metadata_str:
        from playscript import PScLineType, PScLine
        
        new_lines = []
        found_title = False
        author_injected = False
        
        for line in script.lines:
            if line.type == PScLineType.TITLE:
                found_title = True
                new_lines.append(line)
                # タイトル直後にAuthor行を挿入する場合（まだ挿入していなくて、かつこの次がAuthorでない場合）
                # ただし、既存のAuthor行があるかどうかはこのループ内だけでは判断しにくいので
                # タイトル行を見つけたらフラグを立てておき、既存Author行があれば置換、なければ挿入というロジックにする
                
            elif line.type == PScLineType.AUTHOR:
                # 既存のAuthor行を、生成したmetadata文字列に置き換える
                line.text = final_metadata_str
                new_lines.append(line)
                author_injected = True
            
            else:
                # Title行の後、かつまだAuthor行に出会っていない（=最初のセリフやト書きなど）場合
                # ここでAuthor行を挿入する
                if found_title and not author_injected:
                    # Author行を作成して挿入
                    author_line = PScLine(type=PScLineType.AUTHOR, text=final_metadata_str)
                    new_lines.append(author_line)
                    author_injected = True
                
                new_lines.append(line)
        
        # 万が一TITLE行もAUTHOR行もなかった場合（レアケースだが）
        if not found_title and not author_injected:
             # 先頭に挿入
             author_line = PScLine(type=PScLineType.AUTHOR, text=final_metadata_str)
             new_lines.insert(0, author_line)
             
        # TITLE行はあるがそれ以降何もない場合などでまだ挿入されていない場合
        if found_title and not author_injected:
             author_line = PScLine(type=PScLineType.AUTHOR, text=final_metadata_str)
             new_lines.append(author_line)

        script.lines = new_lines

    # PDFストリームを生成
    # 縦書き・明朝体を使用
    # 演劇台本の標準的な書式である「縦書き・横置き」にするため、用紙サイズを横向き(landscape)に設定
    # 用紙サイズはA4とする
    pdf_stream = pdf.psc_to_pdf(script, font_name=DEFAULT_FONT, size=landscape(A4))
    
    # バイト列として返す
    return pdf_stream.getvalue()
