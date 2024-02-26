# Use Debian 12 (Bookworm) as the base image
FROM ubuntu:22.04

# Set the working directory in the container
WORKDIR /usr/src/app

# Install required system packages and Python 3
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv poppler-utils tesseract-ocr && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the pdf-to-template directory contents into the container at /usr/src/app
COPY pdf-to-template/ .

# Create a Python virtual environment and activate it
RUN python3 -m venv venv
ENV PATH="/usr/src/app/venv/bin:$PATH"

# Install Python dependencies in the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
#EXPOSE 800

# Command to run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8001", "app:app", "--worker-class", "gevent", "--timeout", "90"]

