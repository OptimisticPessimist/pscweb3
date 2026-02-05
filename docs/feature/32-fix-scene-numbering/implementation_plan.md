# Scene Numbering Fix Implementation Plan

## Problem Description
When a user includes a Section Heading (e.g., `# Scene 1`) immediately followed by a Scene Heading (e.g., `INT. ROOM - DAY`), the parser interprets BOTH as separate scenes.
- `# Scene 1` -> Creates Scene 1
- `INT. ROOM - DAY` -> Creates Scene 2

This results in the actual scene content starting at Scene 2, shifting all scene numbers by +1.

## User Review Required
> [!IMPORTANT]
> This change will alter how scenes are parsed. If a Section Heading is followed immediately by a Scene Heading, they will be merged into a single scene (Scene Heading overwrites or appends to Section Heading). This logic assumes that such a sequence is intended to represent a single scene.

## Proposed Changes

### Backend

#### [MODIFY] [fountain_parser.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/services/fountain_parser.py)
- In `parse_fountain_and_create_models`:
    - Track if the *previous* element was a Section Heading that triggered a scene creation.
    - When a `Scene Heading` is encountered:
        - Check if `current_scene` exists and was just created by a Section Heading (and has no lines yet).
        - If yes:
            - Update `current_scene.heading` with the new Scene Heading text (or combine them).
            - Do NOT increment `scene_number`.
            - Do NOT create a new `Scene` object.
        - If no:
            - Proceed as normal (increment scene number, create new Scene).

## Verification Plan

### Automated Tests
- Run the reproduction test `backend/tests/unit/test_bug_reproduction.py`.
- Verify that `INT. SCENE 1` is parsed as Scene 1, not Scene 2.
- Verify that `INT. SCENE 2` is parsed as Scene 2.
- Run existing tests `backend/tests/unit/test_fountain_parser.py` to ensure no regression.

### Manual Verification
- None required (Unit tests cover this logic).
