import os
import tempfile
import unittest
from fastapi.testclient import TestClient

from todolist.app.api import app
from todolist.app.backends.sqlite import SQLiteTodoBackend
from todolist.app.todo_service import TodoService


class TestApi(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for the SQLite database
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db_path = self.temp_db_file.name
        self.temp_db_file.close()
        
        # Set environment variables for testing
        os.environ["TODO_BACKEND"] = "sqlite"
        os.environ["SQLITE_DB_PATH"] = self.temp_db_path
        
        # Create a test client
        self.client = TestClient(app)
    
    def tearDown(self):
        # Remove the temporary database file
        os.unlink(self.temp_db_path)
    
    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "todo-list"})
    
    def test_create_todo(self):
        # Create a new todo
        response = self.client.post(
            "/todos",
            json={"title": "Test Todo", "completed": False}
        )
        
        # Verify that the todo was created
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["title"], "Test Todo")
        self.assertFalse(data["completed"])
        self.assertIn("id", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        
        # Store the todo ID for later tests
        todo_id = data["id"]
        
        # Verify that the todo can be retrieved
        response = self.client.get(f"/todos/{todo_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "Test Todo")
    
    def test_get_todos(self):
        # Create a few todos
        self.client.post("/todos", json={"title": "Todo 1"})
        self.client.post("/todos", json={"title": "Todo 2"})
        self.client.post("/todos", json={"title": "Todo 3"})
        
        # Get all todos
        response = self.client.get("/todos")
        
        # Verify that all todos are returned
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 3)
    
    def test_get_todo(self):
        # Create a todo
        response = self.client.post(
            "/todos",
            json={"title": "Get This Todo", "completed": True}
        )
        todo_id = response.json()["id"]
        
        # Get the todo
        response = self.client.get(f"/todos/{todo_id}")
        
        # Verify that the todo is returned
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "Get This Todo")
        self.assertTrue(data["completed"])
    
    def test_get_nonexistent_todo(self):
        # Try to get a nonexistent todo
        response = self.client.get("/todos/nonexistent-id")
        
        # Verify that a 404 is returned
        self.assertEqual(response.status_code, 404)
    
    def test_update_todo(self):
        # Create a todo
        response = self.client.post(
            "/todos",
            json={"title": "Original Title", "completed": False}
        )
        todo_id = response.json()["id"]
        
        # Update the todo
        response = self.client.patch(
            f"/todos/{todo_id}",
            json={"title": "Updated Title", "completed": True}
        )
        
        # Verify that the todo was updated
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "Updated Title")
        self.assertTrue(data["completed"])
        
        # Get the todo and verify the update
        response = self.client.get(f"/todos/{todo_id}")
        data = response.json()
        self.assertEqual(data["title"], "Updated Title")
        self.assertTrue(data["completed"])
    
    def test_toggle_todo(self):
        # Create a todo
        response = self.client.post(
            "/todos",
            json={"title": "Toggle This Todo", "completed": False}
        )
        todo_id = response.json()["id"]
        
        # Toggle the todo
        response = self.client.post(f"/todos/{todo_id}/toggle")
        
        # Verify that the todo was toggled to completed
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["completed"])
        
        # Toggle the todo again
        response = self.client.post(f"/todos/{todo_id}/toggle")
        
        # Verify that the todo was toggled back to not completed
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["completed"])
    
    def test_delete_todo(self):
        # Create a todo
        response = self.client.post(
            "/todos",
            json={"title": "Delete This Todo"}
        )
        todo_id = response.json()["id"]
        
        # Delete the todo
        response = self.client.delete(f"/todos/{todo_id}")
        
        # Verify that the todo was deleted
        self.assertEqual(response.status_code, 204)
        
        # Try to get the deleted todo
        response = self.client.get(f"/todos/{todo_id}")
        
        # Verify that the todo no longer exists
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()