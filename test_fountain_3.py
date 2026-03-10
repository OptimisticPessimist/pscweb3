from fountain.fountain import Fountain

content = """
BRICK
(whispering)
Hello.

EXT. ROOM - DAY

BRICK
Hi.
"""

f = Fountain(content)
for element in f.elements:
    print(f"{element.element_type}: {element.original_content}")
