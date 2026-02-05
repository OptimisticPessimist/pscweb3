# Walkthrough - Scene Numbering Fix

## Summary
Fixed an issue where scenes were double-counted when a Section Heading (e.g., `# Scene 1`) was immediately followed by a Scene Heading (e.g., `INT. ROOM`). This caused scene numbering to start from 2 instead of 1.

## Changes

### Backend

#### `fountain_parser.py`
- Added `last_scene_was_section` flag to track if the current scene was created by a Section Heading.
- If a `Scene Heading` immediately follows such a section, the two are merged into a single scene.
- The flag is reset when `Action`, `Dialogue`, or `Character` elements are encountered to ensure only immediate sequences are merged.

## Verification Results

### Automated Tests
- Created `test_bug_reproduction.py` to verify the fix.
    - Input: Section Heading followed by Scene Heading.
    - Expected: 2 scenes with numbers 1 and 2, and merged headings.
    - Result: **PASSED**
- Ran `test_fountain_parser.py`.
    - Result: **PASSED**
- Ran `test_scene_chart_generator.py`.
    - Result: **FAILED** (Note: These tests were already failing independently of this change).

### Manual Verification
N/A
