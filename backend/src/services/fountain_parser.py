import logging
import re
from fountain.fountain import Fountain
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Character, Line, Scene, Script


logger = logging.getLogger("uvicorn")


async def parse_fountain_and_create_models(
    script: Script, fountain_content: str, db: AsyncSession
) -> None:
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
                processed_lines.append(line)
                processed_lines.append("") # Ensure blank line after character heading
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
    
    character_map: dict[str, Character] = {}
    current_order_index = 1
    
    # 1. カスタムセクション「# 登場人物」または「# Character」を探して明示的な順序と詳細情報を抽出
    in_character_section = False
    
    for element in f.elements:
        content = element.original_content.strip()
        
        # セクション見出しの検出
        if element.element_type == "Section Heading":
            if "登場人物" in content or "Character" in content:
                in_character_section = True
                logger.info("Found Character Definition Section")
            else:
                in_character_section = False
        
        # セクション内の要素を解析
        elif in_character_section and element.element_type in ["Action", "Character", "Dialogue"]:
            # Action要素内の各行を処理（Fountainパーサーが複数行を1つのActionとしてまとめる場合があるため）
            # ! で始まる場合は除去する (前処理で追加された場合)
            if content.startswith("!"):
                content = content[1:]

            lines = content.splitlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # "Name: Description" 形式を探す (コロン区切り)。なければ名前のみ
                if ":" in line:
                    parts = line.split(":", 1)
                    name_part = parts[0].strip()
                    desc_part = parts[1].strip()
                else:
                    name_part = line.strip()
                    desc_part = ""
                
                if name_part.startswith("@"):
                    name_part = name_part[1:].strip()
                
                # 既存キャラクターがなければ新規作成
                if name_part and name_part not in character_map:
                    character = Character(
                        script_id=script.id,
                        name=name_part,
                        description=desc_part,
                        order=current_order_index
                    )
                    db.add(character)
                    character_map[name_part] = character
                    current_order_index += 1
                    logger.info(f"Added character from section: {name_part} (order: {current_order_index-1})")

    # 2. 本文からその他のキャラクターを登場順に抽出
    in_character_section = False
    
    for element in f.elements:
        content = element.original_content.strip()
        
        if element.element_type == "Section Heading":
            if "登場人物" in content or "Character" in content:
                in_character_section = True
            else:
                in_character_section = False
                
        elif not in_character_section and element.element_type == "Character":
            char_name = content
            if char_name.startswith("@"):
                char_name = char_name[1:]
            
            if char_name and char_name not in character_map:
                character = Character(
                    script_id=script.id,
                    name=char_name,
                    order=current_order_index
                )
                db.add(character)
                character_map[char_name] = character
                current_order_index += 1

    await db.flush()  # Characterのidを取得

    # シーンとセリフを抽出
    current_scene: Scene | None = None
    scene_number = 0
    current_act_number: int | None = None
    line_order = 0
    current_character: Character | None = None
    collecting_description = False
    last_scene_was_section = False # 節（Section Heading）でシーンが作成されたかのフラグ

    for element in f.elements:
        content_stripped = element.original_content.strip()
        
        # Act検出
        # 1. Section Heading level 1 (starts with #, not ##)
        # 2. Forced Scene Heading level 1 (starts with .1)
        
        # NOTE: 本来Fountainでは # はSection Heading (Act相当) だが、
        # ユーザーが "# シーン1" のように書くケース救済のため、キーワードが含まれる場合はシーンとして扱う
        SCENE_KEYWORDS = ["Scene", "scene", "シーン", "씬", "场", "場", "あらすじ", "Synopsis", "synopsis", "SYNOPSIS", "줄거리", "梗概"]
        has_scene_keyword = any(k in content_stripped for k in SCENE_KEYWORDS)
        
        if "登場人物" in content_stripped or "Character" in content_stripped:
            has_scene_keyword = False
        
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
                             
        if "登場人物" in content_stripped or "Character" in content_stripped:
            is_valid_scene_heading = False
            is_section_scene = False

        if is_valid_scene_heading or is_section_scene:
            # 新しいシーン
            
            # Check for Synopsis
            SYNOPSIS_KEYWORDS = ["あらすじ", "Synopsis", "synopsis", "SYNOPSIS", "줄거리", "梗概"]
            is_synopsis = any(k in content_stripped for k in SYNOPSIS_KEYWORDS)

            # 既存のSection Sceneのすぐ後にScene Headingが来た場合の結合処理
            if is_valid_scene_heading and last_scene_was_section and current_scene and not is_synopsis:
                heading_text = content_stripped
                if heading_text.startswith("."):
                    if heading_text.startswith(".2"):
                        heading_text = heading_text[2:].strip()
                    else:
                        heading_text = heading_text.lstrip(".").strip()
                
                # 前のSection名と新しいScene Headingを結合
                current_scene.heading = f"{current_scene.heading} ({heading_text})"
                logger.info(f"Merged Scene Heading into previous Section: {current_scene.heading}")
                
                # シーン番号は増やさない
                last_scene_was_section = False # 結合したのでリセット
                line_order = 0
                collecting_description = True
                current_character = None
                continue

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
            last_scene_was_section = is_section_scene

        elif element.element_type == "Character":
            # 登場人物検出 -> 説明収集終了
            collecting_description = False
            last_scene_was_section = False


            # セリフを言う登場人物
            char_name = content_stripped
            if char_name.startswith("@"):
                char_name = char_name[1:]
            current_character = character_map.get(char_name)


        elif element.element_type in ["Action", "Synopsis", "Parenthetical", "Transition", "Centered Text"]:
            # ト書き、あらすじ、括弧書き、移行、中央揃え
            content = element.original_content.rstrip()
            
            # マーカーの除去
            marker_removed_content = content
            if element.element_type == "Action" and marker_removed_content.startswith("!"):
                marker_removed_content = marker_removed_content[1:]
            elif element.element_type == "Synopsis" and marker_removed_content.startswith("="):
                marker_removed_content = marker_removed_content[1:].lstrip()
            elif element.element_type == "Centered Text":
                if marker_removed_content.startswith(">") and marker_removed_content.endswith("<"):
                    marker_removed_content = marker_removed_content[1:-1].strip()
                elif marker_removed_content.startswith(">"):
                    marker_removed_content = marker_removed_content[1:].strip()

            stripped_content = marker_removed_content.strip()
            
            if not stripped_content:
                continue

            # 一行セリフの判定 (@Name Dialogue) - Action の場合のみ
            if element.element_type == "Action" and stripped_content.startswith("@") and (" " in stripped_content or "　" in stripped_content):
                collecting_description = False
                last_scene_was_section = False

                # Split by first whitespace (half or full width)
                parts = re.split(r'[ 　]', stripped_content, maxsplit=1) # Split by space or full-width space
                
                if len(parts) >= 2:
                    char_name_raw = parts[0][1:] # Remove @
                    dialogue_content = parts[1]
                    
                    # Get or create character
                    if char_name_raw not in character_map:
                        new_char = Character(
                            script_id=script.id,
                            name=char_name_raw,
                            order=current_order_index
                        )
                        db.add(new_char)
                        character_map[char_name_raw] = new_char
                        current_order_index += 1
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
                            content=marker_removed_content,
                            order=line_order,
                        )
                        db.add(line)

            else:
                # 通常のト書き、あらすじ、またはその他の要素
                if current_scene:
                    # シーン冒頭のあらすじやト書きを詳細記述として収集
                    if collecting_description and element.element_type in ["Action", "Synopsis"]:
                         if current_scene.description:
                             current_scene.description += "\n" + stripped_content
                         else:
                             current_scene.description = stripped_content
                    else:
                         # 最初のト書きセクション以外、または非Action/Synopsis要素が来たら収集終了
                         collecting_description = False

                    line_order += 1
                    # 括弧書きの場合は、直前のキャラクターに紐付ける
                    line_character_id = None
                    if element.element_type == "Parenthetical" and current_character:
                        line_character_id = current_character.id

                    line = Line(
                        scene_id=current_scene.id,
                        character_id=line_character_id,
                        content=marker_removed_content,
                        order=line_order,
                    )
                    db.add(line)
                
                last_scene_was_section = False

        elif element.element_type == "Dialogue":
            # Description collection ends
            collecting_description = False
            last_scene_was_section = False

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
