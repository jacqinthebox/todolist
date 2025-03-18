import os
import unittest
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch

from todolist.app.backends.base import TodoItem
from todolist.app.backends.sqlite import SQLiteTodoBackend
from todolist.app.todo_service import TodoService


class TestTodoService(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for the SQLite database
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db_path = self.temp_db_file.name
        self.temp_db_file.close()
        
        # Initialize the SQLite backend with the temporary file
        self.backend = SQLiteTodoBackend(db_path=self.temp_db_path)
        self.service = TodoService(backend=self.backend)
    
    def tearDown(self):
        # Remove the temporary database file
        os.unlink(self.temp_db_path)
    
    def test_add_task(self):
        # Add a task
        task = self.service.add_task(title="Test Task")
        
        # Verify that the task was added
        self.assertIsNotNone(task)
        self.assertEqual(task.title, "Test Task")
        self.assertFalse(task.completed)
        self.assertIsNotNone(task.id)
        
        # Verify that the task can be retrieved
        retrieved_task = self.service.get_task(task.id)
        self.assertIsNotNone(retrieved_task)
        self.assertEqual(retrieved_task.title, "Test Task")
    
    def test_add_completed_task(self):
        # Add a completed task
        task = self.service.add_task(title="Completed Task", completed=True)
        
        # Verify that the task was added with completed=True
        self.assertTrue(task.completed)
        
        # Verify that the task can be retrieved with completed=True
        retrieved_task = self.service.get_task(task.id)
        self.assertTrue(retrieved_task.completed)
    
    def test_get_all_tasks(self):
        # Add multiple tasks
        task1 = self.service.add_task(title="Task 1")
        task2 = self.service.add_task(title="Task 2")
        task3 = self.service.add_task(title="Task 3")
        
        # Get all tasks
        tasks = self.service.get_all_tasks()
        
        # Verify that all tasks are returned
        self.assertEqual(len(tasks), 3)
        
        # Verify that the tasks are in the correct order (most recent first)
        task_ids = [task.id for task in tasks]
        self.assertIn(task1.id, task_ids)
        self.assertIn(task2.id, task_ids)
        self.assertIn(task3.id, task_ids)
    
    def test_update_task(self):
        # Add a task
        task = self.service.add_task(title="Original Title")
        
        # Update the task title
        updated_task = self.service.update_task(task.id, title="Updated Title")
        
        # Verify that the title was updated
        self.assertEqual(updated_task.title, "Updated Title")
        
        # Verify that the task can be retrieved with the updated title
        retrieved_task = self.service.get_task(task.id)
        self.assertEqual(retrieved_task.title, "Updated Title")
    
    def test_update_task_completion(self):
        # Add a task
        task = self.service.add_task(title="Task", completed=False)
        
        # Update the task completion status
        updated_task = self.service.update_task(task.id, completed=True)
        
        # Verify that the completion status was updated
        self.assertTrue(updated_task.completed)
        
        # Verify that the task can be retrieved with the updated completion status
        retrieved_task = self.service.get_task(task.id)
        self.assertTrue(retrieved_task.completed)
    
    def test_toggle_task(self):
        # Add a task
        task = self.service.add_task(title="Task", completed=False)
        
        # Toggle the task completion status
        toggled_task = self.service.toggle_task(task.id)
        
        # Verify that the completion status was toggled to True
        self.assertTrue(toggled_task.completed)
        
        # Toggle the task completion status again
        toggled_task = self.service.toggle_task(task.id)
        
        # Verify that the completion status was toggled back to False
        self.assertFalse(toggled_task.completed)
    
    def test_delete_task(self):
        # Add a task
        task = self.service.add_task(title="Task to Delete")
        
        # Verify that the task exists
        self.assertIsNotNone(self.service.get_task(task.id))
        
        # Delete the task
        result = self.service.delete_task(task.id)
        
        # Verify that the deletion was successful
        self.assertTrue(result)
        
        # Verify that the task no longer exists
        self.assertIsNone(self.service.get_task(task.id))
    
    def test_delete_nonexistent_task(self):
        # Try to delete a task that doesn't exist
        result = self.service.delete_task("nonexistent-id")
        
        # Verify that the deletion was not successful
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()