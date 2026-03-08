export const detailedFeaturesEn = `
---

## 📚 Detailed Feature Guide

This section provides detailed explanations of each feature of the system.

<a id="feature-project"></a>
### 📁 Project Management & Invitations
A "Project" is the unit for a single production or shooting.

- **Owner**: The user who creates a project is automatically the Owner and can change all settings.
- **Invitation**: Share the invitation link generated in Settings via Discord or Messenger. Users who log in via the link are automatically added as members.
- **Permissions**:
  - **Owner**: Full access.
  - **Editor**: Can create schedules and update scripts.
  - **Viewer**: Can read scripts and respond to attendance.

<a id="feature-script"></a>
### 📝 Scripts & Fountain Format
The system uses the **Fountain format** for script management.

- **Upload**: Upload files with the \x60.fountain\x60 extension.
- **Automation**: Characters and scene headings are automatically extracted and reflected in scene charts and scheduling.
- **Native Support**: Handles Japanese/Chinese vertical layouts and unique character line formats.

<a id="feature-scene-chart"></a>
### 📊 Scene Chart
A list of "who appears in which scene" based on the script.

- **Auto-Generation**: Created automatically upon script upload.
- **Manual Edit**: You can manually adjust who appears in which scene via the "Scene Chart" tab in the script details page.
- **Integration**: Used for "Automatic Participant Selection" when creating schedules.

<a id="feature-casting"></a>
### 🎭 Casting
The task of linking "script characters" to "actual users (actors)".

- **Role**: Assign actors to each character.
- **Benefit**: Allows actors to use "My Schedule" to filter only the practices/shoots they are involved in.

<a id="feature-schedule"></a>
### 🗓 Schedule Management
Create practice or shooting dates.

- **Scene Linking**: Selecting scenes for practice automatically lists required members as "Participants" based on the scene chart and casting.

<a id="feature-attendance"></a>
### ✅ Attendance & Reminders
Manage member responses for each event.

- **Discord integration**: Sends messages with buttons to Discord channels for one-tap responses.
- **Auto-notifications**: You can configure automated reminders for unanswered members or upcoming rehearsals.

<a id="feature-poll"></a>
### 🗳 Schedule Polls
A feature to facilitate consensus on practice dates.

- **Options**: Present multiple dates for members to answer with Yes/Maybe/No.
- **Best Dates**: The system tells you which day works best for everyone or key cast members.

---
[⬆️ Back to Role Guide](#manual-top)
`;
