
import os
import sys

# Add backend/src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.pdf_generator import generate_script_pdf

def test_metadata_newline():
    fountain_content = """
Title: Vertical Layout Test
Author: Test User
Date: 2026-02-01
Revision: 3.0
Contact: 090-1234-5678
Contact: test@example.com
Notes: This is a note.
Notes: It has multiple lines.
Notes: And should appear vertically.

!

# あらすじ

This is the body.
"""
    
    print("Generating PDF with vertical metadata...")
    try:
        pdf_bytes = generate_script_pdf(fountain_content)
        print(f"PDF generated successfully. Size: {len(pdf_bytes)} bytes")
        
        output_path = "test_metadata_newline.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"Saved to {output_path}")
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        with open("error.log", "w") as f:
            traceback.print_exc(file=f)

if __name__ == "__main__":
    test_metadata_newline()
