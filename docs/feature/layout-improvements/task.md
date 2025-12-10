# Phase 9: UI Improvements & User Profile

## Objectives
- Screen Transition & Layout Usability Improvements.
- Enhance User Profile with Discord information (Avatar, Display Name).

## Tasks

### 1. User Profile Enhancement
- [x] **Backend**: 
  - Modify `User` model: Add `display_name`, `avatar_url`, `email`.
  - Database Migration: Generate and apply.
  - Auth Logic: Update `src/auth/discord.py` to capture and update these fields from Discord OAuth.
  - Schema: Update `UserResponse` in `src/schemas/auth.py`.
- [x] **Frontend**:
  - Update `User` type definitions (`types/index.ts`, `features/auth/types/index.ts`).
  - Update `Sidebar.tsx` to display Avatar, Display Name, and Discord Username.

### 2. Navigation Improvements
- [x] **Frontend**:
  - Create `Breadcrumbs.tsx` component (resolves Project Name dynamically).
  - Update `Header.tsx` to include `Breadcrumbs`.

## Status
Completed.
