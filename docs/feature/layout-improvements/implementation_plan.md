# Implementation Plan - UI Improvements

## Phase 9: UI Improvements & User Profile

### Backend
#### [MODIFY] [src/db/models.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/db/models.py)
- Add `display_name`, `avatar_url`, `email` columns to `User` model.

#### [MIGRATION]
- `alembic revision --autogenerate`
- `alembic upgrade head`

#### [MODIFY] [src/auth/discord.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/auth/discord.py)
- Update `get_or_create_user_from_discord` to populate new fields.

#### [MODIFY] [src/schemas/auth.py](file:///f:/src/PythonProject/pscweb3-1/backend/src/schemas/auth.py)
- Add fields to `UserResponse`.

### Frontend
#### [MODIFY] [src/types/index.ts](file:///f:/src/PythonProject/pscweb3-1/frontend/src/types/index.ts)
- Update `User` interface.

#### [MODIFY] [src/components/layout/Sidebar.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/components/layout/Sidebar.tsx)
- Use `useAuth` hook.
- Display `avatar_url`, `display_name`, `discord_username`.

#### [NEW] [src/components/Breadcrumbs.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/components/Breadcrumbs.tsx)
- Implement Breadcrumbs with `useQuery` for project name resolution.

#### [MODIFY] [src/components/layout/Header.tsx](file:///f:/src/PythonProject/pscweb3-1/frontend/src/components/layout/Header.tsx)
- Use `Breadcrumbs` component.
