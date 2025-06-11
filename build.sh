#!/bin/bash
# build.sh

set -e  # Exit on error

# Optional: Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build the project using hatch
hatch build