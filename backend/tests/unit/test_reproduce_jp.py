
import pytest
from fountain import fountain

def test_reproduce_jp_fountain_parsing():
    custom_fountain = """Title: JP Test
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

    print("\n--- Parsing Start ---")
    f = fountain.Fountain(custom_fountain)

    for element in f.elements:
        print(f"Type: {element.element_type}, Content: '{element.original_content.strip()}'")

    print("--- Parsing End ---")

    # Assertions based on expectations (what we WANT)
    # This might fail if current behavior is different
    
    # 1. Forced Scene Heading
    # ".1 冒頭のシーン" -> Should be Scene Heading
    # Current library might parse it as Action or Scene Heading
    
    # 2. Forced Character
    # "@ピーター" -> Should be Character
    
    # 3. Section Heading
    # "## シーン2..." -> Should be Section Heading (which our parser converts to Scene)
