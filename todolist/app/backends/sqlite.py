import os
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from .base import TodoBackend, TodoItem


class SQLiteTodoBackend(TodoBackend):
    def __init__(self, db_path: str = "todo.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def initialize(self) -> None:
        """Initialize the SQLite database."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Create todos table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def add_item(self, item: TodoItem) -> TodoItem:
        """Add a new todo item to the SQLite database."""
        if not item.id:
            item.id = str(uuid.uuid4())
        
        self.cursor.execute('''
            INSERT INTO todos (id, title, completed, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            item.id,
            item.title,
            1 if item.completed else 0,
            item.created_at.isoformat(),
            item.updated_at.isoformat()
        ))
        self.conn.commit()
        return item

    def get_item(self, item_id: str) -> Optional[TodoItem]:
        """Get a todo item by ID from the SQLite database."""
        self.cursor.execute('SELECT * FROM todos WHERE id = ?', (item_id,))
        row = self.cursor.fetchone()
        
        if not row:
            return None
            
        return TodoItem.from_dict({
            "id": row["id"],
            "title": row["title"],
            "completed": bool(row["completed"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        })

    def get_all_items(self) -> List[TodoItem]:
        """Get all todo items from the SQLite database."""
        self.cursor.execute('SELECT * FROM todos ORDER BY created_at DESC')
        rows = self.cursor.fetchall()
        
        items = []
        for row in rows:
            items.append(TodoItem.from_dict({
                "id": row["id"],
                "title": row["title"],
                "completed": bool(row["completed"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }))
            
        return items

    def update_item(self, item: TodoItem) -> TodoItem:
        """Update an existing todo item in the SQLite database."""
        item.updated_at = datetime.now()
        
        self.cursor.execute('''
            UPDATE todos
            SET title = ?, completed = ?, updated_at = ?
            WHERE id = ?
        ''', (
            item.title,
            1 if item.completed else 0,
            item.updated_at.isoformat(),
            item.id
        ))
        self.conn.commit()
        return item

    def delete_item(self, item_id: str) -> bool:
        """Delete a todo item by ID from the SQLite database."""
        self.cursor.execute('DELETE FROM todos WHERE id = ?', (item_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0