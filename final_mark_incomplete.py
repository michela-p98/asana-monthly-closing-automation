"""
Asana Mark Incomplete Script
Marks all completed tasks and subtasks as incomplete to prepare
for a new monthly cycle

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

# ============================================
# API FUNCTIONS
# ============================================

def get_all_tasks(project_id):
    """
    Retrieve all tasks from an Asana project
    
    Args:
        project_id (str): The Asana project GID
        
    Returns:
        list: List of tasks with name, gid, completed status, and parent
    """
    url = "https://app.asana.com/api/1.0/tasks"
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}",
        "Accept": "application/json"
    }
    params = {
        "project": project_id,
        "opt_fields": "name,gid,completed,parent"
    }
    
    all_tasks = []
    
    while True:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Error retrieving tasks: {response.status_code}")
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
            print(f"❌ Error: {e}")
            break
    
    return all_tasks


def get_subtasks(task_id):
    """
    Retrieve all subtasks for a specific task
    
    Args:
        task_id (str): The parent task GID
        
    Returns:
        list: List of subtasks with name, gid, and completed status
    """
    url = f"https://app.asana.com/api/1.0/tasks/{task_id}/subtasks"
    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}",
        "Accept": "application/json"
    }
    params = {
        "opt_fields": "name,gid,completed"
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


def mark_task_incomplete(task_id):
    """
    Mark a task as incomplete (not completed)
    
    Args:
        task_id (str): The task GID to update
        
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
            "completed": False
        }
    }
    
    try:
        response = requests.put(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Error updating task {task_id}: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error updating task {task_id}: {e}")
        return False


# ============================================
# MAIN FUNCTION
# ============================================

def main():
    """Main execution function"""
    print("=" * 70)
    print("Asana Mark Incomplete Script")
    print("All tasks and subtasks will be marked as incomplete")
    print("=" * 70)
    print()
    
    # 1. Retrieve all tasks from project
    print("📥 Retrieving all tasks from project...")
    all_tasks = get_all_tasks(PROJECT_ID)
    print(f"✅ Found {len(all_tasks)} tasks in project")
    print()
    
    # 2. Identify completed tasks and their subtasks
    print("🔍 Analyzing completed tasks and subtasks...")
    tasks_to_uncomplete = []
    subtasks_found = []
    
    for i, task in enumerate(all_tasks, 1):
        # Add main task if completed
        if task.get('completed'):
            tasks_to_uncomplete.append({
                'gid': task['gid'],
                'name': task['name'],
                'is_subtask': task.get('parent') is not None,
                'type': 'subtask' if task.get('parent') else 'task'
            })
        
        # Retrieve subtasks (even if main task is not completed)
        if i % 20 == 0:
            print(f"  Processed {i}/{len(all_tasks)} tasks...")
            
        subtasks = get_subtasks(task['gid'])
        for subtask in subtasks:
            if subtask.get('completed'):
                subtasks_found.append({
                    'gid': subtask['gid'],
                    'name': subtask['name'],
                    'parent_name': task['name'],
                    'is_subtask': True,
                    'type': 'subtask'
                })
        time.sleep(0.1)
    
    # Merge tasks and subtasks
    all_items_to_uncomplete = tasks_to_uncomplete + subtasks_found
    
    print()
    print(f"📊 Summary:")
    print(f"   - Completed main tasks: {len([t for t in tasks_to_uncomplete if not t['is_subtask']])}")
    print(f"   - Completed subtasks: {len(subtasks_found)}")
    print(f"   - TOTAL to mark as incomplete: {len(all_items_to_uncomplete)}")
    print()
    
    if len(all_items_to_uncomplete) == 0:
        print("✅ No completed tasks found! Everything is already incomplete.")
        return
    
    # 3. Show preview
    print("📋 Preview of tasks to be marked as incomplete (first 15):")
    print("-" * 70)
    for i, item in enumerate(all_items_to_uncomplete[:15], 1):
        tipo = "📌 SUBTASK" if item['is_subtask'] else "📋 TASK"
        print(f"{i}. {tipo}: {item['name'][:55]}")
        if 'parent_name' in item:
            print(f"   └─ Under: {item['parent_name'][:50]}")
    
    if len(all_items_to_uncomplete) > 15:
        print(f"\n... and {len(all_items_to_uncomplete) - 15} more tasks/subtasks")
    print("-" * 70)
    print()
    
    # 4. Ask for confirmation
    print("⚠️  WARNING: This will mark all tasks as INCOMPLETE.")
    print("   All checkmarks will be removed!")
    print()
    confirm = input("Do you want to proceed? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("❌ Operation cancelled")
        return
    
    print()
    print("🚀 Starting operation...")
    print()
    
    # 5. Mark all as incomplete
    success_count = 0
    fail_count = 0
    
    for i, item in enumerate(all_items_to_uncomplete, 1):
        tipo = "SUBTASK" if item['is_subtask'] else "TASK"
        print(f"[{i}/{len(all_items_to_uncomplete)}] Marking {tipo} as incomplete...")
        print(f"  {item['name'][:60]}")
        
        if mark_task_incomplete(item['gid']):
            success_count += 1
            print(f"  ✅ Marked as incomplete!")
        else:
            fail_count += 1
            print(f"  ❌ Error!")
        
        print()
        time.sleep(0.5)
    
    # 6. Final summary
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"✅ Tasks marked as incomplete: {success_count}")
    print(f"❌ Errors: {fail_count}")
    print(f"📊 Total processed: {len(all_items_to_uncomplete)}")
    print()
    print("🎉 Operation completed!")
    print()
    print("💡 All tasks and subtasks are now marked as INCOMPLETE")


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
