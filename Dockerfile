# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install Nmap and other system dependencies
# procps provides utilities like ps, free, top - useful for debugging running containers.
# tini is a lightweight init system for containers, helps manage signal handling and zombie reaping.
RUN apt-get update && \
    apt-get install -y nmap procps tini && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
# This includes src/, nmap_parallel_scanner.py, web_ui/, etc.
# Ensure .dockerignore is used if there are files/dirs not to be copied (e.g. .git, __pycache__)
COPY . .
# For more fine-grained control, one could use:
# COPY src/ ./src/
# COPY web_ui/ ./web_ui/
# COPY nmap_parallel_scanner.py .
# COPY requirements.txt .
# (and any other necessary files/dirs like 'data' if it contains default assets)


# Expose the port the Flask app runs on (as defined in web_ui/app.py)
EXPOSE 5000

# Define the entry point for the container.
# Using tini as the executable to properly handle signals and reap zombie processes.
# Then, python runs the main CLI script.
# This allows users to pass arguments to nmap_parallel_scanner.py when using 'docker run'.
ENTRYPOINT ["/usr/bin/tini", "--", "python", "nmap_parallel_scanner.py"]

# Default command if no arguments are provided to 'docker run <image_name>'
# This will show the help message for the nmap_parallel_scanner.py script.
CMD ["--help"]
