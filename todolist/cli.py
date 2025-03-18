#!/usr/bin/env python3
import argparse
import os
import sys
import json
from datetime import datetime

from .app.backends.base import TodoItem
from .app.backends.sqlite import SQLiteTodoBackend
from .app.todo_service import TodoService


def print_task(task):
    """Print a task with formatting."""
    status = "✓" if task.completed else "☐"
    print(f"{task.id}: [{status}] {task.title}")


def list_tasks(service):
    """List all tasks."""
    tasks = service.get_all_tasks()
    if not tasks:
        print("No tasks found.")
        return

    print("\nTasks:")
    print("------")
    for task in tasks:
        print_task(task)


def add_task(service, title):
    """Add a new task."""
    task = service.add_task(title=title)
    print(f"Task added: {task.id}")
    print_task(task)


def complete_task(service, task_id):
    """Mark a task as completed."""
    task = service.update_task(task_id=task_id, completed=True)
    if task:
        print(f"Task completed: {task.id}")
        print_task(task)
    else:
        print(f"Task not found: {task_id}")


def toggle_task(service, task_id):
    """Toggle a task's completion status."""
    task = service.toggle_task(task_id=task_id)
    if task:
        status = "completed" if task.completed else "incomplete"
        print(f"Task {task.id} marked as {status}")
        print_task(task)
    else:
        print(f"Task not found: {task_id}")


def delete_task(service, task_id):
    """Delete a task."""
    success = service.delete_task(task_id=task_id)
    if success:
        print(f"Task deleted: {task_id}")
    else:
        print(f"Task not found: {task_id}")


def main():
    parser = argparse.ArgumentParser(description="Todo List CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # List tasks
    list_parser = subparsers.add_parser("list", help="List all tasks")
    
    # Add task
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", help="Task title")
    
    # Complete task
    complete_parser = subparsers.add_parser("complete", help="Mark a task as completed")
    complete_parser.add_argument("task_id", help="Task ID")
    
    # Toggle task
    toggle_parser = subparsers.add_parser("toggle", help="Toggle a task's completion status")
    toggle_parser.add_argument("task_id", help="Task ID")
    
    # Delete task
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", help="Task ID")
    
    args = parser.parse_args()
    
    # Initialize SQLite backend with default path
    db_path = os.environ.get("SQLITE_DB_PATH", os.path.expanduser("~/.todolist.db"))
    backend = SQLiteTodoBackend(db_path=db_path)
    service = TodoService(backend=backend)
    
    if args.command == "list":
        list_tasks(service)
    elif args.command == "add":
        add_task(service, args.title)
    elif args.command == "complete":
        complete_task(service, args.task_id)
    elif args.command == "toggle":
        toggle_task(service, args.task_id)
    elif args.command == "delete":
        delete_task(service, args.task_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()