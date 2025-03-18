import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from todolist.app.backends.base import TodoItem
from todolist.app.backends.azure_table import AzureTableTodoBackend, AZURE_AVAILABLE


@unittest.skipIf(not AZURE_AVAILABLE, "Azure Table Storage packages not available")
class TestAzureTableBackend(unittest.TestCase):
    def setUp(self):
        # Create mock objects
        self.mock_table_client = MagicMock()
        self.mock_table_service = MagicMock()
        self.mock_table_service.get_table_client.return_value = self.mock_table_client
        
        # Create a sample TodoItem
        self.sample_item = TodoItem(
            id="test-id-1",
            title="Test Item",
            completed=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @patch('azure.data.tables.TableServiceClient.from_connection_string')
    def test_initialize_with_connection_string(self, mock_from_connection_string):
        # Configure the mock
        mock_from_connection_string.return_value = self.mock_table_service
        
        # Create the backend
        backend = AzureTableTodoBackend(
            connection_string="mock-connection-string",
            table_name="test-table"
        )
        
        # Initialize the backend
        backend.initialize()
        
        # Verify that the connection was established using connection string
        mock_from_connection_string.assert_called_once_with("mock-connection-string")
        
        # Verify that the table client was created
        self.mock_table_service.get_table_client.assert_called_once_with("test-table")
    
    @patch('azure.identity.DefaultAzureCredential')
    @patch('azure.data.tables.TableServiceClient')
    def test_initialize_with_workload_identity(self, mock_table_service_client, mock_default_credential):
        # Configure the mocks
        mock_default_credential.return_value = "mock-credential"
        mock_table_service_client.return_value = self.mock_table_service
        
        # Create the backend
        backend = AzureTableTodoBackend(
            account_url="https://mockaccount.table.core.windows.net",
            table_name="test-table",
            use_workload_identity=True
        )
        
        # Initialize the backend
        backend.initialize()
        
        # Verify that DefaultAzureCredential was used
        mock_default_credential.assert_called_once()
        
        # Verify that the TableServiceClient was created with the right parameters
        mock_table_service_client.assert_called_once_with(
            endpoint="https://mockaccount.table.core.windows.net",
            credential="mock-credential"
        )
        
        # Verify that the table client was created
        self.mock_table_service.get_table_client.assert_called_once_with("test-table")
    
    def test_add_item(self):
        # Set up the backend with mocks
        backend = AzureTableTodoBackend(connection_string="mock-connection-string")
        backend.table_client = self.mock_table_client
        
        # Add an item
        result = backend.add_item(self.sample_item)
        
        # Verify that create_entity was called with the correct data
        self.mock_table_client.create_entity.assert_called_once()
        args = self.mock_table_client.create_entity.call_args[0][0]
        self.assertEqual(args["PartitionKey"], "todos")
        self.assertEqual(args["RowKey"], self.sample_item.id)
        self.assertEqual(args["title"], self.sample_item.title)
        self.assertEqual(args["completed"], self.sample_item.completed)
        
        # Verify that the result is the same as the input item
        self.assertEqual(result, self.sample_item)
    
    def test_get_item(self):
        # Set up the backend with mocks
        backend = AzureTableTodoBackend(connection_string="mock-connection-string")
        backend.table_client = self.mock_table_client
        
        # Mock the get_entity response
        self.mock_table_client.get_entity.return_value = {
            "PartitionKey": "todos",
            "RowKey": self.sample_item.id,
            "title": self.sample_item.title,
            "completed": self.sample_item.completed,
            "created_at": self.sample_item.created_at.isoformat(),
            "updated_at": self.sample_item.updated_at.isoformat()
        }
        
        # Get the item
        result = backend.get_item(self.sample_item.id)
        
        # Verify that get_entity was called with the correct parameters
        self.mock_table_client.get_entity.assert_called_once_with(
            partition_key="todos",
            row_key=self.sample_item.id
        )
        
        # Verify that the result has the expected values
        self.assertEqual(result.id, self.sample_item.id)
        self.assertEqual(result.title, self.sample_item.title)
        self.assertEqual(result.completed, self.sample_item.completed)
    
    def test_get_nonexistent_item(self):
        # Set up the backend with mocks
        backend = AzureTableTodoBackend(connection_string="mock-connection-string")
        backend.table_client = self.mock_table_client
        
        # Mock get_entity to raise an exception (item not found)
        self.mock_table_client.get_entity.side_effect = Exception("Item not found")
        
        # Try to get a nonexistent item
        result = backend.get_item("nonexistent-id")
        
        # Verify that the result is None
        self.assertIsNone(result)
    
    def test_update_item(self):
        # Set up the backend with mocks
        backend = AzureTableTodoBackend(connection_string="mock-connection-string")
        backend.table_client = self.mock_table_client
        
        # Update an item
        updated_item = TodoItem(
            id=self.sample_item.id,
            title="Updated Title",
            completed=True,
            created_at=self.sample_item.created_at,
            updated_at=datetime.now()
        )
        
        # Call update_item
        result = backend.update_item(updated_item)
        
        # Verify that update_entity was called with the correct data
        self.mock_table_client.update_entity.assert_called_once()
        
        # Verify that the result has the updated values
        self.assertEqual(result.id, updated_item.id)
        self.assertEqual(result.title, "Updated Title")
        self.assertTrue(result.completed)
    
    def test_delete_item(self):
        # Set up the backend with mocks
        backend = AzureTableTodoBackend(connection_string="mock-connection-string")
        backend.table_client = self.mock_table_client
        
        # Delete an item
        result = backend.delete_item(self.sample_item.id)
        
        # Verify that delete_entity was called with the correct parameters
        self.mock_table_client.delete_entity.assert_called_once_with(
            partition_key="todos",
            row_key=self.sample_item.id
        )
        
        # Verify that the result is True
        self.assertTrue(result)
    
    def test_delete_nonexistent_item(self):
        # Set up the backend with mocks
        backend = AzureTableTodoBackend(connection_string="mock-connection-string")
        backend.table_client = self.mock_table_client
        
        # Mock delete_entity to raise an exception (item not found)
        self.mock_table_client.delete_entity.side_effect = Exception("Item not found")
        
        # Try to delete a nonexistent item
        result = backend.delete_item("nonexistent-id")
        
        # Verify that the result is False
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()