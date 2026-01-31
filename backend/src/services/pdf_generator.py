
from playscript.conv import fountain, pdf as psc_pdf
import io
import os
from collections import namedtuple
from reportlab.lib.pagesizes import landscape, A4, portrait, A5
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from playscript import PScLineType, PScLine

# Font registration logic (kept from previous version)
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.abspath(os.path.join(current_dir, "../assets/fonts/ShipporiMincho-Regular.ttf"))
    
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('ShipporiMincho', font_path))
            DEFAULT_FONT = 'HeiseiMin-W3' # Fallback for playscript internal compatibility if needed, but we control PageMan now
            # For our CustomPageMan, we can use 'ShipporiMincho' if we want, 
            # but to be safe and consistent with previous working state, let's keep 'HeiseiMin-W3' as default 
            # or try to use ShipporiMincho if properly registered.
            # Let's stick to HeiseiMin-W3 for now to avoid KeyError as noted in comments previously.
            DEFAULT_FONT = 'HeiseiMin-W3' 
        except Exception:
             pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
             DEFAULT_FONT = 'HeiseiMin-W3'
    else:
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
        DEFAULT_FONT = 'HeiseiMin-W3'
except Exception:
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
    DEFAULT_FONT = 'HeiseiMin-W3'

_Size = namedtuple('Size', 'w h')

class CustomPageMan:
    """PDF ストリーム生成クラス (Customized for Synopsis and Cover Page)"""
    def __init__(self, size, margin=None, upper_space=None,
                 font_name='HeiseiMin-W3', num_font_name='Times-Roman',
                 font_size=10.0, line_space=None, before_init_page=None):
        
        self.size = _Size(*size)
        self.font_name = font_name
        self.num_font_name = num_font_name
        self.font_size = font_size
        self.before_init_page = before_init_page

        self.margin = _Size(*margin) if margin else _Size(2 * cm, 2 * cm)
        self.upper_space = self.size.h / 4 if upper_space is None else upper_space
        self.line_space = self.font_size * 0.95 if line_space is None else line_space

        self.pdf = io.BytesIO()
        self.canvas = canvas.Canvas(self.pdf, pagesize=self.size)
        self._init_page()

    def _get_line_x(self, l_idx):
        x = self.size.w - self.margin.w - self.font_size / 2
        x = x - l_idx * (self.font_size + self.line_space)
        return x

    def _get_line_y(self, indent):
        y = self.size.h - self.margin.h - self.upper_space - indent
        return y

    def _max_line_count(self):
        area_w = self.size.w - 2 * self.margin.w + self.line_space
        count = area_w // (self.font_size + self.line_space)
        return int(count)

    def _init_page(self):
        if self.before_init_page:
            self.before_init_page(self)

        x1 = self.margin.w - self.line_space
        x2 = self.size.w - self.margin.w + self.line_space
        y = self.size.h - self.margin.h - self.upper_space
        self.canvas.setLineWidth(0.1)
        self.canvas.line(x1, y, x2, y)

        self.canvas.setFont(self.font_name, self.font_size)

    def _commit_page(self):
        self.canvas.showPage()
    
    def force_page_break(self):
        self._commit_page()
        self._init_page()
        return 0 # new l_idx

    def close(self):
        self._commit_page()
        self.canvas.save()
        self.pdf.seek(0)

    def _draw_line(self, l_idx, text, indent=None):
        if indent is None:
            indent = self.font_size

        x = self._get_line_x(l_idx)
        y = self._get_line_y(indent)

        height = self.size.h - 2 * self.margin.h - self.upper_space - indent
        max_len = int(height // self.font_size)

        if len(text) > max_len and text[max_len] in '、。」':
            max_len += 1
            if len(text) > max_len and text[max_len] == '」':
                max_len -= 2

        self.canvas.drawString(x, y, text[:max_len])
        return text[max_len:]

    def _draw_lines(self, l_idx, lines, indent=None, first_indent=None):
        if not first_indent:
            first_indent = indent

        texts = lines.splitlines()
        first_line = True

        for text in texts:
            line = text
            while len(line) > 0:
                if l_idx >= self._max_line_count():
                    self.force_page_break()
                    l_idx = 0

                line_indent = first_indent if first_line else indent
                line = self._draw_line(l_idx, line, indent=line_indent)
                first_line = False
                l_idx += 1
        return l_idx

    def _draw_single_line(self, l_idx, line, indent=None):
        if l_idx >= self._max_line_count():
            self.force_page_break()
            l_idx = 0
        _ = self._draw_line(l_idx, line, indent=indent)
        return l_idx + 1

    def _draw_line_bottom(self, l_idx, line):
        indent = self.font_size
        height = self.size.h - 2 * self.margin.h - self.upper_space - indent
        max_len = int(height // self.font_size)
        line = line[:max_len]
        indent += (max_len - len(line)) * self.font_size
        l_idx = self._draw_single_line(l_idx, line, indent=indent)
        return l_idx

    def draw_title(self, l_idx, ttl_line):
        indent = self.font_size * 7
        l_idx = self._draw_lines(l_idx, ttl_line.text, indent=indent)
        return l_idx

    def draw_author(self, l_idx, athr_line):
        self._draw_line_bottom(l_idx, athr_line.text)
        return l_idx + 1

    def draw_charsheadline(self, l_idx, chead_line):
        indent = self.font_size * 8
        l_idx = self._draw_single_line(l_idx, chead_line.text, indent=indent)
        return l_idx

    def draw_character(self, l_idx, char_line):
        name = char_line.name
        text = char_line.text if hasattr(char_line, 'text') else ''
        if text:
            if len(name) < 2: name += '　'
            text = name + '　' + text
        else:
            text = name
        first_indent = self.font_size * 7
        indent = self.font_size * 10
        l_idx = self._draw_lines(l_idx, text, indent=indent, first_indent=first_indent)
        return l_idx

    def draw_slugline(self, l_idx, hx_line, number=None, border=False):
        l_idx = self._draw_single_line(l_idx, hx_line.text)
        if border:
            x = self._get_line_x(l_idx - 1)
            x1 = x + self.font_size / 2 + self.line_space * 0.8
            x2 = x - self.font_size / 2 - self.line_space * 0.8
            y1 = self._get_line_y(-(self.font_size * 3))
            y2 = self.margin.h - self.font_size
            self.canvas.setLineWidth(0.1)
            self.canvas.line(x1, y1, x1, y2)
            self.canvas.line(x1, y1, x2, y1)
            self.canvas.line(x2, y1, x2, y2)
        if number is not None:
            num_str = str(number)
            w = self.canvas.stringWidth(num_str, self.num_font_name, self.font_size)
            x = self._get_line_x(l_idx - 1) - w / 2
            y = self._get_line_y(-self.font_size)
            self.canvas.setFont(self.num_font_name, self.font_size)
            self.canvas.drawString(x, y, num_str)
            self.canvas.setFont(self.font_name, self.font_size)
        return l_idx

    def draw_direction(self, l_idx, drct_line):
        indent = self.font_size * 7
        l_idx = self._draw_lines(l_idx, drct_line.text, indent=indent)
        return l_idx

    def draw_synopsis_text(self, l_idx, text):
        """Draw text specifically for synopsis body"""
        # Synopsis style: 
        # - Slightly more indented top or bottom? 
        # - Or just block indent?
        # Let's match typical Japanese novel text or just standard indentation but distinct.
        # Standard direction is *7. User wants it styled differently from other chapters.
        # Let's try indentation *2 (closer to top/character names) but not *7.
        # Or maybe *4?
        indent = self.font_size * 4 
        l_idx = self._draw_lines(l_idx, text, indent=indent)
        return l_idx

    def draw_dialogue(self, l_idx, dlg_line):
        name = dlg_line.name
        text = dlg_line.text
        if len(name) == 1: name = ' ' + name + ' '
        elif len(name) == 2: name = name[0] + ' ' + name[1]
        text = name + '「' + text + '」'
        first_indent = self.font_size * 1
        indent = self.font_size * 5
        l_idx = self._draw_lines(l_idx, text, indent=indent, first_indent=first_indent)
        return l_idx

    def draw_endmark(self, l_idx, endmk_line):
        self._draw_line_bottom(l_idx, endmk_line.text)
        return l_idx + 1

    def draw_comment(self, l_idx, cmmt_line):
        indent = self.font_size * 7
        l_idx = self._draw_lines(l_idx, cmmt_line.text, indent=indent)
        return l_idx

    def draw_empty(self, l_idx, empty_line):
        l_idx = self._draw_single_line(l_idx, '')
        return l_idx

def _get_h2_letter(h2_count):
    if h2_count < 1: return ''
    h2_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    max_num = len(h2_letters)
    q = (h2_count - 1) // max_num
    s = (h2_count - 1) % max_num
    return _get_h2_letter(q) + h2_letters[s]

def custom_psc_to_pdf(psc, size=None, margin=None, upper_space=None,
                      font_name='HeiseiMin-W3', num_font_name='Times-Roman',
                      font_size=10.0, line_space=None, before_init_page=None,
                      draw_page_num=True):
    
    def custom_init(pm):
        if before_init_page: before_init_page(pm)
        if draw_page_num:
            if hasattr(pm, 'page_num'): pm.page_num += 1
            else: pm.page_num = 1
            s = f'- {pm.page_num} -'
            f_name = pm.num_font_name
            f_size = pm.font_size * 0.8
            w = pm.canvas.stringWidth(s, f_name, f_size)
            pm.canvas.setFont(f_name, f_size)
            x = pm.size.w / 2 - w / 2
            y = pm.margin.h / 2
            pm.canvas.drawString(x, y, s)

    pdfmetrics.registerFont(UnicodeCIDFont(font_name, isVertical=True))

    if not size: size = portrait(A5)
    if not margin: margin = (2.0 * cm, 2.0 * cm)
    
    pm = CustomPageMan(size, margin=margin, upper_space=upper_space,
                 font_name=font_name, num_font_name=num_font_name,
                 font_size=font_size, line_space=line_space,
                 before_init_page=custom_init)

    last_line_type = None
    h1_count = h2_count = 0
    l_idx = 0
    
    in_synopsis = False
    
    # Pre-scan for Title/Author to ensure we handle the cover page break correctly
    # actually we can just monitor usage.

    # Pre-scan for Title/Author to ensure we handle the cover page break correctly
    # actually we can just monitor usage.

    for i, psc_line in enumerate(psc.lines):
        line_type = psc_line.type

        # Check if we are entering Synopsis section
        if line_type == PScLineType.H1:
             if "あらすじ" in psc_line.text or "Synopsis" in psc_line.text:
                 in_synopsis = True
             else:
                 in_synopsis = False
        
        # 行の種類が変わったら、1行空ける (standard logic)
        # Exception: Don't space between Title and Author
        if last_line_type and (last_line_type != line_type):
            if not (last_line_type == PScLineType.TITLE and line_type == PScLineType.AUTHOR):
                l_idx += 1

        if line_type == PScLineType.TITLE:
            l_idx = pm.draw_title(l_idx, psc_line)

        elif line_type == PScLineType.AUTHOR:
            # Change: Use draw_lines (via draw_charsheadline style or new method) 
            # instead of draw_author/draw_line_bottom which truncates.
            # We want to display full metadata even if it wraps.
            # Let's reuse draw_charsheadline logic but with different indent?
            # Or just use draw_lines with appropriate indent.
            
            # Use indent similar to charsheadline (8 chars) or title (7 chars)?
            # Let's use 4 chars indent to center it relatively well under title
            indent = pm.font_size * 4
            l_idx = pm._draw_lines(l_idx, psc_line.text, indent=indent)
            
            # Force page break after Author (End of Cover Page)
            l_idx = pm.force_page_break()

        elif line_type == PScLineType.CHARSHEADLINE:
            l_idx = pm.draw_charsheadline(l_idx, psc_line)

        elif line_type == PScLineType.CHARACTER:
            l_idx = pm.draw_character(l_idx, psc_line)

        elif line_type == PScLineType.H1:
            if in_synopsis:
                # Do NOT increment h1_count for Synopsis
                # Draw slugline without number
                l_idx = pm.draw_slugline(l_idx, psc_line, number=None, border=True)
            else:
                h1_count += 1
                h2_count = 0
                l_idx = pm.draw_slugline(l_idx, psc_line, number=h1_count, border=True)

        elif line_type == PScLineType.H2:
            h2_count += 1
            number = str(h1_count) + _get_h2_letter(h2_count)
            l_idx = pm.draw_slugline(l_idx, psc_line, number=number)

        elif line_type == PScLineType.H3:
            l_idx = pm.draw_slugline(l_idx, psc_line)

        elif line_type == PScLineType.DIRECTION:
            if in_synopsis:
                l_idx = pm.draw_synopsis_text(l_idx, psc_line.text)
            else:
                l_idx = pm.draw_direction(l_idx, psc_line)

        elif line_type == PScLineType.DIALOGUE:
            if in_synopsis:
                 l_idx = pm.draw_synopsis_text(l_idx, psc_line.text) # Strip name if it was parsed as dialogue?
            else:
                l_idx = pm.draw_dialogue(l_idx, psc_line)

        elif line_type == PScLineType.ENDMARK:
            l_idx = pm.draw_endmark(l_idx, psc_line)

        elif line_type == PScLineType.COMMENT:
            l_idx = pm.draw_comment(l_idx, psc_line)

        elif line_type == PScLineType.EMPTY:
             # Empty line.
             l_idx = pm.draw_empty(l_idx, psc_line)

        else:
             # Unknown, skip or error.
             pass

        last_line_type = line_type

    pm.close()
    return pm.pdf

def generate_script_pdf(fountain_content: str) -> bytes:
    """Fountain形式のテキストから縦書きPDFを生成する."""
    from fountain.fountain import Fountain
    
    # Standard parsing
    f_parser = Fountain(fountain_content)
    metadata = f_parser.metadata
    
    script = fountain.psc_from_fountain(fountain_content)
    
    # --- Metadata Injection Logic (Refined) ---
    extra_info_parts = []
    
    if "date" in metadata:
        extra_info_parts.append(f"Date: {', '.join(metadata['date'])}")
    if "draft date" in metadata:
        extra_info_parts.append(f"Draft: {', '.join(metadata['draft date'])}")
    if "revision" in metadata:
        extra_info_parts.append(f"Rev: {', '.join(metadata['revision'])}")
    if "copyright" in metadata:
        extra_info_parts.append(f"(c) {', '.join(metadata['copyright'])}")
    if "contact" in metadata:
        # Contact might be long, keep it separate or join?
        # Let's join with space but maybe sanitize newlines
        contact = " ".join(metadata['contact']).replace('\n', ' ')
        extra_info_parts.append(f"Contact: {contact}")
    if "notes" in metadata:
        notes = " ".join(metadata['notes']).replace('\n', ' ')
        extra_info_parts.append(f"Note: {notes}")
        
    # Prepare Author
    authors = metadata.get("author", [])
    author_str = ", ".join(authors) if authors else ""
    
    final_metadata_parts = []
    if author_str:
        final_metadata_parts.append(author_str)
    
    if extra_info_parts:
        final_metadata_parts.extend(extra_info_parts)
    
    # HORIZONTAL LAYOUT: Join with wide spaces
    final_metadata_str = "   ".join(final_metadata_parts)
    
    # Inject into Script Object
    if final_metadata_str:
        from playscript import PScLineType, PScLine
        new_lines = []
        found_title = False
        author_injected = False
        
        for line in script.lines:
            if line.type == PScLineType.TITLE:
                found_title = True
                new_lines.append(line)
            elif line.type == PScLineType.AUTHOR:
                line.text = final_metadata_str
                new_lines.append(line)
                author_injected = True
            else:
                if found_title and not author_injected:
                    author_line = PScLine(type=PScLineType.AUTHOR, text=final_metadata_str)
                    new_lines.append(author_line)
                    author_injected = True
                new_lines.append(line)
        
        if not found_title and not author_injected:
             author_line = PScLine(type=PScLineType.AUTHOR, text=final_metadata_str)
             new_lines.insert(0, author_line)
        if found_title and not author_injected:
             author_line = PScLine(type=PScLineType.AUTHOR, text=final_metadata_str)
             new_lines.append(author_line)
             
        script.lines = new_lines

    # Use Custom Generator
    # size=landscape(A4) is what we want
    pdf_stream = custom_psc_to_pdf(script, font_name=DEFAULT_FONT, size=landscape(A4))
    
    return pdf_stream.getvalue()
