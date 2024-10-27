#!/bin/bash

# Exit on any error
set -e

# Maximum number of retries
MAX_RETRIES=10

echo "Starting deployment process..."

# Remove all Docker images
echo "Cleaning up existing Docker images..."
docker images -a && docker rmi $(docker images -a -q) --force 2>/dev/null || true
docker images -a

# Build new Docker image
echo "Building Docker image..."
docker build -t lambda-sftp .

# Tag image for ECR
echo "Tagging Docker image..."
docker tag lambda-sftp:latest 482211574303.dkr.ecr.us-east-1.amazonaws.com/lambda-sftp:latest

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 482211574303.dkr.ecr.us-east-1.amazonaws.com

# Push image to ECR with retries
echo "Pushing image to ECR..."
for ((i=1; i<=MAX_RETRIES; i++)); do
    echo "Attempt $i of $MAX_RETRIES..."
    if docker push 482211574303.dkr.ecr.us-east-1.amazonaws.com/lambda-sftp:latest; then
        echo "Push successful!"
        break
    else
        if [ $i -eq $MAX_RETRIES ]; then
            echo "Failed to push after $MAX_RETRIES attempts"
            exit 1
        fi
        echo "Push failed, retrying in 10 seconds..."
        sleep 10
    fi
done

# Verify deployment
echo "Verifying deployment..."
docker manifest inspect 482211574303.dkr.ecr.us-east-1.amazonaws.com/lambda-sftp:latest

echo "Deployment completed successfully!"
