"""Fountain脚本パーサーサービス."""

from fountain.fountain import Fountain
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
    in_metadata = True # State to check if we are in metadata section
    
    for line in lines:
        stripped = line.strip()
        
        # Metadata section ends at first blank line
        if in_metadata:
            if not stripped:
                in_metadata = False
                processed_lines.append(line)
                continue
            # Logic: If it looks like a heading or @ character before a blank line,
            # metadata also ends (fountain library behavior can be complex but blank line is safest).
            # But the metadata section is at the VERY top.
            # If we see something starting with # or @ early, we might assume header ended,
            # but usually a blank line is mandatory.
            processed_lines.append(line)
            continue

        # Check for block start/end
        if stripped.startswith("#"):
            # Check if this header starts a character block
            if "登場人物" in stripped or "Characters" in stripped:
                in_char_block = True
            else:
                in_char_block = False
            processed_lines.append(line)
            processed_lines.append("") # Ensure blank line after heading
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
                 if is_following_char:
                     # This is likely Dialogue following @Name (Japanese style with no indent)
                     # Keep it as is, but consume the flag
                     is_following_char = False
                     processed_lines.append(line)
                 else:
                     is_following_char = False
                     processed_lines.append(line)
            
    fountain_content = "\n".join(processed_lines)
    
    f = Fountain(fountain_content)
    logger.info(f"Parsed {len(f.elements)} elements from Fountain content.")
    
    # メタデータの抽出と保存
    metadata = f.metadata
    
    if "date" in metadata:
        script.draft_date = "\n".join(metadata["date"])
    elif "draft date" in metadata:
        script.draft_date = "\n".join(metadata["draft date"])
        
    if "copyright" in metadata:
        script.copyright = "\n".join(metadata["copyright"])
        
    if "contact" in metadata:
        script.contact = "\n".join(metadata["contact"])
        
    if "notes" in metadata:
        script.notes = "\n".join(metadata["notes"])
        
    if "revision" in metadata:
        script.revision_text = "\n".join(metadata["revision"])
        
    # authorも反映（フォーム入力がない場合などのため、または優先度によるが、ここではファイル内記述を反映させても良い）
    # ただし、API側で指定されたauthorを優先すべきか？
    # 通常、Fountainファイルの内容が正となることが多いが、アップロード時のフォームもある。
    # ここでは、もしフォームで指定がなく（None）、Fountainにあれば埋める、あるいは常に上書きする？
    # create_or_update logic in script_processor passes author.
    # If we want to support file-based author, we can update it here.
    if "author" in metadata:
        # 既存のauthorがなければ、またはファイル内容を優先する場合
        # 今回はファイル内の情報を優先して反映させる
        script.author = "\n".join(metadata["author"])

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
    collecting_description = False

    for element in f.elements:
        content_stripped = element.original_content.strip()
        
        # Act検出
        # 1. Section Heading level 1 (starts with #, not ##)
        # 2. Forced Scene Heading level 1 (starts with .1)
        
        # NOTE: 本来Fountainでは # はSection Heading (Act相当) だが、
        # ユーザーが "# シーン1" のように書くケース救済のため、キーワードが含まれる場合はシーンとして扱う
        SCENE_KEYWORDS = ["Scene", "scene", "シーン", "씬", "场", "場", "あらすじ", "Synopsis", "synopsis", "SYNOPSIS", "줄거리", "梗概"]
        has_scene_keyword = any(k in content_stripped for k in SCENE_KEYWORDS)
        
        is_section_act = (element.element_type == "Section Heading" and 
                          content_stripped.startswith("#") and 
                          not content_stripped.startswith("##") and
                          not has_scene_keyword) # キーワードがあればActではない
        
        is_dot_act = (element.element_type == "Scene Heading" and 
                      content_stripped.startswith(".1"))
        
        # .1の場合でも、シーンキーワードが含まれていれば幕としては扱わない（シーンとして扱い、Actカウンタを上げないため）
        # ただし、.1 はもともと Scene Heading なので、ここでの除外は Act としての扱いを除外する意味になる。
        if is_dot_act and has_scene_keyword:
            is_dot_act = False
                      
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
        # 4. Level 1 with scene keyword (# Scene...) [NEW]
        
        is_scene_heading_type = element.element_type == "Scene Heading"
        
        # .1 は上でActとして処理済み。それ以外のScene Headingはシーン
        # つまり、通常のINT.や、.2 (Level 2), . (Forced) はシーン
        # ただし、.1 でもキーワードがあればシーンとして扱う (is_dot_actがFalseになっているはず)
        is_valid_scene_heading = (is_scene_heading_type and 
                                  (not content_stripped.startswith(".1") or has_scene_keyword))
        
        is_section_scene = (element.element_type == "Section Heading" and 
                            (content_stripped.startswith("##") or
                             (content_stripped.startswith("#") and has_scene_keyword)))

        if is_valid_scene_heading or is_section_scene:
            # 新しいシーン
            
            # Check for Synopsis
            SYNOPSIS_KEYWORDS = ["あらすじ", "Synopsis", "synopsis", "SYNOPSIS", "줄거리", "梗概"]
            is_synopsis = any(k in content_stripped for k in SYNOPSIS_KEYWORDS)
            
            if is_synopsis:
                current_scene_number = 0
                logger.info(f"Found Synopsis (Scene #0): {content_stripped}")
            else:
                scene_number += 1
                current_scene_number = scene_number
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
                scene_number=current_scene_number,
                act_number=current_act_number,
                heading=heading_text,
                description="" # Initialize description
            )
            db.add(current_scene)
            await db.flush()
            
            # Reset description collection state
            collecting_description = True
            current_character = None 

        elif element.element_type == "Character":
            # 登場人物検出 -> 説明収集終了
            collecting_description = False

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
                # ... One-line dialogue logic ...
                # One-line dialogue also ends description collection
                collecting_description = False

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
                    # Fallback (should typically not happen given if check)
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
                    # Capture description if we are still at the start of the scene
                    if collecting_description:
                         if current_scene.description:
                             current_scene.description += "\n" + stripped_content
                         else:
                             current_scene.description = stripped_content
                         # Update DB (or wait until flush?) - SQLAlchemy tracks changes to objects in session
                    
                    line_order += 1
                    line = Line(
                        scene_id=current_scene.id,
                        character_id=None,
                        content=content, # Use original content for line to preserve indent
                        order=line_order,
                    )
                    db.add(line)

        elif element.element_type == "Dialogue":
            # Description collection ends
            collecting_description = False

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
