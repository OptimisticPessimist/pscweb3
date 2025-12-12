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
        elif in_char_block:
            # Inside character block, ensure strings are separated by blank lines if not empty
            if stripped:
                processed_lines.append(line)
                processed_lines.append("") # Force blank line
            else:
                processed_lines.append(line)
        else:
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
        # Act検出 (Section Heading level 1)
        # FountainのSection Headingは深さを持っているので、#の数で判定するか、fountainライブラリの仕様を確認
        # 実装上、Section Headingで '#' が1つの場合を幕とみなす
        if element.element_type == "Section Heading":
             if element.original_content.strip().startswith("#") and not element.original_content.strip().startswith("##"):
                  # Level 1 Heading detected
                  heading_content = element.original_content.strip()
                  
                  # "登場人物" や "Character" は幕としてカウントしない
                  if "登場人物" in heading_content or "Character" in heading_content:
                      pass
                  else:
                      # 幕番号を抽出（簡易的にカウンターでもいいが、ここでは単純にインクリメントするか、内容からパースするか）
                      # 今回はシンプルに登場順に番号を振る
                      if current_act_number is None:
                          current_act_number = 1
                      else:
                          current_act_number += 1
                      logger.info(f"Found Act #{current_act_number}: {heading_content}")

        is_scene_heading = element.element_type == "Scene Heading"
        is_section_scene = element.element_type == "Section Heading" and element.original_content.strip().startswith("##")

        if is_scene_heading or is_section_scene:
            # 新しいシーン（標準Fountain または Fountain-JP ##）
            scene_number += 1
            logger.info(f"Found Scene Heading #{scene_number}: {element.original_content.strip()}")
            line_order = 0
            
            # 見出しから "##" などを除去して綺麗にする（Section Headingの場合）
            heading_text = element.original_content.strip()
            if element.element_type == "Section Heading":
                 heading_text = heading_text.lstrip("#").strip()

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
            char_name = element.original_content.strip()
            if char_name.startswith("@"):
                char_name = char_name[1:]
            current_character = character_map.get(char_name)


        elif element.element_type == "Action":
            # ト書き (Action)
            if current_scene:
                line_order += 1
                line = Line(
                    scene_id=current_scene.id,
                    character_id=None,
                    content=element.original_content.strip(),
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
