import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { useTranslation } from 'react-i18next';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

const fountainContent: Record<string, string> = {
    ja: `
# 📝 Fountain JA 書き方マニュアル

本システムは脚本管理に **Fountain形式（日本語拡張版）** を採用しています。
\x60.fountain\x60 拡張子のテキストファイルをアップロードすると、キャラクター名・シーン構成・香盤表が自動解析されます。

---

## 📄 基本構造

Fountain JA ファイルは、主に以下の4つの要素で構成されます。

### 1. メタデータ（ファイル冒頭）
ファイルの **一番最初に** 記述します。メタデータ部とスクリプト本体の間には **必ず空行** を入れてください。

\x60\x60\x60
Title: タイトル名
Author: 作者名
Draft date: 2025-01-01
Copyright: (c) 作者名

（ここで空行が1行必要）
\x60\x60\x60

### 2. 登場人物定義（任意）
\x60# 登場人物\x60 セクションで、キャラクターと説明を定義できます。

\x60\x60\x60
# 登場人物
太郎: 主人公。大学生。
花子: 太郎の幼馴染。
\x60\x60\x60

> 💡 ここで定義しなくても、本文中の \x60@キャラクター名\x60 から自動的にキャラクターが抽出されます。

### 3. 幕・シーン見出し
\x60#\x60 で幕（Act）、\x60##\x60 でシーンを定義します。
ドット記法も使用可能です。

| 記法 | 意味 | 例 |
|---|---|---|
| \x60#\x60 | 幕（Act） | \x60# 第一幕\x60 |
| \x60##\x60 | シーン | \x60## シーン１ リビング\x60 |
| \x60.1\x60 | 幕（Act）※ドット記法 | \x60.1 第一幕\x60 |
| \x60.2\x60 | シーン ※ドット記法 | \x60.2 シーン１ リビング\x60 |

### 4. セリフとト書き

**セリフ（一行形式）**
\x60@キャラクター名 セリフ\x60 の形式で1行に記述できます。

\x60\x60\x60
@太郎 久しぶりだね、花子。
@花子 本当に！もう3年ぶりじゃない？
\x60\x60\x60

**セリフ（複数行形式）**
\x60@キャラクター名\x60 の次行にセリフを記述する形式です。

\x60\x60\x60
@太郎
久しぶりだね、花子。
3年ぶりか。
\x60\x60\x60

**ト書き（舞台指示）**
セリフ以外の地の文がト書きになります。行頭に全角スペースを入れるとインデントが保持されます。

\x60\x60\x60
　太郎、窓の外を見ながら微笑む。
\x60\x60\x60

---

## 📋 あらすじの記述

あらすじ（Synopsis）は特別扱いされ、**シーン番号 #0** として保存されます。
香盤表やスケジュールのシーン選択には**含まれません**。

\x60\x60\x60
# あらすじ
ある地方の小さな劇場で、役者たちが新作公演に向けて稽古を始める。
しかし、主演女優が突然の失踪。残された劇団員は…。
\x60\x60\x60

> 💡 多言語キーワードにも対応しています: \x60Synopsis\x60, \x60줄거리\x60, \x60梗概\x60

---

## 📖 完全なサンプル

\x60\x60\x60
Title: 小さな劇場の奇跡
Author: 山田太郎
Draft date: 2025-06-01

# 登場人物
太郎: 主人公。新人演出家。
花子: ベテラン女優。
次郎: 舞台監督。

# あらすじ
新人演出家の太郎が、閉館寸前の劇場で最後の公演に挑む物語。

.1 第一幕

## シーン１ 稽古場
@太郎 みんな、今日から本格的に稽古を始めます。
@花子 演出さん、台本の修正はもうないの？

　太郎、少し困った顔をする。

@太郎 ……実は、昨日もう少し直したいところが見つかって。
@次郎 おいおい、本番まであと2週間だぞ。

## シーン２ 楽屋
@花子 太郎くん、大丈夫？
@太郎 うん。ありがとう、花子さん。

　花子、優しく微笑む。

.1 第二幕

## シーン３ 舞台上（本番当日）
@次郎 開演5分前！全員スタンバイ！
@太郎 よし、行こう。
\x60\x60\x60

---

## ⚠️ よくある間違い

| ❌ NGパターン | ⭕ 正しい書き方 | 理由 |
|---|---|---|
| メタデータの後に空行なし | メタデータの後に空行を1行入れる | 空行がないとメタデータとの区切りが認識されない |
| \x60@ 太郎 セリフ\x60（@の後にスペース） | \x60@太郎 セリフ\x60 | @の直後にキャラクター名を書く |
| \x60#シーン1\x60（#の後にスペースなし） | \x60# シーン1\x60 | \x60#\x60 の後には半角スペースが必要 |
| \x60# シーン1\x60（#1つでシーン） | \x60## シーン1\x60 | \x60#\x60 は幕（Act）、\x60##\x60 がシーン |

---

## 🔗 香盤表との連動

Fountain JA ファイルが正しくパースされると、以下が自動的に行われます：

1. **キャラクター抽出**: \x60@名前\x60 から全キャラクターが自動登録されます
2. **シーン構造**: \x60##\x60 や \x60.2\x60 から各シーンが作成されます
3. **香盤表生成**: 各シーンでセリフを持つキャラクターが、香盤表に自動でマッピングされます
4. **あらすじ除外**: あらすじ（シーン#0）は香盤表に表示されず、シーン本文は **#1 から** 表示されます
`,
    en: `
# 📝 Fountain JA Writing Manual

The system uses the **Fountain format (Japanese Extended)** for script management.
Upload a \x60.fountain\x60 text file and characters, scenes, and the scene chart will be parsed automatically.

---

## 📄 Basic Structure

##### 1. Metadata (Top of File)
Written at the very beginning. A **blank line is required** between metadata and the script body.

\x60\x60\x60
Title: My Play
Author: John Doe
Draft date: 2025-01-01

(blank line required here)
\x60\x60\x60

##### 2. Character Definitions (Optional)
Define characters under a \x60# 登場人物\x60 (or \x60# Characters\x60) section.

\x60\x60\x60
# Characters
Taro: The protagonist. A college student.
Hanako: Taro's childhood friend.
\x60\x60\x60

> 💡 Characters are also automatically extracted from \x60@CharacterName\x60 lines in the body.

##### 3. Act & Scene Headings
Use \x60#\x60 for Acts, \x60##\x60 for Scenes. Dot notation is also supported.

| Notation | Meaning | Example |
|---|---|---|
| \x60#\x60 | Act | \x60# Act One\x60 |
| \x60##\x60 | Scene | \x60## Scene 1 - Living Room\x60 |
| \x60.1\x60 | Act (dot) | \x60.1 Act One\x60 |
| \x60.2\x60 | Scene (dot) | \x60.2 Scene 1\x60 |

##### 4. Dialogue & Stage Directions

**One-line Dialogue**: \x60@CharacterName Dialogue text\x60

\x60\x60\x60
@Taro Long time no see, Hanako.
@Hanako It really is! It's been 3 years!
\x60\x60\x60

**Multi-line Dialogue**: \x60@CharacterName\x60 on its own line, followed by dialogue.

\x60\x60\x60
@Taro
Long time no see, Hanako.
It's been 3 years.
\x60\x60\x60

**Stage Directions (Action)**: Non-dialogue text. Leading full-width spaces are preserved for indentation.

---

## 📋 Synopsis

The synopsis is treated as **Scene #0** and is **excluded** from the scene chart and schedule selections.

\x60\x60\x60
# Synopsis
A small theater company faces its greatest challenge...
\x60\x60\x60

> 💡 Multilingual keywords: \x60あらすじ\x60, \x60Synopsis\x60, \x60줄거리\x60, \x60梗概\x60

---

## ⚠️ Common Mistakes

| ❌ Wrong | ⭕ Correct | Reason |
|---|---|---|
| No blank line after metadata | Add a blank line | Parser can't distinguish metadata |
| \x60@ Taro Line\x60 (space after @) | \x60@Taro Line\x60 | Name must follow @ immediately |
| \x60#Scene1\x60 (no space) | \x60# Scene1\x60 | Space required after \x60#\x60 |
| \x60# Scene1\x60 (single #) | \x60## Scene1\x60 | \x60#\x60 = Act, \x60##\x60 = Scene |

---

## 🔗 Scene Chart Integration

1. **Characters** are auto-extracted from \x60@Name\x60 lines
2. **Scenes** are created from \x60##\x60 or \x60.2\x60 headings
3. **Scene chart** maps characters to scenes based on their dialogue
4. **Synopsis excluded**: Scene #0 is hidden; scenes start from **#1**
`,
    ko: `
# 📝 Fountain JA 작성 매뉴얼

본 시스템은 극본 관리에 **Fountain 형식（일본어 확장판）**을 채택하고 있습니다.
\x60.fountain\x60 확장자의 텍스트 파일을 업로드하면, 캐릭터, 장면 구성, 향반표가 자동으로 분석됩니다.

---

## 📄 기본 구조

### 1. 메타데이터 (파일 맨머리)
파일의 가장 처음에 기술합니다. 메타데이터와 본문 사이에 **반드시 빈 줄**을 넣어 주세요.

\x60\x60\x60
Title: 제목명
Author: 작가명
Draft date: 2025-01-01

(여기에 빈 줄 필수)
\x60\x60\x60

### 2. 등장인물 정의 (선택사항)
\x60# 登場人物\x60 섹션에서 캐릭터와 설명을 정의할 수 있습니다.

> 💡 본문에서 \x60@캐릭터이름\x60 으로부터 자동 추출도 됩니다.

### 3. 막(Act) 및 장면(Scene) 제목

| 표기법 | 의미 | 예 |
|---|---|---|
| \x60#\x60 | 막 (Act) | \x60# 제1막\x60 |
| \x60##\x60 | 장면 (Scene) | \x60## 장면1 거실\x60 |
| \x60.1\x60 | 막 (점 기법) | \x60.1 제1막\x60 |
| \x60.2\x60 | 장면 (점 기법) | \x60.2 장면1\x60 |

### 4. 대사 및 지문

**한줄 대사**: \x60@캐릭터이름 대사\x60

\x60\x60\x60
@태로 오랜만이네, 하나코.
@하나코 정말! 벌써 3년이나 됐잖아!
\x60\x60\x60

**여러 줄 대사**: \x60@캐릭터이름\x60 다음 줄에 대사 기술

**지문**: 대사 이외의 서술. 전각 스페이스 들여쓰기 유지됨.

---

## 📋 줄거리 (Synopsis)

줄거리는 **장면 번호 #0**으로 저장되며 향반표에 **포함되지 않습니다**.

\x60\x60\x60
# 줄거리
지방의 작은 극장에서 배우들이 신작 공연 연습을 시작한다...
\x60\x60\x60

> 💡 다국어 키워드 대응: \x60あらすじ\x60, \x60Synopsis\x60, \x60줄거리\x60, \x60梗概\x60

---

## ⚠️ 자주 하는 실수

| ❌ 잘못된 패턴 | ⭕ 올바른 표기 | 이유 |
|---|---|---|
| 메타데이터 뒤에 빈 줄 없음 | 빈 줄 삽입 | 경계 인식 불가 |
| \x60@ 태로 대사\x60 | \x60@태로 대사\x60 | @바로 뒤에 이름 |
| \x60#장면1\x60 | \x60# 장면1\x60 | \x60#\x60 뒤 스페이스 필요 |
| \x60# 장면1\x60 (\x60#\x60 1개) | \x60## 장면1\x60 | \x60#\x60 = 막, \x60##\x60 = 장면 |
`,
    'zh-Hans': `
# 📝 Fountain JA 写作手册

本系统采用 **Fountain 格式（日语扩展版）** 进行剧本管理。
上传 \x60.fountain\x60 文件后，角色、场景结构和场景表将被自动解析。

---

## 📄 基本结构

### 1. 元数据（文件开头）
**必须在元数据后加一个空行**。

\x60\x60\x60
Title: 标题名
Author: 作者名
Draft date: 2025-01-01

（此处需要空行）
\x60\x60\x60

### 2. 登场人物定义（可选）
在 \x60# 登場人物\x60 段落中定义角色。

> 💡 系统也会从正文的 \x60@角色名\x60 自动提取角色。

### 3. 幕与场景标题

| 记法 | 含义 | 示例 |
|---|---|---|
| \x60#\x60 | 幕 (Act) | \x60# 第一幕\x60 |
| \x60##\x60 | 场景 (Scene) | \x60## 场景1 客厅\x60 |
| \x60.1\x60 | 幕（点记法） | \x60.1 第一幕\x60 |
| \x60.2\x60 | 场景（点记法） | \x60.2 场景1\x60 |

### 4. 台词与舞台指示

**单行台词**: \x60@角色名 台词\x60

\x60\x60\x60
@太郎 好久不见啊，花子。
@花子 是啊！已经3年了吧！
\x60\x60\x60

**多行台词**: \x60@角色名\x60 单独一行，下一行写台词。

**舞台指示**: 非台词叙述。全角空格缩进会被保留。

---

## 📋 梗概（Synopsis）

梗概保存为 **场景编号 #0**，**不会出现**在场景表中。

\x60\x60\x60
# 梗概
在地方的小剧场里，演员们开始排练...
\x60\x60\x60

> 💡 支持多语言关键词：\x60あらすじ\x60、\x60Synopsis\x60、\x60줄거리\x60、\x60梗概\x60

---

## ⚠️ 常见错误

| ❌ 错误 | ⭕ 正确 | 原因 |
|---|---|---|
| 元数据后没有空行 | 加一个空行 | 无法识别边界 |
| \x60@ 太郎 台词\x60 | \x60@太郎 台词\x60 | @后紧跟角色名 |
| \x60#场景1\x60 | \x60# 场景1\x60 | \x60#\x60 后需空格 |
| \x60# 场景1\x60 | \x60## 场景1\x60 | \x60#\x60 = 幕, \x60##\x60 = 场景 |
`,
    'zh-Hant': `
# 📝 Fountain JA 寫作手冊

本系統採用 **Fountain 格式（日語擴展版）** 進行劇本管理。
上傳 \x60.fountain\x60 檔案後，角色、場景結構和場景表將被自動解析。

---

## 📄 基本結構

### 1. 元數據（檔案開頭）
**必須在元數據後加一個空行**。

\x60\x60\x60
Title: 標題名
Author: 作者名
Draft date: 2025-01-01

（此處需要空行）
\x60\x60\x60

### 2. 登場人物定義（可選）
在 \x60# 登場人物\x60 段落中定義角色。

> 💡 系統也會從正文的 \x60@角色名\x60 自動提取角色。

### 3. 幕與場景標題

| 記法 | 含義 | 範例 |
|---|---|---|
| \x60#\x60 | 幕 (Act) | \x60# 第一幕\x60 |
| \x60##\x60 | 場景 (Scene) | \x60## 場景1 客廳\x60 |
| \x60.1\x60 | 幕（點記法） | \x60.1 第一幕\x60 |
| \x60.2\x60 | 場景（點記法） | \x60.2 場景1\x60 |

### 4. 台詞與舞台指示

**單行台詞**: \x60@角色名 台詞\x60

\x60\x60\x60
@太郎 好久不見啊，花子。
@花子 是啊！已經3年了吧！
\x60\x60\x60

**多行台詞**: \x60@角色名\x60 單獨一行，下一行寫台詞。

**舞台指示**: 非台詞敘述。全形空格縮排會被保留。

---

## 📋 梗概（Synopsis）

梗概保存為 **場景編號 #0**，**不會出現**在場景表中。

\x60\x60\x60
# 梗概
在地方的小劇場裡，演員們開始排練...
\x60\x60\x60

> 💡 支持多語言關鍵字：\x60あらすじ\x60、\x60Synopsis\x60、\x60줄거리\x60、\x60梗概\x60

---

## ⚠️ 常見錯誤

| ❌ 錯誤 | ⭕ 正確 | 原因 |
|---|---|---|
| 元數據後沒有空行 | 加一個空行 | 無法識別邊界 |
| \x60@ 太郎 台詞\x60 | \x60@太郎 台詞\x60 | @後緊跟角色名 |
| \x60#場景1\x60 | \x60# 場景1\x60 | \x60#\x60 後需空格 |
| \x60# 場景1\x60 | \x60## 場景1\x60 | \x60#\x60 = 幕, \x60##\x60 = 場景 |
`,
};

function getContent(lang: string): string {
    if (lang in fountainContent) return fountainContent[lang];
    if (lang.startsWith('zh-Hant') || lang === 'zh-TW') return fountainContent['zh-Hant'];
    if (lang.startsWith('zh')) return fountainContent['zh-Hans'];
    if (lang.startsWith('ko')) return fountainContent['ko'];
    return fountainContent['en'];
}

export function FountainManualPage() {
    const { i18n } = useTranslation();
    const content = getContent(i18n.language);

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
                <div className="max-w-5xl mx-auto px-6 py-4 flex items-center gap-4">
                    <Link
                        to="/manual"
                        className="flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors p-2 -ml-2 rounded-lg hover:bg-gray-100"
                    >
                        <ArrowLeft className="w-5 h-5" />
                        <span className="hidden sm:inline font-medium">
                            {i18n.language.startsWith('ja') ? 'マニュアルに戻る' :
                                i18n.language.startsWith('ko') ? '매뉴얼로 돌아가기' :
                                    i18n.language.startsWith('zh') ? '返回手冊' :
                                        'Back to Manual'}
                        </span>
                    </Link>
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-6 py-8">
                <section className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 sm:p-12 overflow-hidden">
                    <div className="prose prose-gray max-w-none
                        prose-headings:font-bold
                        prose-h1:text-4xl prose-h1:mb-10 prose-h1:pb-5 prose-h1:border-b
                        prose-h2:text-3xl prose-h2:mt-24 prose-h2:mb-10
                        prose-h3:text-2xl prose-h3:mt-20 prose-h3:mb-8
                        prose-h4:text-xl prose-h4:mt-12 prose-h4:mb-5
                        prose-h5:text-lg prose-h5:mt-10 prose-h5:mb-4
                        prose-p:my-6 prose-p:leading-relaxed prose-p:text-gray-700
                        prose-ul:my-6 prose-ul:pl-8 prose-ul:list-disc
                        prose-ol:my-6 prose-ol:pl-8 prose-ol:list-decimal
                        prose-li:my-2
                        prose-table:my-6
                        prose-th:bg-gray-100 prose-th:p-3 prose-th:border
                        prose-td:p-3 prose-td:border
                        prose-blockquote:bg-blue-50 prose-blockquote:border-l-4 prose-blockquote:border-blue-400 prose-blockquote:p-6 prose-blockquote:my-8 prose-blockquote:rounded-r-lg
                        prose-a:text-blue-600 prose-a:hover:text-blue-800 prose-a:font-semibold prose-a:no-underline prose-a:hover:underline
                        prose-code:bg-gray-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-rose-600 before:content-none after:content-none
                        prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-pre:p-6 prose-pre:rounded-xl prose-pre:my-8 prose-pre:overflow-x-auto
                        prose-hr:my-16 prose-hr:border-gray-200
                    ">
                        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                            {content}
                        </ReactMarkdown>
                    </div>
                </section>
            </main>
        </div>
    );
}
