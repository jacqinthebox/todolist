import os
import unittest
import tempfile
from datetime import datetime
from todolist.app.backends.base import TodoItem
from todolist.app.backends.sqlite import SQLiteTodoBackend


class TestSQLiteBackend(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for the SQLite database
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db_path = self.temp_db_file.name
        self.temp_db_file.close()
        
        # Initialize the SQLite backend with the temporary file
        self.backend = SQLiteTodoBackend(db_path=self.temp_db_path)
        self.backend.initialize()
    
    def tearDown(self):
        # Close the database connection
        if self.backend.conn:
            self.backend.conn.close()
        
        # Remove the temporary database file
        os.unlink(self.temp_db_path)
    
    def test_add_item(self):
        # Create a todo item
        item = TodoItem(
            id="test-id-1",
            title="Test Item",
            completed=False
        )
        
        # Add the item to the database
        added_item = self.backend.add_item(item)
        
        # Verify that the item was added
        self.assertEqual(added_item.id, "test-id-1")
        self.assertEqual(added_item.title, "Test Item")
        self.assertFalse(added_item.completed)
    
    def test_get_item(self):
        # Create and add a todo item
        item = TodoItem(
            id="test-id-2",
            title="Test Item 2",
            completed=True
        )
        self.backend.add_item(item)
        
        # Retrieve the item
        retrieved_item = self.backend.get_item("test-id-2")
        
        # Verify that the item was retrieved correctly
        self.assertIsNotNone(retrieved_item)
        self.assertEqual(retrieved_item.id, "test-id-2")
        self.assertEqual(retrieved_item.title, "Test Item 2")
        self.assertTrue(retrieved_item.completed)
    
    def test_get_nonexistent_item(self):
        # Try to retrieve an item that doesn't exist
        retrieved_item = self.backend.get_item("nonexistent-id")
        
        # Verify that the item is None
        self.assertIsNone(retrieved_item)
    
    def test_get_all_items(self):
        # Create and add multiple todo items
        item1 = TodoItem(id="test-id-3", title="Item 1", completed=False)
        item2 = TodoItem(id="test-id-4", title="Item 2", completed=True)
        item3 = TodoItem(id="test-id-5", title="Item 3", completed=False)
        
        self.backend.add_item(item1)
        self.backend.add_item(item2)
        self.backend.add_item(item3)
        
        # Retrieve all items
        items = self.backend.get_all_items()
        
        # Verify that all items were retrieved
        self.assertEqual(len(items), 3)
        
        # Verify that the items contain the expected data
        item_ids = [item.id for item in items]
        self.assertIn("test-id-3", item_ids)
        self.assertIn("test-id-4", item_ids)
        self.assertIn("test-id-5", item_ids)
    
    def test_update_item(self):
        # Create and add a todo item
        item = TodoItem(
            id="test-id-6",
            title="Original Title",
            completed=False
        )
        self.backend.add_item(item)
        
        # Update the item
        item.title = "Updated Title"
        item.completed = True
        updated_item = self.backend.update_item(item)
        
        # Verify that the item was updated
        self.assertEqual(updated_item.title, "Updated Title")
        self.assertTrue(updated_item.completed)
        
        # Retrieve the item and verify the update
        retrieved_item = self.backend.get_item("test-id-6")
        self.assertEqual(retrieved_item.title, "Updated Title")
        self.assertTrue(retrieved_item.completed)
    
    def test_delete_item(self):
        # Create and add a todo item
        item = TodoItem(
            id="test-id-7",
            title="Item to Delete",
            completed=False
        )
        self.backend.add_item(item)
        
        # Verify that the item exists
        self.assertIsNotNone(self.backend.get_item("test-id-7"))
        
        # Delete the item
        result = self.backend.delete_item("test-id-7")
        
        # Verify that the deletion was successful
        self.assertTrue(result)
        
        # Verify that the item no longer exists
        self.assertIsNone(self.backend.get_item("test-id-7"))
    
    def test_delete_nonexistent_item(self):
        # Try to delete an item that doesn't exist
        result = self.backend.delete_item("nonexistent-id")
        
        # Verify that the deletion was not successful
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()