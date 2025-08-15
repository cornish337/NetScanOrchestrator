# Stage 1: Build the web UI client
FROM node:20 as client-build

WORKDIR /app/web_ui/client
COPY web_ui/client/package*.json ./
RUN npm ci
COPY web_ui/client/ ./
RUN npm run build

# Stage 2: Runtime environment
FROM python:3.11-slim

# Install system dependencies and clean up apt caches
RUN apt-get update \
    && apt-get install -y nmap procps tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Copy built client assets from the build stage
COPY --from=client-build /app/web_ui/client/dist ./web_ui/client/dist

EXPOSE 5000

ENTRYPOINT ["tini", "--"]
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
# Example production command using Gunicorn:
# CMD ["gunicorn", "-b", "0.0.0.0:5000", "web_ui.app:app"]

