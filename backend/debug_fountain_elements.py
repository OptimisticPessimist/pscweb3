
from fountain import fountain
import sys

# Set encoding to utf-8 for Windows console
sys.stdout.reconfigure(encoding='utf-8')

example_content = """# シーン1
舞台中央やや奥めにデスク。左右から座れるようになっている。

捨村と京野、大きな保存容器を二人で運びながら登場。
容器は人が一人入れそうな大きさで、カウントダウン・タイマーが付いているが、今は動いていない。

@京野
置く場所ねえぞこれ。

@捨村
もういいよもう、どこでも。どっか、空いてるとこ。
"""

def debug_parse(fountain_content):
    fountain_content = fountain_content.strip()

    # Pre-process logic (Copied from fountain_parser.py)
    lines = fountain_content.splitlines()
    processed_lines = []
    in_char_block = False
    is_following_char = False
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith("#"):
            if "登場人物" in stripped or "Characters" in stripped:
                in_char_block = True
            else:
                in_char_block = False
            processed_lines.append(line)
            is_following_char = False
        elif in_char_block:
            if stripped:
                processed_lines.append(line)
                processed_lines.append("")
                is_following_char = False
            else:
                processed_lines.append(line)
                is_following_char = False
        else:
            if not stripped:
                is_following_char = False
                processed_lines.append(line)
                continue

            if stripped.startswith("@"):
                if " " in stripped or "　" in stripped:
                    is_following_char = False
                else:
                    is_following_char = True
                
                processed_lines.append(line)
                continue

            is_indented = line.startswith(" ") or line.startswith("　")
            
            if is_indented:
                if is_following_char:
                    is_following_char = False
                    processed_lines.append(line)
                else:
                    processed_lines.append("!" + line)
                    is_following_char = False
            else:
                 # Normal line (Action or other)
                 if is_following_char:
                     is_following_char = False
                     processed_lines.append(line)
                 else:
                     is_following_char = False
                     processed_lines.append(line)
            
    processed_content = "\n".join(processed_lines)
    
    f = fountain.Fountain(processed_content)
    
    # Simulate Character Map Extraction
    character_map = {}
    for element in f.elements:
        if element.element_type == "Character":
            char_name = element.original_content.strip()
            if char_name.startswith("@"):
                char_name = char_name[1:]
            
            if char_name and char_name not in character_map:
                character_map[char_name] = True
                print(f"DEBUG: Found Character '{char_name}'")

    # Simulate Line Extraction
    current_character = None
    
    for i, element in enumerate(f.elements):
        content_stripped = element.original_content.strip()
        
        if element.element_type == "Character":
            char_name = content_stripped
            if char_name.startswith("@"):
                char_name = char_name[1:]
            
            if char_name in character_map:
                current_character = char_name
                print(f"[{i}] Character Set to: {current_character}")
            else:
                current_character = None
                print(f"[{i}] Character NOT FOUND in map: {char_name}")

        elif element.element_type == "Dialogue":
            if current_character:
                print(f"[{i}] Dialogue Added for {current_character}: {element.original_content.strip()}")
            else:
                print(f"[{i}] Dialogue SKIPPED (No current character): {element.original_content.strip()}")

        elif element.element_type == "Action":
             print(f"[{i}] Action: {element.original_content.strip()}")

if __name__ == "__main__":
    debug_parse(example_content)
