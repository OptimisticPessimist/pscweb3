
import subprocess
import sys

# Use .venv python if available, or just sys.executable if running inside venv
python_exe = sys.executable

import os
env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'

cmd = [python_exe, "-m", "pytest", "backend/tests/unit/test_jp_features.py", "-s"]
print(f"Running: {cmd}")
try:
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', env=env)
    with open("test_output_utf8.txt", "w", encoding="utf-8") as f:
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\nSTDERR:\n")
        f.write(result.stderr)
    print("Done. Output written to test_output_utf8.txt")
except Exception as e:
    print(f"Error: {e}")
