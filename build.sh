#!/bin/bash

IMAGE_TAG="$(git describe --always --dirty)"
IMAGE="ramielrowe/darksky_10day:${IMAGE_TAG}"

docker build -t ${IMAGE} .

echo "Built Image: ${IMAGE}"
