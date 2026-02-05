
import sys
import os

# Ensure backend/src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from src.services.pdf_generator import generate_script_pdf

def verify_bold_title():
    fountain_content = """Title: **BOLD TITLE TEST**
Author: Me

INT. ROOM - DAY

Action here.
"""
    # Note: the **BOLD** markdown in title isn't parsed by the fountain parser as bold usually, 
    # but our code change forces the TITLE line to be drawn as bold in the PDF.
    # The text itself will just be "**BOLD TITLE TEST**" or whatever the parser extracts.
    
    # Actually, standard Fountain parser just takes everything after "Title:".
    
    print("Generating PDF...")
    try:
        pdf_bytes = generate_script_pdf(fountain_content)
        output_path = "verification_bold_title.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"Successfully generated {output_path}")
        print("Please open this file and verify the title is BOLD.")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_bold_title()
