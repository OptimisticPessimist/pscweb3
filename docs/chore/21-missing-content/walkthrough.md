# Walkthrough - Scene Detection Fix

This walkthrough documents the fix for the Fountain parser issue where `# Scene Name` was being parsed as an Act instead of a Scene, causing missing content in the viewer.

## Issue Description
Content like:
```fountain
# シーン1
```
was being parsed as:
- Act: 1 (Section Heading Level 1)
- Scene: None
This caused subsequent lines to be orphaned.

## Changes

### Backend
- **File**: `backend/src/services/fountain_parser.py`
- **Fix**: Modified the Act/Scene detection logic.
    - Added logic to check for scene keywords (`Scene`, `シーン`, `씬`, `场`, `場`) in lines starting with `#`.
    - If a keyword is found, it is **excluded** from Act detection and **included** in Scene detection.
    - Also updated `.1` (Forced Scene) handling to respect this keyword override (though `.1` was already largely handled, this reinforces it).

### Documentation
- **File**: `docs/role_manual.md`
- **Update**: Added a note in the "Editor Manual" -> "Japanese Fountain Syntax" section explaining that `# SceneName` is supported as a valid Scene heading.

## Verification
- **Script**: `backend/debug_scene_creation.py` (Created and then deleted)
- **Result**: Confirmed that `# シーン1` is now parsed as `Scene Created: #1`, and lines following it are correctly associated with that scene.

## Conclusion
The parser now correctly handles "loose" scene headings that use `#` (technically Act/Section Heading) combined with an explicit "Scene" keyword, supporting multiple languages.
