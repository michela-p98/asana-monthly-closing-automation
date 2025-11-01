# 🚀 Asana Monthly Closing Automation

Automated Python scripts for managing recurring monthly closing processes in Asana. These tools eliminate repetitive manual work by automating task renaming, intelligent date shifting, and status resets.

## 📊 The Problem

Our finance team manages monthly closing processes in Asana with 250+ tasks that need to be:
- Renamed from one month to the next (e.g., "MC | 25 09" → "MC | 25 10")
- Rescheduled to maintain the same working day position in the following month
- Reset to "incomplete" status for the new cycle

Doing this manually took **2-3 hours per month** and was error-prone.

## 💡 The Solution

I developed three Python automation scripts that:
- Reduced processing time from **3 hours to 10/15 minutes** (90% time savings)
- Eliminated human error in date calculations
- Automated the entire monthly rollover process
- Handle both parent tasks and nested subtasks

### Key Features

✅ **Smart Date Shifting**: Maintains working day positions across months  
✅ **Bulk Operations**: Processes 250+ tasks in minutes  
✅ **Error Handling**: Robust timeout and connection management  
✅ **Preview Mode**: Shows changes before execution  
✅ **Subtask Support**: Recursively processes all nested subtasks  

## 🛠️ Technical Implementation

### Technologies Used
- **Python 3.7+**: Core programming language
- **Asana REST API**: For task management operations
- **requests**: HTTP library for API calls
- **datetime**: Date manipulation and working day calculations

### Architecture

The project consists of three independent scripts:

1. **rename_tasks.py**: Bulk renaming with pattern replacement
2. **shift_dates.py**: Intelligent date shifting algorithm
3. **mark_incomplete.py**: Status reset for new cycles

## 📋 Scripts Overview

### 1. Rename Tasks Script

Automatically renames all tasks and subtasks by updating month references.

**Example:**
```
Before: MC | 25 09 | HR | Payroll Costs
After:  MC | 25 10 | HR | Payroll Costs
```

**Features:**
- Pattern-based search and replace
- Recursive subtask processing
- Preview before execution
- Progress tracking

### 2. Shift Dates Script

Intelligently shifts dates while maintaining working day positions.

**Algorithm:**
1. Calculate which working day of the month each date represents
2. Find the corresponding working day in the next month
3. Update both `start_on` and `due_on` dates

**Example:**
```
October 1, 2025 (Wednesday - 1st working day)
  → November 3, 2025 (Monday - 1st working day)

October 24, 2025 (Friday - 17th working day)
  → November 20, 2025 (Thursday - 17th working day)
```

**Why This Matters:**
- Simple "+30 days" fails when months have different lengths
- Calendar date shifting ignores weekends and holidays
- Our approach maintains proportional positioning in the work cycle

### 3. Mark Incomplete Script

Resets completion status for all tasks and subtasks to prepare for the new month.

**Features:**
- Finds all completed tasks
- Recursively processes subtasks
- Bulk status update
- Confirmation prompts

## 🚀 Installation

### Prerequisites
```bash
Python 3.7 or higher
pip (Python package manager)
Asana account with API access
```

### Setup Instructions

### 🔒 .gitignore

To protect your credentials, make sure your `.gitignore` file includes:
.env
pycache/
*.pyc


1. **Clone the repository**
```bash
git clone https://github.com/yourusername/asana-monthly-closing-automation.git
cd asana-monthly-closing-automation
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Get your Asana API token**
   - Navigate to [Asana Developer Console](https://app.asana.com/0/my-apps)
   - Click "Create new token"
   - Give it a descriptive name (e.g., "Monthly Closing Automation")
   - Copy the generated token (you'll only see it once!)

4. **Configure environment variables**

Create a `.env` file in the project root:
```bash
ASANA_TOKEN=your_token_here
ASANA_PROJECT_ID=your_project_id
ASANA_WORKSPACE_ID=your_workspace_id
```

**Finding your IDs:**
- **Project ID**: Open project in Asana, check URL: `app.asana.com/0/PROJECT_ID/list`
- **Workspace ID**: Same from URL or use Asana API explorer

## 📖 Usage

### Script 1: Rename Tasks

```bash
python rename_tasks.py
```

**Output:**
```
============================================================
Script di rinominazione task Asana
MC | 25 09 → MC | 25 10
============================================================

📥 Recupero tutte le task del progetto...
✅ Trovate 264 task totali nel progetto

📥 Recupero tutte le subtask...
✅ Trovate 45 subtask totali

🎯 Trovate 235 task/subtask da aggiornare

Task/Subtask che verranno modificate:
------------------------------------------------------------
1. MC | 25 09 | Set up next Month Closing Project
2. MC | 25 09 | HR | Provide German employees' avg cost/hours
...

⚠️  Vuoi procedere con l'aggiornamento? (si/no): si

🚀 Inizio aggiornamento...
[1/235] Aggiornamento task...
  ✅ Successo!
...
```

### Script 2: Shift Dates

```bash
python shift_dates.py
```

**Output:**
```
============================================================
Script di spostamento date task Asana
Sposta le date al mese successivo (stesso giorno lavorativo)
============================================================

📋 Anteprima delle modifiche (prime 10 task/subtask):
------------------------------------------------------------
1. MC | 25 10 | Set up next Month Closing Project
   Due:   2025-10-24 (17° giorno lav.) → 2025-11-20

2. MC | 25 10 | HR | Provide German employees' avg cost/hours
   Due:   2025-10-03 (2° giorno lav.) → 2025-11-04
...
```

### Script 3: Mark as Incomplete

```bash
python mark_incomplete.py
```

**Output:**
```
============================================================
Script per marcare task come 'DA COMPLETARE'
============================================================

📊 Riepilogo:
   - Task principali completate: 215
   - Subtask completate: 38
   - TOTALE da marcare come 'da completare': 253
...
```

## 📁 Project Structure

```
asana-monthly-closing-automation/
├── README.md # Project documentation
├── requirements.txt # Python dependencies
├── .gitignore # Files to exclude from Git
├── LICENSE # MIT License
├── .env.example # Environment variables template
├── .env # (ignored) Your local environment variables
├── rename_tasks.py # Task renaming script
├── shift_dates.py # Date shifting script
└── mark_incomplete.py # Status reset script
```

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.


## ⚠️ Disclaimer

This project is not officially associated with or endorsed by Asana, Inc. Use at your own risk. Always test on non-production data first and maintain backups of important projects.

---

