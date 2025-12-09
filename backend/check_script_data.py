import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from uuid import UUID
from sqlalchemy import select, func
from src.db import async_session_maker
from src.db.models import Script, Scene, SceneChart, SceneCharacterMapping

async def check_script(script_id_str):
    script_id = UUID(script_id_str)
    async with async_session_maker() as db:
        print(f"Checking Script: {script_id}")
        
        # Check Script
        script = await db.get(Script, script_id)
        if not script:
            print("Script not found!")
            return
        print(f"Script Title: {script.title}")
        
        # Check Scenes
        result = await db.execute(select(func.count(Scene.id)).where(Scene.script_id == script_id))
        scene_count = result.scalar()
        print(f"Scene Count: {scene_count}")
        
        # Check Chart
        result = await db.execute(select(SceneChart).where(SceneChart.script_id == script_id))
        chart = result.scalar_one_or_none()
        
        if chart:
            print(f"SceneChart ID: {chart.id}")
            # Check Mappings
            result = await db.execute(select(func.count(SceneCharacterMapping.id)).where(SceneCharacterMapping.chart_id == chart.id))
            mapping_count = result.scalar()
            print(f"Mapping Count: {mapping_count}")
        else:
            print("SceneChart NOT found!")

if __name__ == "__main__":
    asyncio.run(check_script("8776036b-aba5-4447-a377-241b2691e816"))
