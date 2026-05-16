# PSCWEB3 User Manual
## Project Management System for Theater & Video Production

This system is designed to streamline the management of theater productions and video projects.
It includes features for script management, scheduling, attendance tracking, and cast/staff management.

---

## Table of Contents
1. [About Roles](#1-about-roles)
2. [Getting Started (For Everyone)](#2-getting-started-for-everyone)
3. [🎫 Ticket Reservation (For General Visitors)](#3-🎫-ticket-reservation-for-general-visitors)
4. [Viewer Manual](#4-viewer-manual)
5. [Editor Manual](#5-editor-manual)
   - [Milestone Reservation List](#🎫-milestone-reservation-list)
6. [Owner Manual](#6-owner-manual)
7. [Feature Permissions Table](#7-feature-permissions-table)

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

> 💡 **About Project Creation Limits**
> Normally, a user can own up to **2 private projects**.
> However, **projects containing "Public" scripts are excluded from this limit**, allowing you to create unlimited public projects.
> Publish your works and expand your activities!

### 🌐 Language Switching
Use the button in the upper right to switch display language:
- 日本語 / English / 한국어 / 简体中文 / 繁體中文

---

## 3. 🎫 Ticket Reservation (For General Visitors)

This section is for **general visitors** attending the performance.  
※ Project members (cast/staff) should refer to the following sections.

### How to Reserve Tickets

1. Access the **reservation page URL** shared via SNS or official website.
2. Enter the following information:
   - **Name**: Your name
   - **Email Address**: Email where you'll receive confirmation
   - **Number of Tickets**: Number of tickets needed (1 or more)
   - **Referred by**: (Optional) Select a cast/staff member if you know someone
3. Click the **"Reserve"** button.
4. You'll receive a confirmation email - please check the details.

> 💡 **After Reservation**  
> - The confirmation email includes performance date, location, and reservation details.
> - It also includes a link to add to Google Calendar.
> - If you need to cancel, use the cancellation link in the email.

> 🌐 **Multi-language Support**  
> The reservation page supports 5 languages (Japanese, English, Korean, Simplified Chinese, Traditional Chinese).  
> It automatically displays in your browser's language setting.

---

## 4. Viewer Manual

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
2. Your project's scripts are displayed.
3. Scripts are displayed in an easy-to-read vertical format.

### 🌍 Viewing Public Scripts
You can read scripts published by other users.

1. Select **"Public Scripts"** from the dashboard or menu.
2. Choose a script to view.
3. You can also **Import** a script you like as your own project (details below).

### 📊 Viewing Scene Charts
See which characters appear in each scene.

1. On the script detail page, select the **"Scene Chart"** tab.
2. Characters appearing in each scene are listed.

> 💡 **How to Read the Chart**
> - **●**: Appearance based on script dialogue (auto-generated)
> - **○**: Manually added appearance
> - **・**: Not appearing

---

## 5. Editor Manual

Features for those managing the project, such as directing and production staff.

### 📝 Uploading Scripts
Upload script files in Fountain format.

1. Select **"Scripts"** → **"Upload"** from the menu.
2. Select a file (or drag and drop).
3. Confirm the title and click **"Upload"**.

> 💡 **What is Fountain format?**  
> A simple text format for writing scripts.  
> Learn more at [fountain.io](https://fountain.io/).
>
> **🇯🇵 Japanese Fountain Syntax**:
> This system supports extended syntax for easier Japanese script writing.
> 1. **One-line Dialogue**: Start with `@` (e.g., `@Character Dialogue`).
> 2. **Forced Headings**: Start with `.` (e.g., `.1 Act 1`, `.2 Scene 1`).
> 3. **Indented Action**: Lines starting with a space are treated as Action with indentation preserved.

### 📝 Script Information
You can set the following when uploading:
- **Author**: Screenplay author name (Optional).
- **Public**: Check "Public" to allow other users to view and import.
    - *Note: Making it public removes the project from your creation limit count.*

### 🗓 Creating Schedules
Create rehearsal or shooting schedules.

1. Select **"Schedule"** from the menu.
2. Click the **"Create New"** button.
3. Enter and save the following:
   - Date and time
   - Location
   - Target scenes (multiple selection available)
   - Notes

### 🚩 Milestone Settings
Set major deadlines and performance dates (milestones).

1. Add from **"Milestone Settings"** in project settings.
2. Set title, date, color, etc., and save.
3. Displayed on the schedule; can automatically create attendance confirmation events.
4. Setting **reservation capacity** generates a ticket reservation page link.
   - Share the generated link with performance announcements on SNS.
   - Visitors can reserve by entering name, email, number of tickets, etc.

### 🎫 Milestone Reservation List
Check reservation status for each performance (milestone) and manage visitor attendance.

1. Open **"Milestone Settings"** in project settings.
2. Click the **"Reservation Page"** link for milestones with reservation capacity set.
3. The reservation list displays the following information:
   - Visitor name and email address
   - Number of tickets reserved
   - Referrer (if cast/staff)
   - Reservation date and time
4. Use the **attendance toggle** to record visitor attendance.
   - Toggle ON marks as "Attended".
   - The list clearly shows attended vs. unattended.

> 💡 **Multi-language Support**  
> The reservation page supports 5 languages (Japanese, English, Korean, Simplified Chinese, Traditional Chinese).  
> It automatically displays according to visitors' browser settings.

### 📊 Editing Scene Charts
Set which characters appear in each scene.

1. On the script detail page, select the **"Scene Chart"** tab.
2. Click on each scene row to toggle character appearance:
   - Click **・** (not appearing) → changes to **○** (manual appearance)
   - Click **○** (manual appearance) → changes to **・** (not appearing)
   - **●** (dialogue-based appearance) cannot be clicked (auto-generated from script)

#### Adding Custom Characters
Add characters that don't exist in the script.

1. Click the **"+ Add Character"** button at the top of the scene chart.
2. Enter the character name and add.
3. Custom characters are distinguished by italic, orange-colored headers.
4. Unnecessary custom characters can be removed with the delete button.

#### Adding Custom Scenes
Add scenes that don't exist in the script.

1. Click the **"+ Add Scene"** button at the bottom of the scene chart.
2. Enter the scene heading, act number, and scene number.
3. Custom scenes are distinguished by an orange background.
4. Unnecessary custom scenes can be removed with the delete button.

#### Editing Scenes
Change scene headings and numbers.

1. Click the **pencil icon** at the left of a scene row.
2. Edit the scene heading, act number, and scene number in the modal.

### 🔄 Resetting Scripts
Delete existing script data while keeping custom data.

1. Select **"Reset Script"** from the script menu.
2. A confirmation dialog will appear.
3. Resetting deletes script-derived characters, scenes, and mappings.
4. Manually added custom characters, scenes, and manual mappings are preserved.

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

## 6. Owner Manual

Features for those managing the entire project.

### 🚀 Creating a Project
Create a new production or shooting project.

1. Click **"Create New Project"** on the Dashboard.
2. Enter the project name (production title, etc.).
3. Enter a description (optional) and click **"Create"**.

> 💡 **Using Projects Without Scripts**
> Projects can be used without uploading a script. You can manually add custom characters and scenes to freely configure the scene chart.

### 📥 Importing Scripts
Create a new project based on a public script.

1. Open the **"Public Scripts"** page.
2. Click the **"Import"** button on the script you want to use.
3. Enter a new project name to create.
   - Imported scripts are saved as **"Private"** (copy) in your project.
   - You can benefit from the limit exclusion by setting it to Public again.

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

#### 🤖 Inviting the Discord Bot (First Time Only)
To send attendance confirmation messages with buttons, you need to invite the Discord Bot to your server.

> ⚠️ **This operation requires Discord server administrator permission.**

1. Access the following URL:
   
   👉 **[Invite Discord Bot](https://discord.com/oauth2/authorize?client_id=1447907388337422398&permissions=2048&scope=bot)**
2. Select the Discord server to invite the bot to.
3. Click **"Authorize"**.
4. Confirm that the Bot has joined the server.

> 💡 **Required Permission**: Only "Send Messages" is needed.

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

## 7. Feature Permissions Table

| Feature | 👑 Owner | ✏️ Editor | 👀 Viewer |
| :--- | :---: | :---: | :---: |
| **Create/Delete Projects** | ☑ | - | - |
| **Invite Members/Change Permissions** | ☑ | - | - |
| **Discord Notification Settings** | ☑ | - | - |
| **Upload/Edit Scripts** | ☑ | ☑ | - |
| **Create/Edit Schedules** | ☑ | ☑ | - |
| **Milestone Management** | ☑ | ☑ | - |
| **Ticket Reservation Management** | ☑ | ☑ | - |
| **Edit Scene Charts** | ☑ | ☑ | - |
| **Add Custom Characters/Scenes** | ☑ | ☑ | - |
| **Reset Script** | ☑ | ☑ | - |
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
