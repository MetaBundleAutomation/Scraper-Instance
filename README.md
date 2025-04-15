# Scraper-Instance

Lightweight container that runs a mock scrape task and sends back a success message.

## Features

- Simulates a scraping job
- Outputs JSON response with container metadata
- Designed to be launched by Scraper-Manager

## How It Works

When launched, the Scraper-Instance:
1. Logs "I'm alive" message
2. Gets environment variables passed from the manager
3. Simulates a scraping task with progress updates
4. Returns a JSON response with:
   - Container ID
   - Manager ID
   - Spawn time
   - Completion time

## Development

### Requirements

- Python 3.9+
- Docker (for deployment)

### Testing Locally

```
python main.py
```

## Docker Deployment

```
docker build -t scraper-instance:latest .
docker run -e MANAGER_ID=test -e SPAWN_TIME="2025-04-15 18:00:00" scraper-instance:latest
```
