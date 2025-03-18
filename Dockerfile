FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .
RUN pip install --no-cache-dir -e .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["todolist", "--host", "0.0.0.0", "--port", "8000"]