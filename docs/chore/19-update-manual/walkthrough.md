# Walkthrough - Manual Update & i18n

This walkthrough documents the updates made to the user manual (documentation) and the frontend implementation for internationalization, including fixes for build errors.

## Changes

### Documentation (docs/)
Updated `docs/role_manual.md` and created translated versions (`en`, `ko`, `zh-Hans`, `zh-Hant`) to include new features:
- **Project Creation Limit Exception**: Explained that projects with public scripts are excluded from the 2-project limit.
- **Viewing Public Scripts**: Added "Public Scripts" section and import guide.
- **Fountain Syntax**: Detailed Japanese Fountain syntax (One-line dialogue `@`, Forced headings `.`, Indented action).

### Frontend (frontend/)
- **Manual Content**: Updated `frontend/src/pages/manualContent/*.ts` files (ja, en, ko, zh-Hans, zh-Hant) to match the documentation.
- **Bug Fix**: Resolved `Unterminated template literal` build errors in TypeScript.
    - **Issue**: Backticks in the markdown content (e.g., in the Fountain Syntax section) were interfering with the TypeScript template literal delimiters.
    - **Fix**: Replaced all internal backticks in the content strings with hex escapes (`\x60`) and ensured the closing backtick was not escaped by a preceding backslash.

## Verification

### Automated Tests
- **Build Verification**: Ran `npm run build` in `frontend/`.
    - Result: **Success** (Exit code 0).
    - Verified that all 5 manual content files are correctly parsed by the TypeScript compiler.

### Manual Review
- Confirmed that `ja.ts` and other language files contain the correct escaped sequences (`\x60`) and valid structure.
