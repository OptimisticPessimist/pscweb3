from src.services.pdf_generator import generate_script_pdf
import os

dummy_fountain = """
Title: Test Script
Author: Antigravity

INT. ROOM - DAY

CHARACTER
Hello world.
"""

try:
    print("Generating PDF...")
    pdf_bytes = generate_script_pdf(dummy_fountain)
    print(f"Success! Generated {len(pdf_bytes)} bytes.")
    with open("test_output.pdf", "wb") as f:
        f.write(pdf_bytes)
except Exception as e:
    print(f"Error generating PDF: {e}")
    import traceback
    traceback.print_exc()
