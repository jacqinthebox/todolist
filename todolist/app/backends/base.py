from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any


class TodoItem:
    def __init__(
        self,
        id: str,
        title: str,
        completed: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.title = title
        self.completed = completed
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TodoItem":
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


class TodoBackend(ABC):
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the backend storage."""
        pass

    @abstractmethod
    def add_item(self, item: TodoItem) -> TodoItem:
        """Add a new todo item."""
        pass

    @abstractmethod
    def get_item(self, item_id: str) -> Optional[TodoItem]:
        """Get a todo item by ID."""
        pass

    @abstractmethod
    def get_all_items(self) -> List[TodoItem]:
        """Get all todo items."""
        pass

    @abstractmethod
    def update_item(self, item: TodoItem) -> TodoItem:
        """Update an existing todo item."""
        pass

    @abstractmethod
    def delete_item(self, item_id: str) -> bool:
        """Delete a todo item by ID."""
        pass