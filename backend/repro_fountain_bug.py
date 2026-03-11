
import re
from fountain.fountain import Fountain

def clean_fountain_content(content):
    # Replace all lines that only contain whitespace with truly empty lines
    return re.sub(r'^[ \t]+$', '', content, flags=re.MULTILINE)

def test_fountain_bug(content):
    content = clean_fountain_content(content)
    print(f"Testing with content: {repr(content)}")
    try:
        f = Fountain(content)
        print("Success!")
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()

content4 = "Title: Test\n\n\nINT. TEST - DAY"
test_fountain_bug(content4)

content5 = "Title: Test\n\t\nAuthor: John"
test_fountain_bug(content5)

content6 = "Title: Test\n\nAuthor: John"
test_fountain_bug(content6)
