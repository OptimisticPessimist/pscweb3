from fountain.fountain import Fountain

content = """
# Synopsis
= This is a synopsis line.
= This is another synopsis line.

EXT. BRICK'S PATIO - DAY
A synopsis of this scene.
= Scene synopsis.

BRICK
Hello.
"""

f = Fountain(content)
for element in f.elements:
    print(f"{element.element_type}: {element.original_content}")
