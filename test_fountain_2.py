from fountain.fountain import Fountain

content = """
BRICK
(whispering)
Hello.

> TRANSITION:
"""

f = Fountain(content)
for element in f.elements:
    print(f"{element.element_type}: {element.original_content}")
