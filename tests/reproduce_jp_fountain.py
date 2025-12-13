
from fountain import fountain

custom_fountain = """
Title: JP Test
Author: Tester

.1 冒頭のシーン
（強制シーン見出しのテスト）

@ピーター
ピザが好きなんです。

@花子 (ハナコ)
私も好きです。

# 第一幕

## シーン2（セクション見出し）

ただのアクション行（ト書き）。

　　（空白インデントによるト書き？）

@太郎
これはセリフです。
"""

print("--- Parsing Start ---")
f = fountain.Fountain(custom_fountain)

for element in f.elements:
    print(f"Type: {element.element_type}, Content: '{element.original_content.strip()}'")

print("--- Parsing End ---")
