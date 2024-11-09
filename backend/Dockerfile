# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source code
COPY src /app/src

# Copy .env file
COPY .env /app/

# Expose the backend port (default: 8000 for FastAPI)
EXPOSE 8000

# Run the application with uvicorn
CMD ["python", "src/app.py", "--port", "8000"]
