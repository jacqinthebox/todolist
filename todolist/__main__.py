import uvicorn
import argparse
import os
import logging

from todolist.app.api import app
from todolist.app.logging_config import configure_logging


def main():
    parser = argparse.ArgumentParser(description="Todo List API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--backend", choices=["sqlite", "azure"], default="sqlite", 
                        help="Backend storage to use (sqlite or azure)")
    parser.add_argument("--db-path", help="Path to SQLite database file (for sqlite backend)")
    parser.add_argument("--azure-table", help="Azure Table name (for azure backend)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        default=None, help="Logging level")
    parser.add_argument("--log-to-file", action="store_true", help="Log to file instead of console")
    parser.add_argument("--log-file", help="Path to log file (when using --log-to-file)")
    
    args = parser.parse_args()
    
    # Set environment variables based on args
    os.environ["TODO_BACKEND"] = args.backend
    
    if args.backend == "sqlite" and args.db_path:
        os.environ["SQLITE_DB_PATH"] = args.db_path
        
    if args.backend == "azure" and args.azure_table:
        os.environ["AZURE_TABLE_NAME"] = args.azure_table
    
    # Configure logging
    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level
    
    if args.log_to_file:
        os.environ["LOG_TO_FILE"] = "true"
        
    if args.log_file:
        os.environ["LOG_FILE_PATH"] = args.log_file
    
    # Initialize logging
    logger = configure_logging()
    logger.info(f"Starting Todo List API with backend: {args.backend}")
    
    # Start the server
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()