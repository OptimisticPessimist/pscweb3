
import re

def preprocess_fountain(fountain_content: str) -> str:
    """Fountainテキストのパース前の前処理.

    python-fountainライブラリの制限（空行のない連続したト書きの消失など）を回避するために、
    適切な場所に空行を挿入します。
    """
    # Fix for fountain library bug with whitespace-only lines causing IndexError
    fountain_content = re.sub(r"^[ \t]+$", "", fountain_content, flags=re.MULTILINE)
    fountain_content = fountain_content.strip()

    lines = fountain_content.splitlines()
    processed_lines = []
    in_char_block = False
    is_following_char = False
    is_in_synopsis_section = False
    in_metadata = True

    for line in lines:
        stripped = line.strip()

        # Metadata section
        if in_metadata:
            if not stripped:
                in_metadata = False
                processed_lines.append(line)
                continue
            # If a heading starts before metadata ends, end metadata
            if stripped.startswith("#") or any(stripped.startswith(x) for x in ["INT.", "EXT.", "INT/EXT", "I/E"]):
                in_metadata = False
            else:
                processed_lines.append(line)
                continue

        # Body Processing
        if not stripped:
            is_following_char = False
            processed_lines.append(line)
            continue

        # Element Specific Processing
        
        # 1. Section/Scene Headings
        if stripped.startswith("#"):
            if processed_lines and processed_lines[-1].strip():
                processed_lines.append("")
            
            # Check if this is a synopsis section
            if any(k in stripped for k in ["あらすじ", "Synopsis", "synopsis", "줄거리", "梗概"]):
                is_in_synopsis_section = True
            else:
                is_in_synopsis_section = False
            
            processed_lines.append(line)
            processed_lines.append("") # Ensure blank line after heading
            is_following_char = False
            continue

        # 2. Synopsis Marker
        if stripped.startswith("="):
            if processed_lines and processed_lines[-1].strip():
                processed_lines.append("")
            
            processed_lines.append(line)
            is_following_char = False
            continue

        # 3. Transition Marker
        if stripped.startswith(">") and not (stripped.startswith("> <") or (processed_lines and processed_lines[-1].strip().startswith("@"))):
            if processed_lines and processed_lines[-1].strip():
                processed_lines.append("")
            processed_lines.append(line)
            is_following_char = False
            continue

        # 4. Character Marker (Forced @)
        if stripped.startswith("@"):
            if processed_lines and processed_lines[-1].strip():
                processed_lines.append("")
            
            if " " in stripped or "　" in stripped:
                # One-line dialogue (@Name Text)
                processed_lines.append(line)
                is_following_char = False
            else:
                # Standard character header
                processed_lines.append(line)
                is_following_char = True
            continue

        # 5. Dialogue/Parenthetical Body (following a character)
        if is_following_char:
            processed_lines.append(line)
            # We stay in "following char" mode until a blank line is hit (handled at top)
            continue

        # 6. Standard Character detection (uppercase)
        is_all_caps = stripped.isupper() and any(c.isalpha() for c in stripped)
        if is_all_caps:
            if processed_lines and processed_lines[-1].strip():
                processed_lines.append("")
            processed_lines.append(line)
            is_following_char = True
            continue

        # 7. Everything else (Action)
        # Prefix with '!' to ensure it's not misidentified as character/dialogue
        # but avoid adding empty lines before parentheticals if they were meant to be dialogue
        if processed_lines and processed_lines[-1].strip():
            if not stripped.startswith("("):
                processed_lines.append("")
        
        if stripped.startswith("(") or stripped.startswith("!"):
            processed_lines.append(line)
        else:
            processed_lines.append("!" + line)
        is_following_char = False

    return "\n".join(processed_lines)
