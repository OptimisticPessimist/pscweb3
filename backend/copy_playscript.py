
import playscript.conv.pdf as pdf
import shutil

print(f"Copying from {pdf.__file__}")
shutil.copy(pdf.__file__, 'backend/temp_playscript_pdf.py')
print("Copy complete.")
