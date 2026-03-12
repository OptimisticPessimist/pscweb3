
from fountain.fountain import Fountain

def test_multi_line_action():
    # Test if multiple action lines without blank lines are preserved
    content = "Action Line 1\nAction Line 2\nAction Line 3"
    f = Fountain(content)
    print("--- Elements ---")
    for i, e in enumerate(f.elements):
        print(f"[{i}] {e.element_type}: {repr(e.original_content)}")

if __name__ == "__main__":
    test_multi_line_action()
