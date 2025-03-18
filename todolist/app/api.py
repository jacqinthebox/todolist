import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .todo_service import TodoService
from .backends.base import TodoItem
from .backends.sqlite import SQLiteTodoBackend
from .backends.azure_table import AzureTableTodoBackend, AZURE_AVAILABLE
from .logging_config import configure_logging

# Configure logging
logger = configure_logging(app_name="todolist.api")


app = FastAPI(title="Todo List API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class TodoItemCreate(BaseModel):
    title: str
    completed: bool = False


class TodoItemUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None


class TodoItemResponse(BaseModel):
    id: str
    title: str
    completed: bool
    created_at: str
    updated_at: str


def get_todo_service() -> TodoService:
    """Dependency to get the appropriate TodoService based on configuration."""
    backend_type = os.environ.get("TODO_BACKEND", "sqlite").lower()
    
    logger.info(f"Initializing TodoService with backend: {backend_type}")
    
    if backend_type == "azure" and AZURE_AVAILABLE:
        use_workload_identity = os.environ.get("USE_WORKLOAD_IDENTITY", "false").lower() == "true"
        
        if use_workload_identity:
            # Use workload identity for authentication
            account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
            account_url = os.environ.get("AZURE_STORAGE_ACCOUNT_URL")
            table_name = os.environ.get("AZURE_TABLE_NAME", "todos")
            
            logger.info(f"Using Azure Table Storage with workload identity, account: {account_name}, table: {table_name}")
            
            backend = AzureTableTodoBackend(
                table_name=table_name,
                account_name=account_name,
                account_url=account_url,
                use_workload_identity=True
            )
        else:
            # Use connection string for authentication
            connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
            table_name = os.environ.get("AZURE_TABLE_NAME", "todos")
            
            if not connection_string:
                logger.error("AZURE_STORAGE_CONNECTION_STRING environment variable is missing")
                raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable is required when not using workload identity")
            
            logger.info(f"Using Azure Table Storage with connection string, table: {table_name}")    
            backend = AzureTableTodoBackend(connection_string=connection_string, table_name=table_name)
    else:
        db_path = os.environ.get("SQLITE_DB_PATH", "todo.db")
        logger.info(f"Using SQLite backend with database: {db_path}")
        backend = SQLiteTodoBackend(db_path=db_path)
    
    # Initialize the backend    
    try:
        service = TodoService(backend=backend)
        logger.info("TodoService initialization successful")
        return service
    except Exception as e:
        logger.error(f"Failed to initialize TodoService: {str(e)}")
        raise


@app.get("/")
def index():
    """Serve the main HTML page."""
    return FileResponse(static_dir / "index.html")

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "todo-list"}


@app.post("/todos", response_model=TodoItemResponse, status_code=201)
def create_todo(todo: TodoItemCreate, service: TodoService = Depends(get_todo_service)):
    logger.info(f"Creating new todo: {todo.title}")
    item = service.add_task(title=todo.title, completed=todo.completed)
    logger.debug(f"Created todo with ID: {item.id}")
    return item.to_dict()


@app.get("/todos", response_model=List[TodoItemResponse])
def get_todos(service: TodoService = Depends(get_todo_service)):
    logger.info("Getting all todos")
    items = service.get_all_tasks()
    logger.debug(f"Found {len(items)} todos")
    return [item.to_dict() for item in items]


@app.get("/todos/{todo_id}", response_model=TodoItemResponse)
def get_todo(todo_id: str, service: TodoService = Depends(get_todo_service)):
    logger.info(f"Getting todo with ID: {todo_id}")
    item = service.get_task(todo_id)
    if not item:
        logger.warning(f"Todo not found with ID: {todo_id}")
        raise HTTPException(status_code=404, detail="Todo not found")
    return item.to_dict()


@app.patch("/todos/{todo_id}", response_model=TodoItemResponse)
def update_todo(todo_id: str, todo: TodoItemUpdate, service: TodoService = Depends(get_todo_service)):
    logger.info(f"Updating todo with ID: {todo_id}")
    
    # Log what's being updated
    update_details = []
    if todo.title is not None:
        update_details.append(f"title='{todo.title}'")
    if todo.completed is not None:
        update_details.append(f"completed={todo.completed}")
    
    logger.debug(f"Update details: {', '.join(update_details)}")
    
    item = service.update_task(
        task_id=todo_id,
        title=todo.title,
        completed=todo.completed
    )
    if not item:
        logger.warning(f"Todo not found with ID: {todo_id}")
        raise HTTPException(status_code=404, detail="Todo not found")
    
    logger.debug(f"Todo updated successfully: {item.id}")
    return item.to_dict()


@app.post("/todos/{todo_id}/toggle", response_model=TodoItemResponse)
def toggle_todo(todo_id: str, service: TodoService = Depends(get_todo_service)):
    logger.info(f"Toggling todo with ID: {todo_id}")
    item = service.toggle_task(todo_id)
    if not item:
        logger.warning(f"Todo not found with ID: {todo_id}")
        raise HTTPException(status_code=404, detail="Todo not found")
    
    logger.debug(f"Toggled todo to completed={item.completed}")
    return item.to_dict()


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: str, service: TodoService = Depends(get_todo_service)):
    logger.info(f"Deleting todo with ID: {todo_id}")
    success = service.delete_task(todo_id)
    if not success:
        logger.warning(f"Todo not found with ID: {todo_id}")
        raise HTTPException(status_code=404, detail="Todo not found")
    
    logger.debug(f"Todo deleted successfully: {todo_id}")
    return None