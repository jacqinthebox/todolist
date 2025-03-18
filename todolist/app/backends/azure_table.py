import os
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .base import TodoBackend, TodoItem

# Import is conditional to avoid requiring azure-data-tables for SQLite-only users
try:
    from azure.data.tables import TableServiceClient, TableClient, UpdateMode
    from azure.core.credentials import TokenCredential
    from azure.identity import DefaultAzureCredential, ClientSecretCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


class AzureTableTodoBackend(TodoBackend):
    def __init__(
        self,
        connection_string: Optional[str] = None,
        table_name: str = "todos",
        account_name: Optional[str] = None,
        account_url: Optional[str] = None,
        use_workload_identity: bool = False
    ):
        if not AZURE_AVAILABLE:
            raise ImportError(
                "Azure Table Storage backend requires azure-data-tables and azure-identity packages. "
                "Install them with: pip install azure-data-tables azure-identity"
            )
            
        self.table_name = table_name or os.environ.get("AZURE_TABLE_NAME", "todos")
        self.account_name = account_name or os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
        self.account_url = account_url or os.environ.get("AZURE_STORAGE_ACCOUNT_URL")
        self.connection_string = connection_string or os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        self.use_workload_identity = use_workload_identity or os.environ.get("USE_WORKLOAD_IDENTITY", "false").lower() == "true"
        self.table_client = None
        
        # Validate required configuration
        if not self.use_workload_identity and not self.connection_string:
            # If not using workload identity, connection string is required
            if not self.connection_string:
                raise ValueError(
                    "When not using workload identity, Azure Storage connection string is required. "
                    "Provide it as a parameter or set AZURE_STORAGE_CONNECTION_STRING environment variable."
                )
        elif self.use_workload_identity and not self.account_url and not self.account_name:
            # If using workload identity, either account URL or account name is required
            raise ValueError(
                "When using workload identity, Azure Storage account URL or account name is required. "
                "Provide account_url/account_name parameter or set AZURE_STORAGE_ACCOUNT_URL/AZURE_STORAGE_ACCOUNT_NAME environment variable."
            )

    def initialize(self) -> None:
        """Initialize the Azure Table Storage."""
        if self.use_workload_identity:
            logging.info("Using workload identity for Azure Table Storage authentication")
            # Use DefaultAzureCredential which supports workload identity
            credential = DefaultAzureCredential()
            
            # Determine account URL if only account name was provided
            if self.account_url:
                account_url = self.account_url
            else:
                account_url = f"https://{self.account_name}.table.core.windows.net"
                
            # Create the table service client using managed identity
            table_service = TableServiceClient(endpoint=account_url, credential=credential)
        else:
            logging.info("Using connection string for Azure Table Storage authentication")
            # Use connection string authentication
            table_service = TableServiceClient.from_connection_string(self.connection_string)
        
        # Create table if it doesn't exist
        try:
            table_service.create_table(self.table_name)
        except Exception as e:
            # Table already exists or permissions issue
            logging.warning(f"Failed to create table {self.table_name}: {e}")
            pass
            
        self.table_client = table_service.get_table_client(self.table_name)

    def add_item(self, item: TodoItem) -> TodoItem:
        """Add a new todo item to Azure Table Storage."""
        if not item.id:
            item.id = str(uuid.uuid4())
            
        # In Azure Tables, PartitionKey and RowKey are required
        entity = {
            "PartitionKey": "todos",
            "RowKey": item.id,
            "title": item.title,
            "completed": item.completed,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat()
        }
        
        self.table_client.create_entity(entity)
        return item

    def get_item(self, item_id: str) -> Optional[TodoItem]:
        """Get a todo item by ID from Azure Table Storage."""
        try:
            entity = self.table_client.get_entity(partition_key="todos", row_key=item_id)
            return TodoItem.from_dict({
                "id": entity["RowKey"],
                "title": entity["title"],
                "completed": entity["completed"],
                "created_at": entity["created_at"],
                "updated_at": entity["updated_at"]
            })
        except Exception:
            return None

    def get_all_items(self) -> List[TodoItem]:
        """Get all todo items from Azure Table Storage."""
        entities = self.table_client.query_entities(query_filter="PartitionKey eq 'todos'")
        
        items = []
        for entity in entities:
            items.append(TodoItem.from_dict({
                "id": entity["RowKey"],
                "title": entity["title"],
                "completed": entity["completed"],
                "created_at": entity["created_at"],
                "updated_at": entity["updated_at"]
            }))
            
        return items

    def update_item(self, item: TodoItem) -> TodoItem:
        """Update an existing todo item in Azure Table Storage."""
        item.updated_at = datetime.now()
        
        entity = {
            "PartitionKey": "todos",
            "RowKey": item.id,
            "title": item.title,
            "completed": item.completed,
            "updated_at": item.updated_at.isoformat()
        }
        
        self.table_client.update_entity(entity=entity, mode=UpdateMode.MERGE)
        return item

    def delete_item(self, item_id: str) -> bool:
        """Delete a todo item by ID from Azure Table Storage."""
        try:
            self.table_client.delete_entity(partition_key="todos", row_key=item_id)
            return True
        except Exception:
            return False