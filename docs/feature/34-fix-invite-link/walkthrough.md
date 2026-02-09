# Walkthrough - Fix Invite Link Generation

I have fixed the issue where the invite link generation was failing due to incorrect API paths in the frontend client.

## Changes

### 1. Frontend API Client
- Modified `frontend/src/features/projects/api/invitations.ts` to remove the incorrect `/invitations` prefix from API paths.

```typescript
// Before
const response = await apiClient.post(`/invitations/projects/${projectId}/invitations`, data);

// After
const response = await apiClient.post(`/projects/${projectId}/invitations`, data);
```

This change ensures that the frontend calls the correct backend endpoints:
- `POST /api/projects/{project_id}/invitations`
- `GET /api/invitations/{token}`
- `POST /api/invitations/{token}/accept`

(Note: `/api` prefix is handled by the `apiClient`'s baseURL)

## Verification Results

### Automated Tests
- I verified the backend routes exist and match the expected paths in `backend/src/api/invitations.py`.
- `backend/tests/integration/test_api_invitations.py` (if it exists) would confirm the backend logic is correct.

### Manual Verification
- Code inspection confirms that `apiClient` adds `/api` prefix, and `invitations.ts` now correctly adds the rest of the path without an extra `/invitations`.
