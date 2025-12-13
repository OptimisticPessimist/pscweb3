
from fountain import fountain
import sys

def verify():
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

@ピーター 一行で書くセリフ（許容される？）

!　　強制アクションインデント
"""

    f = fountain.Fountain(custom_fountain)
    
    results = {
        "dot_scene": False,
        "at_character": False,
        "section_scene": False
    }

    print("--- Elements ---")
    for e in f.elements:
        content = e.original_content
        print(f"[{e.element_type}] {repr(content)}")
        stripped = content.strip()
        
        if stripped == ".1 冒頭のシーン":
            if e.element_type == "Scene Heading":
                results["dot_scene"] = True
        
        if content == "@ピーター":
            if e.element_type == "Character":
                results["at_character"] = True
                
        if "シーン2" in content:
            # Note: fountain might strip ## or keep it depending on implementation
            if e.element_type == "Section Heading":
                 results["section_scene"] = True
            elif e.element_type == "Scene Heading":
                 # Some parsers treat ## as Scene Heading directly
                 results["section_scene"] = True

        if "一行で書くセリフ" in content:
            print(f"One-line dialogue parsed as: {e.element_type}")

    print("--- Verification Results ---")
    print(f"Dot Scene (.1 ...): {'OK' if results['dot_scene'] else 'FAIL'}")
    print(f"At Character (@...): {'OK' if results['at_character'] else 'FAIL'}")
    print(f"Section/Scene (## ...): {'OK' if results['section_scene'] else 'FAIL'}")

    if all(results.values()):
        print("ALL PASS")
        sys.exit(0)
    else:
        print("SOME FAIL")
        sys.exit(1)

if __name__ == "__main__":
    verify()
