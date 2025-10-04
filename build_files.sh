#!/bin/bash

# Build script for Vercel deployment
echo "BUILD START"

# Install dependencies
python3.9 -m pip install -r requirements.txt

# Collect static files
python3.9 manage.py collectstatic --noinput --clear

# Copy static files to build directory
cp -r staticfiles/* .

echo "BUILD END"