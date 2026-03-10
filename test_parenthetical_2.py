from fountain.fountain import Fountain

content = """
EXT. ROOM - DAY

BRICK
(whispering)
Hello.
"""

f = Fountain(content)
for element in f.elements:
    print(f"{element.element_type}: {element.original_content}")
