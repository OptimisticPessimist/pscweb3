
import sys
import os
sys.path.append(os.getcwd())

from src.config import settings

print(f"Environment: {settings.environment}")
print(f"Database URL: {settings.database_url}")
print(f"CORS Allowed Origins: {['*'] if settings.environment == 'development' else []}")
