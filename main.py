import os
import json
import time
import uuid
import socket
import requests
import logging
import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("scraper-instance")

# Get environment variables
MANAGER_URL = os.environ.get("MANAGER_URL", "http://scraper-manager:8000")
WORKER_ID = os.environ.get("HOSTNAME", socket.gethostname())
MAX_TASKS = int(os.environ.get("MAX_TASKS", "5"))  # Maximum number of concurrent tasks

# Task states
class TaskState:
    QUEUED = "queued"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"

# Task data models
class TaskRequest(BaseModel):
    task_id: str
    url: str
    depth: int = 2
    max_pages: int = 10
    
class TaskResult(BaseModel):
    task_id: str
    status: str
    result: Dict[str, Any]
    start_time: Optional[str] = None
    end_time: Optional[str] = None

# Create FastAPI app
app = FastAPI(title="Scraper Instance Worker")

# In-memory storage for tasks
tasks = {}
active_tasks_count = 0
registered_with_manager = False

@app.on_event("startup")
async def startup_event():
    """Register with manager on startup"""
    global registered_with_manager
    
    logger.info(f"Worker {WORKER_ID} starting up")
    logger.info(f"Connecting to manager at {MANAGER_URL}")
    
    # Try to register with the manager
    for _ in range(5):  # Retry 5 times
        try:
            response = requests.post(
                f"{MANAGER_URL}/worker/register",
                json={"worker_id": WORKER_ID, "max_tasks": MAX_TASKS}
            )
            if response.status_code == 200:
                registered_with_manager = True
                logger.info(f"Successfully registered with manager")
                # Send initial hello message
                hello_response = requests.post(
                    f"{MANAGER_URL}/container/hello",
                    json={
                        "container_id": WORKER_ID,
                        "message": f"Hello World! I'm worker {WORKER_ID}, ready to process tasks."
                    }
                )
                if hello_response.status_code == 200:
                    logger.info("Hello message sent successfully")
                break
            else:
                logger.warning(f"Failed to register with manager: {response.status_code}")
        except Exception as e:
            logger.error(f"Error registering with manager: {e}")
        time.sleep(2)
    
    if not registered_with_manager:
        logger.error("Failed to register with manager after multiple attempts")

@app.get("/")
async def root():
    """Basic health check endpoint"""
    return {
        "status": "alive",
        "worker_id": WORKER_ID,
        "tasks_count": len(tasks),
        "active_tasks": active_tasks_count,
        "registered": registered_with_manager
    }

@app.get("/tasks")
async def get_tasks():
    """Get list of all tasks and their status"""
    return {"tasks": tasks}

@app.post("/task")
async def add_task(task: TaskRequest):
    """Add a new task to the worker queue"""
    global active_tasks_count
    
    # Check if we're already at capacity
    if active_tasks_count >= MAX_TASKS:
        raise HTTPException(status_code=503, detail="Worker at maximum capacity")
    
    # Store the task
    tasks[task.task_id] = {
        "status": TaskState.QUEUED,
        "data": task.dict(),
        "result": None,
        "queued_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Start processing the task in the background (this would normally be a thread or task queue)
    # For now, we'll just process it directly
    active_tasks_count += 1
    try:
        process_task(task.task_id)
    finally:
        active_tasks_count -= 1
    
    return {"status": "accepted", "task_id": task.task_id}

@app.get("/task/{task_id}")
async def get_task(task_id: str):
    """Get the status and result of a specific task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return tasks[task_id]

def process_task(task_id: str):
    """Process a scraping task"""
    if task_id not in tasks:
        logger.error(f"Task {task_id} not found")
        return
    
    # Update task status
    tasks[task_id]["status"] = TaskState.RUNNING
    tasks[task_id]["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Simulate scraping work
        logger.info(f"Processing task {task_id}")
        task_data = tasks[task_id]["data"]
        
        # Simulate some work
        time.sleep(2)
        
        # Generate a result
        result = {
            "pages_scraped": task_data["max_pages"],
            "depth_reached": task_data["depth"],
            "url": task_data["url"],
            "data": {"example": "This is simulated scraped data"}
        }
        
        # Update task with success
        tasks[task_id]["status"] = TaskState.COMPLETED
        tasks[task_id]["result"] = result
        tasks[task_id]["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Report completion to manager
        try:
            requests.post(
                f"{MANAGER_URL}/container/complete",
                json={
                    "container_id": WORKER_ID,
                    "task_id": task_id,
                    "status": "success",
                    "result": result
                }
            )
            logger.info(f"Task {task_id} completed successfully and reported to manager")
        except Exception as e:
            logger.error(f"Error reporting task completion to manager: {e}")
    
    except Exception as e:
        logger.exception(f"Error processing task {task_id}: {e}")
        tasks[task_id]["status"] = TaskState.FAILED
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Report failure to manager
        try:
            requests.post(
                f"{MANAGER_URL}/container/complete",
                json={
                    "container_id": WORKER_ID,
                    "task_id": task_id,
                    "status": "error",
                    "result": {"error": str(e)}
                }
            )
            logger.info(f"Task {task_id} failure reported to manager")
        except Exception as report_error:
            logger.error(f"Error reporting task failure to manager: {report_error}")

if __name__ == "__main__":
    # Start the FastAPI server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")
