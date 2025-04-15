import os
import json
import time
import sys

def main():
    # Log that the instance is alive
    print("I'm alive!")
    
    # Get environment variables passed from manager
    manager_id = os.environ.get("MANAGER_ID", "unknown_manager")
    spawn_time = os.environ.get("SPAWN_TIME", "unknown_time")
    container_id = os.environ.get("HOSTNAME", "unknown_container")
    
    # Create response message
    message = {
        "message": f"Hello World! I'm {container_id}, son of {manager_id}, spawned at {spawn_time}."
    }
    
    # Print message to stdout (will be captured by Docker logs)
    print(json.dumps(message))
    
    # Simulate some work
    print("Starting mock scraping task...")
    for i in range(5):
        print(f"Scraping progress: {i*20}%")
        time.sleep(1)
    
    print("Scraping completed successfully!")
    
    # Return final result
    result = {
        "status": "success",
        "container_id": container_id,
        "manager_id": manager_id,
        "spawn_time": spawn_time,
        "completion_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    print(json.dumps(result))
    return 0

if __name__ == "__main__":
    sys.exit(main())
