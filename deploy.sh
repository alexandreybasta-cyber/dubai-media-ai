#!/bin/bash
# Auto-deploy script for Dubai Media AI
# Usage: 
#   First time: ./deploy.sh --setup
#   Auto-deploy (cron): ./deploy.sh
#
# Cron entry (every 60s): * * * * * /root/dubai-media/deploy.sh >> /var/log/dubai-media-deploy.log 2>&1

set -e

REPO_DIR="${REPO_DIR:-/root/dubai-media}"
REPO_URL="${REPO_URL:-https://github.com/alexandreybasta-cyber/dubai-media-ai.git}"
BRANCH="main"

cd "$REPO_DIR" 2>/dev/null || {
    echo "$(date): Repo not found at $REPO_DIR. Run with --setup first."
    exit 1
}

# Setup mode: clone repo and do initial deploy
if [ "$1" = "--setup" ]; then
    echo "$(date): Setting up Dubai Media AI deployment..."
    
    if [ ! -d "$REPO_DIR/.git" ]; then
        echo "$(date): Cloning repository..."
        git clone "$REPO_URL" "$REPO_DIR"
        cd "$REPO_DIR"
    fi
    
    # Create .env if it doesn't exist
    if [ ! -f .env ]; then
        echo "$(date): Creating .env from .env.example..."
        cp .env.example .env
        echo "⚠️  EDIT .env with your actual API keys before starting!"
        echo "    nano $REPO_DIR/.env"
        exit 0
    fi
    
    # Build and start
    echo "$(date): Building and starting services..."
    docker compose up -d --build
    echo "$(date): Setup complete! Services starting..."
    docker compose ps
    exit 0
fi

# Auto-deploy mode: check for new commits and redeploy if needed
CURRENT=$(git rev-parse HEAD)
git fetch origin "$BRANCH" --quiet

REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$CURRENT" = "$REMOTE" ]; then
    # No changes
    exit 0
fi

echo "$(date): New commits detected ($CURRENT -> $REMOTE). Deploying..."
git pull origin "$BRANCH" --quiet

# Rebuild and restart (only services that changed)
docker compose up -d --build --remove-orphans

echo "$(date): Deployment complete."
docker compose ps
