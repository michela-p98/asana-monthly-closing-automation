"""
Asana Date Shifting Script
Intelligently shifts task dates to the next month while maintaining
the same working day position (Monday-Friday only)

Example: 
    October 1 (1st working day) → November 3 (1st working day)
    October 24 (17th working day) → November 20 (17th working day)

Author: Finance Automation
"""

import requests
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================
# CONFIGURATION
# Get these values from your .env file
# ============================================
ASANA_ACCESS_TOKEN = os.getenv('ASANA_TOKEN', 'YOUR_TOKEN_HERE')
PROJECT_ID = os.getenv('ASANA_PROJECT_ID', 'YOUR_PROJECT_ID')
WORKSPACE_ID = os.getenv('ASANA_WORKSPACE_ID', 'YOUR_WORKSPACE_ID')

# ============================================
# WORKING DAY CALCULATION FUNCTIONS
# ============================================

def is_weekday(date):
    """
    Check if a date is a working day (Monday-Friday)
    
    Args:
        date: datetime object
        
    Returns:
        bool: True if Monday-Friday, False if weekend
    """
    return date.weekday() < 5  # 0=Monday, 4=Friday


def get_working_day_number(date):
    """
    Calculate which working day of the month this date represents
    
    Args:
        date: datetime object
        
    Returns:
        int: Working day number (e.g., 1 for first working day)
        
    Example:
        October 1, 2025 (Wednesday) → 1 (first working day)
        October 6, 2025 (Monday) → 4 (fourth working day)
    """
    # Start from first day of the month
    first_day = date.replace(day=1)
    
    working_days = 0
    current = first_day
    
    # Count working days up to and including the target date
    while current <= date:
        if is_weekday(current):
            working_days += 1
        current += timedelta(days=1)
    
    return working_days


def get_nth_working_day_of_month(year, month, n):
    """
    Find the nth working day of a specific month
    
    Args:
        year: int
        month: int (1-12)
        n: int (which working day to find)
        
    Returns:
        datetime: The nth working day, or None if not found
        
    Example:
        get_nth_working_day_of_month(2025, 11, 1) → November 3, 2025
    """
    first_day = datetime(year, month, 1)
    working_days = 0
    current = first_day
    
    # Find the nth working day
    while working_days < n:
        if is_weekday(current):
            working_days += 1
            if working_days == n:
                return current
        current += timedelta(days=1)
        
        # Safety check: don't go beyond next month
        if current.month != month:
            return None
    
    return current


def shift_date_to_next_month(date):
    """
    Shift a date to the next month maintaining the same working day position
    
    Args:
        date: datetime object
        
    Returns:
        datetime: Shifted date in next month, or None if invalid
        
    Example:
        Input: October 1, 2025 (1st working day)
        Output: November 3, 2025 (1st working day)
    """
    if not date:
        return None
    
    # Calculate which working day this is
    working_day_num = get_working_day_number(date)
    
    # Calculate next month
    if date.month == 12:
        next_year = date.year + 1
        next_month = 1
    else:
        next_year = date.year
        next_month = date.month + 1
    
    # Find the same working day in next month
    new_date = get_nth_working_day_of_month(next_year, next_month, working_day_num)
    
    return new_date


# ============================================
# API FUNCTIONS
# ============================================

def get_all_tasks(project_id):
    """
    Retrieve all tasks from an Asana project with date information
    
    Args:
        project_id (str): The Asana project GID
        
    Returns:
        list: List of tasks with name, gid, due_on, start_on
    """
    url = "https://app.asana.com/api/1.0/tasks"
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}",
        "Accept": "application/json"
    }
    params = {
        "project": project_id,
        "opt_fields": "name,gid,due_on,start_on"
    }
    
    all_tasks = []
    
    while True:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"Error retrieving tasks: {response.status_code}")
                print(response.text)
                break
            
            data = response.json()
            all_tasks.extend(data.get('data', []))
            
            # Handle pagination
            next_page = data.get('next_page')
            if next_page and next_page.get('uri'):
                url = next_page['uri']
                params = {}
            else:
                break
            
            time.sleep(0.2)
            
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            break
    
    return all_tasks


def get_subtasks(task_id):
    """
    Retrieve all subtasks for a specific task with date information
    
    Args:
        task_id (str): The parent task GID
        
    Returns:
        list: List of subtasks with name, gid, due_on, start_on
    """
    url = f"https://app.asana.com/api/1.0/tasks/{task_id}/subtasks"
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}",
        "Accept": "application/json"
    }
    params = {
        "opt_fields": "name,gid,due_on,start_on"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        return data.get('data', [])
        
    except requests.exceptions.Timeout:
        print(f"  ⚠️ Timeout for task {task_id}, skipping...")
        return []
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️ Error for task {task_id}: {e}")
        return []


def update_task_dates(task_id, new_due_date=None, new_start_date=None):
    """
    Update the dates of a task
    
    Args:
        task_id (str): The task GID to update
        new_due_date (datetime): New due date (optional)
        new_start_date (datetime): New start date (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"https://app.asana.com/api/1.0/tasks/{task_id}"
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    data = {"data": {}}
    
    if new_due_date:
        data["data"]["due_on"] = new_due_date.strftime("%Y-%m-%d")
    
    if new_start_date:
        data["data"]["start_on"] = new_start_date.strftime("%Y-%m-%d")
    
    try:
        response = requests.put(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            return True
        else:
            print(f"Error updating task {task_id}: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error updating task {task_id}: {e}")
        return False


# ============================================
# MAIN FUNCTION
# ============================================

def main():
    """Main execution function"""
    print("=" * 70)
    print("Asana Date Shifting Script")
    print("Shifts dates to next month (same working day position)")
    print("=" * 70)
    print()
    
    # 1. Retrieve all tasks
    print("📥 Retrieving all tasks from project...")
    all_tasks = get_all_tasks(PROJECT_ID)
    print(f"✅ Found {len(all_tasks)} total tasks in project")
    print()
    
    # 2. Retrieve all subtasks
    print("📥 Retrieving all subtasks...")
    print("   (This may take a few minutes...)")
    all_subtasks = []
    for i, task in enumerate(all_tasks, 1):
        if i % 10 == 0:
            print(f"   Processed {i}/{len(all_tasks)} tasks...")
        subtasks = get_subtasks(task['gid'])
        all_subtasks.extend(subtasks)
        time.sleep(0.15)
    
    print(f"✅ Found {len(all_subtasks)} total subtasks")
    print()
    
    # 3. Combine tasks and subtasks
    all_items = all_tasks + all_subtasks
    
    # 4. Filter items with dates to update
    items_to_update = []
    for item in all_items:
        if item.get('due_on') or item.get('start_on'):
            items_to_update.append(item)
    
    print(f"🎯 Found {len(items_to_update)} tasks/subtasks with dates to update")
    print()
    
    if len(items_to_update) == 0:
        print("✅ No tasks/subtasks with dates to update!")
        return
    
    # 5. Calculate new dates and show preview
    print("📋 Preview of changes (first 10 tasks/subtasks):")
    print("-" * 70)
    
    updates = []
    for item in items_to_update:
        task_update = {
            'gid': item['gid'],
            'name': item['name'],
            'old_due': item.get('due_on'),
            'old_start': item.get('start_on'),
            'new_due': None,
            'new_start': None
        }
        
        # Calculate new due_date
        if item.get('due_on'):
            old_due = datetime.strptime(item['due_on'], "%Y-%m-%d")
            new_due = shift_date_to_next_month(old_due)
            task_update['new_due'] = new_due
        
        # Calculate new start_date
        if item.get('start_on'):
            old_start = datetime.strptime(item['start_on'], "%Y-%m-%d")
            new_start = shift_date_to_next_month(old_start)
            task_update['new_start'] = new_start
        
        updates.append(task_update)
    
    # Show first 10
    for i, update in enumerate(updates[:10], 1):
        print(f"{i}. {update['name'][:60]}")
        if update['old_start']:
            old_start = datetime.strptime(update['old_start'], "%Y-%m-%d")
            wd_num = get_working_day_number(old_start)
            new_date_str = update['new_start'].strftime('%Y-%m-%d') if update['new_start'] else 'N/A'
            print(f"   Start: {update['old_start']} ({wd_num}° working day) → {new_date_str}")
        if update['old_due']:
            old_due = datetime.strptime(update['old_due'], "%Y-%m-%d")
            wd_num = get_working_day_number(old_due)
            new_date_str = update['new_due'].strftime('%Y-%m-%d') if update['new_due'] else 'N/A'
            print(f"   Due:   {update['old_due']} ({wd_num}° working day) → {new_date_str}")
        print()
    
    if len(updates) > 10:
        print(f"... and {len(updates) - 10} more tasks/subtasks")
    print("-" * 70)
    print()
    
    # 6. Ask for confirmation
    confirm = input("⚠️  Do you want to proceed with the date updates? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("❌ Operation cancelled")
        return
    
    print()
    print("🚀 Starting update...")
    print()
    
    # 7. Update tasks/subtasks
    success_count = 0
    fail_count = 0
    
    for i, update in enumerate(updates, 1):
        print(f"[{i}/{len(updates)}] Updating: {update['name'][:50]}...")
        
        if update_task_dates(update['gid'], update['new_due'], update['new_start']):
            success_count += 1
            print(f"  ✅ Success!")
        else:
            fail_count += 1
            print(f"  ❌ Error!")
        
        print()
        time.sleep(0.5)
    
    # 8. Final summary
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"✅ Successfully updated: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"📊 Total processed: {len(updates)}")
    print()
    print("🎉 Operation completed!")


# ============================================
# SCRIPT EXECUTION
# ============================================
if __name__ == "__main__":
    # Verify configuration
    if ASANA_ACCESS_TOKEN == "YOUR_TOKEN_HERE":
        print("⚠️  ERROR: Configuration required!")
        print()
        print("Please set up your environment:")
        print("1. Create a .env file in the project directory")
        print("2. Add your Asana credentials (see .env.example)")
        print("3. Get your token from: https://app.asana.com/0/my-apps")
        print()
    else:
        main()
