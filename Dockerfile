# Use an official Python image as the base
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY main.py /app/main.py

RUN chmod -R 755 /app

# Install ffmpeg and required Python packages
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir flask requests