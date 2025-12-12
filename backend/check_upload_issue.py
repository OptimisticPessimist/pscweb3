import asyncio
import logging
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.db import async_session_maker
from src.db.models import Script, Scene, Line, Character, TheaterProject, User, ProjectMember
from src.services.scene_chart_generator import generate_scene_chart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting check_upload_issue check...")
    
    async with async_session_maker() as db:
        try:
            # 1. Verify schema by attempting to insert a Line with None character_id
            logger.info("Step 1: Creating test data...")
            
            # Find a project and user to attach to (or create dummy)
            stmt = select(TheaterProject).limit(1)
            project = (await db.execute(stmt)).scalar_one_or_none()
            
            stmt = select(User).limit(1)
            user = (await db.execute(stmt)).scalar_one_or_none()
            
            if not project or not user:
                logger.error("No project or user found to test with.")
                return

            # Create Dummy Script (Empty content initially)
            script_id = uuid4()
            script = Script(
                id=script_id,
                project_id=project.id,
                uploaded_by=user.id,
                title="Debug Parser Check",
                content="", # Will be set by parser? No, parser takes content string
                is_public=False
            )
            db.add(script)
            await db.flush()

            # Test Content with Actions
            import textwrap
            fountain_text = textwrap.dedent("""\
            Title: Upload Debug
            
            INT. TEST ROOM - DAY

            This is an action line (Togaki).

            CHARACTER
            Dialogue line.

            (Startled)
            Parenthetical.

            Another action.
            """)

            # 2. Verify Parser
            logger.info("Step 2: Testing parse_fountain_and_create_models...")
            from src.services.fountain_parser import parse_fountain_and_create_models
            
            await parse_fountain_and_create_models(script, fountain_text, db)
            await db.commit()
            logger.info("Step 2 Success: Parser completed without error.")
            
            # 3. Verify Scene Chart Generation
            logger.info("Step 3: Testing generate_scene_chart...")
            
            # Reload script with relationships
            stmt = (
                select(Script)
                .where(Script.id == script_id)
                .options(
                    selectinload(Script.scenes).options(
                        selectinload(Scene.lines).options(selectinload(Line.character))
                    ),
                    selectinload(Script.characters),
                )
            )
            result = await db.execute(stmt)
            script_loaded = result.scalar_one()
            
            # Verify lines were created
            logger.info(f"Loaded {len(script_loaded.scenes)} scenes.")
            if script_loaded.scenes:
                 logger.info(f"Scene 1 has {len(script_loaded.scenes[0].lines)} lines.")
                 for l in script_loaded.scenes[0].lines:
                     logger.info(f"Line: '{l.content}' (CharID: {l.character_id})")

            await generate_scene_chart(script_loaded, db)
            await db.commit()
            logger.info("Step 3 Success: Scene chart generated.")
            
            # Clean up
            # await db.delete(script_loaded)
            # await db.commit()
            
        except Exception as e:
            logger.error(f"CHECK FAILED: {e}")
            import traceback
            error_msg = traceback.format_exc()
            print(error_msg)
            with open("check_upload_debug.log", "w", encoding="utf-8") as f:
                f.write(error_msg)
        finally:
            logger.info("Finished.")

if __name__ == "__main__":
    asyncio.run(main())
