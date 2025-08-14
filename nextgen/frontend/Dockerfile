# Stage 1: Build the SvelteKit app
FROM node:18-alpine AS builder

WORKDIR /app

# Copy dependency files
COPY package.json ./
# Assuming npm, if using yarn or pnpm, this would be different
COPY package.json package-lock.json* ./
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:stable-alpine

# Copy the built app from the builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy the nginx configuration
# I will create this file next
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80
