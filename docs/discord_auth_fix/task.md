# Task Checklist: Discord Authentication Fix

- [x] **Diagnose Hanging Issue** (Windows Environment)
    - [x] Isolate network calls from async loop
    - [x] Implement detached subprocess (`auth_helper.py`)
    - [x] Implement file-based result polling

- [x] **Fix Auth Callback Logic**
    - [x] Verify token exchange in helper
    - [x] Pass user data back to main process
    - [x] Handle DB user creation/retrieval

- [x] **Refactor API Structure**
    - [x] Create `src/api/users.py` for `/users/me`
    - [x] Remove legacy `/me` from `auth.py`
    - [x] Update `main.py` router registration
    - [x] Update frontend `auth.ts` to point to `/users/me`

- [x] **Fix JWT Implementation**
    - [x] Debug 401 Unauthorized errors
    - [x] Fix `sub` claim type (int -> str)
    - [x] Update verification logic

- [x] **Cleanup & Documentation**
    - [x] Remove `debug_panic.log` writers
    - [x] Remove logging from `auth_helper.py`
    - [x] Create walkthrough documentation
