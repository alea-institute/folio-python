#!/usr/bin/env bash
# This script is used to test a clean install and tests for
# the built wheel images.

# Build the wheel
poetry build

# Test 22.04
docker build -t folio-python-ubuntu2204-install -f docker/ubuntu2204-install/Dockerfile . \
  && \
  docker run folio-python-ubuntu2204-install:latest \
  && \
  docker build -t folio-python-ubuntu2404-install -f docker/ubuntu2404-install/Dockerfile . \
  && \
  docker run folio-python-ubuntu2404-install:latest
