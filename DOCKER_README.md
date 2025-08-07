# Docker Setup for Tenant Electricity Bill Calculator

This document explains how to run the Tenant Electricity Bill Calculator using Docker and Docker Compose.

## Quick Start

### Using Docker Compose (Recommended)

1. **Run in production mode:**
   ```bash
   docker-compose up -d
   ```
   The application will be available at `http://localhost:5000`

2. **Run in development mode:**
   ```bash
   docker-compose --profile dev up -d tenant-electricity-calculator-dev
   ```
   The application will be available at `http://localhost:5001` with live reload enabled.

### Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t tenant-electricity-calculator .
   ```

2. **Run the container:**
   ```bash
   docker run -d -p 5000:5000 \
     -v $(pwd)/uploads:/app/uploads \
     -v $(pwd)/outputs:/app/outputs \
     -v $(pwd)/app_config.json:/app/app_config.json \
     -v $(pwd)/transactions.csv:/app/transactions.csv \
     --name tenant-electricity-calculator \
     tenant-electricity-calculator
   ```

## Data Persistence

The application uses several directories and files that are ignored by Git but are essential for operation:

- **`uploads/`** - Stores uploaded CSV files
- **`outputs/`** - Stores generated PDF reports
- **`app_config.json`** - Stores application configuration (Git settings, preferences)
- **`__pycache__/`** - Python bytecode cache

### Docker Volumes

The Docker setup automatically handles these directories:

1. **Dockerfile** creates the necessary directories (`uploads/`, `outputs/`)
2. **docker-compose.yml** mounts these as volumes to persist data between container restarts
3. **Volume mounts ensure**:
   - CSV files uploaded through the web interface persist
   - Generated PDF reports are accessible on the host
   - Configuration settings are maintained
   - Transaction data is preserved

## GitHub Container Registry

The repository includes a GitHub Actions workflow that automatically builds and publishes Docker images to GitHub Container Registry when you push to the main branch.

### Using Pre-built Images

You can use the pre-built images from GitHub Container Registry:

```bash
# Pull the latest image
docker pull ghcr.io/your-username/tenant-electricity-bill-calculator:main

# Run using the pre-built image
docker run -d -p 5000:5000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/app_config.json:/app/app_config.json \
  -v $(pwd)/transactions.csv:/app/transactions.csv \
  ghcr.io/your-username/tenant-electricity-bill-calculator:main
```

### Automatic Builds

The GitHub Actions workflow:
- Builds multi-platform images (AMD64 and ARM64)
- Publishes to GitHub Container Registry on push to main/master
- Creates tagged versions for Git tags (e.g., v1.0.0)
- Includes proper metadata and attestations

## Environment Variables

The following environment variables can be configured:

- `FLASK_ENV` - Set to `development` or `production` (default: `production`)
- `FLASK_APP` - Application entry point (default: `app.py`)
- `FLASK_DEBUG` - Enable debug mode (default: `0` in production)
- `PYTHONUNBUFFERED` - Ensure Python output is not buffered (default: `1`)

## Health Checks

The container includes health checks that verify the application is responding on port 5000. The health check runs every 30 seconds with a 10-second timeout.

## Security

- The application runs as a non-root user (`app`)
- Only necessary system packages are installed
- Multi-stage builds could be implemented for further size reduction

## Troubleshooting

1. **Port already in use**: Change the host port in docker-compose.yml or the docker run command
2. **Permission issues**: Ensure the mounted directories have appropriate permissions
3. **Container won't start**: Check logs with `docker logs tenant-electricity-calculator`
4. **Health check failing**: Verify the application is starting correctly and port 5000 is accessible

## Development

For development with live code reload:

```bash
# Start development environment
docker-compose --profile dev up tenant-electricity-calculator-dev

# View logs
docker-compose logs -f tenant-electricity-calculator-dev

# Stop development environment
docker-compose --profile dev down
```

The development setup mounts the entire project directory for live code changes.