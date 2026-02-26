# 日程調整カレンダービューでの役職・役名表示

## 概要
日程調整のカレンダービューにおいて、参加可能メンバー（および参加可能かもしれないメンバー）の名前だけでなく、それぞれの役職や役名も表示するようにする。

## User Review Required
特になし。既存のカレンダービューの情報を拡張するのみであるため。

## Proposed Changes

### バックエンド

#### [MODIFY] `schemas/schedule_poll.py`
ユーザー情報と役職の両方を保持するスキーマモデルを新設し、分析結果として返すようにする。
```python
class CalendarMemberInfo(BaseModel):
    user_id: UUID
    name: str
    role: str | None = None

class PollCandidateAnalysis(BaseModel):
    ...
    # 既存の available_user_names / maybe_user_names は後方互換性やコード変更最小化の観点で残しても良いが、より構造化されたデータにするために以下を追加する
    available_members: list[CalendarMemberInfo] = []
    maybe_members: list[CalendarMemberInfo] = []
```

#### [MODIFY] `schedule_poll_service.py`
`get_calendar_analysis` 関数におけるデータ作成部分を変更する。
メンバーの `default_staff_role` および `CharacterCasting` 情報から、ユーザーごとの役職・役名を収集する処理を追加。
取得した役職情報を含めた `CalendarMemberInfo` オブジェクトを生成して返すようにする。

### フロントエンド

#### [MODIFY] `schedulePoll.ts`
バックエンドから送られてくる新しいスキーマ構造に合わせてインターフェースを更新する。
```typescript
export interface CalendarMemberInfo {
    user_id: string;
    name: string;
    role: string | null;
}

export interface PollCandidateAnalysis {
    ...
    available_members: CalendarMemberInfo[];
    maybe_members: CalendarMemberInfo[];
}
```

#### [MODIFY] `SchedulePollCalendar.tsx`
メンバーリストの表示部分（現在は `available_user_names` を `.map` で回している箇所）を、`available_members` を利用するように変更する。
メンバー名の下または隣に小さく役職・役名一覧を表示する。役職がない場合は表示しないなどの条件分岐を入れる。
全体のデザインが崩れないように Tailwind CSS のクラスを調整し、プレミアム感のあるデザインを維持する。

## Verification Plan

### Automated Tests
- フロントエンドおよびバックエンドのTypeScript/Pythonの型チェックとビルドの通過

### Manual Verification
- 実際に開発サーバーを立ち上げ、日程調整画面（カレンダービュー）で候補日程をクリックする。
- パネル内に表示される「参加可能メンバー」の部分に名前と役職（"演出" や "ロミオ" など）が期待通りに表示されるか確認する。
