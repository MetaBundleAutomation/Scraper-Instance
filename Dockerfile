FROM python:3.9-alpine

WORKDIR /app

# Install curl for Docker API access and requests library
RUN apk --no-cache add curl

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Expose the FastAPI port for worker-manager communication
EXPOSE 8000

# Command to run the application
CMD ["python", "main.py"]
