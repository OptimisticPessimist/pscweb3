"""Fountain脚本パーサーサービス."""

import fountain
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
    f = fountain.Fountain(fountain_content)

    # 登場人物を抽出してマップを作成
    character_map: dict[str, Character] = {}
    for element in f.elements:
        if element.element_type == "Character":
            char_name = element.text.strip()
            if char_name and char_name not in character_map:
                character = Character(script_id=script.id, name=char_name)
                db.add(character)
                character_map[char_name] = character

    await db.flush()  # Characterのidを取得

    # シーンとセリフを抽出
    current_scene: Scene | None = None
    scene_number = 0
    line_order = 0
    current_character: Character | None = None

    for element in f.elements:
        if element.element_type == "Scene Heading":
            # 新しいシーン
            scene_number += 1
            line_order = 0
            current_scene = Scene(
                script_id=script.id,
                scene_number=scene_number,
                heading=element.text.strip(),
            )
            db.add(current_scene)
            await db.flush()

        elif element.element_type == "Character":
            # セリフを言う登場人物
            char_name = element.text.strip()
            current_character = character_map.get(char_name)

        elif element.element_type == "Dialogue":
            # セリフ
            if current_scene and current_character:
                line_order += 1
                line = Line(
                    scene_id=current_scene.id,
                    character_id=current_character.id,
                    content=element.text.strip(),
                    order=line_order,
                )
                db.add(line)

    await db.flush()
