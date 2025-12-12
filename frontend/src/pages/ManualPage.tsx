import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useTranslation } from 'react-i18next';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

// Japanese manual content
const manualJa = `# PSCWEB3 利用者マニュアル
## 演劇・映像制作のためのプロジェクト管理システム

このシステムは、演劇の公演や映像制作プロジェクトの運営をスムーズにするためのツールです。
脚本管理、スケジュール調整、出欠確認、キャスト・スタッフ管理など、制作に必要な機能が揃っています。

---

## 目次
1. [役割（ロール）について](#1-役割ロールについて)
2. [はじめに（全員共通）](#2-はじめに全員共通)
3. [閲覧者向けマニュアル](#3-閲覧者向けマニュアル)
4. [編集者向けマニュアル](#4-編集者向けマニュアル)
5. [管理者向けマニュアル](#5-管理者向けマニュアル)
6. [機能一覧表](#6-機能一覧表)

---

## 1. 役割（ロール）について

システムには3つの役割があります。自分の役割を確認しましょう。

### 👑 管理者 (Owner)
**演劇:** 部長、演出家、制作チーフ  
**映像:** 監督、プロデューサー、制作統括

- プロジェクトの作成・削除
- メンバーの招待・権限管理
- Discord通知の設定
- すべての機能を利用可能

### ✏️ 編集者 (Editor)
**演劇:** 演出助手、舞台監督、各セクションチーフ  
**映像:** 助監督、撮影監督、各部門リーダー

- 脚本（台本）のアップロード・編集
- スケジュールの作成・編集
- 出欠未回答者への回答催促
- 香盤表（出番表）の管理
- キャスティングの設定

### 👀 閲覧者 (Viewer)
**演劇:** キャスト（役者）、スタッフ、顧問  
**映像:** 出演者、スタッフ、クライアント

- スケジュールの確認
- 脚本（台本）の閲覧
- 出欠の回答
- 自分のマイスケジュール確認

---

## 2. はじめに（全員共通）

### 🔐 ログイン方法
1. システムのURLにアクセスします。
2. **「Discordでログイン」** ボタンをクリックします。
3. Discordアカウントで認証すると、自動的にログインできます。

> 💡 Discordアカウントを持っていない場合は、先に [Discord](https://discord.com/) で無料アカウントを作成してください。

### 🏠 ダッシュボード
ログイン後、ダッシュボードが表示されます。
- 参加しているプロジェクトの一覧
- 直近のスケジュール
- 各種機能へのリンク

### 🌐 言語切り替え
画面右上のボタンで、表示言語を切り替えられます。
- 日本語 / English / 한국어 / 简体中文 / 繁體中文

---

## 3. 閲覧者向けマニュアル

キャスト・スタッフの皆さんが主に使う機能です。

### 📅 スケジュールの確認
稽古や撮影の日程を確認できます。

1. メニューから **「スケジュール」** を選択します。
2. カレンダー形式で日程が表示されます。
3. 日付をクリックすると詳細（場所、シーン、参加者など）が見られます。

### 📆 マイスケジュール
自分が関わる稽古・撮影だけを確認できます。

1. メニューから **「マイスケジュール」** を選択します。
2. 自分がキャストされているシーンの稽古が一覧表示されます。

### ✅ 出欠の回答
稽古や撮影への出欠を回答します。

**Discord経由の場合:**
1. Discordに通知が届きます。
2. 「出席」「欠席」などのボタンを押すだけで完了です。

**システム内での回答:**
1. メニューから **「出欠確認」** を選択します。
2. 対象のイベントを選び、出欠を回答します。

### 📖 脚本（台本）を読む
いつでもスマホやPCから最新の脚本が読めます。

1. メニューから **「脚本」** を選択します。
2. 脚本の一覧から読みたい脚本を選びます。
3. 縦書き表示で読みやすく表示されます。

### 📊 香盤表の確認
どのシーンに誰が出るかを確認できます。

1. 脚本詳細ページで **「香盤表」** タブを選択します。
2. シーンごとの登場キャラクターが一覧表示されます。

---

## 4. 編集者向けマニュアル

演出スタッフ、制作スタッフなど、プロジェクトを運営する人向けの機能です。

### 📝 脚本のアップロード
Fountain形式の脚本ファイルをアップロードできます。

1. メニューから **「脚本」** → **「アップロード」** を選択します。
2. ファイルを選択（またはドラッグ＆ドロップ）します。
3. タイトルを確認して **「アップロード」** をクリックします。

> 💡 **Fountain形式とは？**  
> シンプルなテキスト形式で脚本を書けるフォーマットです。  
> 詳しくは [fountain.io](https://fountain.io/) または [fountain-JA](https://satamame.github.io/playscript/master/fountain.html)を参照してください。

### 🗓 スケジュールの作成
稽古や撮影の日程を作成します。

1. メニューから **「スケジュール」** を選択します。
2. **「新規作成」** ボタンをクリックします。
3. 以下を入力して保存します：
   - 日時
   - 場所
   - 対象シーン（複数選択可）
   - メモ

### 📊 香盤表の編集
各シーンに登場するキャラクターを設定します。

1. 脚本詳細ページで **「香盤表」** タブを選択します。
2. 各シーンの行で、登場するキャラクターにチェックを入れます。
3. 自動保存されます。

### 🎭 キャスティングの設定
キャラクターと役者を紐付けます。

1. メニューから **「キャスティング」** を選択します。
2. キャラクター一覧から設定したいキャラクターを選びます。
3. 担当する役者を選択します。
4. ダブルキャスト（複数人が同じ役）にも対応しています。

### 👥 スタッフ管理
スタッフの役割を設定します。

1. メニューから **「スタッフ」** を選択します。
2. メンバー一覧で各スタッフの担当役割を設定します。

### 📢 出欠確認の催促
未回答のメンバーにリマインダーを送信できます。

1. メニューから **「出欠確認」** を選択します。
2. 対象のイベントを選びます。
3. **「未回答者に催促」** ボタンをクリックします。
4. Discordで未回答のメンバーにメンション付きのリマインダーが送信されます。

---

## 5. 管理者向けマニュアル

プロジェクト全体を管理する人向けの機能です。

### 🚀 プロジェクトの作成
新しい公演や撮影プロジェクトを作成します。

1. ダッシュボードで **「新規プロジェクト作成」** をクリックします。
2. プロジェクト名（公演タイトルなど）を入力します。
3. 説明（任意）を入力して **「作成」** をクリックします。

### 📩 メンバーの招待
プロジェクトにメンバーを招待します。

1. プロジェクトの **「設定」** を開きます。
2. **「招待リンクを作成」** ボタンをクリックします。
3. 表示されたURLをコピーして、LINEやDiscordで共有します。
4. メンバーがリンクからログインすると、自動的にプロジェクトに参加します。

### ⚙️ メンバー権限の変更
メンバーの役割（管理者/編集者/閲覧者）を変更します。

1. プロジェクトの **「設定」** → **「メンバー管理」** を開きます。
2. 変更したいメンバーの **「役割」** を選択します。
3. 変更は即座に反映されます。

### 🔔 Discord通知の設定
プロジェクトの通知をDiscordに送るための設定です。

#### Webhook URL（一般通知用）
プロジェクト更新などの通知を受け取ります。

1. Discordで通知を受け取りたいチャンネルの **「チャンネル設定」** を開きます。
2. **「連携サービス」** → **「ウェブフック」** を選択します。
3. **「新しいウェブフック」** を作成し、URLをコピーします。
4. システムの設定画面で **「Discord Webhook URL」** に貼り付けます。

#### Webhook URL（脚本通知用）
脚本アップロード時の通知は別チャンネルに送れます（任意）。

#### チャンネルID（出欠確認用）
出欠確認のボタン付きメッセージを送るための設定です。

**チャンネルIDの取得方法:**
1. Discordの **「ユーザー設定」** → **「詳細設定」** を開きます。
2. **「開発者モード」** をオンにします。
3. 対象チャンネルを **右クリック** → **「チャンネルIDをコピー」** を選択します。
4. システムの設定で **「Discord Channel ID」** に貼り付けます。

---

## 6. 機能一覧表

| 機能 | 👑 管理者 | ✏️ 編集者 | 👀 閲覧者 |
| :--- | :---: | :---: | :---: |
| **プロジェクト作成・削除** | ☑ | - | - |
| **メンバー招待・権限変更** | ☑ | - | - |
| **Discord通知設定** | ☑ | - | - |
| **脚本アップロード・編集** | ☑ | ☑ | - |
| **スケジュール作成・編集** | ☑ | ☑ | - |
| **香盤表の編集** | ☑ | ☑ | - |
| **キャスティング設定** | ☑ | ☑ | - |
| **スタッフ役割設定** | ☑ | ☑ | - |
| **出欠の催促送信** | ☑ | ☑ | - |
| **出欠の回答** | ☑ | ☑ | ☑ |
| **スケジュール閲覧** | ☑ | ☑ | ☑ |
| **マイスケジュール確認** | ☑ | ☑ | ☑ |
| **脚本閲覧** | ☑ | ☑ | ☑ |
| **香盤表閲覧** | ☑ | ☑ | ☑ |

---

## お問い合わせ

困ったことやバグを見つけたら、プロジェクト管理者または開発担当までご連絡ください。
`;

// English manual content
const manualEn = `# PSCWEB3 User Manual
## Project Management System for Theater & Video Production

This system is designed to streamline the management of theater productions and video projects.
It includes features for script management, scheduling, attendance tracking, and cast/staff management.

---

## Table of Contents
1. [About Roles](#1-about-roles)
2. [Getting Started (For Everyone)](#2-getting-started-for-everyone)
3. [Viewer Manual](#3-viewer-manual)
4. [Editor Manual](#4-editor-manual)
5. [Owner Manual](#5-owner-manual)
6. [Feature Permissions Table](#6-feature-permissions-table)

---

## 1. About Roles

The system has three roles. Check which role you have.

### 👑 Owner
**Theater:** Club president, director, production chief  
**Video:** Director, producer, production manager

- Create and delete projects
- Invite members and manage permissions
- Configure Discord notifications
- Access to all features

### ✏️ Editor
**Theater:** Assistant director, stage manager, section chiefs  
**Video:** Assistant director, cinematographer, department leads

- Upload and edit scripts
- Create and edit schedules
- Send attendance reminders to non-respondents
- Manage scene charts
- Configure casting

### 👀 Viewer
**Theater:** Cast (actors), staff, advisors  
**Video:** Performers, staff, clients

- View schedules
- Read scripts
- Respond to attendance
- Check personal schedule

---

## 2. Getting Started (For Everyone)

### 🔐 How to Log In
1. Access the system URL.
2. Click the **"Login with Discord"** button.
3. Authenticate with your Discord account to log in automatically.

> 💡 If you don't have a Discord account, create a free account at [Discord](https://discord.com/) first.

### 🏠 Dashboard
After logging in, you'll see the Dashboard:
- List of projects you're participating in
- Upcoming schedules
- Links to various features

### 🌐 Language Switching
Use the button in the upper right to switch display language:
- 日本語 / English / 한국어 / 简体中文 / 繁體中文

---

## 3. Viewer Manual

Features primarily used by cast and staff members.

### 📅 Checking the Schedule
View rehearsal and shooting dates.

1. Select **"Schedule"** from the menu.
2. Dates are displayed in calendar format.
3. Click a date to view details (location, scenes, participants, etc.).

### 📆 My Schedule
View only the rehearsals/shoots you're involved in.

1. Select **"My Schedule"** from the menu.
2. Rehearsals for scenes you're cast in are displayed.

### ✅ Responding to Attendance
Respond to attendance for rehearsals or shoots.

**Via Discord:**
1. You'll receive a notification on Discord.
2. Simply press buttons like "Attending" or "Absent" to complete.

**Within the System:**
1. Select **"Attendance"** from the menu.
2. Choose the event and respond to attendance.

### 📖 Reading Scripts
Access the latest scripts anytime from your phone or PC.

1. Select **"Scripts"** from the menu.
2. Choose the script you want to read from the list.
3. Scripts are displayed in an easy-to-read vertical format.

### 📊 Viewing Scene Charts
See which characters appear in each scene.

1. On the script detail page, select the **"Scene Chart"** tab.
2. Characters appearing in each scene are listed.

---

## 4. Editor Manual

Features for those managing the project, such as directing and production staff.

### 📝 Uploading Scripts
Upload script files in Fountain format.

1. Select **"Scripts"** → **"Upload"** from the menu.
2. Select a file (or drag and drop).
3. Confirm the title and click **"Upload"**.

> 💡 **What is Fountain format?**  
> A simple text format for writing scripts.  
> Learn more at [fountain.io](https://fountain.io/).

### 🗓 Creating Schedules
Create rehearsal or shooting schedules.

1. Select **"Schedule"** from the menu.
2. Click the **"Create New"** button.
3. Enter and save the following:
   - Date and time
   - Location
   - Target scenes (multiple selection available)
   - Notes

### 📊 Editing Scene Charts
Set which characters appear in each scene.

1. On the script detail page, select the **"Scene Chart"** tab.
2. Check the characters that appear in each scene's row.
3. Changes are auto-saved.

### 🎭 Configuring Casting
Link characters to actors.

1. Select **"Casting"** from the menu.
2. Choose the character you want to configure from the list.
3. Select the assigned actor.
4. Double casting (multiple actors for the same role) is also supported.

### 👥 Staff Management
Set staff roles.

1. Select **"Staff"** from the menu.
2. Set each staff member's assigned role in the member list.

### 📢 Sending Attendance Reminders
Send reminders to members who haven't responded.

1. Select **"Attendance"** from the menu.
2. Choose the target event.
3. Click the **"Send Reminder"** button.
4. A reminder with mentions is sent to non-respondents via Discord.

---

## 5. Owner Manual

Features for those managing the entire project.

### 🚀 Creating a Project
Create a new production or shooting project.

1. Click **"Create New Project"** on the Dashboard.
2. Enter the project name (production title, etc.).
3. Enter a description (optional) and click **"Create"**.

### 📩 Inviting Members
Invite members to the project.

1. Open the project **"Settings"**.
2. Click the **"Create Invite Link"** button.
3. Copy the displayed URL and share via LINE or Discord.
4. When members log in via the link, they automatically join the project.

### ⚙️ Changing Member Permissions
Change a member's role (Owner/Editor/Viewer).

1. Open **"Settings"** → **"Member Management"** for the project.
2. Select the **"Role"** for the member you want to change.
3. Changes are applied immediately.

### 🔔 Discord Notification Settings
Settings for sending project notifications to Discord.

#### Webhook URL (General Notifications)
Receive notifications for project updates, etc.

1. Open **"Channel Settings"** for the Discord channel where you want to receive notifications.
2. Select **"Integrations"** → **"Webhooks"**.
3. Create a **"New Webhook"** and copy the URL.
4. Paste it in the **"Discord Webhook URL"** field in the system settings.

#### Webhook URL (Script Notifications)
Script upload notifications can be sent to a separate channel (optional).

#### Channel ID (Attendance)
Settings for sending attendance confirmation messages with buttons.

**How to get the Channel ID:**
1. Open Discord **"User Settings"** → **"Advanced"**.
2. Turn on **"Developer Mode"**.
3. **Right-click** the target channel → select **"Copy Channel ID"**.
4. Paste it in the **"Discord Channel ID"** field in the system settings.

---

## 6. Feature Permissions Table

| Feature | 👑 Owner | ✏️ Editor | 👀 Viewer |
| :--- | :---: | :---: | :---: |
| **Create/Delete Projects** | ☑ | - | - |
| **Invite Members/Change Permissions** | ☑ | - | - |
| **Discord Notification Settings** | ☑ | - | - |
| **Upload/Edit Scripts** | ☑ | ☑ | - |
| **Create/Edit Schedules** | ☑ | ☑ | - |
| **Edit Scene Charts** | ☑ | ☑ | - |
| **Configure Casting** | ☑ | ☑ | - |
| **Set Staff Roles** | ☑ | ☑ | - |
| **Send Attendance Reminders** | ☑ | ☑ | - |
| **Respond to Attendance** | ☑ | ☑ | ☑ |
| **View Schedules** | ☑ | ☑ | ☑ |
| **View My Schedule** | ☑ | ☑ | ☑ |
| **View Scripts** | ☑ | ☑ | ☑ |
| **View Scene Charts** | ☑ | ☑ | ☑ |

---

## Contact

If you encounter issues or find bugs, please contact the project administrator or development team.
`;

// Map language codes to manual content
const manualContent: Record<string, string> = {
    ja: manualJa,
    en: manualEn,
    ko: manualEn, // Fallback to English
    'zh-Hans': manualEn, // Fallback to English
    'zh-Hant': manualEn, // Fallback to English
};

export function ManualPage() {
    const { t, i18n } = useTranslation();
    const currentLanguage = i18n.language;

    // Get the appropriate manual content, fallback to English
    const content = manualContent[currentLanguage] || manualContent['en'] || manualJa;

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-6 py-4">
                <div className="max-w-4xl mx-auto flex items-center gap-4">
                    <Link
                        to="/dashboard"
                        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                        <span>{t('common.back')}</span>
                    </Link>
                </div>
            </header>

            {/* Content */}
            <main className="max-w-4xl mx-auto px-6 py-8">
                <article className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
                    <div className="prose prose-gray max-w-none
                        prose-headings:font-bold
                        prose-h1:text-3xl prose-h1:mb-4 prose-h1:pb-2 prose-h1:border-b
                        prose-h2:text-2xl prose-h2:mt-8 prose-h2:mb-4
                        prose-h3:text-xl prose-h3:mt-6 prose-h3:mb-3
                        prose-p:my-3 prose-p:leading-relaxed
                        prose-ul:my-3 prose-ul:pl-6
                        prose-ol:my-3 prose-ol:pl-6
                        prose-li:my-1
                        prose-table:my-4
                        prose-th:bg-gray-100 prose-th:p-2 prose-th:border
                        prose-td:p-2 prose-td:border
                        prose-blockquote:bg-blue-50 prose-blockquote:border-l-4 prose-blockquote:border-blue-400 prose-blockquote:p-4 prose-blockquote:my-4
                        prose-a:text-blue-600 prose-a:hover:underline
                        prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded
                        prose-hr:my-8
                    ">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {content}
                        </ReactMarkdown>
                    </div>
                </article>
            </main>
        </div>
    );
}
