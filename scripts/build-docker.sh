#!/bin/bash
# Build Docker images for different environments
# Usage: ./scripts/build-docker.sh [local|k8s|all]

set -e

IMAGE_NAME="jaysuzi5/jretirewise"
VERSION="v1.0.0-otel"

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

build_local() {
    echo -e "${BLUE}Building local Mac image (ARM64)...${NC}"
    docker build -t "$IMAGE_NAME:local-arm64" -t "$IMAGE_NAME:local" .
    echo -e "${GREEN}✓ Local image built: $IMAGE_NAME:local${NC}"
}

build_k8s() {
    echo -e "${BLUE}Building Kubernetes image (Linux x86_64) and pushing to Docker Hub...${NC}"
    docker buildx build --platform linux/amd64 -t "$IMAGE_NAME:latest" -t "$IMAGE_NAME:$VERSION" --push .
    echo -e "${GREEN}✓ Kubernetes image built and pushed: $IMAGE_NAME:latest${NC}"
}

build_all() {
    build_local
    echo ""
    build_k8s
}

show_usage() {
    echo "Usage: $0 [local|k8s|all]"
    echo ""
    echo "Options:"
    echo "  local  - Build local Mac image (ARM64) for testing"
    echo "  k8s    - Build and push Kubernetes image (Linux x86_64) to Docker Hub"
    echo "  all    - Build both local and k8s images (default)"
    echo ""
    echo "Examples:"
    echo "  $0 local     # Build for local testing"
    echo "  $0 k8s       # Build and deploy to Kubernetes"
    echo "  $0 all       # Build both"
}

# Default to 'all' if no argument provided
TARGET="${1:-all}"

case "$TARGET" in
    local)
        build_local
        ;;
    k8s)
        build_k8s
        ;;
    all)
        build_all
        ;;
    *)
        echo "Error: Invalid option '$TARGET'"
        echo ""
        show_usage
        exit 1
        ;;
esac
