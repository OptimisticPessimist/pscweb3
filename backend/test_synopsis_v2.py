
import os
import sys

# Add backend/src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.pdf_generator import generate_script_pdf

def test_synopsis_pdf():
    fountain_content = """
Title: Feature Test
Author: Jane Doe
Date: 2026-02-01
Draft date: 2026-02-01

!

# あらすじ

昔々あるところに、おじいさんとおばあさんがいました。
二人は楽しく暮らしていました。
これはあらすじです。

# 第一章

INT. ROOM - DAY

CHARACTER
Hello world.
"""
    
    print("Generating PDF with custom synopsis styling...")
    try:
        pdf_bytes = generate_script_pdf(fountain_content)
        print(f"PDF generated successfully. Size: {len(pdf_bytes)} bytes")
        
        output_path = "test_synopsis_v2.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"Saved to {output_path}")
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_synopsis_pdf()
