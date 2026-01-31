
import inspect
import sys
import os

try:
    import playscript
    from playscript.conv import pdf
    print(f"playscript location: {os.path.dirname(playscript.__file__)}")
    print("Source of psc_to_pdf:")
    print(inspect.getsource(pdf.psc_to_pdf))
except Exception as e:
    print(f"Error: {e}")
