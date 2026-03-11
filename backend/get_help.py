import sys

import playscript.conv.pdf

with open("help_output.txt", "w") as f:
    sys.stdout = f
    help(playscript.conv.pdf)
