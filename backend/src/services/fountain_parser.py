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
    f = fountain.Fountain(fountain_content)
    logger.info(f"Parsed {len(f.elements)} elements from Fountain content.")

    # 登場人物を抽出してマップを作成

    character_map: dict[str, Character] = {}
    for element in f.elements:
        if element.element_type == "Character":
            char_name = element.original_content.strip()
            if char_name.startswith("@"):
                char_name = char_name[1:]
            
            if char_name and char_name not in character_map:
                character = Character(script_id=script.id, name=char_name)
                db.add(character)
                character_map[char_name] = character

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
