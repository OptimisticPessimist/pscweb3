"""Fountain脚本パーサーサービス."""

from fountain import fountain
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Character, Line, Scene, Script


async def parse_fountain_and_create_models(
    script: Script, fountain_content: str, db: AsyncSession
) -> None:
    """Fountain脚本をパースしてDBモデルを作成.

    Args:
        script: Scriptモデルインスタンス
        fountain_content: Fountain形式の脚本内容
        db: データベースセッション
    """
    # Fountainパース
    import logging
    logger = logging.getLogger("uvicorn")
    fountain_content = fountain_content.strip() # Fix for fountain library bug with empty lines in header

    # Pre-process: Inject blank lines in Character blocks to ensure proper parsing
    lines = fountain_content.splitlines()
    processed_lines = []
    in_char_block = False
    is_following_char = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check for block start/end
        if stripped.startswith("#"):
            # Check if this header starts a character block
            if "登場人物" in stripped or "Characters" in stripped:
                in_char_block = True
            else:
                in_char_block = False
            processed_lines.append(line)
            is_following_char = False
        elif in_char_block:
            # Inside character block, ensure strings are separated by blank lines if not empty
            if stripped:
                processed_lines.append(line)
                processed_lines.append("") # Force blank line
                is_following_char = False
            else:
                processed_lines.append(line)
                is_following_char = False
        else:
            # General body processing
            
            # Reset state on blank line
            if not stripped:
                is_following_char = False
                processed_lines.append(line)
                continue

            # Check for Character line (@Name)
            if stripped.startswith("@"):
                # Check if it is one-line dialogue (@Name Dialogue)
                # If it has space/full-width space, it is one-line dialogue -> Dialogue consumes Character immediately
                if " " in stripped or "　" in stripped:
                    is_following_char = False
                else:
                    is_following_char = True
                
                processed_lines.append(line)
                continue

            # Check for indented line
            is_indented = line.startswith(" ") or line.startswith("　")
            
            if is_indented:
                if is_following_char:
                    # Indented Dialogue following @Name
                    # Do nothing to preserve as Dialogue (fountain will strip indent but that's standard behavior)
                    is_following_char = False
                    processed_lines.append(line)
                else:
                    # Indented Action (Togaki) - Force preservation
                    processed_lines.append("!" + line)
                    is_following_char = False
            else:
                 # Normal line (Action or other)
                 is_following_char = False
                 processed_lines.append(line)
            
    fountain_content = "\n".join(processed_lines)
    
    f = fountain.Fountain(fountain_content)
    logger.info(f"Parsed {len(f.elements)} elements from Fountain content.")

    # 登場人物を抽出してマップを作成
    
    # 標準のCharacter要素とカスタムセクション「登場人物」の両方から抽出
    character_map: dict[str, Character] = {}
    
    # 1. まず標準的なCharacter要素から基本リストを作成
    for element in f.elements:
        if element.element_type == "Character":
            char_name = element.original_content.strip()
            if char_name.startswith("@"):
                char_name = char_name[1:]
            
            if char_name and char_name not in character_map:
                character = Character(script_id=script.id, name=char_name)
                db.add(character)
                character_map[char_name] = character

    # 2. カスタムセクション「# 登場人物」または「# Character」を探して詳細情報を付与
    in_character_section = False
    
    for element in f.elements:
        content = element.original_content.strip()
        
        # セクション見出しの検出
        if element.element_type == "Section Heading":
            # "登場人物" または "Character" を含む見出し（レベル問わず）
            if "登場人物" in content or "Character" in content:
                in_character_section = True
                logger.info("Found Character Definition Section")
            else:
                in_character_section = False
        
        # セクション内の要素を解析
        elif in_character_section and element.element_type in ["Action", "Character", "Dialogue"]:
            # Action要素内の各行を処理（Fountainパーサーが複数行を1つのActionとしてまとめる場合があるため）
            lines = content.splitlines()
            for line in lines:
                line = line.strip()
                # "Name: Description" 形式を探す (コロン区切り)
                if ":" in line:
                    parts = line.split(":", 1)
                    name_part = parts[0].strip()
                    desc_part = parts[1].strip()
                    
                    # 既存キャラクターがあれば更新、なければ新規作成
                    if name_part:
                        if name_part in character_map:
                            character = character_map[name_part]
                            character.description = desc_part
                        else:
                            character = Character(script_id=script.id, name=name_part, description=desc_part)
                            db.add(character)
                            character_map[name_part] = character
                        logger.info(f"Updated description for {name_part}")

    await db.flush()  # Characterのidを取得

    # シーンとセリフを抽出
    current_scene: Scene | None = None
    scene_number = 0
    current_act_number: int | None = None
    line_order = 0
    current_character: Character | None = None

    for element in f.elements:
        content_stripped = element.original_content.strip()
        
        # Act検出
        # 1. Section Heading level 1 (starts with #, not ##)
        # 2. Forced Scene Heading level 1 (starts with .1)
        is_section_act = (element.element_type == "Section Heading" and 
                          content_stripped.startswith("#") and 
                          not content_stripped.startswith("##"))
        
        is_dot_act = (element.element_type == "Scene Heading" and 
                      content_stripped.startswith(".1"))
                      
        if is_section_act or is_dot_act:
             # Level 1 Heading detected (Act)
             heading_content = content_stripped
             
             # "登場人物" や "Character" は幕としてカウントしない
             if "登場人物" in heading_content or "Character" in heading_content:
                 pass
             else:
                 # 幕番号作成
                 if current_act_number is None:
                     current_act_number = 1
                 else:
                     current_act_number += 1
                 logger.info(f"Found Act #{current_act_number}: {heading_content}")
                 
             # .1 の場合はSceneとして処理しないようにcontinueする
             # ただし、Section Headingの場合はcontinueしなくても下のis_scene_heading等で弾かれる(Section Headingだから)
             # is_dot_actの場合はScene Headingなので、ここでcontinueしないと下でSceneとして作られてしまう
             if is_dot_act:
                 continue

        # Scene検出
        # 1. Standard Scene Heading (INT./EXT. etc or Forced . but NOT .1)
        # 2. Section Heading level 2 (starts with ##)
        # 3. Forced Scene Heading level 2 (starts with .2)
        
        is_scene_heading_type = element.element_type == "Scene Heading"
        
        # .1 は上でActとして処理済み。それ以外のScene Headingはシーン
        # つまり、通常のINT.や、.2 (Level 2), . (Forced) はシーン
        is_valid_scene_heading = is_scene_heading_type and not content_stripped.startswith(".1")
        
        is_section_scene = (element.element_type == "Section Heading" and 
                            content_stripped.startswith("##"))

        if is_valid_scene_heading or is_section_scene:
            # 新しいシーン
            scene_number += 1
            logger.info(f"Found Scene Heading #{scene_number}: {content_stripped}")
            line_order = 0
            
            heading_text = content_stripped
            
            # Clean up heading text
            if element.element_type == "Section Heading":
                 # Remove ##...
                 heading_text = heading_text.lstrip("#").strip()
            
            if heading_text.startswith("."):
                # Remove . or .2 etc
                # If .2, remove .2
                # If ., remove .
                if heading_text.startswith(".2"):
                    heading_text = heading_text[2:].strip()
                else:
                    heading_text = heading_text.lstrip(".").strip()

            current_scene = Scene(
                script_id=script.id,
                scene_number=scene_number,
                act_number=current_act_number,
                heading=heading_text,
            )
            db.add(current_scene)
            await db.flush()

        elif element.element_type == "Character":
            # セリフを言う登場人物
            char_name = content_stripped
            if char_name.startswith("@"):
                char_name = char_name[1:]
            current_character = character_map.get(char_name)


        elif element.element_type == "Action":
            # ト書き (Action) または 一行セリフ (@Name Dialogue)
            content = element.original_content.rstrip()  # Preserve leading whitespace for Togaki
            
            # Remove forced Action marker '!' if present (added by pre-processor)
            if content.startswith("!"):
                content = content[1:]

            stripped_content = content.strip()

            # Check for one-line dialogue: @Character Dialogue (must have at least one space)
            if stripped_content.startswith("@") and (" " in stripped_content or "　" in stripped_content):
                # Split by first whitespace (half or full width)
                import re
                parts = re.split(r'[ 　]', stripped_content, maxsplit=1) # Split by space or full-width space
                
                if len(parts) >= 2:
                    char_name_raw = parts[0][1:] # Remove @
                    dialogue_content = parts[1]
                    
                    # Get or create character
                    if char_name_raw not in character_map:
                        new_char = Character(script_id=script.id, name=char_name_raw)
                        db.add(new_char)
                        character_map[char_name_raw] = new_char
                        await db.flush()
                    
                    char_obj = character_map[char_name_raw]
                    
                    if current_scene:
                        line_order += 1
                        line = Line(
                            scene_id=current_scene.id,
                            character_id=char_obj.id,
                            content=dialogue_content,
                            order=line_order,
                        )
                        db.add(line)
                else:
                    # Fallback
                     if current_scene:
                        line_order += 1
                        line = Line(
                            scene_id=current_scene.id,
                            character_id=None,
                            content=content,
                            order=line_order,
                        )
                        db.add(line)

            else:
                # Normal Action (Togaki)
                if current_scene:
                    line_order += 1
                    line = Line(
                        scene_id=current_scene.id,
                        character_id=None,
                        content=content,
                        order=line_order,
                    )
                    db.add(line)

        elif element.element_type == "Dialogue":
            # セリフ
            if current_scene and current_character:
                line_order += 1
                line = Line(
                    scene_id=current_scene.id,
                    character_id=current_character.id,
                    content=element.original_content.strip(),
                    order=line_order,
                )
                db.add(line)

    await db.flush()
