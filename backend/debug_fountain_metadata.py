from fountain import fountain

script = """Title: My Script
Credit: Written by
Author: John Doe
Source: Story by Jane Doe
Draft date: 2023-01-01
Contact:
    123 Main St.
    Anytown, USA
Copyright: (c) 2023
Notes:
    This is a note.
    Another line of note.
Revision: 2.0 Blue Revised

INT. SCENE - DAY

Action.
"""

f = fountain.Fountain(script)
print(f.metadata)
