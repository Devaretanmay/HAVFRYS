#!/usr/bin/env bash
set -euo pipefail

echo "================================================================================"
echo "          KOYOTE HERMETIC CONTAINER REPLAY RUNNER"
echo "================================================================================"

IMAGE_NAME="koyote-replay:latest"
docker build -t "$IMAGE_NAME" -f docker/Dockerfile.replay .

echo "[RUNNING] Executing ground-truth benchmark suite inside container..."
docker run --rm -it "$IMAGE_NAME"

echo "================================================================================"
echo "          CONTAINER BENCHMARK EXECUTION COMPLETED"
echo "================================================================================"
