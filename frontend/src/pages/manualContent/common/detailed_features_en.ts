export const detailedFeaturesEn = `
---

## 📚 Detailed Feature Guide

This section provides detailed explanations of each feature of the system.

<a id="feature-project"></a>
### 📁 Project Management & Invitations
A "Project" is the unit for a single production or shooting.

- **Owner**: The user who creates a project is automatically the Owner and can change all settings.
- **Invitation**: Share the invitation link generated in Settings via **Discord** or other platforms.
- **Permissions**: Three levels: "Owner", "Editor", and "Viewer".

<a id="feature-script"></a>
### 📝 Scripts & Fountain Format
The system uses the **Fountain format (Japanese Extended)** for script management.

- **Upload**: Upload files with the \x60.fountain\x60 extension.
- **Automation**: Characters and scene headings are automatically extracted and reflected in scene charts and scheduling.
- **Vertical Layout**: Read scripts in a beautiful vertical layout on mobile or desktop.
- 📖 **[Fountain JA Writing Manual](/manual/fountain)**

<a id="feature-scene-chart"></a>
### 📊 Scene Chart
A list of "who appears in which scene" based on the script.

- **Auto-Generation**: Created automatically upon script upload.
- **Manual Edit**: Adjust who appears in which scene via the "Scene Chart" tab.
- **Integration**: Used for "Automatic Participant Selection" when creating schedules.
- **Synopsis excluded**: Synopsis (Scene #0) is not shown. Scenes start from #1.

<a id="feature-casting"></a>
### 🎭 Casting
The task of linking "script characters" to "actual users (actors)".

- **Role**: Assign actors to each character.
- **Benefit**: Allows actors to use "My Schedule" to filter only their rehearsals.

<a id="feature-schedule"></a>
### 🗓 Schedule Management
Create practice or shooting dates.

- **Scene Linking**: Selecting scenes for practice automatically lists required members based on the scene chart and casting.

<a id="feature-attendance"></a>
### ✅ Attendance & Discord Integration
Manage member responses for each event.

- **Discord Bot Setup**:
  - Invite the bot to your server via the "Invite Discord Bot" button in project settings.
  - The bot handles automated attendance messages with buttons and reminders.
- **Channel ID Configuration**:
  - Enable "Developer Mode" in Discord Settings -> Advanced.
  - Right-click the destination channel, select "Copy Channel ID", and paste it into the project settings.
- **Automatic Reminders**: Schedule automated reminders for unanswered members or upcoming rehearsals.

<a id="feature-poll"></a>
### 🗳 Schedule Polls
A feature to facilitate consensus on practice dates.

- **Options**: Present multiple dates for members to answer with Yes/Maybe/No.
- **Best Dates**: The system calculates and suggests the best dates for key cast members.

---
[⬆️ Back to Role Guide](#manual-top)
`;
