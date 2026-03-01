import traceback
import sys
import logging

logging.basicConfig(level=logging.INFO)

from alembic.config import Config
from alembic import command

try:
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
except Exception as e:
    print(f"Exception: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
