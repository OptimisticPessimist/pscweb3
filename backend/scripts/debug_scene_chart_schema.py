import asyncio
import os
import sys

# Backend root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.api.scene_charts import _build_scene_chart_response
from src.db import async_session_maker
from src.db.models import SceneCharacterMapping, SceneChart


async def main():
    async with async_session_maker() as db:
        # Get the first scene chart
        stmt = (
            select(SceneChart)
            .options(
                selectinload(SceneChart.mappings).selectinload(SceneCharacterMapping.scene),
                selectinload(SceneChart.mappings).selectinload(SceneCharacterMapping.character)
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        chart = result.scalar_one_or_none()

        if not chart:
            print("No chart found.")
            return

        print(f"Checking Chart ID: {chart.id} for Script: {chart.script_id}")

        try:
            # Replicate API logic
            response_model = _build_scene_chart_response(chart)
            # Force validation (fastapi does this automatically)
            json_model = response_model.model_dump()
            print("Validation Valid!")
            # print(json_model)
        except Exception as e:
            print("Validation FAILED!")
            print(e)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
