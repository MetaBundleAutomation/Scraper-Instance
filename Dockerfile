FROM python:3.9-slim

WORKDIR /app

COPY main.py .

# No additional dependencies needed for this simple script

CMD ["python", "main.py"]
