
import asyncio
from fountain.fountain import Fountain

def test_fountain_library():
    # Test how the library handles multi-line synopsis and action
    content = """
= Synopsis Line 1
Synopsis Line 2 (indented or not)

Action Line 1
Action Line 2
"""
    f = Fountain(content)
    print("--- Fountain Elements ---")
    for i, element in enumerate(f.elements):
        print(f"[{i}] {element.element_type}: {repr(element.original_content)}")

if __name__ == "__main__":
    test_fountain_library()
