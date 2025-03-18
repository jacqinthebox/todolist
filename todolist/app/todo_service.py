import uuid
from typing import Dict, List, Optional, Any

from .backends.base import TodoBackend, TodoItem


class TodoService:
    def __init__(self, backend: TodoBackend):
        self.backend = backend
        self.backend.initialize()

    def add_task(self, title: str, completed: bool = False) -> TodoItem:
        """Add a new task to the todo list."""
        item = TodoItem(id=str(uuid.uuid4()), title=title, completed=completed)
        return self.backend.add_item(item)

    def get_task(self, task_id: str) -> Optional[TodoItem]:
        """Get a task by ID."""
        return self.backend.get_item(task_id)

    def get_all_tasks(self) -> List[TodoItem]:
        """Get all tasks in the todo list."""
        return self.backend.get_all_items()

    def update_task(self, task_id: str, title: Optional[str] = None, completed: Optional[bool] = None) -> Optional[TodoItem]:
        """Update an existing task."""
        item = self.backend.get_item(task_id)
        if not item:
            return None
            
        if title is not None:
            item.title = title
        if completed is not None:
            item.completed = completed
            
        return self.backend.update_item(item)

    def toggle_task(self, task_id: str) -> Optional[TodoItem]:
        """Toggle the completed status of a task."""
        item = self.backend.get_item(task_id)
        if not item:
            return None
            
        item.completed = not item.completed
        return self.backend.update_item(item)

    def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID."""
        return self.backend.delete_item(task_id)