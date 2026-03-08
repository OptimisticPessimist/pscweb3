# 実装計画: スクリプトのシーン番号バグ修正

## 目的
`# 登場人物` というプレーンテキストが、`SCENE_KEYWORDS` 内の `場` という文字を含んでいるためにシーンとして誤認され、実際の `## 第1場` がシーン2となってしまうバグを修正します。

## 提案する変更

### バックエンドのパーサー修正
#### [MODIFY] `fountain_parser.py`(file:///f:/src/PythonProject/pscweb3-1/backend/src/services/fountain_parser.py)
`has_scene_keyword` および `is_section_scene` を判定する際、`登場人物` や `Character` が含まれる場合はシーンキーワードがないものとして扱い、シーン(Section Scene)としても判定されないようにします。

```python
        SCENE_KEYWORDS = ["Scene", "scene", "シーン", "씬", "场", "場", "あらすじ", "Synopsis", "synopsis", "SYNOPSIS", "줄거리", "梗概"]
        has_scene_keyword = any(k in content_stripped for k in SCENE_KEYWORDS)
        
        # "登場人物" または "Character" が含まれている場合はシーン見出しキーワードとして扱わない
        if "登場人物" in content_stripped or "Character" in content_stripped:
            has_scene_keyword = False
            
        is_section_act = (element.element_type == "Section Heading" and 
                          content_stripped.startswith("#") and 
                          not content_stripped.startswith("##") and
                          not has_scene_keyword) # キーワードがあればActではない
         ...
        
        is_section_scene = (element.element_type == "Section Heading" and 
                            (content_stripped.startswith("##") or
                             (content_stripped.startswith("#") and has_scene_keyword)))

        # 念のための追加ガード: "登場人物" や "Character" は絶対にシーンにはならない
        if "登場人物" in content_stripped or "Character" in content_stripped:
            is_section_scene = False
```

### テスト
`backend/tests/unit/test_fountain_parser.py` 等で、`# 登場人物` と `## 第1場` が同時に存在するスクリプトをパースし、シーン1が `第1場` から始まることを確認するテストを追加します。

## 検証計画
- `pytest` を使用した単体テストの実行。
- 該当のスクリプト文字列を用いた結合テスト。
