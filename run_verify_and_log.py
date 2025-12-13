
import subprocess
import sys
import os

python_exe = sys.executable
env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'

cmd = [python_exe, "tests/verify_jp_parsing.py"]
print(f"Running: {cmd}")
try:
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', env=env)
    with open("verify_output_utf8.txt", "w", encoding="utf-8") as f:
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\nSTDERR:\n")
        f.write(result.stderr)
    print("Done. Output written to verify_output_utf8.txt")
except Exception as e:
    print(f"Error: {e}")
