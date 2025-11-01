"""
Asana Task Renaming Script
Automatically renames tasks and subtasks by updating month references

Example: "MC | 25 09 | Task Name" becomes "MC | 25 10 | Task Name"

Author: Finance Automation
"""

import requests
import time
import os
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

# What to search for and replace
OLD_PATTERN = "MC | 25 09"  # Change this to match your naming pattern
NEW_PATTERN = "MC | 25 10"  # Change this to your new pattern

# ============================================
# API FUNCTIONS
# ============================================

def get_all_tasks(project_id):
    """
    Retrieve all tasks from an Asana project
    
    Args:
        project_id (str): The Asana project GID
        
    Returns:
        list: List of tasks with name and gid
    """
    url = "https://app.asana.com/api/1.0/tasks"
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}",
        "Accept": "application/json"
    }
    params = {
        "project": project_id,
        "opt_fields": "name,gid"
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
            
            time.sleep(0.2)  # Prevent rate limiting
            
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            break
    
    return all_tasks


def get_subtasks(task_id):
    """
    Retrieve all subtasks for a specific task
    
    Args:
        task_id (str): The parent task GID
        
    Returns:
        list: List of subtasks with name and gid
    """
    url = f"https://app.asana.com/api/1.0/tasks/{task_id}/subtasks"
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}",
        "Accept": "application/json"
    }
    params = {
        "opt_fields": "name,gid"
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


def update_task_name(task_id, new_name):
    """
    Update the name of a task
    
    Args:
        task_id (str): The task GID to update
        new_name (str): The new name for the task
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"https://app.asana.com/api/1.0/tasks/{task_id}"
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {
        "data": {
            "name": new_name
        }
    }
    
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
    print("=" * 60)
    print("Asana Task Renaming Script")
    print(f"{OLD_PATTERN} → {NEW_PATTERN}")
    print("=" * 60)
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
        if i % 10 == 0:  # Show progress every 10 tasks
            print(f"   Processed {i}/{len(all_tasks)} tasks...")
        subtasks = get_subtasks(task['gid'])
        all_subtasks.extend(subtasks)
        time.sleep(0.15)  # Prevent rate limiting
    
    print(f"✅ Found {len(all_subtasks)} total subtasks")
    print()
    
    # 3. Combine tasks and subtasks
    all_items = all_tasks + all_subtasks
    
    # 4. Filter items containing the old pattern
    items_to_update = []
    for item in all_items:
        if OLD_PATTERN in item['name']:
            items_to_update.append(item)
    
    print(f"🎯 Found {len(items_to_update)} tasks/subtasks to update")
    print()
    
    if len(items_to_update) == 0:
        print("✅ No tasks to update!")
        return
    
    # 5. Show preview
    print("Tasks/Subtasks to be modified:")
    print("-" * 60)
    for i, item in enumerate(items_to_update[:10], 1):  # Show first 10
        print(f"{i}. {item['name']}")
    if len(items_to_update) > 10:
        print(f"... and {len(items_to_update) - 10} more tasks/subtasks")
    print("-" * 60)
    print()
    
    # 6. Ask for confirmation
    confirm = input("⚠️  Do you want to proceed with the update? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("❌ Operation cancelled")
        return
    
    print()
    print("🚀 Starting update...")
    print()
    
    # 7. Update tasks/subtasks
    success_count = 0
    fail_count = 0
    
    for i, item in enumerate(items_to_update, 1):
        old_name = item['name']
        new_name = old_name.replace(OLD_PATTERN, NEW_PATTERN)
        
        print(f"[{i}/{len(items_to_update)}] Updating task...")
        print(f"  From: {old_name}")
        print(f"  To:   {new_name}")
        
        if update_task_name(item['gid'], new_name):
            success_count += 1
            print(f"  ✅ Success!")
        else:
            fail_count += 1
            print(f"  ❌ Error!")
        
        print()
        time.sleep(0.5)  # Prevent rate limiting
    
    # 8. Final summary
    print("=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully updated: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"📊 Total processed: {len(items_to_update)}")
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
