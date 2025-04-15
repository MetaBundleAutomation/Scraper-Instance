import os
import json
import time
import sys
import requests
import subprocess
import logging

# Configure logging based on environment variable
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("scraper-instance")

# Get environment variables
MANAGER_URL = os.environ.get("MANAGER_URL", "http://scraper-manager:8000")

def main():
    """Main function that runs the scraper instance"""
    logger.info("Scraper instance starting up...")
    
    # Get environment variables
    hostname = os.environ.get("HOSTNAME", "unknown_container")
    
    # Manager is accessible via the Docker network
    logger.info(f"Connecting to manager at {MANAGER_URL}...")
    
    try:
        # Request identity and task
        logger.info(f"Requesting identity and task from manager at {MANAGER_URL}...")
        response = requests.post(
            f"{MANAGER_URL}/request_task",
            json={"hostname": hostname}
        )
        
        if response.status_code != 200:
            logger.error(f"Error requesting task: {response.status_code} - {response.text}")
            return 1
        
        # Parse the task data
        task_data = response.json()
        container_id = task_data.get("container_id")
        manager_id = task_data.get("manager_id")
        spawn_time = task_data.get("spawn_time")
        
        logger.info(f"Received identity: container_id={container_id}, manager_id={manager_id}, spawn_time={spawn_time}")
        
        # Create Hello World message
        hello_message = {
            "message": f"Hello World! I'm {container_id}, son of {manager_id}, spawned at {spawn_time}."
        }
        
        # Send Hello World message to manager
        hello_response = requests.post(
            f"{MANAGER_URL}/container/hello",
            json={
                "container_id": container_id,
                "message": hello_message["message"]
            }
        )
        
        if hello_response.status_code != 200:
            logger.error(f"Error sending hello message: {hello_response.status_code} - {hello_response.text}")
        else:
            logger.info("Hello message sent successfully")
        
        # Print message to stdout (will be captured by Docker logs)
        print(json.dumps(hello_message))
        
        # /// Here we would do the actual scraping work
        # /// But for now, we just use the Hello World message as our result
        
        # Prepare result (same as Hello World message)
        result = {
            "status": "success",
            "container_id": container_id,
            "manager_id": manager_id,
            "spawn_time": spawn_time,
            "completion_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "message": hello_message["message"]
        }
        
        # Send results back to manager with retry logic
        confirmation_received = False
        max_retries = 5
        retry_count = 0
        
        while not confirmation_received and retry_count < max_retries:
            try:
                logger.info(f"Sending results to manager (attempt {retry_count + 1}/{max_retries})...")
                response = requests.post(
                    f"{MANAGER_URL}/container/complete",
                    json={
                        "container_id": container_id,
                        "status": "success",
                        "result": result
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"Results sent successfully: {response.text}")
                    confirmation_data = response.json()
                    if confirmation_data.get("status") == "success":
                        confirmation_received = True
                        logger.info("Received confirmation from manager")
                    else:
                        logger.warning("Manager response did not confirm success, waiting to retry...")
                        time.sleep(1)
                        retry_count += 1
                else:
                    logger.error(f"Error sending results: {response.status_code} - {response.text}")
                    time.sleep(1)
                    retry_count += 1
            except Exception as e:
                logger.exception(f"Exception sending results: {e}")
                time.sleep(1)
                retry_count += 1
        
        if confirmation_received:
            logger.info("Results confirmed by manager, self-terminating...")
            
            # Use Docker API to remove the container
            try:
                # Connect to Docker socket
                socket_path = "/var/run/docker.sock"
                if os.path.exists(socket_path):
                    # Create a curl command to delete the container
                    delete_cmd = [
                        "curl", "-s", "--unix-socket", socket_path,
                        "-X", "DELETE",
                        f"http://localhost/v1.40/containers/{hostname}?force=true"
                    ]
                    
                    # Execute the command
                    logger.info(f"Removing container {hostname}...")
                    subprocess.run(delete_cmd, check=True)
                else:
                    logger.warning("Docker socket not found, container will need to be removed externally")
            except Exception as e:
                logger.exception(f"Error removing container: {e}")
                # Even if we can't remove the container, we still want to exit
            
            return 0
        else:
            logger.error("Failed to get confirmation from manager after maximum retries")
            return 1
            
    except Exception as e:
        logger.exception(f"Error in scraper instance: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
