
import sys
import os

# PYTHONPATHの調整
sys.path.append(os.path.join(os.getcwd(), "backend"))
sys.path.append(os.getcwd())

from fountain.fountain import Fountain
from src.utils.fountain_utils import preprocess_fountain

def test_multi_line_preservation():
    fountain_text = """
Title: Multi-line Test

# Synopsis
= Line 1
Line 2
Line 3
Indented Line

# Scene 1
Action line 1
Action line 2
Action line 3

@Speaker
Dialogue Line 1
Dialogue Line 2
"""
    
    print("--- Original ---")
    print(fountain_text)
    
    preprocessed = preprocess_fountain(fountain_text)
    print("\n--- Preprocessed ---")
    print(preprocessed)
    
    f = Fountain(preprocessed)
    
    print("\n--- Parsed Elements ---")
    description_sim = []
    in_synopsis_scene = False

    for element in f.elements:
        etype = element.element_type
        content = element.original_content.strip()
        print(f"[{etype}] {content}")
        
        # Simulating fountain_parser.py logic for description collection
        if etype == "Section Heading" and "Synopsis" in content:
            in_synopsis_scene = True
            continue
        elif etype == "Section Heading":
            in_synopsis_scene = False
            
        if in_synopsis_scene and etype in ["Action", "Synopsis"]:
            # Clean marker if any (simulating marker removal)
            if etype == "Synopsis" and content.startswith("="):
                content = content[1:].strip()
            elif etype == "Action" and content.startswith("!"):
                content = content[1:].strip()
            
            if content:
                description_sim.append(content)

    print("\n--- Simulated Scene #0 Description ---")
    print("\n".join(description_sim))

    # Verify results
    assert len(description_sim) >= 4, f"Description count too low: {len(description_sim)}"
    
    # Check if Dialogue is kept together
    dialogue_elements = [e for e in f.elements if e.element_type == "Dialogue"]
    print(f"\nDialogue count: {len(dialogue_elements)}")
    for i, e in enumerate(dialogue_elements):
         print(f"D{i}: {repr(e.original_content.strip())}")
    
    if len(dialogue_elements) > 0:
        all_dialogue_content = " ".join([e.original_content.strip() for e in dialogue_elements])
        assert "Dialogue Line 1" in all_dialogue_content
        assert "Dialogue Line 2" in all_dialogue_content

if __name__ == "__main__":
    test_multi_line_preservation()
