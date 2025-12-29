import asyncio
from src.services.pdf_generator import generate_script_pdf

sample_fountain = """
Title: Test Script
Author: Antigravity

# Scene 1

INT. ROOM - DAY

CHARACTER
Hello world.
"""

def test_pdf():
    try:
        pdf_bytes = generate_script_pdf(sample_fountain)
        print(f"Success! PDF size: {len(pdf_bytes)} bytes")
        with open("test_output.pdf", "wb") as f:
            f.write(pdf_bytes)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf()
