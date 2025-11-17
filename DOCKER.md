# Docker Setup for Analyst1

This guide explains how to run Analyst1 in a Docker container.

## Prerequisites

- Docker installed and running
- Docker Compose (optional, for easier management)

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and run the container**
   ```bash
   docker-compose up -d
   ```

2. **View logs**
   ```bash
   docker-compose logs -f
   ```

3. **Stop the container**
   ```bash
   docker-compose down
   ```

### Using Docker directly

1. **Build the image**
   ```bash
   docker build -t analyst1 .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     --name analyst1 \
     -p 5001:5001 \
     analyst1
   ```

3. **View logs**
   ```bash
   docker logs -f analyst1
   ```

4. **Stop the container**
   ```bash
   docker stop analyst1
   docker rm analyst1
   ```

## Environment Variables

Optional environment variables (defaults are set in the Dockerfile):

- `PORT`: Port to run on (default: 5001)
- `HOST`: Host to bind to (default: 0.0.0.0)
- `FLASK_ENV`: Set to "production" to disable debug mode

Example:
```bash
docker run -d -p 5001:5001 -e PORT=8080 analyst1
```

## Accessing the Application

Once running, access the application at:
- http://localhost:5001

## Features

- **Tesseract OCR**: Pre-installed and configured
- **No local dependencies**: Everything runs in the container
- **Health checks**: Container health is monitored automatically
- **Auto-restart**: Container restarts automatically if it crashes

## Troubleshooting

### Container won't start
- Check logs: `docker logs analyst1`
- Ensure port 5001 is not already in use
- Try: `docker-compose down` then `docker-compose up --build`

### OCR not working
- Tesseract is pre-installed in the container
- If issues persist, check logs for Tesseract errors

### Permission issues
- The container runs with appropriate permissions
- No volume mounts are required (stateless application)

## Building for Production

For production deployments:

1. Use a specific tag:
   ```bash
   docker build -t analyst1:v1.0.0 .
   ```

2. Push to a registry:
   ```bash
   docker tag analyst1:v1.0.0 your-registry/analyst1:v1.0.0
   docker push your-registry/analyst1:v1.0.0
   ```

