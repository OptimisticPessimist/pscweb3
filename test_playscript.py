
from playscript.conv import fountain
from playscript import PScLineType

def test_playscript_synopsis():
    content = """Title: Test
Synopsis: Metadata Synopsis Line 1
  Metadata Synopsis Line 2

# Scene 1
= Inline Synopsis Line 1
= Inline Synopsis Line 2
Action line.
"""
    psc = fountain.psc_from_fountain(content)
    print("--- Playscript Lines ---")
    for i, line in enumerate(psc.lines):
        print(f"[{i}] {line.type}: {repr(line.text)}")

if __name__ == "__main__":
    test_playscript_synopsis()
