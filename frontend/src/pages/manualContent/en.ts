export const manualEn = `# PSCWEB3 User Manual
## Project Management System for Theater & Video Production

This system is designed to streamline the management of theater productions and video projects.
It includes features for script management, scheduling, attendance tracking, and cast/staff management.

---

## Table of Contents
1. [About Roles](#1-about-roles)
2. [Getting Started (For Everyone)](#2-getting-started-for-everyone)
3. [Viewer Manual](#3-viewer-manual)
4. [Editor Manual](#4-editor-manual)
5. [Owner Manual](#5-owner-manual)
6. [Feature Permissions Table](#6-feature-permissions-table)

---

## 1. About Roles

The system has three roles. Check which role you have.

### 👑 Owner
**Theater:** Club president, director, production chief  
**Video:** Director, producer, production manager

- Create and delete projects
- Invite members and manage permissions
- Configure Discord notifications
- Access to all features

### ✏️ Editor
**Theater:** Assistant director, stage manager, section chiefs  
**Video:** Assistant director, cinematographer, department leads

- Upload and edit scripts
- Create and edit schedules
- Send attendance reminders to non-respondents
- Manage scene charts
- Configure casting

### 👀 Viewer
**Theater:** Cast (actors), staff, advisors  
**Video:** Performers, staff, clients

- View schedules
- Read scripts
- Respond to attendance
- Check personal schedule

---

## 2. Getting Started (For Everyone)

### 🔐 How to Log In
1. Access the system URL.
2. Click the **"Login with Discord"** button.
3. Authenticate with your Discord account to log in automatically.

> 💡 If you don't have a Discord account, create a free account at [Discord](https://discord.com/) first.

### 🏠 Dashboard
After logging in, you'll see the Dashboard:
- List of projects you're participating in
- Upcoming schedules
- Links to various features

### 🌐 Language Switching
Use the button in the upper right to switch display language:
- 日本語 / English / 한국어 / 简体中文 / 繁體中文

---

## 3. Viewer Manual

Features primarily used by cast and staff members.

### 📅 Checking the Schedule
View rehearsal and shooting dates.

1. Select **"Schedule"** from the menu.
2. Dates are displayed in calendar format.
3. Click a date to view details (location, scenes, participants, etc.).

### 📆 My Schedule
View only the rehearsals/shoots you're involved in.

1. Select **"My Schedule"** from the menu.
2. Rehearsals for scenes you're cast in are displayed.

### ✅ Responding to Attendance
Respond to attendance for rehearsals or shoots.

**Via Discord:**
1. You'll receive a notification on Discord.
2. Simply press buttons like "Attending" or "Absent" to complete.

**Within the System:**
1. Select **"Attendance"** from the menu.
2. Choose the event and respond to attendance.

### 📖 Reading Scripts
Access the latest scripts anytime from your phone or PC.

1. Select **"Scripts"** from the menu.
2. Choose the script you want to read from the list.
3. Scripts are displayed in an easy-to-read vertical format.

### 📊 Viewing Scene Charts
See which characters appear in each scene.

1. On the script detail page, select the **"Scene Chart"** tab.
2. Characters appearing in each scene are listed.

---

## 4. Editor Manual

Features for those managing the project, such as directing and production staff.

### 📝 Uploading Scripts
Upload script files in Fountain format.

1. Select **"Scripts"** → **"Upload"** from the menu.
2. Select a file (or drag and drop).
3. Confirm the title and click **"Upload"**.

> 💡 **What is Fountain format?**  
> A simple text format for writing scripts.  
> Learn more at [fountain.io](https://fountain.io/).

### 🗓 Creating Schedules
Create rehearsal or shooting schedules.

1. Select **"Schedule"** from the menu.
2. Click the **"Create New"** button.
3. Enter and save the following:
   - Date and time
   - Location
   - Target scenes (multiple selection available)
   - Notes

### 📊 Editing Scene Charts
Set which characters appear in each scene.

1. On the script detail page, select the **"Scene Chart"** tab.
2. Check the characters that appear in each scene's row.
3. Changes are auto-saved.

### 🎭 Configuring Casting
Link characters to actors.

1. Select **"Casting"** from the menu.
2. Choose the character you want to configure from the list.
3. Select the assigned actor.
4. Double casting (multiple actors for the same role) is also supported.

### 👥 Staff Management
Set staff roles.

1. Select **"Staff"** from the menu.
2. Set each staff member's assigned role in the member list.

### 📢 Sending Attendance Reminders
Send reminders to members who haven't responded.

1. Select **"Attendance"** from the menu.
2. Choose the target event.
3. Click the **"Send Reminder"** button.
4. A reminder with mentions is sent to non-respondents via Discord.

---

## 5. Owner Manual

Features for those managing the entire project.

### 🚀 Creating a Project
Create a new production or shooting project.

1. Click **"Create New Project"** on the Dashboard.
2. Enter the project name (production title, etc.).
3. Enter a description (optional) and click **"Create"**.

### 📩 Inviting Members
Invite members to the project.

1. Open the project **"Settings"**.
2. Click the **"Create Invite Link"** button.
3. Copy the displayed URL and share via LINE or Discord.
4. When members log in via the link, they automatically join the project.

### ⚙️ Changing Member Permissions
Change a member's role (Owner/Editor/Viewer).

1. Open **"Settings"** → **"Member Management"** for the project.
2. Select the **"Role"** for the member you want to change.
3. Changes are applied immediately.

### 🔔 Discord Notification Settings
Settings for sending project notifications to Discord.

#### Webhook URL (General Notifications)
Receive notifications for project updates, etc.

1. Open **"Channel Settings"** for the Discord channel where you want to receive notifications.
2. Select **"Integrations"** → **"Webhooks"**.
3. Create a **"New Webhook"** and copy the URL.
4. Paste it in the **"Discord Webhook URL"** field in the system settings.

#### Webhook URL (Script Notifications)
Script upload notifications can be sent to a separate channel (optional).

#### Channel ID (Attendance)
Settings for sending attendance confirmation messages with buttons.

**How to get the Channel ID:**
1. Open Discord **"User Settings"** → **"Advanced"**.
2. Turn on **"Developer Mode"**.
3. **Right-click** the target channel → select **"Copy Channel ID"**.
4. Paste it in the **"Discord Channel ID"** field in the system settings.

---

## 6. Feature Permissions Table

| Feature | 👑 Owner | ✏️ Editor | 👀 Viewer |
| :--- | :---: | :---: | :---: |
| **Create/Delete Projects** | ☑ | - | - |
| **Invite Members/Change Permissions** | ☑ | - | - |
| **Discord Notification Settings** | ☑ | - | - |
| **Upload/Edit Scripts** | ☑ | ☑ | - |
| **Create/Edit Schedules** | ☑ | ☑ | - |
| **Edit Scene Charts** | ☑ | ☑ | - |
| **Configure Casting** | ☑ | ☑ | - |
| **Set Staff Roles** | ☑ | ☑ | - |
| **Send Attendance Reminders** | ☑ | ☑ | - |
| **Respond to Attendance** | ☑ | ☑ | ☑ |
| **View Schedules** | ☑ | ☑ | ☑ |
| **View My Schedule** | ☑ | ☑ | ☑ |
| **View Scripts** | ☑ | ☑ | ☑ |
| **View Scene Charts** | ☑ | ☑ | ☑ |

---

## Contact

If you encounter issues or find bugs, please contact the project administrator or development team.
`;
