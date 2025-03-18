# Todo List API

A simple Todo List API with multiple storage backend options (SQLite and Azure Table Storage).

## Features

- RESTful API for managing todo items
- Multiple backend storage options:
  - SQLite (default)
  - Azure Table Storage
- Simple web UI for local usage
- Command line interface
- Docker container support
- Kubernetes deployment configuration
- Virtual environment support

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/todolist.git
cd todolist

# Install the package
pip install -e .

# For Azure Table Storage support
pip install -e ".[azure]"
```

## Usage

### Quick Start with Virtual Environment

For convenience, you can use the provided script to set up a virtual environment and run the application:

```bash
# Make the script executable
chmod +x run_local.sh

# Run the application
./run_local.sh
```

### Running the Application Manually

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate

# Install the package
pip install -e .

# Using SQLite backend (default)
todolist

# Using SQLite with a custom database path
todolist --backend sqlite --db-path /path/to/todo.db

# Using Azure Table Storage backend
export AZURE_STORAGE_CONNECTION_STRING="your-connection-string"
todolist --backend azure --azure-table your-table-name
```

### Command Line Interface

The package also provides a simple CLI for managing your tasks locally:

```bash
# List all tasks
todo list

# Add a new task
todo add "Buy groceries"

# Complete a task
todo complete <task-id>

# Toggle task status
todo toggle <task-id>

# Delete a task
todo delete <task-id>
```

By default, the CLI uses a SQLite database stored at `~/.todolist.db`.

### Web Interface

When running the application locally, you can access a simple web UI by opening http://localhost:8000 in your browser. This interface provides a user-friendly way to manage your tasks.

## Running the Web App

### Locally

1. Using the convenience script (recommended):
```bash
# Make the script executable (if not already)
chmod +x run_local.sh

# Run the application
./run_local.sh
```

2. Manual setup:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install the package
pip install -e .

# Run the application
todolist --host 127.0.0.1 --port 8000
```

Either method will start the web app at http://localhost:8000

## Testing

### Running Tests

The project includes unit tests for all components. To run the tests:

```bash
# Make the script executable (if not already)
chmod +x run_tests.sh

# Run all tests with coverage
./run_tests.sh

# Run specific tests
./run_tests.sh tests/test_todo_service.py

# Run with specific pytest options
./run_tests.sh -k "test_add_task"
```

You can also run the tests manually:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install with test dependencies
pip install -e ".[test]"

# Run all tests
pytest

# Run with coverage report
pytest --cov=todolist tests/
```

### With Docker

1. Build the image:
```bash
docker build -t todolist:latest .
```

2. Run the container:
```bash
# Using SQLite backend (data won't persist after container stops)
docker run -p 8000:8000 todolist:latest

# With volume mount for data persistence
docker run -p 8000:8000 -v $(pwd)/data:/app/data \
  -e SQLITE_DB_PATH=/app/data/todo.db todolist:latest

# Using Azure Table Storage with connection string
docker run -p 8000:8000 \
  -e TODO_BACKEND=azure \
  -e AZURE_STORAGE_CONNECTION_STRING="your-connection-string" \
  -e AZURE_TABLE_NAME="todos" \
  todolist:latest
  
# Using Azure Table Storage with workload identity (for containerized apps with MSI)
# Note: This requires running in an environment with managed identity support
docker run -p 8000:8000 \
  -e TODO_BACKEND=azure \
  -e USE_WORKLOAD_IDENTITY=true \
  -e AZURE_STORAGE_ACCOUNT_NAME="yourstorageaccount" \
  -e AZURE_TABLE_NAME="todos" \
  todolist:latest
```

Access the web app at http://localhost:8000

### API Endpoints

- `GET /`: Web UI
- `GET /health`: Health check
- `GET /todos`: List all todo items
- `POST /todos`: Create a new todo item
- `GET /todos/{todo_id}`: Get a specific todo item
- `PATCH /todos/{todo_id}`: Update a todo item
- `POST /todos/{todo_id}/toggle`: Toggle the completion status of a todo item
- `DELETE /todos/{todo_id}`: Delete a todo item

## Docker

### Building the Docker Image

```bash
docker build -t todolist:latest .
```

### Running with Docker

```bash
# Using SQLite backend
docker run -p 8000:8000 todolist:latest

# Using Azure Table Storage backend
docker run -p 8000:8000 \
  -e TODO_BACKEND=azure \
  -e AZURE_STORAGE_CONNECTION_STRING="your-connection-string" \
  -e AZURE_TABLE_NAME="your-table-name" \
  todolist:latest
```

## Kubernetes Deployment

### Basic Deployment

```bash
# Apply the Kubernetes manifests
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

### Azure Table Storage with Connection String

For Azure Table Storage using a connection string:

```bash
# Create a Kubernetes secret for the connection string
kubectl create secret generic azure-storage-secret \
  --from-literal=connection-string="your-connection-string"
```

Then uncomment and configure the connection string section in `kubernetes/deployment.yaml`.

### Azure Table Storage with Workload Identity

For Azure Table Storage using workload identity in AKS:

1. Set up Azure Workload Identity on your AKS cluster (if not already done):

```bash
# Install the aks-preview extension
az extension add --name aks-preview

# Register the EnableWorkloadIdentityPreview feature flag
az feature register --namespace "Microsoft.ContainerService" --name "EnableWorkloadIdentityPreview"

# Wait for the feature to be registered
az feature show --namespace "Microsoft.ContainerService" --name "EnableWorkloadIdentityPreview"

# Refresh the registration
az provider register --namespace Microsoft.ContainerService

# Enable workload identity on your AKS cluster
az aks update -g myResourceGroup -n myAKSCluster --enable-workload-identity
```

2. Create an Azure managed identity and grant it access to your Azure Storage account:

```bash
# Create managed identity
az identity create --name todolist-identity --resource-group myResourceGroup

# Get the client ID and object ID of the managed identity
IDENTITY_CLIENT_ID=$(az identity show --name todolist-identity --resource-group myResourceGroup --query clientId -o tsv)
IDENTITY_OBJECT_ID=$(az identity show --name todolist-identity --resource-group myResourceGroup --query principalId -o tsv)

# Grant the managed identity access to your storage account
az role assignment create \
  --role "Storage Table Data Contributor" \
  --assignee-object-id $IDENTITY_OBJECT_ID \
  --scope "/subscriptions/your-subscription-id/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/yourstorageaccount"
```

3. Create a service account and establish the federated identity:

```bash
# Create the service account in your cluster
export AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)
export AZURE_CLIENT_ID=$IDENTITY_CLIENT_ID

# Apply the service account manifest with substituted values
envsubst < kubernetes/serviceaccount.yaml | kubectl apply -f -

# Establish the federated identity credential
az identity federated-credential create \
  --name todolist-federated-credential \
  --identity-name todolist-identity \
  --resource-group myResourceGroup \
  --issuer $(az aks show -g myResourceGroup -n myAKSCluster --query "oidcIssuerProfile.issuerUrl" -o tsv) \
  --subject system:serviceaccount:default:todolist-sa \
  --audience api://AzureADTokenExchange
```

4. Deploy the application with workload identity configuration:

```bash
# Update the deployment.yaml file with your storage account name
# Uncomment the Workload Identity section in deployment.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

## Logging

The application includes a comprehensive logging system that is especially useful when running in Kubernetes.

### Logging Configuration

- Logs are sent to stdout/stderr by default, making them accessible through `kubectl logs`
- All API operations, backend initialization, and error conditions are logged
- Log levels are configurable via environment variables or command line arguments

### Viewing Logs in Kubernetes

```bash
# Get logs from the pod
kubectl logs -f deployment/todolist

# Filter logs (using grep)
kubectl logs deployment/todolist | grep "ERROR"

# Tail logs
kubectl logs --tail=100 deployment/todolist
```

### Log Levels

- `DEBUG`: Detailed information, typically of interest only when diagnosing problems
- `INFO`: Confirmation that things are working as expected (default)
- `WARNING`: Indication that something unexpected happened, but the application still works
- `ERROR`: Due to a more serious problem, the application has not been able to perform some function
- `CRITICAL`: A serious error, indicating that the application itself may be unable to continue running

### Setting Log Level

When running with Docker:
```bash
docker run -p 8000:8000 -e LOG_LEVEL=DEBUG todolist:latest
```

When running in Kubernetes, edit the `deployment.yaml` file:
```yaml
env:
  - name: LOG_LEVEL
    value: "DEBUG"
```

When running locally:
```bash
todolist --log-level DEBUG
```

## Environment Variables

### Common Variables
- `TODO_BACKEND`: Storage backend to use (`sqlite` or `azure`)
- `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- `LOG_TO_FILE`: Set to "true" to log to a file instead of just console output
- `LOG_FILE_PATH`: Path to log file when `LOG_TO_FILE` is "true" (defaults to `/var/log/todolist/app.log`)

### SQLite Backend Variables
- `SQLITE_DB_PATH`: Path to SQLite database file (for sqlite backend)

### Azure Table Storage Variables

When using connection string authentication:
- `AZURE_STORAGE_CONNECTION_STRING`: Azure Storage account connection string

When using workload identity authentication:
- `USE_WORKLOAD_IDENTITY`: Set to "true" to use workload identity authentication
- `AZURE_STORAGE_ACCOUNT_NAME`: Name of the Azure Storage account
- `AZURE_STORAGE_ACCOUNT_URL`: Full URL to the Azure Storage account (alternative to account name)

Common Azure variables:
- `AZURE_TABLE_NAME`: Azure Table name (defaults to "todos")