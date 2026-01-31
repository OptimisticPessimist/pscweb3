
import playscript.conv.pdf as pdf
import os

print(f"File path: {pdf.__file__}")
try:
    with open(pdf.__file__, 'r', encoding='utf-8') as f:
        print(f.read())
except Exception as e:
    print(f"Error reading file: {e}")
