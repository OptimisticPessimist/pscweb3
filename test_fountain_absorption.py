
from fountain.fountain import Fountain

def test_fountain_absorption():
    content = "= Line 1\nLine 2\nLine 3\n\nAction Line"
    f = Fountain(content)
    print("--- Elements ---")
    for i, e in enumerate(f.elements):
        print(f"[{i}] {e.element_type}: {repr(e.original_content)}")
    
    content2 = "= Line 1\n\nLine 2\n\nLine 3"
    f2 = Fountain(content2)
    print("\n--- Elements with blank lines ---")
    for i, e in enumerate(f2.elements):
        print(f"[{i}] {e.element_type}: {repr(e.original_content)}")

if __name__ == "__main__":
    test_fountain_absorption()
