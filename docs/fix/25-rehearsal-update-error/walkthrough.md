# Fix Rehearsal Update 500 Error

## Problem
The `update_rehearsal` endpoint was failing with a 500 Internal Server Error when trying to update a rehearsal.

## Cause
A syntax error was found in `backend/src/api/rehearsals.py` during the construction of the `casts` response list. A loop was malformed, containing a duplicate entry and incorrect indentation.

## Solution
Removed the duplicative and malformed code lines and corrected the indentation of the loop responsible for processing default casts.

### Changes
#### [MODIFY] [rehearsals.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/api/rehearsals.py)
- Fixed syntax error in `update_rehearsal` function.

```diff
-                    for casting in char.castings:
-                        casts_response_list.append(RehearsalCastResponse(
-                            character_id=char.id,
-                            character_name=char.name,
-                        for casting in char.castings:
+                    for casting in char.castings:
```

## Verification
- Verified that the file acts as valid Python code using `python -m py_compile`.
