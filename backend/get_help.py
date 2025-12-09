import playscript.conv.pdf
import sys

with open("help_output.txt", "w") as f:
    sys.stdout = f
    help(playscript.conv.pdf)
