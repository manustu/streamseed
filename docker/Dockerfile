# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Verify installed packages
RUN pip list

# Copy the current directory contents into the container at /app
COPY . /app

# Set environment variable for PATH
ENV PATH="/root/.local/bin:$PATH"

# Make port 80 available to the world outside this container
EXPOSE 80

# Run the FastAPI application using Uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "80"]
