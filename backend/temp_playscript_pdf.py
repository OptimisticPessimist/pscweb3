from collections import namedtuple
import io

from reportlab.lib.pagesizes import portrait, A5
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

from .. import PScLineType

_Size = namedtuple('Size', 'w h')


class PageMan:
    """PDF ストリーム生成クラス
    """
    def __init__(self, size, margin=None, upper_space=None,
                 font_name='HeiseiMin-W3', num_font_name='Times-Roman',
                 font_size=10.0, line_space=None, before_init_page=None):
        """コンストラクタ

        Parameters
        ----------
        size : tuple
            ページのサイズ (ポイント)
        margin : tuple
            左右と上下のマージン (ポイント)
        upper_space : float
            上の余白 (ポイント)
        font_name : str
            本文のフォント
        num_font_name : str
            数字のフォント
        font_size : float
            本文のフォントサイズ (ポイント)
        line_space : float
            本文の行間 (ポイント)
        before_init_page : function
            ページ初期化時のカスタム処理の関数
        """

        # 属性の設定
        self.size = _Size(*size)
        self.font_name = font_name
        self.num_font_name = num_font_name
        self.font_size = font_size
        self.before_init_page = before_init_page

        self.margin = _Size(*margin) if margin else _Size(2 * cm, 2 * cm)
        self.upper_space = self.size.h / 4 if upper_space is None \
            else upper_space
        self.line_space = self.font_size * 0.95 if line_space is None \
            else line_space

        # 書き出しの準備
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
        """ページごとの初期化処理
        """
        # カスタム処理
        if self.before_init_page:
            self.before_init_page(self)

        # 横線を書き出す
        x1 = self.margin.w - self.line_space
        x2 = self.size.w - self.margin.w + self.line_space
        y = self.size.h - self.margin.h - self.upper_space
        self.canvas.setLineWidth(0.1)
        self.canvas.line(x1, y, x2, y)

        # フォントを設定する
        self.canvas.setFont(self.font_name, self.font_size)

    def _commit_page(self):
        """現在のページを確定し、次から新しいページに書き出す
        """
        self.canvas.showPage()

    def close(self):
        """PDF ストリームへの書き出しを終了する
        """
        self._commit_page()
        self.canvas.save()
        self.pdf.seek(0)

    def save(self, file_name):
        """PDF ストリームをファイルに出力する
        """
        with open(file_name, 'wb') as f:
            f.write(self.pdf.read())

    def _draw_line(self, l_idx, text, indent=None):
        """テキストを行末まで書き出して残りを返す
        """
        # インデントのデフォルトを1文字分とする
        if indent is None:
            indent = self.font_size

        x = self._get_line_x(l_idx)
        y = self._get_line_y(indent)

        height = self.size.h - 2 * self.margin.h - self.upper_space \
            - indent
        max_len = int(height // self.font_size)

        # 簡易的ぶら下げ処理
        if len(text) > max_len and text[max_len] in '、。」':
            max_len += 1
            if len(text) > max_len and text[max_len] == '」':
                max_len -= 2

        # テキストを書き出す
        self.canvas.drawString(x, y, text[:max_len])
        return text[max_len:]

    def _draw_lines(self, l_idx, lines, indent=None, first_indent=None):
        """複数行に渡るテキストを書き出す
        """
        if not first_indent:
            first_indent = indent

        # 改行で分ける
        texts = lines.splitlines()
        first_line = True

        for text in texts:
            line = text
            while len(line) > 0:
                # l_idx をチェックして改ページ
                if l_idx >= self._max_line_count():
                    self._commit_page()
                    self._init_page()
                    l_idx = 0

                # 1行分だけ書き出す
                line_indent = first_indent if first_line else indent
                line = self._draw_line(l_idx, line, indent=line_indent)
                first_line = False
                l_idx += 1
        return l_idx

    def _draw_single_line(self, l_idx, line, indent=None):
        """1行に収まるテキストを書き出す
        """
        # l_idx をチェックして改ページ
        if l_idx >= self._max_line_count():
            self._commit_page()
            self._init_page()
            l_idx = 0

        # テキストを書き出す
        _ = self._draw_line(l_idx, line, indent=indent)
        return l_idx + 1

    def _draw_line_bottom(self, l_idx, line):
        """テキストを下寄せで書き出す
        """
        # インデント (1文字分)
        indent = self.font_size

        # 1行に収まる文字数にする
        height = self.size.h - 2 * self.margin.h - self.upper_space \
            - indent
        max_len = int(height // self.font_size)
        line = line[:max_len]

        # 下端につくようにインデントを増やす
        indent += (max_len - len(line)) * self.font_size

        # テキストを1行として書き出す
        l_idx = self._draw_single_line(l_idx, line, indent=indent)
        return l_idx

    def draw_title(self, l_idx, ttl_line):
        """題名を PDF ストリームに書き出す
        """
        indent = self.font_size * 7
        l_idx = self._draw_lines(l_idx, ttl_line.text, indent=indent)
        return l_idx

    def draw_author(self, l_idx, athr_line):
        """著者名を PDF ストリームに書き出す
        """
        self._draw_line_bottom(l_idx, athr_line.text)
        return l_idx + 1

    def draw_charsheadline(self, l_idx, chead_line):
        """登場人物見出し行を PDF ストリームに書き出す
        """
        # インデント (8文字分)
        indent = self.font_size * 8

        # テキストを1行として書き出す
        l_idx = self._draw_single_line(l_idx, chead_line.text, indent=indent)
        return l_idx

    def draw_character(self, l_idx, char_line):
        """登場人物行を PDF ストリームに書き出す
        """
        name = char_line.name
        text = char_line.text if hasattr(char_line, 'text') else ''

        # 名前に説明をつけて一個の文字列にする
        if text:
            # 名前が2文字未満の場合は空白を足してから説明をつける
            if len(name) < 2:
                name += '　'
            text = name + '　' + text
        else:
            text = name

        # インデント (7文字分 -> 10文字分)
        first_indent = self.font_size * 7
        indent = self.font_size * 10

        # テキストを書き出す
        l_idx = self._draw_lines(
            l_idx, text, indent=indent, first_indent=first_indent)
        return l_idx

    def draw_slugline(self, l_idx, hx_line, number=None, border=False):
        """柱を PDF ストリームに書き出す
        """
        # テキストを1行として書き出す
        l_idx = self._draw_single_line(l_idx, hx_line.text)

        # 囲み線
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

        # 数字
        if number is not None:
            num_str = str(number)
            w = self.canvas.stringWidth(
                num_str, self.num_font_name, self.font_size)
            x = self._get_line_x(l_idx - 1) - w / 2
            y = self._get_line_y(-self.font_size)

            # 数字を書き出す
            self.canvas.setFont(self.num_font_name, self.font_size)
            self.canvas.drawString(x, y, num_str)

            # フォントを元に戻す
            self.canvas.setFont(self.font_name, self.font_size)

        return l_idx

    def draw_direction(self, l_idx, drct_line):
        """ト書き行を PDF ストリームに書き出す
        """
        indent = self.font_size * 7
        l_idx = self._draw_lines(l_idx, drct_line.text, indent=indent)
        return l_idx

    def draw_dialogue(self, l_idx, dlg_line):
        """セリフ行を PDF ストリームに書き出す
        """
        name = dlg_line.name
        text = dlg_line.text

        # 名前にセリフをつけて一個の文字列にする
        if len(name) == 1:
            name = ' ' + name + ' '
        elif len(name) == 2:
            name = name[0] + ' ' + name[1]
        text = name + '「' + text + '」'

        # インデント (1文字分 -> 5文字分)
        first_indent = self.font_size * 1
        indent = self.font_size * 5

        # テキストを書き出す
        l_idx = self._draw_lines(
            l_idx, text, indent=indent, first_indent=first_indent)
        return l_idx

    def draw_endmark(self, l_idx, endmk_line):
        """エンドマークを PDF ストリームに書き出す
        """
        self._draw_line_bottom(l_idx, endmk_line.text)
        return l_idx + 1

    def draw_comment(self, l_idx, cmmt_line):
        """コメント行を PDF ストリームに書き出す
        """
        indent = self.font_size * 7
        l_idx = self._draw_lines(l_idx, cmmt_line.text, indent=indent)
        return l_idx

    def draw_empty(self, l_idx, empty_line):
        """空行を PDF ストリームに書き出す
        """
        # 空文字列を1行として書き出す
        l_idx = self._draw_single_line(l_idx, '')
        return l_idx


def _get_h2_letter(h2_count):
    if h2_count < 1:
        return ''
    h2_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    max_num = len(h2_letters)
    q = (h2_count - 1) // max_num
    s = (h2_count - 1) % max_num
    return _get_h2_letter(q) + h2_letters[s]


def psc_to_pdf(psc, size=None, margin=None, upper_space=None,
               font_name='HeiseiMin-W3', num_font_name='Times-Roman',
               font_size=10.0, line_space=None, before_init_page=None,
               draw_page_num=True):
    """台本オブジェクトから PDF ストリームを生成する

    Parameters
    ----------
    psc : PSc
        ソースとなる台本オブジェクト
    size : tuple
        ページのサイズ (ポイント)
    margin : tuple
        左右と上下のマージン (ポイント)
    upper_space : float
        上の余白 (ポイント)
    font_name : str
        本文のフォント
    num_font_name : str
        数字のフォント
    font_size : float
        本文のフォントサイズ (ポイント)
    line_space : float
        本文の行間 (ポイント)
    before_init_page : function
        ページ初期化時のカスタム処理の関数
    draw_page_num : bool
        ページ番号を書き出すかどうか

    Returns
    -------
    PDF ストリーム : BytesIO
    """
    # ページ初期化時のカスタム処理
    def custom_init(pm):
        if before_init_page:
            before_init_page(pm)

        if draw_page_num:
            # ページ番号を加算して文字列にする
            if hasattr(pm, 'page_num'):
                pm.page_num += 1
            else:
                pm.page_num = 1
            s = f'- {pm.page_num} -'

            # フォントと位置の準備
            f_name = pm.num_font_name
            f_size = pm.font_size * 0.8
            w = pm.canvas.stringWidth(s, f_name, f_size)
            pm.canvas.setFont(f_name, f_size)
            x = pm.size.w / 2 - w / 2
            y = pm.margin.h / 2

            # 書き出す
            pm.canvas.drawString(x, y, s)

    # フォントの設定
    pdfmetrics.registerFont(UnicodeCIDFont(font_name, isVertical=True))

    # ページの設定
    if not size:
        size = portrait(A5)
    if not margin:
        margin = (2.0 * cm, 2.0 * cm)
    pm = PageMan(size, margin=margin, upper_space=upper_space,
                 font_name=font_name, num_font_name=num_font_name,
                 font_size=font_size, line_space=line_space,
                 before_init_page=custom_init)

    last_line_type = None
    h1_count = h2_count = 0
    l_idx = 0

    # 行ごとの処理
    for psc_line in psc.lines:
        line_type = psc_line.type

        # 行の種類が変わったら、1行空ける
        if last_line_type and (last_line_type != line_type):
            if not (last_line_type == PScLineType.TITLE
                    and line_type == PScLineType.AUTHOR):
                l_idx += 1

        if line_type == PScLineType.TITLE:
            l_idx = pm.draw_title(l_idx, psc_line)

        elif line_type == PScLineType.AUTHOR:
            l_idx = pm.draw_author(l_idx, psc_line)

        elif line_type == PScLineType.CHARSHEADLINE:
            l_idx = pm.draw_charsheadline(l_idx, psc_line)

        elif line_type == PScLineType.CHARACTER:
            l_idx = pm.draw_character(l_idx, psc_line)

        elif line_type == PScLineType.H1:
            h1_count += 1
            h2_count = 0
            l_idx = pm.draw_slugline(
                l_idx, psc_line, number=h1_count, border=True)

        elif line_type == PScLineType.H2:
            h2_count += 1
            number = str(h1_count) + _get_h2_letter(h2_count)
            l_idx = pm.draw_slugline(l_idx, psc_line, number=number)

        elif line_type == PScLineType.H3:
            l_idx = pm.draw_slugline(l_idx, psc_line)

        elif line_type == PScLineType.DIRECTION:
            l_idx = pm.draw_direction(l_idx, psc_line)

        elif line_type == PScLineType.DIALOGUE:
            l_idx = pm.draw_dialogue(l_idx, psc_line)

        elif line_type == PScLineType.ENDMARK:
            l_idx = pm.draw_endmark(l_idx, psc_line)

        elif line_type == PScLineType.COMMENT:
            l_idx = pm.draw_comment(l_idx, psc_line)

        elif line_type == PScLineType.EMPTY:
            l_idx = pm.draw_empty(l_idx, psc_line)

        else:
            raise TypeError(f'{line_type} はサポートされていません。')

        last_line_type = line_type

    # PDF の入ったバイナリストリームを返す
    pm.close()
    return pm.pdf
